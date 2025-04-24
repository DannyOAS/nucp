from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from ..forms import ContactForm
from ..models import ContactMessage, BlogPost

def home(request):
    return render(request, "home.html")

def about(request):
    """About page view"""
    return render(request, "about.html")

def contact(request):
    """Contact page view with form handling"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Save the contact message
            form.save()
            return redirect('contact_success')
    else:
        form = ContactForm()
    return render(request, "contact.html", {'form': form})

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
