import io
import pdfplumber
import json
import os
import json_repair # to correct malformed json returned from grok by adding symbols to close json format correctly
from dotenv import load_dotenv
#----------------
# Note:To make .env visible
#----------------
load_dotenv()
from openai import OpenAI
#----------------
# Note: llm client created
#----------------




client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)


def resume_reader(pdf_file):
    #use the bytes of the 
        raw_bytes=pdf_file.read()   #read() gives raw bytes
        resume_text=parse_resume_to_summary(raw_bytes)


        return resume_text
            
def parse_resume_to_text(file_bytes : bytes)->str:
    file_placeholder=io.BytesIO(file_bytes) #placeholder for that file in memory only, witout saving to laptop
    text=[]
    Max_Len=2500 #guard against huge/malformed PDFs blowing up token cost
    try:
        with pdfplumber.open(file_placeholder) as pdf:
            for page in pdf.pages:
                page_text=page.extract_text()

                if page_text:
                    text.append(page_text)


        #.join function to make a list into text
        full_text="\n".join(text).strip()
    except ValueError as e:
        return f"maybe full_text does not exist or pdf was a image, error : {str(e)}"    
    
    return full_text[:Max_Len]




RESUME_SYSTEM_PROMPT = """You are extracting structured information from a
resume's raw text. The text may have layout artifacts from PDF extraction
(broken lines, odd spacing) — work around that.
 
STRICT RULES:
- Only extract what is explicitly present in the text. Do not infer
  skills or experience that aren't stated.
- If a section (e.g. education, certifications) is missing entirely,
  return an empty list for it — do not guess.
- Keep skill names as the resume states them (don't normalize "Python3"
  to "Python" etc.) — normalization happens later in the pipeline, not here.
 
Respond ONLY with valid JSON matching this schema, no markdown fences:
 
{
  "name": string or null,
  "current_role": string or null,
  "total_experience_summary": string,
  "skills_listed": [string],
  "work_experience": [
    {"role": string, "company": string, "duration": string, "key_responsibilities": [string]}
  ],
  "projects_mentioned": [
    {"name": string, "description": string, "tech_used": [string]}
  ],
  "education": [
    {"degree": string, "institution": string, "year": string}
  ]
}
"""

def parse_resume_to_summary(file_bytes: bytes) -> dict:
    raw_text = parse_resume_to_text(file_bytes)
    
 
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": RESUME_SYSTEM_PROMPT},
            {"role": "user", "content": f"Resume text:\n\n{raw_text}"},
        ],
        temperature=0.1,  # near-zero — this is extraction, not reasoning
    )
 
    raw = response.choices[0].message.content
    
    try:
        return json.loads(raw)
        
    except json.JSONDecodeError:
        cleaned = raw.strip().strip("```json").strip("```").strip()
        return json.loads(cleaned)




#------------------------------------------------------------------------------

if __name__ == "__main__":
    import sys


    path_to_resume=sys.argv[1]
    with open(path_to_resume,"rb") as f:
         resume_bytes=f.read() #converts to raw bytes

    print(parse_resume_to_summary(resume_bytes))