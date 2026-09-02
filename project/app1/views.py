from django.shortcuts import render
from rest_framework.views import APIView,Response
from rest_framework import status

from .models import *
from django.contrib.auth import authenticate,login
from django.contrib.auth.models import User #. <- important
from .serializer import *
from .models import *

import json
from django.core.cache import cache # <----here cache django redis cache
from .redis_client import redis_client # <----- here is redis server only

#token related
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated


from django.shortcuts import render
#calling the chatbot login template
def home_view(request):
    return render(request, 'login.html')

#calling the chatbot UI template
def chatUIPage(request):
    return render(request,'chatUI.html')

def selectbot(request):
    return render(request,'selectbot.html')

def jobseekerdetails(request):
    return render(request,'jobseekerUI.html')

def jobseekerChatUI(request):
    return render(request,'jobseekerChatUI.html')

#CSRF authentication bypass
from rest_framework.authentication import SessionAuthentication

class SafeSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # skip CSRF check


class login_auth(APIView):        
    authentication_classes = [SafeSessionAuthentication] #csrf

    def post(self,request):
        ret={}
        message=request.data
        
        serializer=LoginApiSerializer(data=message)

        if serializer.is_valid():
            name=serializer.validated_data.get("name")
            phone=serializer.validated_data.get("phone")
            
            obj=User.objects.filter(username=name).first()
            #if first time logging in
            if not obj:
                #first timer logging in->we are checking if username entered does not already 
                # exist as username in auth_user is unique

                # **imporant**
                o1=User.objects.create_user(username=name,password=phone) #create auth_user table entry
                UserProfile.objects.create(user=o1,name=name,phone=phone) #add userprofiel table entry too
                ret["username old/new"]=["new"]
            else:
                ret["username old/new"]=["old"]
                ret["error_msg"]=["checking existing username"]

            #if not first time-> he would have an auth_user table entry->directly authenticate
            #authenticate

            user=authenticate(username=name,password=phone)
            if user is not None:
                #token generation if the user exists in auth_user table, token created in auth_token
                token,created=Token.objects.get_or_create(user=user)
                ret["token"]=str(token)
                ret["status"]=["logged in"]
                ret["status_code"]=200
                return Response(ret)
                
            if user is None:
                ret["error_msg"]=["Wrong password/Invalid"]
                ret["status_code"]=401
                return Response(ret)
        
        else:
            #invalid entry or mobile number exceeding 10 digits
            return Response({"error":"invalid entry or mobile number exceeding 10 digits"})

        return Response({"error":"invalid credentials"})
            
from .llm import LLM_bot
from .models import *

#if the chosen format is button 1 -> go to job search bot

#assume from front end---->
#const formData = new FormData();
#formData.append("pdf", file);
#formData.append("message", "Analyze this PDF");

#and in body : formdata instead of body : JSON.stringify({"message":"hi from bot"})

#bot : please share the pdf resume
#user : shared here
#bot : please share the git hub username
#user : inderashsahu0111
MAX_UPLOAD_SIZE_MB=5
from .script_resume_parser import resume_reader
from .script_readGithub import summarize_profile

class read_profile(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request):
        pdf_file=request.FILES.get("pdf",None)
        github_username=request.data.get("github_username")
        option = request.data.get("option")  # "Gap Analysis" | "Live Listings" | "Compare Resume"
        location=request.data.get("location")
        job_title=request.data.get("job_title")
        
        #-------------------------------------------------
        # BLOCK 1: Resume handling — independent
        #-------------------------------------------------
        resume_summary=None
        if pdf_file is not None:
            #if pdf file is provided
            if pdf_file is None:
                return Response({"error":"no file received.Expected resume file "},status.HTTP_400_BAD_REQUEST)

            if not pdf_file.name.lower().endswith(".pdf"):
                return Response({"error":"Not a pdf file.Expected file is .pdf"},status.HTTP_400_BAD_REQUEST)

            if pdf_file.size > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                return Response({"error": f"File too large. Max {MAX_UPLOAD_SIZE_MB}MB."},status=status.HTTP_400_BAD_REQUEST,)

            try:
                resume_summary=resume_reader(pdf_file)     #send the whole resume file to be read   
                # Create a new Resume everytime it is stored.
                Resume.objects.create(user=UserProfile.objects.filter(user=request.user).first(),resume_summary=resume_summary)
            except ValueError as e:
                return Response({"error":f"{str(e)}"},status.HTTP_422_UNPROCESSABLE_ENTITY) 
            except Exception as e:
                return Response({"error":f"error is {str(e)}"},status.HTTP_400_BAD_REQUEST)
            
        #-------------------------------------------------
        # BLOCK 2: GitHub handling — independent, optional 
        #-------------------------------------------------
        github_summary=None
        if github_username:

            #enter the github summary into the existing model obj, if doesn't exist then make one and save
            obj,created=Resume.objects.get_or_create(user=UserProfile.objects.get(user=request.user),github_username=github_username)
            github_summary=summarize_profile(github_username)
            obj.github_summary=github_summary
            obj.save()
        
        #-------------------------------------------------
        # BLOCK 3: None is given
        #-------------------------------------------------
        if resume_summary is None and github_summary is None:
            return Response(
                {"error": "Provide at least a resume or a GitHub username."},
                status=status.HTTP_400_BAD_REQUEST,
            )


        return Response({"message":"passed through read_profile api"},status.HTTP_200_OK)


        
#         #-------------------------------------------------
#         # BLOCK 4: Option based Resume and GitHub handling 
#         #-------------------------------------------------
#         if option == "Gap Analysis":
#             user_profile=UserProfile.objects.get(user=request.user).first()
#             return self._handle_analysis(user_profile, resume_summary)
        
#         elif option == "Live listings":
#             return self._handle_listings(resume_summary, github_summary)

#         elif option == "Compare Resume":
#             return self._handle_compare(resume_summary, github_summary)

#         else:
#             return Response(
#                 {"error": "Invalid or missing 'option'. Gap Analysis | Live listings | Compare Resume."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
# #-------------------------------------------------
# # To work on tomorrow
# #-------------------------------------------------
#     def _handle_analysis(self, user_profile, resume_summary):
#         previous_resumes = Resume.objects.filter(user=user_profile).order_by("-uploaded_at")[1:6]
#         # TODO: build actual comparison logic against previous_resumes
#         return Response({"comparison_summary": "placeholder — compare logic goes here"})
 
#     def _handle_listings(self, resume_summary, github_summary):
#         # TODO: call job_market_tool.search_india_jobs() using signal
#         # extracted from resume_summary/github_summary as the query
#         return Response({"jobs": []})
 
#     def _handle_compare(self, resume_summary, github_summary):
#         # TODO: combine resume + github + live listings, rank matches
#         return Response({"matches": []})

# #-------------------------------------------------
# # To work on tomorrow
# #-------------------------------------------------





#-------------------------------------------------
#Connecting mcp and chat step 1
#-------------------------------------------------
from .llm import chat_with_tools

class query_job_seeker(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
    #redis based daily message limit
        count_key=f"daily limit:{request.user.id}"
        count=redis_client.get(count_key)

        if count is None:
            redis_client.set(count_key,1)
            redis_client.expire(count_key,86400)
        else:
            count=int(count)
            if count > 5:
                return Response({"error": "Message limit reached for today."},status=status.HTTP_429_TOO_MANY_REQUESTS)

            else:
                redis_client.incr(count_key)
        

        try:
            data=request.data
            user_message=data.get("message")
            if not user_message:
                return Response({"error":"Message is required"},status=status.HTTP_400_BAD_REQUEST)
            bot_reply=chat_with_tools(request, user_message)
        except Exception as e:
            return Response({"error":f"error message is {str(e)}"},status=status.HTTP_404_NOT_FOUND)

        return Response({"bot_reply":bot_reply},status=status.HTTP_200_OK)



#if the chosen format is button 2 -> go to usual bot chat
class query_bot_chat(APIView):
     #TO MAKE AUTHENTICATED
    #authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self,request):
        ret={}
        count_key=f"daily limit:{request.user.id}"
#------------------------------------------------------------
    #redis based daily message limit

        count=redis_client.get(count_key)
        if count is None:
            redis_client.set(count_key,1)
            redis_client.expire(count_key,86400)
        else:
            count=int(count)
            if count > 5:
                return Response({"message": "Message limit reached for today."},
                status=status.HTTP_429_TOO_MANY_REQUESTS)
            else:
                redis_client.incr(count_key)
#------------------------------------------------------------
        try:
            data=request.data
            user_message=data.get("message")
            message=user_llm_interaction("user",user_message,request)
            #return_obj=LLM_bot(message)
            ret["status_code"]=200
            ret["bot message"]=message
            return Response({"response":ret})
        except Exception as e:
            ret["status_code"]=400
            ret["error"]=str(e)
            return Response({"response":ret})




import time 
from django.utils import timezone
from datetime import timedelta

#sits between bot and query api(or frontend)
    #takes in message and user details
    #send back bot message

def user_llm_interaction(label,message,request):

    try:
        username=request.user.username #user name taken from login auth
        user_profile_obj=UserProfile.objects.filter(user__username=username).first()
        #save the messag from user to message history
        messages=update_redis_cache("user",message,request)

        bot_data=LLM_bot(messages)
        bot_message=bot_data.get("bot_message")
#------------------------------------------------------------------------
#updating GROK analytics data 

        #total messages
        user_profile_obj.total_messages += 1
        #total tokens
        user_profile_obj.total_tokens += bot_data.get("total_tokens")
        #average response time
        elapsed=bot_data.get("elapsed_time")
        user_profile_obj.avg_response_time=(user_profile_obj.avg_response_time * user_profile_obj.total_messages + elapsed)/(user_profile_obj.total_messages + 1)

        
        #save the total sessions
        user_profile_obj.total_sessions=ChatSession.objects.filter(user__user__username=username).count()
        user_profile_obj.save()
        

#------------------------------------------------------------------------
        
        messages=update_redis_cache("bot",bot_message,request)

#----------------------------------------------------------------     
        #add to sessions table

        #if no active:
        #   create a new session for that user
        #else(active session):
        #   check the activity condition(after 30 mins of no activity)
        #       if inactive:
        #           set end_sesion time
        #           turn is_active=False 
        
        now=timezone.now()
        session_obj=ChatSession.objects.filter(user=user_profile_obj,is_active=True).first()
        


        if session_obj is None: # if no session 
            session_obj=ChatSession.objects.create(user=user_profile_obj,last_active=now) # return new object to session
            #update a chat session for dashboard analytcis anytime a chat session is created
            user_profile_obj.total_sessions+=1
            user_profile_obj.save(update_fields=["total_sessions"])

        elif session_obj:       #if already running session
            #to check if session is stale now-> if so create a new session else just skip and go on with open session_obj defined above
            #next line runs only if session is to be closed now 
            if now-session_obj.last_active>timedelta(minutes=30): #if time to expire-> close this session and give new session
                session_obj.is_active=False
                session_obj.ended_at=timezone.now()
                session_obj.save(update_fields=["is_active","ended_at"])
                session_obj = ChatSession.objects.create(user=user_profile_obj,last_active=now)
                #update a chat session for dashboard analytcis anytime a chat session is created
                user_profile_obj.total_sessions+=1
                user_profile_obj.save(update_fields=["total_sessions"])
        
        
            
                
#----------------------------------------------------------------            
        #save the messages from user to messagehistory under this session
        message_history.objects.create(session=session_obj,user=user_profile_obj,sender="user",username=request.user.username,message=message)
        
        #save the messages from bot to messagehistory under this session
        message_history.objects.create(session=session_obj,user=user_profile_obj,sender="bot",message=bot_message)
        #update the last_active
        session_obj.last_active=now
        session_obj.save(update_fields=["last_active"])
        #return the lllm fetched answer
        return bot_message 
    except Exception as e:
        return f"error is : {str(e)}"
#needs to be fixed for production



def update_redis_cache(label,message,request):
      #FLOW
        #use redis memory to send to llm last 10 msgs
        #call llm 
        #add to redis + memory

        cache_key_str=f"user_data:{request.user.id}"

        #data=cache.get_or_set(cache_key_str,lambda:{"recent_messages":[],"daily_msg_count":0})
        #enter new data to redis
        #storing a dictionary as json because redis can't store dict, it can store string, list etc.

        redis_client.lpush(cache_key_str,json.dumps({"role":"user","content":message}))

        #fetch the last 10 messages from redis list and convert back to python dict

        messages=redis_client.lrange(cache_key_str,0,-1)
        dict_messages=[json.loads(i) for i in messages]
        dict_messages=reversed(dict_messages)
        
        #trim the redis cache if total messages > 10
        if redis_client.llen(cache_key_str)>10:
            redis_client.ltrim(cache_key_str,-10,-1)

        return dict_messages

class Analytics(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        try:
            user=request.user.username
            user_obj=UserProfile.objects.filter(user__username=user).first()
            serializer=AnalyticsSerializer(instance=user_obj)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error from Analtics api:":str(e)})


