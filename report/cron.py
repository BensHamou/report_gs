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

def send_stock_state_by_site():
    today = timezone.now().date()
    sites = Site.objects.all()
    families = Family.objects.all()

    for site in sites:
        subject = f"Etat Stock {site.designation} - {today}"
        
        family_data = []
        for family in families:
            family_disponibilities = Disponibility.objects.filter(emplacement__warehouse__site=site, product__family=family).values('product__designation', 'product__packing__unit'
                                            ).annotate(total_palette=Sum('palette'), total_qte=Sum('qte')).order_by('product__designation')

            if family_disponibilities:
                total_palette = sum(item['total_palette'] for item in family_disponibilities)
                total_qte = sum(item['total_qte'] for item in family_disponibilities)

                family_data.append({'family': family, 'disponibilities': family_disponibilities, 'total_palette': total_palette,'total_qte': total_qte})

        html_message = render_to_string('fragment/stock_state.html', {'site': site, 'today': today,'family_data': family_data})

        addresses = site.address.split('&') if site.address else []
        if not addresses:
            addresses = ['mohammed.senoussaoui@grupopuma-dz.com']

        email = EmailMultiAlternatives(subject, None, 'Puma Stock', addresses)
        email.attach_alternative(html_message, "text/html")
        email.send()



