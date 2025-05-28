from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from .models import Disponibility, TemporaryEmplacementAlert, Family, Product, MoveLine
from account.models import Site
from django.utils import timezone
from django.db.models import Sum, F
from datetime import timedelta
from collections import defaultdict
import math
from itertools import groupby
from operator import attrgetter


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
    global_mp, by_site_mp = check_min_max_mp_global()
    by_site_pf = check_min_max_pf_by_site()
    
    def prepare_items(items):
        return [item for item in items if item is not None]
    
    all_mp = prepare_items(global_mp) + prepare_items(by_site_mp)
    all_pf = prepare_items(by_site_pf)
    
    def organize_by_site_and_family(items):
        
        sorted_items = sorted(items, key=lambda x: (x.get('site').designation if 'site' in x else 'Global', x.get('product').family.sequence, x.get('nj')))

        site_groups = {}
        for item in sorted_items:
            site_name = item.get('site').designation if 'site' in item else 'Global'
            family_name = item.get('product').family.designation
            
            if site_name not in site_groups:
                site_groups[site_name] = {}
            
            if family_name not in site_groups[site_name]:
                site_groups[site_name][family_name] = []
            
            site_groups[site_name][family_name].append(item)
        
        return site_groups
    
    mp_min = organize_by_site_and_family([item for item in all_mp if 'min' in item.get('type')])
    mp_max = organize_by_site_and_family([item for item in all_mp if 'max' in item.get('type')])
    pf_min = organize_by_site_and_family([item for item in all_pf if 'min' in item.get('type')])
    pf_max = organize_by_site_and_family([item for item in all_pf if 'max' in item.get('type')])
    
    sites = list(Site.objects.all()) + [None]
    
    for site in sites:
        site_name = site.designation if site else 'Global'
        site_recipients = []
        
        if not site:
            site_recipients = [email for site in Site.objects.all() if site.email for email in site.email.split('&')] or ['mohammed.senoussaoui@grupopuma-dz.com']
        elif site and site.email:
            site_recipients = site.email.split('&')
        else:
            site_recipients = ['mohammed.senoussaoui@grupopuma-dz.com']
        
        if site_name in mp_min and mp_min[site_name]:
            send_site_alert(recipients=site_recipients, subject=f"[MP MIN - {site_name}] Alerte Stock",
                message=f"Veuillez trouver ci-dessous les matières premières en dessous du niveau minimum - {site_name}", alert_data={site_name: mp_min[site_name]})
        
        if site_name in mp_max and mp_max[site_name]:
            send_site_alert(recipients=site_recipients, subject=f"[MP MAX - {site_name}] Alerte Stock",
                message=f"Veuillez trouver ci-dessous les matières premières au dessus du niveau maximum - {site_name}", alert_data={site_name: mp_max[site_name]})
        
        if site and site_name in pf_min and pf_min[site_name]:
            send_site_alert(recipients=site_recipients, subject=f"[PF MIN - {site_name}] Alerte Stock",
                message=f"Veuillez trouver ci-dessous les produits finis en dessous du niveau minimum - {site_name}", alert_data={site_name: pf_min[site_name]})
        
        if site and site_name in pf_max and pf_max[site_name]:
            send_site_alert(recipients=site_recipients, subject=f"[PF MAX - {site_name}] Alerte Stock",
                message=f"Veuillez trouver ci-dessous les produits finis au dessus du niveau maximum - {site_name}", alert_data={site_name: pf_max[site_name]})

    if by_site_mp:
        send_btr_recommendations(prepare_items(by_site_mp))

def send_site_alert(recipients, subject, message, alert_data):
    today = timezone.now().date()
    html = render_to_string('fragment/minmax_alert.html', {'alert_data': alert_data, 'message': message, 'today': today})
    email = EmailMultiAlternatives(subject, None, 'Puma Stock', recipients)
    email.attach_alternative(html, "text/html")
    email.send()

# ====================== MP (Matières Premières) ======================
def check_min_max_mp_global():
    global_mp = []
    by_site_mp = []
    products = Product.objects.filter(type='Matière Première', check_minmax=True, family__nb_days_min__gt=0, family__nb_days_max__gt=0).select_related('family')
    global_qtes = Disponibility.objects.filter(product__in=products).values('product').annotate(total_qte=Sum('qte'))
    qte_dict = {item['product']: item['total_qte'] or 0 for item in global_qtes}
    cons_dict = calculate_global_consumption(products, days=60)

    for mp in products:
        if not mp.family:
            continue
            
        actual_qte = qte_dict.get(mp.id, 0)
        cons_last_2_months = cons_dict.get(mp.id, 0)
        
        if cons_last_2_months <= 0:
            continue
            
        nj = math.floor(actual_qte / cons_last_2_months) * 60
        family = mp.family
        
        if nj < family.nb_days_min:
            global_mp.append({ 'type': 'mp_global_min',  'product': mp,  'nj': nj,  'required': family.nb_days_min, 'actual_qte': actual_qte, 'cons_last_2_months': cons_last_2_months })
        elif nj > family.nb_days_max:
            global_mp.append({ 'type': 'mp_global_max',  'product': mp,  'nj': nj,  'required': family.nb_days_max, 'actual_qte': actual_qte, 'cons_last_2_months': cons_last_2_months })
        else:
            by_site_mp.append(check_min_max_mp_by_site(mp))
    
    return global_mp, by_site_mp

def check_min_max_mp_by_site(product):
    sites = Site.objects.all()
    alerts = []
    
    site_qtes = Disponibility.objects.filter(product=product, emplacement__warehouse__site__in=sites).values('emplacement__warehouse__site').annotate(total_qte=Sum('qte'))
    qte_dict = {item['emplacement__warehouse__site']: item['total_qte'] or 0 for item in site_qtes}
    
    cons_dict = calculate_site_consumption(product, sites)
    
    for site in sites:
        actual_qte = qte_dict.get(site.id, 0)
        cons_last_2_months = cons_dict.get(site.id, 0)
        
        if cons_last_2_months <= 0:
            continue
            
        nj = math.floor(actual_qte / cons_last_2_months) * 60
        family = product.family
        
        if nj < family.nb_days_min:
            return { 'type': 'mp_site_min', 'product': product, 'site': site, 'nj': nj, 'required': family.nb_days_min, 'actual_qte': actual_qte, 'cons_last_2_months': cons_last_2_months }
        elif nj > family.nb_days_max:
            return { 'type': 'mp_site_max', 'product': product, 'site': site, 'nj': nj, 'required': family.nb_days_max, 'actual_qte': actual_qte, 'cons_last_2_months': cons_last_2_months }
    
    return

# ====================== PF (Produits Finis) ======================
def check_min_max_pf_by_site():
    products = Product.objects.filter(type='Produit Fini', check_minmax=True, family__nb_days_min__gt=0, family__nb_days_max__gt=0).select_related('family')
    by_site_mp = []
    for pf in products:
        if not pf.family:
            continue
        by_site_mp.append(check_min_max_pf_by_site_product(pf))

    return by_site_mp

def check_min_max_pf_by_site_product(product):
    sites = Site.objects.all()
    
    site_qtes = Disponibility.objects.filter(product=product, emplacement__warehouse__site__in=sites).values('emplacement__warehouse__site').annotate(total_qte=Sum('qte'))
    qte_dict = {item['emplacement__warehouse__site']: item['total_qte'] or 0 for item in site_qtes}
    
    cons_dict = calculate_site_consumption(product, sites)
    
    for site in sites:
        actual_qte = qte_dict.get(site.id, 0)
        cons_last_2_months = cons_dict.get(site.id, 0)
        
        if cons_last_2_months <= 0:
            continue
            
        nj = math.floor(actual_qte / cons_last_2_months) * 60
        family = product.family
        
        if nj < family.nb_days_min:
            return { 'type': 'pf_site_min', 'product': product, 'site': site, 'nj': nj, 'required': family.nb_days_min, 'actual_qte': actual_qte, 'cons_last_2_months': cons_last_2_months }
        elif nj > family.nb_days_max:
            return { 'type': 'pf_site_max', 'product': product, 'site': site, 'nj': nj, 'required': family.nb_days_max, 'actual_qte': actual_qte, 'cons_last_2_months': cons_last_2_months }
    
    return

# ====================== SHARED HELPER FUNCTIONS ======================
def calculate_global_consumption(products, days=60):
    move_lines = MoveLine.objects.filter(product__in=products, move__type='Sortie', move__state='Validé', move__date__gte=timezone.now() - timedelta(days=days),
                                         move__is_isolation=False).select_related('product')
    
    cons_dict = defaultdict(int)
    for ml in move_lines:
        cons_dict[ml.product_id] += ml.qte
    return cons_dict

def calculate_site_consumption(product, sites):
    move_lines = MoveLine.objects.filter(product=product, move__type='Sortie', move__state='Validé', move__date__gte=timezone.now() - timedelta(days=60), 
                                         move__is_isolation=False, move__site__in=sites).select_related('move__site')
    
    cons_dict = defaultdict(int)
    for ml in move_lines:
        cons_dict[ml.move.site_id] += ml.qte
    return cons_dict

def send_site_inventory_reports():
    today = timezone.now().date()
    sites = Site.objects.all()
    
    for site in sites:
        families = Family.objects.filter(products__disponibilities__emplacement__warehouse__site=site, for_mp=False).distinct()
        
        if not families.exists():
            continue
        
        family_data = []
        
        for family in families:
            products_data = []
            products = Product.objects.filter(family=family, disponibilities__emplacement__warehouse__site=site).distinct()
            
            for product in products:
                lot_groups = Disponibility.objects.filter(product=product, emplacement__warehouse__site=site).values('n_lot', 'expiry_date').annotate(
                    total_palettes=Sum('palette'), total_units=Sum('nqte'), total_quantity=Sum('qte'), 
                    units_per_palette=F('product__qte_per_pal')).order_by('n_lot')
                
                if not lot_groups:
                    continue
                
                products_data.append({'product': product, 'lot_groups': lot_groups,
                    'product_total': {
                        'palettes': sum(lg['total_palettes'] for lg in lot_groups),
                        'units': sum(lg['total_units'] for lg in lot_groups),
                        'quantity': sum(lg['total_quantity'] for lg in lot_groups),
                    }
                })
            
            if products_data:
                family_data.append({'family': family, 'products': products_data,
                    'family_total': {
                        'palettes': sum(p['product_total']['palettes'] for p in products_data),
                        'units': sum(p['product_total']['units'] for p in products_data),
                        'quantity': sum(p['product_total']['quantity'] for p in products_data),
                    }
                })
        
        if not family_data:
            continue
        
        subject = f"[PAR N LOT] Stock {site.designation} - {today.strftime('%d/%m/%Y')}"
        html_message = render_to_string('fragment/site_inventory_report.html', {'site': site, 'today': today, 'family_data': family_data})

        addresses = site.email.split('&') if site.email else []
        if not addresses:
            addresses = ['mohammed.senoussaoui@grupopuma-dz.com']

        print(addresses, subject)
        email = EmailMultiAlternatives(subject, None, 'Puma Stock', addresses)
        email.attach_alternative(html_message, "text/html")
        email.send()


def get_btr_recommendations(alerts):

    def get_alerts_below_threshold(items):
        return [item for item in items if item['nj'] < item['product'].family.nb_min_btr]
    
    recommendations = []
    recommended_alerts = get_alerts_below_threshold(alerts)
    sites = Site.objects.all()
    
    for alert in recommended_alerts:
        filtred_sited = sites.exclude(id=alert['site'].id)
        product = alert['product']
        site_qtes = Disponibility.objects.filter(product=product, emplacement__warehouse__site__in=filtred_sited).values('emplacement__warehouse__site').annotate(total_qte=Sum('qte'))
        qte_dict = {item['emplacement__warehouse__site']: item['total_qte'] or 0 for item in site_qtes}
        cons_dict = calculate_site_consumption(product, filtred_sited)
    
        for site in filtred_sited:
            actual_qte = qte_dict.get(site.id, 0)
            cons_last_2_months = cons_dict.get(site.id, 0)
            
            if cons_last_2_months <= 0:
                continue

            nj = math.floor(actual_qte / cons_last_2_months) * 60
            family = product.family
        
            if nj > family.nb_min_btr:
                recommendations.append({'alert_site': alert['site'], 'alert_nj': alert['nj'], 'type': 'btr_recommendation', 'product': product,
                'site': site, 'nj': nj, 'required': family.nb_min_btr, 'actual_qte': actual_qte, 'cons_last_2_months': cons_last_2_months})
                break

    sorted_items = sorted(recommendations, key=lambda x: (x.get('alert_site').designation, x.get('product').family.sequence, x.get('alert_nj')))

    site_groups = {}
    for item in sorted_items:
        site_name = item.get('alert_site').designation
        if site_name not in site_groups:
            site_groups[site_name] = []
        site_groups[site_name].append(item)
        
    return site_groups

def send_btr_recommendations(alerts):
    sites = list(Site.objects.all())
    alerts = get_btr_recommendations(alerts)
    
    for site in sites:
        site_name = site.designation
        site_recipients = []
        
        if site and site.email:
            site_recipients = site.email.split('&')
        else:
            site_recipients = ['mohammed.senoussaoui@grupopuma-dz.com']

        if site_name in alerts and alerts[site_name]:
            subject=f"[MP BTR - {site_name}] Alerte Stock"
            today = timezone.now().date()
            html = render_to_string('fragment/btr_alert.html', {'alert_data': alerts[site_name], 'today': today})
            email = EmailMultiAlternatives(subject, None, 'Puma Stock', site_recipients)
            email.attach_alternative(html, "text/html")
            email.send()