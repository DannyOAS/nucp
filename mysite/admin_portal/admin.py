from django.contrib import admin
from .models import AIModelConfig, AIUsageLog

# Register your models here
admin.site.register(AIModelConfig)
admin.site.register(AIUsageLog)
