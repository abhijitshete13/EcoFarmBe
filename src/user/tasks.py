
"""
All periodic tasks/Automated tasks/feature based related to User.
"""
import datetime
from django.conf import settings
from celery.task import periodic_task
from celery.schedules import crontab
from django.utils import  timezone
from core.celery import app
from user.models import (User,)
from core.utility import (send_async_user_approval_mail,)
#from knox.settings import knox_settings

#KNOXUSER_SERIALIZER = knox_settings.USER_SERIALIZER

def bypass_verifications_for_email(instance):
    """
    Bypass email,phone verifications for listed emails.
    'is_verified' flag refers to email verification.
    'is_phone_verified' flag refers to phone number verification.
    'is_approved' flag refers to  admin approval.
    """
    instance.is_verified = instance.is_phone_verified = instance.is_approved = True
    instance.approved_on = timezone.now()
    instance.approved_by = {'email':"connect@thrive-society.com(Automated-Bot)"}
    instance.save()
    send_async_user_approval_mail.delay(instance.id)


