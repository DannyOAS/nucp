from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from ...repositories import ProviderRepository
from ...services import FormAutomationService
from ...models import DocumentTemplate, GeneratedDocument

def forms_dashboard(request):
    """Forms dashboard view"""
    provider_id = 1  # In production, get from request.user
    provider = ProviderRepository.get_by_id(provider_id)
    
    # Get forms data
    templates = DocumentTemplate.objects.filter(is_active=True).order_by('name')
    recent_documents = GeneratedDocument.objects.filter(created_by=request.user).order_by('-created_at')[:10]
    
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider['last_name']}",
        'templates': templates,
        'recent_documents': recent_documents,
        'active_section': 'forms'
    }
    
    return render(request, "provider/forms_dashboard.html", context)

def create_form(request, template_id):
    """Create a form from template"""
    provider_id = 1  # In production, get from request.user
    provider = ProviderRepository.get_by_id(provider_id)
    template = get_object_or_404(DocumentTemplate, id=template_id)
    
    if request.method == 'POST':
        # Process form submission
        form_data = request.POST.dict()
        # Remove CSRF token from form data
        form_data.pop('csrfmiddlewaretoken', None)
        
        document = FormAutomationService.create_document(
            template_id=template_id,
            patient_id=form_data.get('patient_id'),
            provider_id=provider_id,
            form_data=form_data
        )
        
        messages.success(request, f"{template.get_template_type_display()} created successfully.")
        return redirect('view_document', document_id=document.id)
    
    # Get patients for dropdown
    patients = ProviderRepository.get_patients(provider_id)
    
    context = {
        'provider': provider,
        'provider_name': f"Dr. {provider['last_name']}",
        'template': template,
        'patients': patients,
        'active_section': 'forms'
    }
    
    return render(request, "provider/create_form.html", context)

def view_document(request, document_id):
    """View generated document"""
    document = get_object_or_404(GeneratedDocument, id=document_id)
    
    context = {
        'document': document,
        'active_section': 'forms'
    }
    
    return render(request, "provider/view_document.html", context)

def download_document_pdf(request, document_id):
    """Download document as PDF"""
    document = get_object_or_404(GeneratedDocument, id=document_id)
    
    # Generate PDF
    pdf_file = FormAutomationService.generate_pdf(document_id)
    
    # Return PDF
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{document.template.name}_{document.patient.get_full_name()}.pdf"'
    return response

@require_POST
def update_document_status(request, document_id):
    """Update document status"""
    document = get_object_or_404(GeneratedDocument, id=document_id)
    new_status = request.POST.get('status')
    
    if new_status in [choice[0] for choice in GeneratedDocument.STATUS_CHOICES]:
        document.status = new_status
        document.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Document status updated to {document.get_status_display()}.'
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Invalid status value.'
        }, status=400)

def templates_dashboard(request):
    """Templates management dashboard"""
    templates = DocumentTemplate.objects.all().order_by('template_type', 'name')
    
    context = {
        'templates': templates,
        'active_section': 'templates',
        'admin_name': 'Admin'
    }
    
    return render(request, "admin/templates_dashboard.html", context)

def create_template(request):
    """Create a new template"""
    if request.method == 'POST':
        # Process form submission
        # In a real implementation, this would use a form class
        template = DocumentTemplate()
        template.name = request.POST.get('name')
        template.description = request.POST.get('description')
        template.template_type = request.POST.get('template_type')
        template.template_content = request.POST.get('content')
        template.requires_patient_data = 'requires_patient_data' in request.POST
        template.requires_provider_data = 'requires_provider_data' in request.POST
        template.created_by = request.user
        template.save()
        
        messages.success(request, f"Template '{template.name}' created successfully.")
        return redirect('templates_dashboard')
    
    context = {
        'active_section': 'templates',
        'admin_name': 'Admin'
    }
    
    return render(request, "admin/create_template.html", context)

def edit_template(request, template_id):
    """Edit an existing template"""
    template = get_object_or_404(DocumentTemplate, id=template_id)
    
    if request.method == 'POST':
        # Process form submission
        template.name = request.POST.get('name')
        template.description = request.POST.get('description')
        template.template_type = request.POST.get('template_type')
        template.template_content = request.POST.get('content')
        template.requires_patient_data = 'requires_patient_data' in request.POST
        template.requires_provider_data = 'requires_provider_data' in request.POST
        template.save()
        
        messages.success(request, f"Template '{template.name}' updated successfully.")
        return redirect('templates_dashboard')
    
    context = {
        'template': template,
        'active_section': 'templates',
        'admin_name': 'Admin'
    }
    
    return render(request, "admin/edit_template.html", context)
