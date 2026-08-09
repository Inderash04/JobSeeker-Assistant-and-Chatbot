from django.contrib import admin
from .models import UserProfile, message_history,ChatSession,Resume
# Register your models here.

admin.site.register(UserProfile)
admin.site.register(message_history)
admin.site.register(ChatSession)
admin.site.register(Resume)