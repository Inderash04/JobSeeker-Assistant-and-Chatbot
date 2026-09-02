from django.urls import path
from .views import login_auth,home_view,chatUIPage,Analytics,query_bot_chat,read_profile,query_job_seeker,selectbot,jobseekerdetails,jobseekerChatUI
urlpatterns = [
    path('login/',login_auth.as_view()),
    path('query_bot_chat/',query_bot_chat.as_view()),
    path('read_profile/',read_profile.as_view()),
    path('query_job_seeker',query_job_seeker.as_view()),
    path('chat/',chatUIPage),
    path('botselection/',selectbot),
    path('analytics/',Analytics.as_view()),
    path('jobseekerdetails/',jobseekerdetails),
    path('jobseekerChatUI/',jobseekerChatUI),
    path('',home_view),
    
]
