from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from common.services import AIConfigurationService
from admin_portal.models import AIModelConfig

def ai_config_dashboard(request):
    """AI configuration dashboard view"""
    # Get AI configuration data
    model_configs = AIModelConfig.objects.all().order_by('model_type', '-is_active')
    
    context = {
        'model_configs': model_configs,
        'active_section': 'ai_config',
        'admin_name': 'Admin'
    }
    
    return render(request, "custom_admin/ai_dashboard.html", context)

def edit_model_config(request, config_id):
    """Edit AI model configuration"""
    model_config = get_object_or_404(AIModelConfig, id=config_id)
    
    if request.method == 'POST':
        # Process form submission
        # In a real implementation, this would use a form class
        model_config.name = request.POST.get('name')
        model_config.api_endpoint = request.POST.get('api_endpoint')
        model_config.configuration_data = request.POST.get('configuration_data')
        model_config.is_active = 'is_active' in request.POST
        model_config.save()
        
        messages.success(request, f"Model configuration '{model_config.name}' updated successfully.")
        return redirect('ai_config_dashboard')
    
    context = {
        'model_config': model_config,
        'active_section': 'ai_config',
        'admin_name': 'Admin'
    }
    
    return render(request, "admin/edit_model_config.html", context)
