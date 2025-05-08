# In provider/admin.py - Enhanced Provider admin

from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Provider, RecordingSession, ClinicalNote, DocumentTemplate, GeneratedDocument

class ProviderInline(admin.StackedInline):
    model = Provider
    can_delete = False
    verbose_name_plural = 'Provider Profile'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    inlines = (ProviderInline, )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_provider_specialty')
    list_select_related = ('provider_profile', )
    
    def get_provider_specialty(self, instance):
        return instance.provider_profile.specialty if hasattr(instance, 'provider_profile') else ''
    get_provider_specialty.short_description = 'Specialty'
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)

# Unregister the default UserAdmin and register our custom version
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Register Provider model directly as well
@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'specialty', 'license_number', 'is_active')
    search_fields = ('user__first_name', 'user__last_name', 'specialty', 'license_number')
    list_filter = ('is_active', 'specialty')
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = 'Name'

# Register other models
@admin.register(RecordingSession)
class RecordingSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'provider', 'start_time', 'transcription_status')
    list_filter = ('transcription_status', 'start_time')
    search_fields = ('provider__user__last_name', 'transcription_text')

@admin.register(ClinicalNote)
class ClinicalNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'provider', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('provider__user__last_name', 'provider_edited_text', 'ai_generated_text')

@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_type', 'is_active')
    list_filter = ('template_type', 'is_active', 'created_at')
    search_fields = ('name', 'description')

@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'template', 'patient', 'provider', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'template__template_type')
    search_fields = ('patient__first_name', 'patient__last_name', 'provider__user__last_name')
