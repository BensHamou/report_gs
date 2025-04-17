from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from .models import Disponibility, TemporaryEmplacementAlert, Family, Product, MoveLine
from account.models import Site
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
from collections import defaultdict

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


def send_stock(include_qrt=False):
    site_state_pf(include_qrt)
    global_state_pf(include_qrt)
    site_state_mp(include_qrt)
    global_state_mp(include_qrt)

def site_state_pf(include_qrt=False):
    today = timezone.now().date()
    sites = Site.objects.all()
    families = Family.objects.all()

    for site in sites:
        if include_qrt:
            subject = f"[PF] Etat Stock Quarantaine {site.designation} - {today}"
        else:
            subject = f"[PF] Etat Stock {site.designation} - {today}"
        
        family_data = []
        for family in families:
            family_disponibilities = Disponibility.objects.filter(emplacement__warehouse__site=site, product__family=family, product__type='Produit Fini',
                                                                  emplacement__quarantine=include_qrt).values('product__designation', 'product__qte_per_pal', 'product__qte_per_cond', 'product__packing__unit'
                                            ).annotate(total_palette=Sum('palette'), total_qte=Sum('qte')).order_by('product__designation')

            if family_disponibilities:
                total_palette = round(sum(item['total_palette'] for item in family_disponibilities), 2)
                total_qte = round(sum(item['total_qte'] for item in family_disponibilities), 2)

                family_data.append({'family': family, 'disponibilities': family_disponibilities, 'total_palette': total_palette,'total_qte': total_qte})

        html_message = render_to_string('fragment/pf_state.html', {'site': site, 'today': today,'family_data': family_data, 'global': False})

        addresses = site.email.split('&') if site.email else []
        if not addresses:
            addresses = ['mohammed.senoussaoui@grupopuma-dz.com']

        print(addresses, subject)

        email = EmailMultiAlternatives(subject, None, 'Puma Stock', addresses)
        email.attach_alternative(html_message, "text/html")
        email.send()

def global_state_pf(include_qrt=False):
    today = timezone.now().date()
    families = Family.objects.all()

    if include_qrt:
        subject = f"[PF] Etat Stock Global Quarantaine - {today}"
    else:
        subject = f"[PF] Etat Stock Global - {today}"
    
    family_data = []
    for family in families:
        
        family_disponibilities = Disponibility.objects.filter(product__family=family, product__type='Produit Fini', emplacement__quarantine=include_qrt).values('product__designation', 'product__qte_per_pal', 'product__qte_per_cond', 'product__packing__unit'
                                        ).annotate(total_palette=Sum('palette'), total_qte=Sum('qte')).order_by('product__designation')

        if family_disponibilities:
            total_palette = round(sum(item['total_palette'] for item in family_disponibilities), 2)
            total_qte = round(sum(item['total_qte'] for item in family_disponibilities), 2)

            family_data.append({'family': family, 'disponibilities': family_disponibilities, 'total_palette': total_palette,'total_qte': total_qte})

    html_message = render_to_string('fragment/pf_state.html', {'site': '/', 'today': today,'family_data': family_data, 'global': True})
    
    addresses = [email for site in Site.objects.all() if site.email for email in site.email.split('&')] or ['mohammed.senoussaoui@grupopuma-dz.com']

    # addresses = ['mohammed.benslimane@groupe-hasnaoui.com']
    
    print(addresses, subject)

    email = EmailMultiAlternatives(subject, None, 'Puma Stock', addresses)
    email.attach_alternative(html_message, "text/html")
    email.send()

def site_state_mp(include_qrt=False):
    today = timezone.now().date()
    sites = Site.objects.all()

    for site in sites:
        if include_qrt:
            subject = f"[MP] Etat Stock Quarantaine {site.designation} - {today}"
        else:
            subject = f"[MP] Etat Stock {site.designation} - {today}"

        data = []
        
        disponibilities = Disponibility.objects.filter(emplacement__warehouse__site=site, product__type='Matière Première', emplacement__quarantine=include_qrt).values('product__designation', 'product__packing__unit'
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

def global_state_mp(include_qrt=False):
    today = timezone.now().date()

    if include_qrt:
        subject = f"[MP] Etat Stock Global Quarantaine - {today}"
    else:
        subject = f"[MP] Etat Stock Global - {today}"
    
    data = []
    disponibilities = Disponibility.objects.filter(product__type='Matière Première', emplacement__quarantine=include_qrt).values('product__designation', 'product__packing__unit'
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


def check_min_max():
    check_min_max_mp_global()
    check_min_max_pf_by_site()

def check_min_max_mp_global():
    products = Product.objects.filter(type='Matière Première').select_related('family')
    
    global_qtes = Disponibility.objects.filter(product__in=products).values('product').annotate(total_qte=Sum('qte'))
    qte_dict = {item['product']: item['total_qte'] or 0 for item in global_qtes}

    
    cons_dict = calculate_global_consumption(products)
       
    alerts = []
    for mp in products:
        actual_qte = qte_dict.get(mp.id, 0)
        cons_last_2_months = cons_dict.get(mp.id, 0)

        if cons_last_2_months > 0:
            print(mp, actual_qte, cons_last_2_months)
        
        if cons_last_2_months <= 0:
            continue
            
        nj = actual_qte / cons_last_2_months
        family = mp.family
        
        if nj < family.nb_days_min:
            alerts.append({'type': 'global_min', 'product': mp, 'nj': nj, 'required': family.nb_days_min})
        elif nj > family.nb_days_max:
            alerts.append({'type': 'global_max', 'product': mp, 'nj': nj, 'required': family.nb_days_max})
        else:
            check_min_max_mp_by_site(mp)
    
    send_batched_alerts(alerts)

def calculate_global_consumption(products):
    move_lines = MoveLine.objects.filter(product__in=products, move__type='Sortie', move__state='Validé', move__date__gte=timezone.now() - timedelta(days=600), 
                                         move__is_isolation=False).select_related('product')
    
    cons_dict = defaultdict(int)
    for ml in move_lines:
        cons_dict[ml.product_id] += ml.qte
    return cons_dict

def check_min_max_mp_by_site(product):
    sites = Site.objects.all()
    alerts = []
    
    site_qtes = product.disponibilities.filter(emplacement__warehouse__site__in=sites).values('emplacement__warehouse__site').annotate(total_qte=Sum('qte'))
    qte_dict = {item['emplacement__warehouse__site']: item['total_qte'] or 0 for item in site_qtes}
    
    cons_dict = calculate_site_consumption(product, sites)
    
    for site in sites:
        actual_qte = qte_dict.get(site.id, 0)
        cons_last_2_months = cons_dict.get(site.id, 0)
        
        if cons_last_2_months <= 0:
            continue
            
        nj = actual_qte / cons_last_2_months
        family = product.family
        
        if nj < family.nb_days_min:
            alerts.append({'type': 'site_min', 'product': product, 'site': site, 'nj': nj, 'required': family.nb_days_min})
        elif nj > family.nb_days_max:
            alerts.append({'type': 'site_max', 'product': product, 'site': site, 'nj': nj, 'required': family.nb_days_max})
    
    send_batched_alerts(alerts)

def calculate_site_consumption(product, sites):
    move_lines = MoveLine.objects.filter(product=product, move__type='Sortie', move__state='Validé', move__date__gte=timezone.now() - timedelta(days=60), 
                                         move__is_isolation=False, move__site__in=sites).select_related('move__site')
    
    cons_dict = defaultdict(int)
    for ml in move_lines:
        cons_dict[ml.move.site_id] += ml.qte
    return cons_dict

def check_min_max_pf_by_site():
    """Check min/max alerts for finished products by site"""
    pass

def send_batched_alerts(alerts):
    if not alerts:
        return
    
    alert_groups = defaultdict(list)
    for alert in alerts:
        alert_groups[alert['type']].append(alert)
    
    for alert_type, group in alert_groups.items():
        if alert_type == 'global_min':
            send_mp_global_min_alert(group)
        elif alert_type == 'global_max':
            send_mp_global_max_alert(group)
        elif alert_type == 'site_min':
            send_mp_site_min_alert(group)
        elif alert_type == 'site_max':
            send_mp_site_max_alert(group)

def send_mp_global_min_alert(alerts):
    """Send batch of global minimum alerts"""
    for alert in alerts:
        print(f"Global MIN alert for {alert['product']}: {alert['nj']} days (min {alert['required']})")

def send_mp_global_max_alert(alerts):
    """Send batch of global maximum alerts"""
    for alert in alerts:
        print(f"Global MAX alert for {alert['product']}: {alert['nj']} days (max {alert['required']})")

def send_mp_site_min_alert(alerts):
    """Send batch of site minimum alerts"""
    for alert in alerts:
        print(f"Site MIN alert for {alert['product']} at {alert['site']}: {alert['nj']} days (min {alert['required']})")

def send_mp_site_max_alert(alerts):
    """Send batch of site maximum alerts"""
    for alert in alerts:
        print(f"Site MAX alert for {alert['product']} at {alert['site']}: {alert['nj']} days (max {alert['required']})")