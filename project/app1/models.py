from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    name=models.CharField(max_length=30)
    phone=models.CharField(max_length=15)
#--------------------------------------------------------------------------------
#since default is 0, we don't need to fill in all parameters while creating an instance of this model.
    total_messages = models.IntegerField(default=0) #check
    total_sessions = models.IntegerField(default=0)#check
    total_tokens = models.IntegerField(default=0)#check
    total_cost = models.FloatField(default=0)
    cache_hits = models.IntegerField(default=0)
    cache_misses = models.IntegerField(default=0)
    avg_response_time = models.FloatField(default=0)#check
    
    def __str__(self):
        return self.user.username
    
#--------------------------------------------------------------------------------
#--------------------------------------------------------------------------------

class ChatSession(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_active=models.DateTimeField(auto_now=True)
   
    def __str__(self):
        return self.user.user.username
#--------------------------------------------------------------------------------


class message_history(models.Model):
    session = models.ForeignKey(
    ChatSession,
    on_delete=models.CASCADE,
    null=True,
    blank=True,
    related_name="messages")
    user=models.ForeignKey(UserProfile,on_delete=models.CASCADE)
    username=models.CharField(max_length=200,null=True,blank=True)
    sender=models.CharField(max_length=30)
    message=models.CharField(max_length=200)
    timestamp=models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.user.user.username
from django.utils import timezone

def generate_resume_name():
    return f"resume-{timezone.now().strftime("%Y%m%d_%H%M%S_%f")}"

class Resume(models.Model):
    user=models.ForeignKey(UserProfile,on_delete=models.CASCADE)
    resume_version=models.CharField(max_length=255,unique=True,default=generate_resume_name)
    resume_summary = models.TextField(null=True)
    github_username=models.CharField(max_length=200,null=True)
    github_summary=models.TextField(null=True)


