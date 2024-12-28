from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from .models import *

def check_temp_emplacements():
    allowed_in_temp = timezone.now() - timezone.timedelta(hours=5)
    alerts = TemporaryEmplacementAlert.objects.filter(email_sent=False, start_time__lte=allowed_in_temp)
    for alert in alerts:
        send_alert(alert)
        alert.email_sent = True

def send_alert(alert):
    subject = f'Stock Temporaire'
    
    html_message = render_to_string('fragment/temp_zone.html', {'alert': alert})

    addresses = alert.dispo.emplacement.warehouse.site.address.split('&')
    if not addresses:
        addresses = ['mohammed.senoussaoui@grupopuma-dz.com']

    email = EmailMultiAlternatives(subject, None, 'Puma Stock', addresses)
    email.attach_alternative(html_message, "text/html") 
    email.send()    

    
