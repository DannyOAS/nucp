# In common/admin.py
from django.contrib import admin
from .models import Prescription, Appointment, Message

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'dose', 'patient', 'doctor', 'status', 'created_at')
    list_filter = ('status', 'doctor')
    search_fields = ('name', 'patient__first_name', 'patient__last_name')
    date_hierarchy = 'created_at'

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'time', 'type', 'status')
    list_filter = ('status', 'type', 'doctor')
    search_fields = ('patient__first_name', 'patient__last_name')
    date_hierarchy = 'time'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'sender', 'recipient', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('subject', 'content', 'sender__first_name', 'sender__last_name', 'recipient__first_name', 'recipient__last_name')
    date_hierarchy = 'created_at'
