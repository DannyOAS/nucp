# provider/admin.py - Complete and corrected version

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django import forms
import ldap

from .models import Provider, RecordingSession, ClinicalNote, DocumentTemplate, GeneratedDocument
from common.utils.ldap_client import LDAPClient

# Enhanced Provider form with LDAP password setting
class ProviderAdminForm(forms.ModelForm):
    """Custom form for Provider admin to include LDAP password setting."""
    ldap_password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        help_text="Set this to create or update the provider's LDAP password."
    )
    
    class Meta:
        model = Provider
        fields = '__all__'

# Provider admin as inline for User admin
class ProviderInline(admin.StackedInline):
    model = Provider
    can_delete = False
    verbose_name_plural = 'Provider Profile'
    fk_name = 'user'
    form = ProviderAdminForm  # Use the enhanced form

# Custom User admin with Provider inline
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
    
    def save_formset(self, request, form, formset, change):
        """Override save_formset to handle LDAP password for inline Provider."""
        instances = formset.save()
        
        # Look for Provider instances and handle LDAP password
        for instance in instances:
            if isinstance(instance, Provider):
                # Find the form with ldap_password
                for form in formset.forms:
                    if hasattr(form, 'cleaned_data') and 'ldap_password' in form.cleaned_data:
                        ldap_password = form.cleaned_data.get('ldap_password')
                        if ldap_password:
                            self._update_ldap_password(request, instance, ldap_password)
                            break
    
    def _update_ldap_password(self, request, provider, ldap_password):
        """Update LDAP password for a provider."""
        ldap_client = LDAPClient()
        if ldap_client.connect():
            # Check if user exists
            username = provider.user.username
            if ldap_client.user_exists(username):
                # Update password
                password_hash = ldap_client.generate_password_hash(ldap_password)
                try:
                    user_dn = f'uid={username},ou=people,dc=isnord,dc=ca'
                    ldap_client.conn.modify_s(
                        user_dn,
                        [(ldap.MOD_REPLACE, 'userPassword', password_hash.encode('utf-8'))]
                    )
                    self.message_user(request, f"LDAP password updated for {username}")
                except Exception as e:
                    self.message_user(request, f"Error updating LDAP password: {e}", level='ERROR')
            else:
                self.message_user(
                    request, 
                    f"User {username} doesn't exist in LDAP yet. They will be created when saved.",
                    level='WARNING'
                )
            ldap_client.disconnect()

# Standalone Provider admin
@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    form = ProviderAdminForm
    list_display = ('get_full_name', 'specialty', 'license_number', 'is_active')
    search_fields = ('user__first_name', 'user__last_name', 'specialty', 'license_number')
    list_filter = ('is_active', 'specialty')
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}" if obj.user else ""
    get_full_name.short_description = 'Name'
    
    def save_model(self, request, obj, form, change):
        """Override save_model to handle LDAP password."""
        super().save_model(request, obj, form, change)
        
        # Check if password was provided
        ldap_password = form.cleaned_data.get('ldap_password')
        if ldap_password:
            self._update_ldap_password(request, obj, ldap_password)
    
    def _update_ldap_password(self, request, provider, ldap_password):
        """Update LDAP password for a provider."""
        ldap_client = LDAPClient()
        if ldap_client.connect():
            # Check if user exists
            username = provider.user.username
            if ldap_client.user_exists(username):
                # Update password
                password_hash = ldap_client.generate_password_hash(ldap_password)
                try:
                    user_dn = f'uid={username},ou=people,dc=isnord,dc=ca'
                    ldap_client.conn.modify_s(
                        user_dn,
                        [(ldap.MOD_REPLACE, 'userPassword', password_hash.encode('utf-8'))]
                    )
                    self.message_user(request, f"LDAP password updated for {username}")
                except Exception as e:
                    self.message_user(request, f"Error updating LDAP password: {e}", level='ERROR')
            else:
                self.message_user(
                    request, 
                    f"User {username} doesn't exist in LDAP yet. They will be created when saved.",
                    level='WARNING'
                )
            ldap_client.disconnect()

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

# Unregister the default UserAdmin and register our custom version
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
