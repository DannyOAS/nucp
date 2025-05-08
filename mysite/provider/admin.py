from django.contrib import admin
from provider.models import RecordingSession, ClinicalNote, DocumentTemplate, GeneratedDocument

# Register your models here
admin.site.register(RecordingSession)
admin.site.register(ClinicalNote)
admin.site.register(DocumentTemplate)
admin.site.register(GeneratedDocument)
