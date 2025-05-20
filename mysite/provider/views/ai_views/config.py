# provider/views/ai_views/config.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
import logging

from provider.services import AIConfigurationService
from provider.utils import get_current_provider
from api.v1.provider.serializers import AIModelConfigSerializer

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
        # Get AI model configurations from service
        config_data = AIConfigurationService.get_ai_model_configurations()
        
        # Format model configs using API serializer if needed
        model_configs = config_data.get('model_configs', [])
        if hasattr(model_configs, 'model'):
            serializer = AIModelConfigSerializer(model_configs, many=True)
            config_data['model_configs'] = serializer.data
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'model_configs': config_data.get('model_configs', []),
            'active_section': 'ai_config',
        }
    except Exception as e:
        logger.error(f"Error retrieving AI model configurations: {str(e)}")
        messages.error(request, "Error retrieving AI model configurations.")
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'model_configs': [],
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
        # Get model config from service
        config_data = AIConfigurationService.get_model_config(config_id)
        
        if not config_data.get('success', False):
            messages.error(request, config_data.get('error', "Error retrieving AI model configuration."))
            return redirect('ai_config_dashboard')
        
        # Format model config using API serializer if needed
        model_config = config_data.get('model_config')
        if model_config and hasattr(model_config, '__dict__'):
            serializer = AIModelConfigSerializer(model_config)
            config_data['model_config'] = serializer.data
    except Exception as e:
        logger.error(f"Error retrieving AI model configuration: {str(e)}")
        messages.error(request, "Error retrieving AI model configuration.")
        return redirect('ai_config_dashboard')
    
    if request.method == 'POST':
        try:
            # Process form submission
            update_data = {
                'name': request.POST.get('name'),
                'api_endpoint': request.POST.get('api_endpoint'),
                'configuration_data': request.POST.get('configuration_data'),
                'is_active': 'is_active' in request.POST
            }
            
            # Update config using service
            result = AIConfigurationService.update_model_config(
                config_id=config_id,
                update_data=update_data
            )
            
            if result.get('success', False):
                messages.success(request, f"Model configuration '{update_data['name']}' updated successfully.")
                return redirect('ai_config_dashboard')
            else:
                messages.error(request, result.get('error', "Error updating AI model configuration."))
        except Exception as e:
            logger.error(f"Error updating AI model configuration: {str(e)}")
            messages.error(request, f"Error updating AI model configuration: {str(e)}")
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'model_config': config_data.get('model_config'),
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
            config_data = {
                'name': request.POST.get('name'),
                'model_type': request.POST.get('model_type'),
                'api_endpoint': request.POST.get('api_endpoint'),
                'configuration_data': request.POST.get('configuration_data'),
                'is_active': 'is_active' in request.POST
            }
            
            # Create config using service
            result = AIConfigurationService.create_model_config(config_data)
            
            if result.get('success', False):
                messages.success(request, f"Model configuration '{config_data['name']}' created successfully.")
                return redirect('ai_config_dashboard')
            else:
                messages.error(request, result.get('error', "Error creating AI model configuration."))
        except Exception as e:
            logger.error(f"Error creating AI model configuration: {str(e)}")
            messages.error(request, f"Error creating AI model configuration: {str(e)}")
    
    # Get model type choices from service
    try:
        model_types_data = AIConfigurationService.get_model_type_choices()
        model_types = model_types_data.get('model_types', [
            ('transcription', 'Transcription'),
            ('summarization', 'Summarization'),
            ('clinical_note', 'Clinical Note Generation'),
            ('speech_to_text', 'Speech to Text')
        ])
    except Exception as e:
        logger.error(f"Error retrieving model types: {str(e)}")
        model_types = [
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
        # Toggle model status using service
        result = AIConfigurationService.toggle_model_status(config_id)
        
        if result.get('success', False):
            status = 'activated' if result.get('is_active', False) else 'deactivated'
            messages.success(request, f"Model configuration {status} successfully.")
        else:
            messages.error(request, result.get('error', "Error toggling AI model status."))
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
        # Test model using service
        result = AIConfigurationService.test_model_config(config_id)
        
        if result.get('success', False):
            messages.success(request, "Test successful! The model is working correctly.")
        else:
            messages.error(request, f"Test failed: {result.get('error', 'Unknown error')}")
    except Exception as e:
        logger.error(f"Error testing AI model: {str(e)}")
        messages.error(request, f"Error testing AI model: {str(e)}")
    
    return redirect('ai_config_dashboard')
