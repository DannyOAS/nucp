# mysite/api/documentation.py
import inspect
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from django.urls import resolve, get_resolver
import markdown

class APIDocumentationGenerator:
    """
    Utility class to generate API documentation based on viewsets and serializers.
    It automatically extracts information from docstrings, serializers, and viewset methods.
    """
    
    def __init__(self, app_name=None):
        """
        Initialize the documentation generator.
        
        Args:
            app_name: Optional name of the app to document (e.g., 'api.v1.patient')
        """
        self.app_name = app_name
        self.docs = {}
    
    def generate_docs_for_viewset(self, viewset_class):
        """
        Generate documentation for a specific viewset.
        
        Args:
            viewset_class: The viewset class to document
            
        Returns:
            dict: Documentation for the viewset
        """
        # Extract basic viewset info
        viewset_name = viewset_class.__name__
        viewset_doc = viewset_class.__doc__ or "No documentation available."
        
        # Extract serializer info
        serializer_class = getattr(viewset_class, 'serializer_class', None)
        serializer_info = self._extract_serializer_info(serializer_class) if serializer_class else {}
        
        # Extract actions
        actions = self._extract_actions(viewset_class)
        
        # Extract permissions
        permission_classes = getattr(viewset_class, 'permission_classes', [])
        permissions = [p.__name__ for p in permission_classes]
        
        # Compile the documentation
        viewset_docs = {
            'name': viewset_name,
            'description': viewset_doc,
            'serializer': serializer_info,
            'actions': actions,
            'permissions': permissions,
            'version': getattr(viewset_class, 'version', 'unknown')
        }
        
        self.docs[viewset_name] = viewset_docs
        return viewset_docs
    
    def _extract_serializer_info(self, serializer_class):
        """Extract information from a serializer class"""
        if not serializer_class or not issubclass(serializer_class, ModelSerializer):
            return {}
            
        # Get model info
        model = serializer_class.Meta.model
        model_name = model.__name__
        
        # Get fields info
        fields = getattr(serializer_class.Meta, 'fields', [])
        read_only_fields = getattr(serializer_class.Meta, 'read_only_fields', [])
        
        # Extract field descriptions from model
        field_info = {}
        for field_name in fields:
            if field_name in serializer_class._declared_fields:
                field = serializer_class._declared_fields[field_name]
                field_info[field_name] = {
                    'type': field.__class__.__name__,
                    'required': getattr(field, 'required', False),
                    'read_only': field_name in read_only_fields or getattr(field, 'read_only', False),
                    'description': getattr(field, 'help_text', '')
                }
            elif hasattr(model, field_name):
                model_field = model._meta.get_field(field_name)
                field_info[field_name] = {
                    'type': model_field.__class__.__name__,
                    'required': not model_field.blank,
                    'read_only': field_name in read_only_fields,
                    'description': model_field.help_text or ''
                }
        
        return {
            'model': model_name,
            'fields': field_info
        }
    
    def _extract_actions(self, viewset_class):
        """Extract actions from a viewset class"""
        actions = {}
        
        # Standard actions (list, create, retrieve, update, partial_update, destroy)
        if hasattr(viewset_class, 'list') and callable(viewset_class.list):
            actions['list'] = {
                'method': 'GET',
                'description': viewset_class.list.__doc__ or 'List objects.',
                'url': '{basename}/'
            }
            
        if hasattr(viewset_class, 'create') and callable(viewset_class.create):
            actions['create'] = {
                'method': 'POST',
                'description': viewset_class.create.__doc__ or 'Create a new object.',
                'url': '{basename}/'
            }
            
        if hasattr(viewset_class, 'retrieve') and callable(viewset_class.retrieve):
            actions['retrieve'] = {
                'method': 'GET',
                'description': viewset_class.retrieve.__doc__ or 'Retrieve an object.',
                'url': '{basename}/{id}/'
            }
            
        if hasattr(viewset_class, 'update') and callable(viewset_class.update):
            actions['update'] = {
                'method': 'PUT',
                'description': viewset_class.update.__doc__ or 'Update an object.',
                'url': '{basename}/{id}/'
            }
            
        if hasattr(viewset_class, 'partial_update') and callable(viewset_class.partial_update):
            actions['partial_update'] = {
                'method': 'PATCH',
                'description': viewset_class.partial_update.__doc__ or 'Partially update an object.',
                'url': '{basename}/{id}/'
            }
            
        if hasattr(viewset_class, 'destroy') and callable(viewset_class.destroy):
            actions['destroy'] = {
                'method': 'DELETE',
                'description': viewset_class.destroy.__doc__ or 'Delete an object.',
                'url': '{basename}/{id}/'
            }
        
        # Custom actions
        for name, method in inspect.getmembers(viewset_class):
            if hasattr(method, 'mapping'):
                action_methods = list(method.mapping.keys())
                url_path = getattr(method, 'url_path', name)
                detail = getattr(method, 'detail', False)
                
                for action_method in action_methods:
                    action_key = f"{name}_{action_method}"
                    actions[action_key] = {
                        'method': action_method.upper(),
                        'description': method.__doc__ or f'{action_method.upper()} {name}.',
                        'url': '{basename}/{id}/' + url_path + '/' if detail else '{basename}/' + url_path + '/'
                    }
        
        return actions
    
    def generate_markdown_docs(self):
        """Generate Markdown documentation for all documented viewsets"""
        if not self.docs:
            return "No viewsets documented."
        
        md = "# API Documentation\n\n"
        
        for viewset_name, viewset_info in self.docs.items():
            md += f"## {viewset_name}\n\n"
            md += f"{viewset_info['description'].strip()}\n\n"
            md += f"Version: {viewset_info['version']}\n\n"
            
            # Permissions
            if viewset_info['permissions']:
                md += "### Permissions\n\n"
                md += ", ".join(viewset_info['permissions']) + "\n\n"
            
            # Serializer
            if 'serializer' in viewset_info and viewset_info['serializer']:
                md += "### Model\n\n"
                md += f"{viewset_info['serializer']['model']}\n\n"
                
                if 'fields' in viewset_info['serializer']:
                    md += "### Fields\n\n"
                    md += "| Field | Type | Required | Read Only | Description |\n"
                    md += "|-------|------|----------|-----------|-------------|\n"
                    
                    for field_name, field_info in viewset_info['serializer']['fields'].items():
                        required = "Yes" if field_info.get('required') else "No"
                        read_only = "Yes" if field_info.get('read_only') else "No"
                        md += f"| {field_name} | {field_info.get('type', 'Unknown')} | {required} | {read_only} | {field_info.get('description', '')} |\n"
                    
                    md += "\n"
            
            # Actions
            if viewset_info['actions']:
                md += "### Endpoints\n\n"
                md += "| Action | Method | URL | Description |\n"
                md += "|--------|--------|-----|-------------|\n"
                
                for action_name, action_info in viewset_info['actions'].items():
                    md += f"| {action_name} | {action_info['method']} | {action_info['url']} | {action_info['description'].strip()} |\n"
                
                md += "\n"
            
            md += "---\n\n"
        
        return md
    
    def generate_docs_for_app(self):
        """Generate documentation for all viewsets in the specified app"""
        if not self.app_name:
            return "No app specified."
        
        # Try to import the app
        try:
            app_module = __import__(self.app_name, fromlist=['views'])
            
            # Find all viewsets in the views module
            if hasattr(app_module, 'views'):
                for name, cls in inspect.getmembers(app_module.views):
                    if inspect.isclass(cls) and issubclass(cls, ViewSet) and cls != ViewSet:
                        self.generate_docs_for_viewset(cls)
        except ImportError:
            return f"Could not import app: {self.app_name}"
        
        return self.generate_markdown_docs()

# Utility function for easy access
def generate_api_docs(viewset_or_app):
    """
    Generate API documentation for a viewset or app.
    
    Args:
        viewset_or_app: A viewset class or app name (str)
        
    Returns:
        str: Markdown documentation
    """
    generator = APIDocumentationGenerator()
    
    if isinstance(viewset_or_app, str):
        generator.app_name = viewset_or_app
        return generator.generate_docs_for_app()
    elif inspect.isclass(viewset_or_app) and issubclass(viewset_or_app, ViewSet):
        generator.generate_docs_for_viewset(viewset_or_app)
        return generator.generate_markdown_docs()
    else:
        return "Invalid input. Please provide a viewset class or app name."
