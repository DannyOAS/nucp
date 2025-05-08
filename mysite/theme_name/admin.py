from django.contrib import admin
from .models import ContactMessage, PatientRegistration, DemoRequest, BlogPost


class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created_at")
    search_fields = ("name", "email", "message")


class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at", "updated_at")
    search_fields = ("title", "content")
    list_filter = ("created_at",)

@admin.register(PatientRegistration)
class PatientRegistrationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'primary_phone', 'date_of_birth', 'provider')
    list_filter = ('provider', 'created_at', 'virtual_care_consent', 'ehr_consent')
    search_fields = ('first_name', 'last_name', 'email', 'primary_phone', 'ohip_number')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'email', 'primary_phone', 'alternate_phone', 'address')
        }),
        ('Medical Information', {
            'fields': ('ohip_number', 'current_medications', 'allergies', 'pharmacy_details')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_alternate_phone')
        }),
        ('Consents', {
            'fields': ('virtual_care_consent', 'ehr_consent')
        }),
        ('Provider Assignment', {
            'fields': ('provider',)
        }),
    )
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Name'

admin.site.register(ContactMessage)
admin.site.register(DemoRequest)
admin.site.register(BlogPost)
