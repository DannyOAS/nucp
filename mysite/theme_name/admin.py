from django.contrib import admin
from .models import ContactMessage, PatientRegistration, DemoRequest, BlogPost


class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created_at")
    search_fields = ("name", "email", "message")


class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at", "updated_at")
    search_fields = ("title", "content")
    list_filter = ("created_at",)


admin.site.register(ContactMessage)
admin.site.register(PatientRegistration)
admin.site.register(DemoRequest)
admin.site.register(BlogPost)
