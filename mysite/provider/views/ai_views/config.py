# provider/views/ai_views/config.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
import logging
import requests

from admin_portal.services import AIConfigurationService
from admin_portal.models import AIModelConfig
from provider.utils import get_current_provider

logger = logging.getLogger(__name__)

@login_required
@user_passes_test(lambda u: u.is_staff)  # Only staff can access AI config
def ai_config_dashboard(request):
    """AI configuration dashboard view with authenticated staff user"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    # Get AI configuration data
    try:
        model_configs = AIModelConfig.objects.all().order_by('model_type', '-is_active')
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri('/api/admin/ai-models/')
        # response = requests.get(api_url)
        # if response.status_code == 200:
        #     model_configs = response.json()
        # else:
        #     messages.error(request, "Error retrieving AI model configurations.")
        #     model_configs = []
    except Exception as e:
        logger.error(f"Error retrieving AI model configurations: {str(e)}")
        messages.error(request, "Error retrieving AI model configurations.")
        model_configs = []
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'model_configs': model_configs,
        'active_section': 'ai_config',
    }
    
    return render(request, "provider/ai_views/ai_dashboard.html", context)

@login_required
@user_passes_test(lambda u: u.is_staff)  # Only staff can access AI config
def edit_model_config(request, config_id):
    """Edit AI model configuration with authenticated staff user"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        model_config = get_object_or_404(AIModelConfig, id=config_id)
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri(f'/api/admin/ai-models/{config_id}/')
        # response = requests.get(api_url)
        # if response.status_code == 200:
        #     model_config = response.json()
        # else:
        #     messages.error(request, "Error retrieving AI model configuration.")
        #     return redirect('ai_config_dashboard')
    except Exception as e:
        logger.error(f"Error retrieving AI model configuration: {str(e)}")
        messages.error(request, "Error retrieving AI model configuration.")
        return redirect('ai_config_dashboard')
    
    if request.method == 'POST':
        try:
            # Process form submission
            # In a real implementation, this would use a form class
            model_config.name = request.POST.get('name')
            model_config.api_endpoint = request.POST.get('api_endpoint')
            model_config.configuration_data = request.POST.get('configuration_data')
            model_config.is_active = 'is_active' in request.POST
            model_config.save()
            
            # API version (commented out for now):
            # api_url = request.build_absolute_uri(f'/api/admin/ai-models/{config_id}/')
            # update_data = {
            #     'name': request.POST.get('name'),
            #     'api_endpoint': request.POST.get('api_endpoint'),
            #     'configuration_data': request.POST.get('configuration_data'),
            #     'is_active': 'is_active' in request.POST
            # }
            # response = requests.patch(api_url, json=update_data)
            # if response.status_code == 200:
            #     messages.success(request, f"Model configuration '{update_data['name']}' updated successfully.")
            # else:
            #     messages.error(request, "Error updating AI model configuration.")
            #     return redirect('ai_config_dashboard')
            
            messages.success(request, f"Model configuration '{model_config.name}' updated successfully.")
            return redirect('ai_config_dashboard')
        except Exception as e:
            logger.error(f"Error updating AI model configuration: {str(e)}")
            messages.error(request, f"Error updating AI model configuration: {str(e)}")
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'model_config': model_config,
        'active_section': 'ai_config',
    }
    
    return render(request, "provider/ai_views/edit_model_config.html", context)

@login_required
@user_passes_test(lambda u: u.is_staff)  # Only staff can access AI config
def create_model_config(request):
    """Create a new AI model configuration with authenticated staff user"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    if request.method == 'POST':
        try:
            # Process form submission
            # In a real implementation, this would use a form class
            new_config = AIModelConfig(
                name=request.POST.get('name'),
                model_type=request.POST.get('model_type'),
                api_endpoint=request.POST.get('api_endpoint'),
                configuration_data=request.POST.get('configuration_data'),
                is_active='is_active' in request.POST
            )
            new_config.save()
            
            # API version (commented out for now):
            # api_url = request.build_absolute_uri('/api/admin/ai-models/')
            # create_data = {
            #     'name': request.POST.get('name'),
            #     'model_type': request.POST.get('model_type'),
            #     'api_endpoint': request.POST.get('api_endpoint'),
            #     'configuration_data': request.POST.get('configuration_data'),
            #     'is_active': 'is_active' in request.POST
            # }
            # response = requests.post(api_url, json=create_data)
            # if response.status_code == 201:  # Created
            #     messages.success(request, f"Model configuration '{create_data['name']}' created successfully.")
            # else:
            #     messages.error(request, "Error creating AI model configuration.")
            
            messages.success(request, f"Model configuration '{new_config.name}' created successfully.")
            return redirect('ai_config_dashboard')
        except Exception as e:
            logger.error(f"Error creating AI model configuration: {str(e)}")
            messages.error(request, f"Error creating AI model configuration: {str(e)}")
    
    # Get model type choices
    model_types = AIModelConfig.MODEL_TYPE_CHOICES if hasattr(AIModelConfig, 'MODEL_TYPE_CHOICES') else [
        ('transcription', 'Transcription'),
        ('summarization', 'Summarization'),
        ('clinical_note', 'Clinical Note Generation'),
        ('speech_to_text', 'Speech to Text')
    ]
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'model_types': model_types,
        'active_section': 'ai_config',
    }
    
    return render(request, "provider/ai_views/create_model_config.html", context)

@login_required
@user_passes_test(lambda u: u.is_staff)  # Only staff can access AI config
def toggle_model_status(request, config_id):
    """Toggle AI model active status with authenticated staff user"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        model_config = get_object_or_404(AIModelConfig, id=config_id)
        
        # Toggle status
        model_config.is_active = not model_config.is_active
        model_config.save()
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri(f'/api/admin/ai-models/{config_id}/toggle-status/')
        # response = requests.post(api_url)
        # if response.status_code == 200:
        #     status = 'activated' if response.json().get('is_active') else 'deactivated'
        #     messages.success(request, f"Model configuration {status} successfully.")
        # else:
        #     messages.error(request, "Error toggling AI model status.")
        
        status = 'activated' if model_config.is_active else 'deactivated'
        messages.success(request, f"Model configuration {status} successfully.")
    except Exception as e:
        logger.error(f"Error toggling AI model status: {str(e)}")
        messages.error(request, f"Error toggling AI model status: {str(e)}")
    
    return redirect('ai_config_dashboard')

@login_required
@user_passes_test(lambda u: u.is_staff)  # Only staff can access AI config
def test_model_config(request, config_id):
    """Test an AI model configuration with authenticated staff user"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        model_config = get_object_or_404(AIModelConfig, id=config_id)
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri(f'/api/admin/ai-models/{config_id}/test/')
        # response = requests.post(api_url)
        # if response.status_code == 200:
        #     result = response.json().get('result', {})
        #     if result.get('success'):
        #         messages.success(request, "Test successful! The model is working correctly.")
        #     else:
        #         messages.error(request, f"Test failed: {result.get('error')}")
        # else:
        #     messages.error(request, "Error testing AI model.")
        
        # Test the model using the service
        result = AIConfigurationService.test_model(model_config)
        
        if result.get('success'):
            messages.success(request, "Test successful! The model is working correctly.")
        else:
            messages.error(request, f"Test failed: {result.get('error')}")
    except Exception as e:
        logger.error(f"Error testing AI model: {str(e)}")
        messages.error(request, f"Error testing AI model: {str(e)}")
    
    return redirect('ai_config_dashboard')
