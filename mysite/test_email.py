from django.core.mail import send_mail
send_mail(
    'Test from Django',
    'If you received this, Django mail integration is working!',
    'postmaster@onmhiconnect.ca',
    ['your-test-recipient@example.com']
)
