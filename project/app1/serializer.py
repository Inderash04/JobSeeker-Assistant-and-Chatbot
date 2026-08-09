from rest_framework import serializers
from .models import * 

class LoginApiSerializer(serializers.Serializer):
    name=serializers.CharField()
    phone=serializers.CharField()

class modelserializer(serializers.ModelSerializer):
    class Meta:
        model=UserProfile
        fields=["name","phone"]

class AnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model=UserProfile
        fields=["total_messages","total_sessions","total_tokens","avg_response_time"]