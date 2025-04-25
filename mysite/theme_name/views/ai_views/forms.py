from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from ...repositories import ProviderRepository
from ...services import FormAutomationService
from ...models import DocumentTemplate, GeneratedDocument

def forms_dashboard(request):
    provider_id = 1
    templates_result = FormAutomationService.get_available_templates()
    patients = ProviderRepository.get_patients(provider_id)
    if not templates_result.get('success'):
        messages.error(request, f"Error loading templates: {templates_result.get('error', 'Unknown error')}")
    recent_documents = [
        {
            'id': 1,
            'template_name': 'Lab Requisition',
            'patient_name': 'Jane Doe',
            'created_at': 'Today, 11:23 AM',
            'status': 'Completed'
        },
        {
            'id': 2,
            'template_name': 'Sick Note',
            'patient_name': 'John Smith',
            'created_at': 'Yesterday, 3:45 PM',
            'status': 'Draft'
        },
        {
            'id': 3,
            'template_name': 'Specialist Referral',
            'patient_name': 'Emily Williams',
            'created_at': 'March 30, 2025',
            'status': 'Sent'
        }
    ]
    context = {
        'active_section': 'forms',
        'provider_name': 'Dr. Provider',
        'templates': templates_result.get('templates', []),
        'patients': patients,
        'recent_documents': recent_documents
    }
    return render(request, "provider/forms_dashboard.html", context)

def create_form(request, template_id):
    template_result = FormAutomationService.get_template_by_id(template_id)
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
        if document_result.get('success'):
            document_id = document_result['document']['id']
            messages.success(request, "Document created successfully!")
            return redirect('view_document', document_id=document_id)
        else:
            messages.error(request, f"Error creating document: {document_result.get('error', 'Unknown error')}")
    patient_id = request.GET.get('patient_id')
    form_data = {}
    if patient_id:
        auto_populate_result = FormAutomationService.auto_populate_form(
            template_id=template_id,
            patient_id=patient_id,
            provider_id=request.user.id
        )
        if auto_populate_result.get('success'):
            form_data = auto_populate_result.get('form_data', {})
    context = {
        'active_section': 'forms',
        'provider_name': 'Dr. Provider',
        'template': template_result.get('template'),
        'form_data': form_data,
        'patients': [
            {'id': 1, 'name': 'Jane Doe'},
            {'id': 2, 'name': 'John Smith'},
            {'id': 3, 'name': 'Robert Johnson'},
            {'id': 4, 'name': 'Emily Williams'}
        ]
    }
    return render(request, 'provider/create_form.html', context)

def view_document(request, document_id):
    render_result = FormAutomationService.render_document(document_id)
    if not render_result.get('success'):
        messages.error(request, f"Error rendering document: {render_result.get('error', 'Unknown error')}")
        return redirect('forms_dashboard')
    context = {
        'active_section': 'forms',
        'provider_name': 'Dr. Provider',
        'document_id': document_id,
        'html_content': render_result.get('html_content'),
        'pdf_available': render_result.get('pdf_available')
    }
    return render(request, 'provider/view_document.html', context)


def download_document_pdf(request, document_id):
    render_result = FormAutomationService.render_document(document_id)
    if not render_result.get('success'):
        messages.error(request, f"Error rendering document: {render_result.get('error', 'Unknown error')}")
        return redirect('forms_dashboard')
    response = HttpResponse(b'PDF content would go here', content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="document_{document_id}.pdf"'
    return response


@require_POST
def update_document_status(request, document_id):
    status_value = request.POST.get('status')
    if not status_value:
        return JsonResponse({'success': False, 'error': 'Status is required'}, status=400)
    result = FormAutomationService.update_document_status(
        document_id=document_id,
        status=status_value,
        updated_by_id=request.user.id
    )
    if result.get('success'):
        return JsonResponse({'success': True, 'document': result.get('document')})
    else:
        return JsonResponse({'success': False, 'error': result.get('error', 'Unknown error')}, status=500)


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
