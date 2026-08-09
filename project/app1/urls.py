from django.urls import path
from .views import login_auth,home_view,chatUIPage,Analytics,query_bot_chat,query_job_assitance
urlpatterns = [
    path('login/',login_auth.as_view()),
    path('query_bot_chat/',query_bot_chat.as_view()),
    path('query_job_assitance/',query_job_assitance.as_view()),
    path('chat/',chatUIPage),
    path('analytics/',Analytics.as_view()),
    path('',home_view),
    
]
