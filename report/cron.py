from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from .models import Disponibility, TemporaryEmplacementAlert, Family
from account.models import Site
from django.utils import timezone
from django.db.models import Sum


def check_temp_emplacements():
    allowed_in_temp = timezone.now() - timezone.timedelta(hours=5)
    alerts = TemporaryEmplacementAlert.objects.filter(email_sent=False, start_time__lte=allowed_in_temp, type='Temporaire')
    for alert in alerts:
        send_alert(alert)
        alert.email_sent = True
        alert.save()


def check_transfer_mirror():
    allowed_in_temp = timezone.now() - timezone.timedelta(hours=48)
    alerts = TemporaryEmplacementAlert.objects.filter(email_sent=False, start_time__lte=allowed_in_temp, type='Transfer')
    for alert in alerts:
        mirror_email(alert.mirror)
        alert.email_sent = True
        alert.save()


def send_alert(alert):
    subject = f'Stock Temporaire'
    
    html_message = render_to_string('fragment/temp_zone.html', {'alert': alert})

    addresses = alert.dispo.emplacement.warehouse.site.email.split('&')
    if not addresses:
        addresses = ['mohammed.senoussaoui@grupopuma-dz.com']

    email = EmailMultiAlternatives(subject, None, 'Puma Stock', addresses)
    email.attach_alternative(html_message, "text/html") 
    email.send()    

def mirror_email(mirror):
    subject = f'BTR Mirroire'
    html_message = render_to_string('fragment/btr_mirror.html', {'move': mirror})
    addresses = mirror.site.email.split('&')
    if not addresses:
        addresses = ['mohammed.senoussaoui@grupopuma-dz.com']

    print(addresses, subject)
    email = EmailMultiAlternatives(subject, None, 'Puma Stock', addresses)
    email.attach_alternative(html_message, "text/html") 
    email.send()    


def send_stock():
    site_state_pf()
    global_state_pf()
    site_state_mp()
    global_state_mp()

def site_state_pf():
    today = timezone.now().date()
    sites = Site.objects.all()
    families = Family.objects.all()

    for site in sites:
        subject = f"[PF] Etat Stock {site.designation} - {today}"
        
        family_data = []
        for family in families:
            family_disponibilities = Disponibility.objects.filter(emplacement__warehouse__site=site, product__family=family, product__type='Produit Fini',
                                                                  emplacement__quarantine=False).values('product__designation', 'product__packing__unit'
                                            ).annotate(total_palette=Sum('palette'), total_qte=Sum('qte')).order_by('product__designation')

            if family_disponibilities:
                total_palette = round(sum(item['total_palette'] for item in family_disponibilities), 2)
                total_qte = round(sum(item['total_qte'] for item in family_disponibilities), 2)

                family_data.append({'family': family, 'disponibilities': family_disponibilities, 'total_palette': total_palette,'total_qte': total_qte})

        html_message = render_to_string('fragment/pf_state.html', {'site': site, 'today': today,'family_data': family_data, 'global': False})

        addresses = site.email.split('&') if site.email else []
        print(addresses, subject)
        if not addresses:
            addresses = ['mohammed.senoussaoui@grupopuma-dz.com']
        email = EmailMultiAlternatives(subject, None, 'Puma Stock', addresses)
        email.attach_alternative(html_message, "text/html")
        email.send()

def global_state_pf():
    today = timezone.now().date()
    families = Family.objects.all()

    subject = f"[PF] Etat Stock Global - {today}"
    
    family_data = []
    for family in families:
        family_disponibilities = Disponibility.objects.filter(product__family=family, product__type='Produit Fini', emplacement__quarantine=False).values('product__designation', 'product__packing__unit'
                                        ).annotate(total_palette=Sum('palette'), total_qte=Sum('qte')).order_by('product__designation')

        if family_disponibilities:
            total_palette = round(sum(item['total_palette'] for item in family_disponibilities), 2)
            total_qte = round(sum(item['total_qte'] for item in family_disponibilities), 2)

            family_data.append({'family': family, 'disponibilities': family_disponibilities, 'total_palette': total_palette,'total_qte': total_qte})

    html_message = render_to_string('fragment/pf_state.html', {'site': '/', 'today': today,'family_data': family_data, 'global': True})
    
    
    addresses = [email for site in Site.objects.all() if site.email for email in site.email.split('&')] or ['mohammed.senoussaoui@grupopuma-dz.com']
    print(addresses, subject)
    email = EmailMultiAlternatives(subject, None, 'Puma Stock', addresses)
    email.attach_alternative(html_message, "text/html")
    email.send()

def site_state_mp():
    today = timezone.now().date()
    sites = Site.objects.all()

    for site in sites:
        subject = f"[MP] Etat Stock {site.designation} - {today}"

        data = []
        
        disponibilities = Disponibility.objects.filter(emplacement__warehouse__site=site, product__type='Matière Première', emplacement__quarantine=False).values('product__designation', 'product__packing__unit'
                                        ).annotate(total_qte=Sum('qte')).order_by('product__designation')
        if disponibilities:
            total_qte = round(sum(item['total_qte'] for item in disponibilities), 2)

            data.append({'disponibilities': disponibilities,'total_qte': total_qte})

        html_message = render_to_string('fragment/mp_state.html', {'site': site, 'today': today, 'datas': data, 'global': False})

        addresses = site.email.split('&') if site.email else []
        if not addresses:
            addresses = ['mohammed.senoussaoui@grupopuma-dz.com']
        print(addresses, subject)
        email = EmailMultiAlternatives(subject, None, 'Puma Stock', addresses)
        email.attach_alternative(html_message, "text/html")
        email.send()

def global_state_mp():
    today = timezone.now().date()

    subject = f"[MP] Etat Stock Global - {today}"
    
    data = []
    disponibilities = Disponibility.objects.filter(product__type='Matière Première', emplacement__quarantine=False).values('product__designation', 'product__packing__unit'
                                    ).annotate(total_qte=Sum('qte')).order_by('product__designation') 
    if disponibilities:
        total_qte = round(sum(item['total_qte'] for item in disponibilities), 2)
        data.append({'disponibilities': disponibilities,'total_qte': total_qte})

    html_message = render_to_string('fragment/mp_state.html', {'site': '/', 'today': today, 'datas': data, 'global': True})

    addresses = [email for site in Site.objects.all() if site.email for email in site.email.split('&')] or ['mohammed.senoussaoui@grupopuma-dz.com']
    print(addresses, subject)
    email = EmailMultiAlternatives(subject, None, 'Puma Stock', addresses)
    email.attach_alternative(html_message, "text/html")
    email.send()
