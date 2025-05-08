import traceback
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.core.mail import send_mail
from ..forms import ContactForm, DemoRequestForm
from ..models import ContactMessage, BlogPost
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)

#def home(request):
#    return render(request, "home.html")
def home(request):
    return render(request, "home2.html")


def about(request):
    """About page view"""
    return render(request, "about.html")
#
#def contact(request):
#    """Contact page view with form handling"""
#    if request.method == 'POST':
#        form = ContactForm(request.POST)
#        if form.is_valid():
#            # Save the contact message
#            form.save()
#            return redirect('contact_success')
#    else:
#        form = ContactForm()
#    return render(request, "contact.html", {'form': form})
def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message_text = request.POST.get('message')
        
        # Create and save the contact message
        contact_message = ContactMessage(
            name=name,
            email=email,
            message=message_text
        )
        contact_message.save()
        
        # Add success message
        messages.success(request, "Your message has been sent successfully!")
        
        # Redirect to clear the form and prevent form resubmission
        return redirect('contact')  # Make sure 'contact' is a valid URL name
    
    # For GET requests, just render the form
    return render(request, 'contact.html')

def blog_list(request):
    """Blog listing page"""
    blog_posts = BlogPost.objects.all().order_by('-created_at')
    
    # Pagination
    paginator = Paginator(blog_posts, 5)  # Show 5 posts per page
    page = request.GET.get('page')
    
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    
    return render(request, "blog/list.html", {'posts': posts})

def blog_detail(request, pk):
    """Blog detail page"""
    try:
        post = BlogPost.objects.get(pk=pk)
    except BlogPost.DoesNotExist:
        raise Http404("Blog post does not exist")
    
    return render(request, "blog/detail.html", {'post': post})

def privacy_policy(request):
    return render(request, "privacy_policy.html")

def terms_of_use(request):
    return render(request, "terms_of_use.html")

@csrf_exempt
def schedule_demo(request):
    if request.method == 'POST':
        try:
            form = DemoRequestForm(request.POST)
            if form.is_valid():
                demo_request = form.save()
                
                try:
                    # Send email
                    subject = f'New Demo Request from {demo_request.name}'
                    body = f"""
New demo request received:

Name: {demo_request.name}
Email: {demo_request.email}
Organization: {demo_request.organization}
User Type: {demo_request.user_type}
Preferred Date: {demo_request.preferred_date}
Preferred Time: {demo_request.preferred_time}
Message: {demo_request.message}
                    """
                    
                    send_mail(
                        subject=subject,
                        message=body,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=['postmaster@onmhiconnect.ca'],  # Replace with actual recipient
                        fail_silently=False,
                    )
                    
                    return JsonResponse({'success': True})
                    
                except Exception as e:
                    logger.error(f"Failed to send email: {str(e)}")
                    return JsonResponse({
                        'success': False, 
                        'error': f'Failed to send email: {str(e)}'
                    })
            else:
                return JsonResponse({
                    'success': False, 
                    'errors': form.errors
                })
                
        except Exception as e:
            # Print full error to console
            print("Error in schedule_demo view:")
            print(traceback.format_exc())
            
            return JsonResponse({
                'success': False, 
                'error': f'Server error: {str(e)}'
            })
    
    # Handle GET request for form display
    try:
        form = DemoRequestForm()
        form_html = render_to_string('theme_name/partials/demo_form.html', {'form': form})
        return JsonResponse({'form_html': form_html})
    except Exception as e:
        print("Error rendering form:")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False, 
            'error': f'Form rendering error: {str(e)}'
        })
