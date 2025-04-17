from django.contrib import admin
from .models import ContactMessage
from .models import BlogPost
from .models import Appointment, Prescription, Message

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created_at")
    search_fields = ("name", "email", "message")

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at", "updated_at")
    search_fields = ("title", "content")
    list_filter = ("created_at",)


admin.site.register(Appointment)
admin.site.register(Prescription)
admin.site.register(Message)
