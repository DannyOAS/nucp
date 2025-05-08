from django.contrib import admin
from .models import Appointment, Prescription, Message, MessageAttachment

# Register your models here
admin.site.register(Appointment)
admin.site.register(Prescription)
admin.site.register(Message)
admin.site.register(MessageAttachment)
