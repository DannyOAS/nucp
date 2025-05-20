# provider/views/ai_views/forms.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
import logging

from provider.services import FormAutomationService
from provider.utils import get_current_provider
from api.v1.provider.serializers import DocumentTemplateSerializer, GeneratedDocumentSerializer

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
        # Get forms dashboard data from service
        forms_data = FormAutomationService.get_forms_dashboard_data(provider.id)
        
        if not forms_data.get('success', False):
            messages.error(request, forms_data.get('error', "Error loading forms dashboard."))
            templates = []
            patients = []
            recent_documents = []
        else:
            # Format templates using API serializer if needed
            templates = forms_data.get('templates', [])
            if hasattr(templates, 'model'):
                serializer = DocumentTemplateSerializer(templates, many=True)
                templates = serializer.data
            
            # Format recent documents using API serializer if needed
            recent_documents = forms_data.get('recent_documents', [])
            if hasattr(recent_documents, 'model'):
                serializer = GeneratedDocumentSerializer(recent_documents, many=True)
                recent_documents = serializer.data
            
            patients = forms_data.get('patients', [])
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'active_section': 'forms',
            'templates': templates,
            'patients': patients,
            'recent_documents': recent_documents
        }
    except Exception as e:
        logger.error(f"Error loading forms dashboard: {str(e)}")
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'active_section': 'forms',
            'templates': [],
            'patients': [],
            'recent_documents': []
        }
        messages.error(request, f"Error loading forms dashboard: {str(e)}")
    
    return render(request, "provider/ai_views/forms_dashboard.html", context)
@login_required
def create_form(request, template_id):
    """Create a new form from a template with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Get template data from service
        template_data = FormAutomationService.get_template_details(
            provider_id=provider.id,
            template_id=template_id
        )
        
        if not template_data.get('success', False):
            messages.error(request, template_data.get('error', "Error loading template."))
            return redirect('forms_dashboard')
        
        # Format template using API serializer if needed
        template = template_data.get('template')
        if template and hasattr(template, '__dict__'):
            serializer = DocumentTemplateSerializer(template)
            template_data['template'] = serializer.data
        
        if request.method == 'POST':
            # Create document using service
            result = FormAutomationService.create_document(
                provider_id=provider.id,
                template_id=template_id,
                form_data=request.POST,
                user=request.user
            )
            
            if result.get('success', False):
                document_id = result.get('document_id')
                messages.success(request, "Document created successfully!")
                return redirect('view_document', document_id=document_id)
            else:
                messages.error(request, result.get('error', "Error creating document."))
        
        # Check for patient_id for auto-population
        patient_id = request.GET.get('patient_id')
        form_data = {}
        
        if patient_id:
            # Auto-populate form data from service
            auto_populate_data = FormAutomationService.auto_populate_form(
                provider_id=provider.id,
                template_id=template_id,
                patient_id=patient_id
            )
            
            if auto_populate_data.get('success', False):
                form_data = auto_populate_data.get('form_data', {})
        
        # Get patients list for form
        patients = FormAutomationService.get_provider_patients(provider.id)
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'active_section': 'forms',
            'template': template_data.get('template'),
            'form_data': form_data,
            'patients': patients
        }
    except Exception as e:
        logger.error(f"Error handling form creation: {str(e)}")
        messages.error(request, f"Error processing form: {str(e)}")
        return redirect('forms_dashboard')
    
    return render(request, 'provider/ai_views/create_form.html', context)

@login_required
def view_document(request, document_id):
    """View a document with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Get document data from service
        document_data = FormAutomationService.get_document_details(
            provider_id=provider.id,
            document_id=document_id
        )
        
        if not document_data.get('success', False):
            messages.error(request, document_data.get('error', "Error loading document."))
            return redirect('forms_dashboard')
        
        # Format document using API serializer if needed
        document = document_data.get('document')
        if document and hasattr(document, '__dict__'):
            serializer = GeneratedDocumentSerializer(document)
            document_data['document'] = serializer.data
        
        # Render document using service
        render_result = FormAutomationService.render_document(
            provider_id=provider.id,
            document_id=document_id
        )
        
        if not render_result.get('success', False):
            messages.error(request, render_result.get('error', "Error rendering document."))
            html_content = "<p>Error: Unable to render document content.</p>"
            pdf_available = False
        else:
            html_content = render_result.get('html_content')
            pdf_available = render_result.get('pdf_available', False)
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'active_section': 'forms',
            'document_id': document_id,
            'document': document_data.get('document'),
            'html_content': html_content,
            'pdf_available': pdf_available
        }
    except Exception as e:
        logger.error(f"Error viewing document: {str(e)}")
        messages.error(request, f"Error viewing document: {str(e)}")
        return redirect('forms_dashboard')
    
    return render(request, 'provider/ai_views/view_document.html', context)

@login_required
def download_document_pdf(request, document_id):
    """Download a document as PDF with authenticated provider"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Generate PDF using service
        pdf_result = FormAutomationService.generate_document_pdf(
            provider_id=provider.id,
            document_id=document_id
        )
        
        if not pdf_result.get('success', False):
            messages.error(request, pdf_result.get('error', "Error generating PDF."))
            return redirect('view_document', document_id=document_id)
        
        # Get PDF content and filename
        pdf_content = pdf_result.get('pdf_content')
        filename = pdf_result.get('filename', f"document_{document_id}.pdf")
        
        # Return PDF as download
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
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
        # Update status using service
        status_value = request.POST.get('status')
        if not status_value:
            return JsonResponse({'success': False, 'error': 'Status is required'}, status=400)
        
        result = FormAutomationService.update_document_status(
            provider_id=provider.id,
            document_id=document_id,
            status=status_value,
            user=request.user
        )
        
        if result.get('success', False):
            return JsonResponse({'success': True, 'document': result.get('document')})
        else:
            return JsonResponse({'success': False, 'error': result.get('error', 'Unknown error')}, status=500)
    except Exception as e:
        logger.error(f"Error updating document status: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(lambda u: u.is_staff)
def templates_dashboard(request):
    """Templates management dashboard with authenticated admin"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Get templates data from service
        templates_data = FormAutomationService.get_templates_dashboard_data()
        
        # Format templates using API serializer if needed
        templates = templates_data.get('templates', [])
        if hasattr(templates, 'model'):
            serializer = DocumentTemplateSerializer(templates, many=True)
            templates = serializer.data
        
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'templates': templates,
            'active_section': 'templates'
        }
    except Exception as e:
        logger.error(f"Error loading templates dashboard: {str(e)}")
        context = {
            'provider': provider_dict,
            'provider_name': f"Dr. {provider_dict['last_name']}",
            'templates': [],
            'active_section': 'templates'
        }
        messages.error(request, f"Error loading templates: {str(e)}")
    
    return render(request, "provider/ai_views/templates_dashboard.html", context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def create_template(request):
    """Create a new template with authenticated admin"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    if request.method == 'POST':
        try:
            # Process form submission
            template_data = {
                'name': request.POST.get('name'),
                'description': request.POST.get('description'),
                'template_type': request.POST.get('template_type'),
                'template_content': request.POST.get('content'),
                'requires_patient_data': 'requires_patient_data' in request.POST,
                'requires_provider_data': 'requires_provider_data' in request.POST
            }
            
            # Create template using service
            result = FormAutomationService.create_template(
                template_data=template_data,
                user=request.user
            )
            
            if result.get('success', False):
                messages.success(request, f"Template '{template_data['name']}' created successfully.")
                return redirect('templates_dashboard')
            else:
                messages.error(request, result.get('error', "Error creating template."))
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            messages.error(request, f"Error creating template: {str(e)}")
    
    context = {
        'provider': provider_dict,
        'provider_name': f"Dr. {provider_dict['last_name']}",
        'active_section': 'templates'
    }
    
    return render(request, "provider/ai_views/create_template.html", context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def edit_template(request, template_id):
    """Edit an existing template with authenticated admin"""
    # Get the current provider
    provider, provider_dict = get_current_provider(request)
    
    # If the function returns None, it has already redirected
    if provider is None:
        return redirect('unauthorized')
    
    try:
        # Get template data from service
        template_data = FormAutomationService.get_template_details(
            provider_id=provider.id,
            template_id=template_id,
            for_admin=True
        )
        
        if not template_data.get('success', False):
            messages.error(request, template_data.get('error', "Error loading template."))
            return redirect('templates_dashboard')
        
        # Format template using API serializer if needed
        template = template_data.get('template')
        if template and hasattr(template, '__dict__'):
            serializer = DocumentTemplateSerializer(template)
            template = serializer.data
        
        if request.method == 'POST':
            # Process form submission
            update_data = {
                'name': request.POST.get('name'),
                'description': request.POST.get('description'),
                'template_type': request.POST.get('template_type'),
                'template_content': request.POST.get('content'),
                'requires_patient_data': 'requires_patient_data' in request.POST,
                'requires_provider_data': 'requires_provider_data' in request.POST
            }
            
            # Update template using service
            result = FormAutomationService.update_template(
                template_id=template_id,
                update_data=update_data,
                user=request.user
            )
            
            if result.get('success', False):
                messages.success(request, f"Template '{update_data['name']}' updated successfully.")
                return redirect('templates_dashboard')
            else:
                messages.error(request, result.get('error', "Error updating template."))
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
    
    return render(request, "provider/ai_views/edit_template.html", context)
