# provider/services/ai_configuration_service.py
import logging
from django.utils import timezone
import json

from provider.models import Provider

logger = logging.getLogger(__name__)

class AIConfigurationService:
    """Service layer for managing AI model configurations."""
    
    @staticmethod
    def get_ai_model_configurations():
        """
        Get all AI model configurations
        """
        try:
            # Get AI model configurations
            try:
                from provider.models import AIModelConfig
                model_configs = AIModelConfig.objects.all().order_by('name')
                
                return {
                    'model_configs': model_configs
                }
            except (ImportError, AttributeError):
                logger.warning("AIModelConfig model not found")
                return {
                    'model_configs': []
                }
                
        except Exception as e:
            logger.error(f"Error in get_ai_model_configurations: {str(e)}")
            return {
                'model_configs': []
            }
    
    @staticmethod
    def get_model_config(config_id):
        """
        Get detailed info for a model config
        """
        try:
            # Get model config
            try:
                from provider.models import AIModelConfig
                model_config = AIModelConfig.objects.get(id=config_id)
                
                return {
                    'success': True,
                    'model_config': model_config
                }
            except (ImportError, AttributeError):
                return {
                    'success': False,
                    'error': 'AIModelConfig model not found'
                }
            except AIModelConfig.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Model configuration not found'
                }
            
        except Exception as e:
            logger.error(f"Error in get_model_config: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def update_model_config(config_id, update_data):
        """
        Update model configuration
        """
        try:
            # Get model config
            try:
                from provider.models import AIModelConfig
                model_config = AIModelConfig.objects.get(id=config_id)
                
                # Update fields
                if 'name' in update_data:
                    model_config.name = update_data['name']
                
                if 'api_endpoint' in update_data:
                    model_config.api_endpoint = update_data['api_endpoint']
                
                if 'configuration_data' in update_data:
                    # Check if it's a JSON string or already a dict
                    if isinstance(update_data['configuration_data'], str):
                        try:
                            # Validate JSON format
                            json_data = json.loads(update_data['configuration_data'])
                            model_config.configuration_data = update_data['configuration_data']
                        except json.JSONDecodeError as e:
                            return {
                                'success': False,
                                'error': f"Invalid JSON data: {str(e)}"
                            }
                    else:
                        # Convert dict to JSON string
                        model_config.configuration_data = json.dumps(update_data['configuration_data'])
                
                if 'is_active' in update_data:
                    model_config.is_active = update_data['is_active']
                
                # Save changes
                model_config.updated_at = timezone.now()
                model_config.save()
                
                return {
                    'success': True,
                    'model_config_id': model_config.id
                }
            except (ImportError, AttributeError):
                return {
                    'success': False,
                    'error': 'AIModelConfig model not found'
                }
            except AIModelConfig.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Model configuration not found'
                }
            
        except Exception as e:
            logger.error(f"Error in update_model_config: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def create_model_config(config_data):
        """
        Create a new model configuration
        """
        try:
            # Validate required fields
            required_fields = ['name', 'model_type', 'api_endpoint']
            for field in required_fields:
                if field not in config_data or not config_data[field]:
                    return {
                        'success': False,
                        'error': f"Field '{field}' is required"
                    }
            
            # Create model config
            try:
                from provider.models import AIModelConfig
                
                # Process configuration_data
                configuration_data = config_data.get('configuration_data', '{}')
                if isinstance(configuration_data, str):
                    try:
                        # Validate JSON format
                        json_data = json.loads(configuration_data)
                    except json.JSONDecodeError as e:
                        return {
                            'success': False,
                            'error': f"Invalid JSON data: {str(e)}"
                        }
                else:
                    # Convert dict to JSON string
                    configuration_data = json.dumps(configuration_data)
                
                model_config = AIModelConfig.objects.create(
                    name=config_data['name'],
                    model_type=config_data['model_type'],
                    api_endpoint=config_data['api_endpoint'],
                    configuration_data=configuration_data,
                    is_active=config_data.get('is_active', True)
                )
                
                return {
                    'success': True,
                    'model_config_id': model_config.id
                }
            except (ImportError, AttributeError):
                return {
                    'success': False,
                    'error': 'AIModelConfig model not found'
                }
            
        except Exception as e:
            logger.error(f"Error in create_model_config: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_model_type_choices():
        """
        Get available model type choices
        """
        try:
            # Get model type choices from model if available
            try:
                from provider.models import AIModelConfig
                if hasattr(AIModelConfig, 'MODEL_TYPE_CHOICES'):
                    model_types = AIModelConfig.MODEL_TYPE_CHOICES
                else:
                    # Default choices
                    model_types = [
                        ('transcription', 'Transcription'),
                        ('summarization', 'Summarization'),
                        ('clinical_note', 'Clinical Note Generation'),
                        ('speech_to_text', 'Speech to Text'),
                        ('form_filling', 'Form Auto-Filling'),
                        ('qa', 'Question Answering')
                    ]
            except (ImportError, AttributeError):
                # Default choices
                model_types = [
                    ('transcription', 'Transcription'),
                    ('summarization', 'Summarization'),
                    ('clinical_note', 'Clinical Note Generation'),
                    ('speech_to_text', 'Speech to Text'),
                    ('form_filling', 'Form Auto-Filling'),
                    ('qa', 'Question Answering')
                ]
            
            return {
                'model_types': model_types
            }
            
        except Exception as e:
            logger.error(f"Error in get_model_type_choices: {str(e)}")
            return {
                'model_types': [
                    ('transcription', 'Transcription'),
                    ('summarization', 'Summarization'),
                    ('clinical_note', 'Clinical Note Generation'),
                    ('speech_to_text', 'Speech to Text')
                ]
            }
    
    @staticmethod
    def toggle_model_status(config_id):
        """
        Toggle model active status
        """
        try:
            # Get model config
            try:
                from provider.models import AIModelConfig
                model_config = AIModelConfig.objects.get(id=config_id)
                
                # Toggle status
                model_config.is_active = not model_config.is_active
                model_config.save()
                
                return {
                    'success': True,
                    'model_config_id': model_config.id,
                    'is_active': model_config.is_active
                }
            except (ImportError, AttributeError):
                return {
                    'success': False,
                    'error': 'AIModelConfig model not found'
                }
            except AIModelConfig.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Model configuration not found'
                }
            
        except Exception as e:
            logger.error(f"Error in toggle_model_status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def test_model_config(config_id):
        """
        Test a model configuration
        """
        try:
            # Get model config
            try:
                from provider.models import AIModelConfig
                model_config = AIModelConfig.objects.get(id=config_id)
                
                # Test connection to API endpoint
                import requests
                import json
                
                # Get configuration data
                try:
                    config = json.loads(model_config.configuration_data)
                except (json.JSONDecodeError, AttributeError):
                    config = {}
                
                # Get test message based on model type
                test_message = "This is a test message."
                if model_config.model_type == 'transcription':
                    test_message = "Test transcription request."
                elif model_config.model_type == 'summarization':
                    test_message = "Test summarization request."
                elif model_config.model_type == 'clinical_note':
                    test_message = "Test clinical note generation request."
                elif model_config.model_type == 'speech_to_text':
                    test_message = "Test speech to text request."
                    
                # Get API key if available
                api_key = config.get('api_key', '')
                
                # Prepare request headers
                headers = {
                    'Content-Type': 'application/json'
                }
                
                if api_key:
                    headers['Authorization'] = f"Bearer {api_key}"
                
                # Prepare request data
                request_data = {
                    'text': test_message,
                    'model': config.get('model_name', 'default')
                }
                
                # Send test request
                try:
                    # Use a timeout to avoid hanging
                    response = requests.post(
                        model_config.api_endpoint, 
                        headers=headers, 
                        json=request_data,
                        timeout=5  # 5 second timeout
                    )
                    
                    # Check response
                    if response.status_code >= 200 and response.status_code < 300:
                        return {
                            'success': True,
                            'message': 'Test successful',
                            'response': response.json() if response.content else {}
                        }
                    else:
                        return {
                            'success': False,
                            'error': f"API returned error code {response.status_code}: {response.text}"
                        }
                except requests.RequestException as e:
                    return {
                        'success': False,
                        'error': f"Request error: {str(e)}"
                    }
                
            except (ImportError, AttributeError):
                return {
                    'success': False,
                    'error': 'AIModelConfig model not found'
                }
            except AIModelConfig.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Model configuration not found'
                }
            
        except Exception as e:
            logger.error(f"Error in test_model_config: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
