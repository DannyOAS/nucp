# provider/views/ai_views/forms.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import logging
import requests

from theme_name.repositories import ProviderRepository
from provider.services import FormAutomationService
from provider.models import DocumentTemplate, GeneratedDocument
from provider.utils import get_current_provider

logger = logging.getLogger(__name__)

@login_required
def forms_dashboard(request):
    """Forms dashboard view with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        templates_result = FormAutomationService.get_available_templates()
        patients = ProviderRepository.get_patients(provider.id)
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri('/api/provider/forms/')
        # response = requests.get(api_url)
        # if response.status_code == 200:
        #     api_data = response.json()
        #     templates_result = {
        #         'success': True,
        #         'templates': api_data.get('templates', [])
        #     }
        #     recent_documents = api_data.get('recent_documents', [])
        # else:
        #     templates_result = {'success': False, 'error': 'API error'}
        #     recent_documents = []
        
        if not templates_result.get('success'):
            messages.error(request, f"Error loading templates: {templates_result.get('error', 'Unknown error')}")
        
        # Get recent documents for this provider
        recent_documents_query = GeneratedDocument.objects.filter(
            provider=provider
        ).order_by('-created_at')[:5]
        
        recent_documents = []
        for doc in recent_documents_query:
            recent_documents.append({
                'id': doc.id,
                'template_name': doc.template.name if doc.template else "Unknown Template",
                'patient_name': f"{doc.patient.first_name} {doc.patient.last_name}" if doc.patient else "Unknown Patient",
                'created_at': doc.created_at.strftime('%B %d, %Y'),
                'status': doc.status
            })
    except Exception as e:
        logger.error(f"Error loading forms dashboard: {str(e)}")
        templates_result = {'success': False, 'error': str(e)}
        patients = []
        recent_documents = []
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'active_section': 'forms',
        'templates': templates_result.get('templates', []),
        'patients': patients,
        'recent_documents': recent_documents
    }
    
    return render(request, "provider/forms_dashboard.html", context)

@login_required
def create_form(request, template_id):
    """Create a new form from a template with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        template_result = FormAutomationService.get_template_by_id(template_id)
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri(f'/api/provider/forms/templates/{template_id}/')
        # response = requests.get(api_url)
        # if response.status_code == 200:
        #     template_result = {
        #         'success': True,
        #         'template': response.json()
        #     }
        # else:
        #     template_result = {'success': False, 'error': 'API error'}
        
        if not template_result.get('success'):
            messages.error(request, f"Error loading template: {template_result.get('error', 'Unknown error')}")
            return redirect('forms_dashboard')
        
        if request.method == 'POST':
            form_data = request.POST.dict()
            document_result = FormAutomationService.create_document(
                template_id=template_id,
                form_data=form_data,
                created_by_id=request.user.id
            )
            
            # API version (commented out for now):
            # api_url = request.build_absolute_uri('/api/provider/forms/documents/')
            # response = requests.post(api_url, json={
            #     'template_id': template_id,
            #     'form_data': form_data
            # })
            # if response.status_code == 201:  # Created
            #     document_result = {
            #         'success': True,
            #         'document': response.json()
            #     }
            # else:
            #     document_result = {'success': False, 'error': 'API error'}
            
            if document_result.get('success'):
                document_id = document_result['document']['id']
                messages.success(request, "Document created successfully!")
                return redirect('view_document', document_id=document_id)
            else:
                messages.error(request, f"Error creating document: {document_result.get('error', 'Unknown error')}")
        
        # Check for patient_id for auto-population
        patient_id = request.GET.get('patient_id')
        form_data = {}
        
        if patient_id:
            auto_populate_result = FormAutomationService.auto_populate_form(
                template_id=template_id,
                patient_id=patient_id,
                provider_id=provider.id
            )
            
            # API version (commented out for now):
            # api_url = request.build_absolute_uri(f'/api/provider/forms/auto-populate/')
            # response = requests.get(api_url, params={
            #     'template_id': template_id,
            #     'patient_id': patient_id
            # })
            # if response.status_code == 200:
            #     auto_populate_result = {
            #         'success': True,
            #         'form_data': response.json()
            #     }
            # else:
            #     auto_populate_result = {'success': False, 'error': 'API error'}
            
            if auto_populate_result.get('success'):
                form_data = auto_populate_result.get('form_data', {})
        
        # Get patients for this provider
        patients = ProviderRepository.get_patients(provider.id)
    except Exception as e:
        logger.error(f"Error handling form creation: {str(e)}")
        messages.error(request, f"Error processing form: {str(e)}")
        return redirect('forms_dashboard')
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'active_section': 'forms',
        'template': template_result.get('template'),
        'form_data': form_data,
        'patients': patients
    }
    
    return render(request, 'provider/create_form.html', context)

@login_required
def view_document(request, document_id):
    """View a document with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Check if this document belongs to the provider
        document = get_object_or_404(GeneratedDocument, id=document_id, provider=provider)
        
        # Render the document
        render_result = FormAutomationService.render_document(document_id)
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri(f'/api/provider/forms/documents/{document_id}/')
        # response = requests.get(api_url)
        # if response.status_code == 200:
        #     render_result = {
        #         'success': True,
        #         'html_content': response.json().get('html_content'),
        #         'pdf_available': response.json().get('pdf_available')
        #     }
        # else:
        #     render_result = {'success': False, 'error': 'API error'}
        
        if not render_result.get('success'):
            messages.error(request, f"Error rendering document: {render_result.get('error', 'Unknown error')}")
            return redirect('forms_dashboard')
    except Exception as e:
        logger.error(f"Error viewing document: {str(e)}")
        messages.error(request, f"Error viewing document: {str(e)}")
        return redirect('forms_dashboard')
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'active_section': 'forms',
        'document_id': document_id,
        'document': document,
        'html_content': render_result.get('html_content'),
        'pdf_available': render_result.get('pdf_available')
    }
    
    return render(request, 'provider/view_document.html', context)

@login_required
def download_document_pdf(request, document_id):
    """Download a document as PDF with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Check if this document belongs to the provider
        document = get_object_or_404(GeneratedDocument, id=document_id, provider=provider)
        
        # Render the document
        render_result = FormAutomationService.render_document(document_id)
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri(f'/api/provider/forms/documents/{document_id}/pdf/')
        # response = requests.get(api_url)
        # if response.status_code == 200:
        #     # This would return the PDF content
        #     pdf_content = response.content
        # else:
        #     messages.error(request, "Error downloading PDF.")
        #     return redirect('view_document', document_id=document_id)
        
        if not render_result.get('success'):
            messages.error(request, f"Error rendering document: {render_result.get('error', 'Unknown error')}")
            return redirect('view_document', document_id=document_id)
        
        # In a real implementation, we would generate and return the PDF
        # For now, just return a placeholder response
        response = HttpResponse(b'PDF content would go here', content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="document_{document_id}.pdf"'
        return response
    except Exception as e:
        logger.error(f"Error downloading document PDF: {str(e)}")
        messages.error(request, f"Error downloading document PDF: {str(e)}")
        return redirect('view_document', document_id=document_id)

@login_required
@require_POST
def update_document_status(request, document_id):
    """Update document status with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)
    
    try:
        # Check if this document belongs to the provider
        document = get_object_or_404(GeneratedDocument, id=document_id, provider=provider)
        
        status_value = request.POST.get('status')
        if not status_value:
            return JsonResponse({'success': False, 'error': 'Status is required'}, status=400)
        
        result = FormAutomationService.update_document_status(
            document_id=document_id,
            status=status_value,
            updated_by_id=request.user.id
        )
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri(f'/api/provider/forms/documents/{document_id}/status/')
        # response = requests.post(api_url, json={'status': status_value})
        # if response.status_code == 200:
        #     result = {
        #         'success': True,
        #         'document': response.json()
        #     }
        # else:
        #     result = {'success': False, 'error': 'API error'}
        
        if result.get('success'):
            return JsonResponse({'success': True, 'document': result.get('document')})
        else:
            return JsonResponse({'success': False, 'error': result.get('error', 'Unknown error')}, status=500)
    except Exception as e:
        logger.error(f"Error updating document status: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def templates_dashboard(request):
    """Templates management dashboard with authenticated admin"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    # Check if the user is an admin
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('forms_dashboard')
    
    try:
        templates = DocumentTemplate.objects.all().order_by('template_type', 'name')
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri('/api/admin/templates/')
        # response = requests.get(api_url)
        # if response.status_code == 200:
        #     templates = response.json()
        # else:
        #     templates = []
        #     messages.error(request, "Error loading templates.")
    except Exception as e:
        logger.error(f"Error loading templates dashboard: {str(e)}")
        templates = []
        messages.error(request, f"Error loading templates: {str(e)}")
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'templates': templates,
        'active_section': 'templates'
    }
    
    return render(request, "provider/templates_dashboard.html", context)

@login_required
def create_template(request):
    """Create a new template with authenticated admin"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    # Check if the user is an admin
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('forms_dashboard')
    
    if request.method == 'POST':
        try:
            # Process form submission
            template = DocumentTemplate()
            template.name = request.POST.get('name')
            template.description = request.POST.get('description')
            template.template_type = request.POST.get('template_type')
            template.template_content = request.POST.get('content')
            template.requires_patient_data = 'requires_patient_data' in request.POST
            template.requires_provider_data = 'requires_provider_data' in request.POST
            template.created_by = request.user
            template.save()
            
            # API version (commented out for now):
            # api_url = request.build_absolute_uri('/api/admin/templates/')
            # template_data = {
            #     'name': request.POST.get('name'),
            #     'description': request.POST.get('description'),
            #     'template_type': request.POST.get('template_type'),
            #     'template_content': request.POST.get('content'),
            #     'requires_patient_data': 'requires_patient_data' in request.POST,
            #     'requires_provider_data': 'requires_provider_data' in request.POST
            # }
            # response = requests.post(api_url, json=template_data)
            # if response.status_code == 201:  # Created
            #     messages.success(request, f"Template '{template_data['name']}' created successfully.")
            # else:
            #     messages.error(request, "Error creating template.")
            #     return redirect('templates_dashboard')
            
            messages.success(request, f"Template '{template.name}' created successfully.")
            return redirect('templates_dashboard')
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            messages.error(request, f"Error creating template: {str(e)}")
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'active_section': 'templates'
    }
    
    return render(request, "provider/create_template.html", context)

@login_required
def edit_template(request, template_id):
    """Edit an existing template with authenticated admin"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    # Check if the user is an admin
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('forms_dashboard')
    
    try:
        template = get_object_or_404(DocumentTemplate, id=template_id)
        
        # API version (commented out for now):
        # api_url = request.build_absolute_uri(f'/api/admin/templates/{template_id}/')
        # response = requests.get(api_url)
        # if response.status_code == 200:
        #     template = response.json()
        # else:
        #     messages.error(request, "Error loading template.")
        #     return redirect('templates_dashboard')
        
        if request.method == 'POST':
            # Process form submission
            template.name = request.POST.get('name')
            template.description = request.POST.get('description')
            template.template_type = request.POST.get('template_type')
            template.template_content = request.POST.get('content')
            template.requires_patient_data = 'requires_patient_data' in request.POST
            template.requires_provider_data = 'requires_provider_data' in request.POST
            template.save()
            
            # API version (commented out for now):
            # api_url = request.build_absolute_uri(f'/api/admin/templates/{template_id}/')
            # template_data = {
            #     'name': request.POST.get('name'),
            #     'description': request.POST.get('description'),
            #     'template_type': request.POST.get('template_type'),
            #     'template_content': request.POST.get('content'),
            #     'requires_patient_data': 'requires_patient_data' in request.POST,
            #     'requires_provider_data': 'requires_provider_data' in request.POST
            # }
            # response = requests.put(api_url, json=template_data)
            # if response.status_code == 200:
            #     messages.success(request, f"Template '{template_data['name']}' updated successfully.")
            # else:
            #     messages.error(request, "Error updating template.")
            #     return redirect('edit_template', template_id=template_id)
            
            messages.success(request, f"Template '{template.name}' updated successfully.")
            return redirect('templates_dashboard')
    except Exception as e:
        logger.error(f"Error editing template: {str(e)}")
        messages.error(request, f"Error editing template: {str(e)}")
        return redirect('templates_dashboard')
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'template': template,
        'active_section': 'templates'
    }
    
    return render(request, "provider/edit_template.html", context)
