# model_validator.py
"""
Utility script to validate that your model structure is ready for database migration.
Run this script to check for common issues before transitioning from mock data.
"""

import inspect
import sys
from django.db import models
from django.apps import apps
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import re

def validate_models():
    """Check all models for common issues."""
    issues_found = 0
    warnings = 0
    
    print("======= Model Validation Report =======\n")
    
    # Get all models from your app
    app_models = [m for m in apps.get_models() if m.__module__.startswith('your_app_name')]
    
    if not app_models:
        print("⚠️  No models found. Make sure you've specified the correct app name.")
        return
    
    print(f"Found {len(app_models)} models to validate.\n")
    
    for model in app_models:
        print(f"Checking model: {model.__name__}")
        
        # 1. Check for primary key
        if not [f for f in model._meta.fields if f.primary_key]:
            print(f"❌ ERROR: Model {model.__name__} has no primary key defined.")
            issues_found += 1
        
        # 2. Check field types
        for field in model._meta.fields:
            # Skip primary key check (already done)
            if field.primary_key:
                continue
                
            # Check if EmailField is used for email fields
            if field.name.lower().endswith('email') and not isinstance(field, models.EmailField):
                print(f"❌ ERROR: Field '{field.name}' appears to be an email but isn't using EmailField")
                issues_found += 1
                
            # Check if DateField/DateTimeField is used for date fields
            if any(date_term in field.name.lower() for date_term in ['date', 'time', 'created', 'updated']) and \
               not isinstance(field, (models.DateField, models.DateTimeField)):
                print(f"⚠️  WARNING: Field '{field.name}' appears to be a date but isn't using DateField/DateTimeField")
                warnings += 1
                
            # Check if proper field types are used for phone numbers
            if any(phone_term in field.name.lower() for phone_term in ['phone', 'mobile', 'cell', 'fax']) and \
               not isinstance(field, models.CharField):
                print(f"⚠️  WARNING: Field '{field.name}' appears to be a phone number but isn't using CharField")
                warnings += 1
        
        # 3. Check for required fields without default values or blank=True
        for field in model._meta.fields:
            if not field.primary_key and \
               not field.null and \
               not field.blank and \
               not field.has_default() and \
               not isinstance(field, models.AutoField):
                print(f"ℹ️  INFO: Required field '{field.name}' has no default value - ensure data migration handles this")
        
        # 4. Check for relationships
        fk_fields = [f for f in model._meta.fields if isinstance(f, models.ForeignKey)]
        for fk in fk_fields:
            # Check for on_delete
            if not fk.remote_field.on_delete:
                print(f"❌ ERROR: ForeignKey '{fk.name}' has no on_delete behavior specified")
                issues_found += 1
            
            # Check for related_name if pointing to the same model multiple times
            target_model = fk.remote_field.model
            similar_fks = [f for f in fk_fields if f.remote_field.model == target_model]
            if len(similar_fks) > 1:
                for similar_fk in similar_fks:
                    if not similar_fk.remote_field.related_name:
                        print(f"❌ ERROR: Multiple ForeignKeys to {target_model.__name__} exist, but '{similar_fk.name}' has no related_name")
                        issues_found += 1
        
        # 5. Check for string representation
        if not hasattr(model, '__str__') or model.__str__ is models.Model.__str__:
            print(f"⚠️  WARNING: Model {model.__name__} has no custom __str__ method")
            warnings += 1
            
        # 6. Check for Meta class and ordering
        if not hasattr(model, 'Meta') or not hasattr(model.Meta, 'ordering'):
            print(f"⚠️  WARNING: Model {model.__name__} has no default ordering in Meta class")
            warnings += 1
            
        print("")  # Line break between models
    
    # Final report
    print("======= Validation Summary =======")
    print(f"Models checked: {len(app_models)}")
    print(f"Issues found: {issues_found}")
    print(f"Warnings: {warnings}")
    
    if issues_found == 0 and warnings == 0:
        print("\n✅ All models passed validation! Your models are ready for migration.")
    elif issues_found == 0:
        print("\n🟡 Models passed validation with some warnings. Consider addressing these for best practices.")
    else:
        print("\n❌ Issues found that should be fixed before database migration.")
    
    return issues_found, warnings

def check_forms_models_alignment():
    """Check that forms align with their corresponding models."""
    from django import forms
    
    # Import all your forms
    try:
        from your_app_name.forms import *
    except ImportError:
        print("❌ ERROR: Could not import forms. Make sure the module path is correct.")
        return 1, 0
    
    issues = 0
    warnings = 0
    print("\n======= Form-Model Alignment Check =======\n")
    
    # Get all ModelForm classes
    form_classes = []
    for name, obj in inspect.getmembers(sys.modules['your_app_name.forms']):
        if inspect.isclass(obj) and issubclass(obj, forms.ModelForm) and obj != forms.ModelForm:
            form_classes.append(obj)
    
    if not form_classes:
        print("⚠️  No ModelForm classes found.")
        return 0, 1
    
    print(f"Found {len(form_classes)} ModelForm classes to check.\n")
    
    for form_class in form_classes:
        print(f"Checking form: {form_class.__name__}")
        
        # Check if Meta class exists and has model attribute
        if not hasattr(form_class, 'Meta') or not hasattr(form_class.Meta, 'model'):
            print(f"❌ ERROR: {form_class.__name__} has no model defined in Meta class")
            issues += 1
            continue
            
        model = form_class.Meta.model
        print(f"  Associated model: {model.__name__}")
        
        # Check if fields are defined
        if not hasattr(form_class.Meta, 'fields'):
            print(f"❌ ERROR: {form_class.__name__} has no fields defined in Meta class")
            issues += 1
            continue
            
        # If fields is __all__, warn about potential security issues
        if form_class.Meta.fields == '__all__':
            print(f"⚠️  WARNING: {form_class.__name__} uses '__all__' for fields, which may expose sensitive fields")
            warnings += 1
            continue
            
        # Check each field in form
        form_fields = form_class.Meta.fields
        model_fields = [f.name for f in model._meta.fields if f.name != 'id']
        
        # Check for fields in form that don't exist in model
        for field in form_fields:
            if field not in model_fields:
                print(f"❌ ERROR: Form field '{field}' does not exist in model {model.__name__}")
                issues += 1
                
        # Check for required model fields not in form
        required_model_fields = [f.name for f in model._meta.fields 
                              if not f.null and not f.blank and not f.has_default() and f.name != 'id']
        missing_required = [f for f in required_model_fields if f not in form_fields]
        
        if missing_required:
            print(f"⚠️  WARNING: Required model fields missing from form: {', '.join(missing_required)}")
            warnings += 1
            
        # Check field widgets
        if hasattr(form_class.Meta, 'widgets'):
            widgets = form_class.Meta.widgets
            for field_name, widget in widgets.items():
                if field_name not in form_fields:
                    print(f"⚠️  WARNING: Widget defined for '{field_name}' but field not in form.fields")
                    warnings += 1
                
        print("")  # Line break between forms
    
    # Final report
    print("======= Form-Model Alignment Summary =======")
    print(f"Forms checked: {len(form_classes)}")
    print(f"Issues found: {issues}")
    print(f"Warnings: {warnings}")
    
    if issues == 0 and warnings == 0:
        print("\n✅ All forms are properly aligned with their models!")
    elif issues == 0:
        print("\n🟡 Forms passed validation with some warnings.")
    else:
        print("\n❌ Issues found that should be fixed before database migration.")
    
    return issues, warnings

if __name__ == "__main__":
    # Set up Django environment
    import os
    import django
    
    # Change these to match your project
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "your_project.settings")
    django.setup()
    
    # Run validation
    model_issues, model_warnings = validate_models()
    form_issues, form_warnings = check_forms_models_alignment()
    
    total_issues = model_issues + form_issues
    total_warnings = model_warnings + form_warnings
    
    print("\n======= Overall Validation Results =======")
    print(f"Total issues: {total_issues}")
    print(f"Total warnings: {total_warnings}")
    
    if total_issues == 0 and total_warnings == 0:
        print("\n✅ All checks passed! Your models and forms are ready for database migration.")
        sys.exit(0)
    elif total_issues == 0:
        print("\n🟡 Validation passed with warnings. Consider addressing these for best practices.")
        sys.exit(1)
    else:
        print("\n❌ Issues found that should be fixed before database migration.")
        sys.exit(2)
