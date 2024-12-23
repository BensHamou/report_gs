from account.decorators import admin_required, getRedirectionURL, admin_or_gs_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.forms import modelformset_factory
from django.core.paginator import Paginator
from django.contrib import messages
from django.db import transaction
from django.urls import reverse
from .filters import *
from .models import *
from account.models import *
from .forms import *
import qrcode
from datetime import date, datetime
from .utils import getMProducts
from django.utils.timezone import now, timedelta

# PACKING

@login_required(login_url='login')
@admin_required
def listPackingView(request):
    packings = Packing.objects.all().order_by('-date_modified')
    filteredData = PackingFilter(request.GET, queryset=packings)
    packings = filteredData.qs
    paginator = Paginator(packings, request.GET.get('page_size', 12))
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    
    context = {'page': page, 'filteredData': filteredData}
    return render(request, 'list_packings.html', context)

@login_required(login_url='login')
@admin_required
def deletePackingView(request, id):
    packing = get_object_or_404(Packing, id=id)
    try:
        packing.delete()
        url_path = reverse('packings')
        return redirect(getRedirectionURL(request, url_path))
    except Exception as e:
        messages.error(request, f"Erreur lors de la suppression de conditionnement : {e}")
        return redirect(getRedirectionURL(request, reverse('packings')))

@login_required(login_url='login')
@admin_required
def createPackingView(request):
    form = PackingForm()
    if request.method == 'POST':
        form = PackingForm(request.POST)
        if form.is_valid():
            form.save()
            url_path = reverse('packings')
            return redirect(getRedirectionURL(request, url_path))
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    
    context = {'form': form}
    return render(request, 'packing_form.html', context)

@login_required(login_url='login')
@admin_required
def editPackingView(request, id):
    packing = get_object_or_404(Packing, id=id)
    form = PackingForm(instance=packing)
    
    if request.method == 'POST':
        form = PackingForm(request.POST, instance=packing)
        if form.is_valid():
            form.save()
            url_path = reverse('packings')
            return redirect(getRedirectionURL(request, url_path))
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    
    context = {'form': form, 'packing': packing}
    return render(request, 'packing_form.html', context)

# FAMILY

@login_required(login_url='login')
@admin_required
def listFamilyView(request):
    families = Family.objects.all().order_by('-date_modified')
    filteredData = FamilyFilter(request.GET, queryset=families)
    families = filteredData.qs
    page_size_param = request.GET.get('page_size')
    page_size = int(page_size_param) if page_size_param else 12
    paginator = Paginator(families, page_size)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {'page': page, 'filteredData': filteredData}
    return render(request, 'list_families.html', context)

@login_required(login_url='login')
@admin_required
def deleteFamilyView(request, id):
    family = get_object_or_404(Family, id=id)
    try:
        family.delete()
        messages.success(request, "Famille supprimée avec succès.")
    except Exception as e:
        messages.error(request, f"Erreur lors de la suppression de la famille : {e}")
    return redirect(getRedirectionURL(request, reverse('families')))

@login_required(login_url='login')
@admin_required
def createFamilyView(request):
    form = FamilyForm()
    if request.method == 'POST':
        form = FamilyForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Famille créée avec succès.")
            return redirect(getRedirectionURL(request, reverse('families')))
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    context = {'form': form}
    return render(request, 'family_form.html', context)

@login_required(login_url='login')
@admin_required
def editFamilyView(request, id):
    family = get_object_or_404(Family, id=id)
    form = FamilyForm(instance=family)
    if request.method == 'POST':
        form = FamilyForm(request.POST, request.FILES, instance=family)
        if form.is_valid():
            form.save()
            messages.success(request, "Famille mise à jour avec succès.")
            return redirect(getRedirectionURL(request, reverse('families')))
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    context = {'form': form, 'family': family}
    return render(request, 'family_form.html', context)

# PRODUCT

@login_required(login_url='login')
@admin_required
def listProductView(request):
    products = Product.objects.filter(type='Produit Fini').order_by('-date_modified')
    sites = Line.objects.filter(id__in=request.user.lines.all()).values('site_id', 'site__designation').distinct()

    selected_site_id = request.GET.get('site')
    selected_site = None

    if selected_site_id:
        selected_site = Site.objects.get(id=selected_site_id)
    else:
        selected_site = request.user.default_site

    filteredData = ProductFilter(request.GET, queryset=products)
    products = filteredData.qs

    page_size_param = request.GET.get('page_size')
    page_size = int(page_size_param) if page_size_param else 12
    paginator = Paginator(products, page_size)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    products_with_stock = []
    if selected_site:
        for product in page:
            products_with_stock.append({
                'id': product.id,
                'designation': product.designation,
                'tn_qte': product.tn_qte(selected_site.id),
                'state_stock': product.state_stock(selected_site.id),
                'last_entry_date': product.last_entry_date(selected_site.id),
                'type': product.type,
            })
    else:
        products_with_stock = [{'id': product.id, 'designation': product.designation, 'tn_qte': None, 'state_stock': 'Site non sélectionné', 'last_entry_date': None} for product in page]

    context = {
        'page': page,
        'products_with_stock': products_with_stock,
        'filteredData': filteredData,
        'allowed_sites': sites,
        'selected_site': selected_site,
        'default_site': request.user.default_site,
        'is_pf': True
    }
    return render(request, 'list_products.html', context)

@login_required(login_url='login')
@admin_required
def deleteProductView(request, id):
    product = get_object_or_404(Product, id=id)
    try:
        product.delete()
        messages.success(request, "Produit supprimée avec succès.")
    except Exception as e:
        messages.error(request, f"Erreur lors de la suppression du produit : {e}")
    return redirect(getRedirectionURL(request, reverse('products')))

@login_required(login_url='login')
@admin_required
def createProductView(request):
    form = ProductForm()
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Produit créé avec succès.")
            return redirect(getRedirectionURL(request, reverse('products')))
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    
    context = {'form': form, 'is_pf': True}
    return render(request, 'product_form.html', context)

@login_required(login_url='login')
@admin_required
def editProductView(request, id):
    product = get_object_or_404(Product, id=id)
    form = ProductForm(instance=product)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Produit mis à jour avec succès.")
            return redirect(getRedirectionURL(request, reverse('products')))
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    
    context = {'form': form, 'product': product, 'is_pf': True}
    return render(request, 'product_form.html', context)


# MP

@login_required(login_url='login')
@admin_required
def listMProductView(request):
    products = Product.objects.filter(type='Matière Première').order_by('-date_modified')
    sites = Line.objects.filter(id__in=request.user.lines.all()).values('site_id', 'site__designation').distinct()

    selected_site_id = request.GET.get('site')
    selected_site = None

    if selected_site_id:
        selected_site = Site.objects.get(id=selected_site_id)
    else:
        selected_site = request.user.default_site

    filteredData = ProductFilter(request.GET, queryset=products)
    products = filteredData.qs

    page_size_param = request.GET.get('page_size')
    page_size = int(page_size_param) if page_size_param else 12
    paginator = Paginator(products, page_size)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    products_with_stock = []
    if selected_site:
        for product in page:
            products_with_stock.append({
                'id': product.id,
                'designation': product.designation,
                'tn_qte': product.tn_qte(selected_site.id),
                'state_stock': product.state_stock(selected_site.id),
                'last_entry_date': product.last_entry_date(selected_site.id),
                'type': product.type,
            })
    else:
        products_with_stock = [{'id': product.id, 'designation': product.designation, 'tn_qte': None, 'state_stock': 'Site non sélectionné', 
                                'last_entry_date': None } for product in page]

    context = {
        'page': page,
        'products_with_stock': products_with_stock,
        'filteredData': filteredData,
        'allowed_sites': sites,
        'selected_site': selected_site,
        'default_site': request.user.default_site,
        'is_pf': False
    }
    return render(request, 'list_products.html', context)

@login_required(login_url='login')
@admin_required
def editMProductView(request, id):
    product = get_object_or_404(Product, id=id)
    form = MProductForm(instance=product)
    
    if request.method == 'POST':
        form = MProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Produit mis à jour avec succès.")
            return redirect(getRedirectionURL(request, reverse('mproducts')))
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    
    context = {'form': form, 'product': product, 'is_pf': False}
    return render(request, 'product_form.html', context)

@login_required(login_url='login')
@admin_required
def syncMProducts(request):
    if request.method == 'POST':
        try:
            for mp in getMProducts():
                designation = f'[{mp[2]}] {mp[1]}'
                odoo_id = mp[0]
                Product.objects.update_or_create(
                    odoo_id=odoo_id,
                    defaults={'designation': designation, 'type': 'Matière Première', 'create_uid': request.user, 'write_uid': request.user, 
                              'qte_per_pal': 0, 'qte_per_cond': 0, 'alert_stock': 0}
                )
            return JsonResponse({'success': True, 'message': 'Matière Première synchronisés avec succès.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erreur pendant la synchronisation: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Méthode de demande non valide.'})

# MOVES

@login_required(login_url='login')
@admin_or_gs_required
def categories_view(request):
    return render(request, 'categories.html')

# MOVE IN

@login_required(login_url='login')
@admin_or_gs_required
def list_move(request):
    moves = Move.objects.filter(Q(gestionaire=request.user) | Q(line__in=request.user.lines.all().values('id'))).order_by('-date_modified')    
    filteredData = MoveFilter(request.GET, queryset=moves)
    moves = filteredData.qs
    page_size_param = request.GET.get('page_size')
    page_size = int(page_size_param) if page_size_param else 12
    paginator = Paginator(moves, page_size)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    today = date.today()
    move_out_today = Move.objects.filter(state='Validé', type='Sortie', date=today)
    palettes_today = sum(m.palette for m in move_out_today)

    move_lines = MoveLine.objects.filter(move__state='Validé', move__type='Sortie').select_related('product')
    
    product_totals = {}
    for move_line in move_lines:
        product_id = move_line.product.id
        if product_id not in product_totals:
            product_totals[product_id] = {
                'designation': move_line.product.designation,
                'image': move_line.product.image.url if move_line.product.image else None,
                'total_qte': 0,
            }
        product_totals[product_id]['total_qte'] += move_line.qte
    top_product = max(product_totals.values(), key=lambda p: p['total_qte'], default=None)
    active_users_count = User.objects.filter(last_login__gte=now() - timedelta(hours=24)).count()


    context = {'page': page, 'filteredData': filteredData, 'palettes_today': palettes_today, 'top_product': top_product, 'active_users_count': active_users_count}
    return render(request, 'move_list.html', context)

@login_required(login_url='login')
@admin_or_gs_required
def delete_move(request, move_id):
    move = get_object_or_404(Move, id=move_id)
    try:
        move.delete()
        messages.success(request, "Movement supprimée avec succès.")
    except Exception as e:
        messages.error(request, f"Erreur lors de la suppression du Movement : {e}")
    return redirect(getRedirectionURL(request, reverse('moves')))

# MOVE IN - Produit Fini

@login_required(login_url='login')
@admin_or_gs_required
def families_view(request):
    families = Family.objects.all()
    return render(request, 'families.html', {'families': families})

@login_required(login_url='login')
@admin_or_gs_required
def products_view(request, family_id):
    family = get_object_or_404(Family, id=family_id)
    products = Product.objects.filter(family=family, type='Produit Fini')
    return render(request, 'products.html', {'products': products, 'family': family})

@login_required(login_url='login')
@admin_or_gs_required
def create_move_in_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    MoveLineDetailFormSet = modelformset_factory(LineDetail, fields=('warehouse', 'emplacement', 'qte'), extra=1)
    
    user = request.user
    user_lines = user.lines.all()
    is_admin = user.role == 'Admin'
    
    default_line = user_lines.first() if user_lines.count() == 1 else None
    show_line_field = user_lines.count() > 1
    if is_admin:
        gestionaires = None if user.lines.count() > 1 else user.lines.first().users.filter(Q(role='Gestionaire') | Q(role='Admin'))
    else:
        gestionaires = None

    formset = MoveLineDetailFormSet(queryset=LineDetail.objects.none())

    return render(request, 'form.html', {'product': product, 'formset': formset, 'lines': user_lines if show_line_field else None, 
                                         'gestionaires': gestionaires, 'default_line': default_line, 'is_admin': is_admin, 'show_line_field': show_line_field})

@login_required(login_url='login')
@admin_or_gs_required
def edit_move_in_view(request, move_line_id):
    move_line = get_object_or_404(MoveLine, id=move_line_id)
    move = move_line.move
    line_details = move_line.details.all()
    user = request.user
    user_lines = user.lines.all()
    is_admin = user.role == 'Admin'
    default_line = move_line.move.line or user_lines.first()
    show_line_field = user_lines.count() > 1 and not move.is_transfer
    gestionaires = default_line.users.filter(Q(role='Gestionaire') | Q(role='Admin'))
    default_shifts = default_line.shifts.all()

    context = {
        'move': move_line.move,
        'move_line': move_line,
        'line_details': line_details,
        'product': move_line.product,
        'default_shifts': default_shifts,
        'lines': user_lines if show_line_field else None,
        'gestionaires': gestionaires,
        'default_line': default_line,
        'is_admin': is_admin,
        'show_line_field': show_line_field,
        'warehouses': move_line.move.site.warehouses.all(),
        'emplacements': Emplacement.objects.all()
    }
    return render(request, 'edit_move.html', context)

@login_required(login_url='login')
@admin_or_gs_required
def create_move_pf(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                site_id = request.POST.get('site')
                line_id = request.POST.get('line')
                shift_id = request.POST.get('shift')
                gestionaire_id = request.POST.get('gestionaire')
                lot_number = request.POST.get('lot_number')
                production_date = request.POST.get('production_date')
                product = request.POST.get('product')
                production_year = datetime.strptime(production_date, "%Y-%m-%d").year
                if not (site_id and line_id and shift_id and gestionaire_id):
                    return JsonResponse({'success': False, 'message': 'Les champs Ligne, Shift, Date et Gestionaire sont obligatoires.'}, status=200)
                existing_move_line = MoveLine.objects.filter(lot_number=lot_number, move__date__year=production_year, move__line_id=line_id, product__type='Produit Fini')
                if existing_move_line.exists():
                    return JsonResponse({'success': False, 'message': f'N° Lot {lot_number} existe déjà.'}, status=200)
                move = Move.objects.create(line_id=line_id, site_id=site_id, shift_id=shift_id, gestionaire_id=gestionaire_id, date=production_date,  
                                           state='Brouillon',  type='Entré',  create_uid=request.user, write_uid=request.user)
                move_line = MoveLine.objects.create(lot_number=lot_number, product_id=product, move_id=move.id, create_uid=request.user, write_uid=request.user, lost_qte=0)
                handleDetails(request, move_line)

                return JsonResponse({'success': True, 'message': 'Entrée créée avec succès.', 'new_record': move_line.move.id}, status=200)

        except Exception as e:
            print(str(e))
            return JsonResponse({'success': False, 'message': f'Erreur lors du traitement de la demande: {str(e)}'}, status=500)

@login_required(login_url='login')
@admin_or_gs_required
def update_move_pf(request, move_line_id):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                site_id = request.POST.get('site', None)
                line_id = request.POST.get('line', None)
                shift_id = request.POST.get('shift', None)
                gestionaire_id = request.POST.get('gestionaire', None)
                lot_number = request.POST.get('lot_number', None)
                production_date = request.POST.get('production_date', None)
                lost_qte = request.POST.get('lost_qte', 0)
                do_check = request.POST.get('do_check')
                move_line = MoveLine.objects.get(id=move_line_id)
                if do_check == 0:
                    production_year = datetime.strptime(production_date, "%Y-%m-%d").year
                    if not (line_id and gestionaire_id):
                        return JsonResponse({'success': False, 'message': 'Les champs Ligne, Date et Gestionaire sont obligatoire.'}, status=200)
                    existing_move_line = MoveLine.objects.filter(lot_number=lot_number, move__line=move_line.move.line, move__date__year=production_year).exclude(id=move_line_id)
                    if existing_move_line.exists() and do_check == 0:
                        return JsonResponse({'success': False, 'message': f'N° Lot {lot_number} existe déjà.'}, status=200)
                    if shift_id:
                        move.shift_id = shift_id
                    else:
                        return JsonResponse({'success': False, 'message': 'Le champs Shift est obligatoire.'}, status=200)
                move = Move.objects.get(id=move_line.move.id)
                if not move.is_transfer:
                    move.site_id = site_id
                    move.line_id = line_id
                    move.gestionaire_id = gestionaire_id
                    move.date = production_date
                    move_line.lot_number = lot_number
                handleDetails(request, move_line)
                move.write_uid = request.user
                move.save()
                move_line.write_uid = request.user
                move_line.lost_qte = lost_qte
                move_line.save()
                return JsonResponse({'success': True, 'message': 'Entrée mise à jour avec succès.'}, status=200)
        except Move.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Entré non trouvée.'}, status=200)
        except MoveLine.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Entré non trouvée.'}, status=200)
        except Exception as e:
            print(str(e))
            return JsonResponse({'success': False, 'message': f'Erreur lors du traitement de la demande: {str(e)}'}, status=500)

# MOVE IN - Matière Première

@login_required(login_url='login')
@admin_or_gs_required
def create_move_in_mp_view(request):
    products = Product.objects.filter(type='Matière Première')
    default_site = request.user.default_site
    default_line = default_site.lines.first()
    MoveLineDetailFormSet = modelformset_factory(LineDetail, fields=('warehouse', 'emplacement', 'qte'), extra=1)
    formset = MoveLineDetailFormSet(queryset=LineDetail.objects.none())
    return render(request, 'form_mp.html', {'products': products, 'formset': formset, 'default_site': default_site.id, 'default_line': default_line.id})

@login_required(login_url='login')
@admin_or_gs_required
def edit_move_in_mp_view(request, move_line_id):
    move_line = get_object_or_404(MoveLine, id=move_line_id)
    products = Product.objects.filter(type='Matière Première')
    line_details = move_line.details.all()
    default_site = move_line.move.site
    default_line = default_site.lines.first()
    return render(request, 'edit_move_mp.html', {'products': products, 'default_site': default_site.id, 'move_line': move_line,
                                                 'default_line': default_line.id, 'default_product': move_line.product, 'warehouses': default_site.warehouses.all(),
                                                 'emplacements': Emplacement.objects.all(), 'line_details': line_details})

@login_required(login_url='login')
@admin_or_gs_required
def create_move_mp(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                site_id = request.POST.get('site')
                lot_number = request.POST.get('lot_number')
                product = request.POST.get('product')
                observation = request.POST.get('observation', '/')
                if not site_id or not lot_number or not product:
                    return JsonResponse({'success': False, 'message': 'Les champs Site, N° Lot et Produit sont obligatoires.'}, status=200)
                cu = request.user
                move = Move.objects.create(site_id=site_id, gestionaire=cu, state='Brouillon', type='Entré', create_uid=cu, write_uid=cu)
                move_line = MoveLine.objects.create(lot_number=lot_number, product_id=product, observation=observation, move_id=move.id, create_uid=cu, write_uid=cu, lost_qte=0)
                handleDetails(request, move_line)
                return JsonResponse({'success': True, 'message': 'Entrée créée avec succès.', 'new_record': move_line.move.id}, status=200)

        except Exception as e:
            print(str(e))
            return JsonResponse({'success': False, 'message': f'Erreur lors du traitement de la demande: {str(e)}'}, status=500)

@login_required(login_url='login')
@admin_or_gs_required
def update_move_mp(request, move_line_id):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                site_id = request.POST.get('site')
                lot_number = request.POST.get('lot_number')
                product = request.POST.get('product')
                observation = request.POST.get('observation', '/')
                lost_qte = request.POST.get('lost_qte', 0)
                if not site_id or not lot_number or not product:
                    return JsonResponse({'success': False, 'message': 'Les champs Site, N° Lot et Produit sont obligatoires.'}, status=200)

                move_line = MoveLine.objects.get(id=move_line_id)
                move = Move.objects.get(id=move_line.move.id)
                cu = request.user

                move.site_id = site_id
                move.gestionaire = cu
                move.write_uid = cu
                move.save()

                move_line.lot_number = lot_number
                move_line.observation = observation
                move_line.write_uid = cu
                move_line.lost_qte = lost_qte
                move_line.save()
                handleDetails(request, move_line)
                            
                return JsonResponse({'success': True, 'message': 'Entrée mise à jour avec succès.'}, status=200)
        except Move.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Entré non trouvée.'}, status=200)
        except MoveLine.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Entré non trouvée.'}, status=200)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erreur lors du traitement de la demande: {str(e)}'}, status=500)


# VIEWS 

@login_required(login_url='login')
@admin_or_gs_required        
def move_detail(request, move_id):
    move = get_object_or_404(Move, id=move_id)
    can_edit, can_cancel, can_confirm, can_validate, can_print = False, False, False, False, move.state == 'Validé' and move.type == 'Entré'
    if request.user.role == 'Admin':
        can_edit = True
        can_cancel = move.state == 'Brouillon'
        can_confirm = move.state == 'Brouillon'
        can_validate = move.state == 'Confirmé'
    elif request.user.role == 'Gestionaire' and move.gestionaire == request.user:
        can_edit = move.state == 'Brouillon'
        can_cancel = move.state == 'Brouillon'
        can_confirm = move.state == 'Brouillon'
    elif request.user.role == 'Validateur' and move.site == request.user.default_site:
        can_validate = move.state == 'Confirmé'

    context = {'move': move, 'can_edit': can_edit, 'can_cancel': can_cancel, 'can_confirm': can_confirm, 'can_validate': can_validate, 'can_print': can_print}
    return render(request, 'details_move.html', context)

@login_required(login_url='login')
@admin_or_gs_required
def confirmMove(request, move_id):
    if request.method == 'POST':
        try:
            move = Move.objects.get(id=move_id)
        except Move.DoesNotExist:
            messages.success(request, 'Movement introuvable')
            return JsonResponse({'success': False, 'message': 'Movement introuvable.'})
        
        if move.is_transfer and move.type == 'Entré':
            try:
                move.check_can_confirm_transfer()
            except ValueError as e:
                return JsonResponse({'success': False, 'message': 'Quantité transférée non égale à la quantité reçue'})
        success = move.changeState(request.user.id, 'Confirmé')
        if success:
            return JsonResponse({'success': True, 'message': 'Movement confirmé avec succès.', 'move_id': move_id})
        else:
            return JsonResponse({'success': False, 'message': 'Erreur lors de la confirmation du movement.'})
    return JsonResponse({'success': False, 'message': 'Méthode de requête non valide.'})

@login_required(login_url='login')
@admin_or_gs_required
def validateMove(request, move_id):
    if request.method == 'POST':
        try:
            move = Move.objects.get(id=move_id)
        except Move.DoesNotExist:
            messages.success(request, 'Movement introuvable')
            return JsonResponse({'success': False, 'message': 'Movement introuvable.'})
        
        # try:
        #     move.can_validate()
        # except ValueError as e:
        #     return JsonResponse({'success': False, 'message': str(e)})
        
        success = move.changeState(request.user.id, 'Validé')
        if success:
            try:
                success, message = move.do_after_validation(request.user)
                return JsonResponse({'success': True, 'message': message, 'move_id': move_id})
            except ValueError as e:
                return JsonResponse({'success': False, 'message': str(e)})
        else:
            return JsonResponse({'success': False, 'message': 'Erreur lors de la validation du movement.'})
    return JsonResponse({'success': False, 'message': 'Méthode de requête non valide.'})

@login_required(login_url='login')
@admin_or_gs_required
def cancelMove(request, move_id):
    if request.method == 'POST':
        try:
            move = Move.objects.get(id=move_id)
        except Move.DoesNotExist:
            messages.success(request, 'Movement introuvable')
            return JsonResponse({'success': False, 'message': 'Movement introuvable.'})
        success = move.changeState(request.user.id, 'Annulé')
        if success:
            return JsonResponse({'success': True, 'message': 'Movement annulé avec succès.', 'move_id': move_id})
        else:
            return JsonResponse({'success': False, 'message': 'Erreur lors de l\'annulation du movement.'})
    return JsonResponse({'success': False, 'message': 'Méthode de requête non valide.'})


# FETCH JSON

@login_required(login_url='login')
@admin_or_gs_required
def get_shifts_and_users_for_line(request):
    line_id = request.GET.get('line_id')
    line = get_object_or_404(Line, id=line_id)
    
    shifts = line.shifts.all()
    users = line.users.filter(Q(role='Gestionaire') | Q(role='Admin'))
    
    shift_data = [{'id': shift.id, 'name': shift.designation} for shift in shifts]
    user_data = [{'id': user.id, 'name': user.fullname} for user in users]
    
    return JsonResponse({'shifts': shift_data, 'users': user_data, 'site': line.site.id})

@login_required(login_url='login')
@admin_or_gs_required
def get_warehouses_for_line(request):
    line_id = request.GET.get('line_id')
    line = Line.objects.get(id=line_id)
    warehouses = Warehouse.objects.filter(site=line.site)
    warehouse_data = [{'id': warehouse.id, 'name': warehouse.designation} for warehouse in warehouses]

    return JsonResponse({'warehouses': warehouse_data, 'site_id': line.site.id})

@login_required(login_url='login')
@admin_or_gs_required
def get_warehouses_for_site(request):
    site_id = request.GET.get('site_id')
    warehouses = Warehouse.objects.filter(site__id=site_id)
    warehouse_data = [{'id': warehouse.id, 'name': warehouse.designation} for warehouse in warehouses]
    return JsonResponse({'warehouses': warehouse_data})

@login_required(login_url='login')
@admin_or_gs_required
def get_emplacements_for_warehouse(request):
    warehouse_id = request.GET.get('warehouse_id')
    warehouse = Warehouse.objects.get(id=warehouse_id)
    emplacements = Emplacement.objects.filter(warehouse=warehouse)
    emplacement_data = [{'id': emplacement.id, 'name': emplacement.designation} for emplacement in emplacements]

    return JsonResponse({'emplacements': emplacement_data})

@login_required(login_url='login')
@admin_or_gs_required
def generateQRCode(request, detail_id):
    try:
        line_detail = LineDetail.objects.get(id=detail_id)
        qr_data = line_detail.code
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')

        response = HttpResponse(content_type="image/png")
        img.save(response, "PNG")
        return response

    except MoveLine.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Move non trouvé.'})

def handleDetails(request, move_line):
    n_lot = move_line.n_lot
    if not len(move_line.details.all()) == 0:
        existing_line_details = LineDetail.objects.filter(move_line=move_line)
        existing_ids = [str(detail.id) for detail in existing_line_details]
        to_update_rows = [key.split('_')[2] for key in request.POST.keys() if key.startswith('detail_id_') and request.POST[key]]
        to_add_rows = [key.split('_')[2] for key in request.POST.keys() if key.startswith('detail_id_') and not request.POST[key]]
        to_update_ids = [request.POST.get(f'detail_id_{row_id}') for row_id in to_update_rows]
        to_delete_ids = [detail_id for detail_id in existing_ids if detail_id not in to_update_ids]

        LineDetail.objects.filter(id__in=to_delete_ids).delete()

        for row_id in to_update_rows:
            detail_id = request.POST.get(f'detail_id_{row_id}')
            warehouse_id = request.POST.get(f'warehouse_{row_id}')
            emplacement_id = request.POST.get(f'emplacement_{row_id}')
            qte = request.POST.get(f'qte_{row_id}')
            if warehouse_id and emplacement_id and qte:
                LineDetail.objects.filter(id=detail_id).update(warehouse_id=warehouse_id, emplacement_id=emplacement_id, qte=int(qte), write_uid=request.user, n_lot=n_lot)

        for row_id in to_add_rows:
            warehouse_id = request.POST.get(f'warehouse_{row_id}')
            emplacement_id = request.POST.get(f'emplacement_{row_id}')
            qte = request.POST.get(f'qte_{row_id}')

            if warehouse_id and emplacement_id and qte:
                LineDetail.objects.create(move_line=move_line, warehouse_id=warehouse_id, emplacement_id=emplacement_id, n_lot=n_lot, 
                                        qte=int(qte), write_uid=request.user, create_uid=move_line.create_uid)
    else:
        row_ids = [key.split('_')[1] for key in request.POST.keys() if key.startswith('warehouse_')]
        for row_id in row_ids:
            warehouse_id = request.POST.get(f'warehouse_{row_id}')
            emplacement_id = request.POST.get(f'emplacement_{row_id}')
            qte = request.POST.get(f'qte_{row_id}')

            if warehouse_id and emplacement_id and qte:
                line_detail = LineDetail.objects.create(move_line=move_line, warehouse_id=warehouse_id, emplacement_id=emplacement_id, 
                                                        n_lot=n_lot, qte=int(qte), create_uid=request.user, write_uid=request.user)
                
