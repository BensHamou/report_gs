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
                    defaults={'designation': designation, 'type': 'Matière Première'}
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
    moves = MoveLine.objects.filter(Q(move__gestionaire=request.user) | Q(move__line__in=request.user.lines.all().values('id'))).order_by('-date_modified')    
    filteredData = MoveLineFilter(request.GET, queryset=moves)
    moves = filteredData.qs
    page_size_param = request.GET.get('page_size')
    page_size = int(page_size_param) if page_size_param else 12
    paginator = Paginator(moves, page_size)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    today = date.today()
    move_out_today = MoveLine.objects.filter(move__state='Confirmé', move__type='Sortie', move__date=today)
    palettes_today = sum(m.palette for m in move_out_today)

    move_lines = MoveLine.objects.filter(move__state='Confirmé', move__type='Sortie').select_related('product')
    
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
def delete_move(request, move_line_id):
    move_line = get_object_or_404(MoveLine, id=move_line_id)
    try:
        if move_line.move.is_transfer:
            for d in move_line.details.all():
                original = LineDetail.objects.get(id=d.mirrored_move.id)
                original.qte += d.qte
                original.save()
        move = Move.objects.get(id=move_line.move.id)
        move_line.delete()
        if move.move_lines.all().count() == 0:
            move.delete()
        messages.success(request, "Move supprimée avec succès.")
    except Exception as e:
        messages.error(request, f"Erreur lors de la suppression du move : {e}")
    return redirect(getRedirectionURL(request, reverse('move_lines')))

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
    default_line = move_line.move.line
    show_line_field = user_lines.count() > 1
    gestionaires = default_line.users.filter(Q(role='Gestionaire') | Q(role='Admin'))
    default_shifts = move.line.shifts.all()

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
        'warehouses': default_line.site.warehouses.all(),
        'emplacements': Emplacement.objects.all(),
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
                
                move_line = MoveLine.objects.create(lot_number=lot_number, product_id=product, move_id=move.id, create_uid=request.user, write_uid=request.user)
                n_lot = move_line.n_lot
                
                row_ids = [key.split('_')[1] for key in request.POST.keys() if key.startswith('warehouse_')]
                for row_id in row_ids:
                    warehouse_id = request.POST.get(f'warehouse_{row_id}')
                    emplacement_id = request.POST.get(f'emplacement_{row_id}')
                    qte = request.POST.get(f'qte_{row_id}')

                    if warehouse_id and emplacement_id and qte:
                        line_detail = LineDetail.objects.create(move_line=move_line, warehouse_id=warehouse_id, emplacement_id=emplacement_id, 
                                                                n_lot=n_lot, qte=int(qte), create_uid=request.user, write_uid=request.user)

                return JsonResponse({'success': True, 'message': 'Entrée créée avec succès.', 'new_record': move_line.id}, status=200)

        except Exception as e:
            print(str(e))
            return JsonResponse({'success': False, 'message': f'Erreur lors du traitement de la demande: {str(e)}'}, status=500)

@login_required(login_url='login')
@admin_or_gs_required
def update_move_pf(request, move_line_id):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                site_id = request.POST.get('site')
                line_id = request.POST.get('line')
                shift_id = request.POST.get('shift', None)
                gestionaire_id = request.POST.get('gestionaire')
                lot_number = request.POST.get('lot_number')
                production_date = request.POST.get('production_date')
                production_year = datetime.strptime(production_date, "%Y-%m-%d").year

                if not (line_id and gestionaire_id):
                    return JsonResponse({'success': False, 'message': 'Les champs Ligne, Date et Gestionaire sont obligatoire.'}, status=200)

                move_line = MoveLine.objects.get(id=move_line_id)

                existing_move_line = MoveLine.objects.filter(lot_number=lot_number, move__line=move_line.move.line, move__date__year=production_year).exclude(id=move_line_id)
                if existing_move_line.exists():
                    return JsonResponse({'success': False, 'message': f'N° Lot {lot_number} existe déjà.'}, status=200)

                move = Move.objects.get(id=move_line.move.id)
                if not move.is_transfer:
                    if shift_id:
                        move.shift_id = shift_id
                    else:
                        return JsonResponse({'success': False, 'message': 'Le champs Shift est obligatoire.'}, status=200)
                    
                move.site_id = site_id
                move.line_id = line_id
                move.gestionaire_id = gestionaire_id
                move.date = production_date
                move.write_uid = request.user
                move.save()

                move_line.lot_number = lot_number
                move_line.write_uid = request.user
                move_line.save()

                n_lot = move_line.n_lot

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

                return JsonResponse({'success': True, 'message': 'Entrée mise à jour avec succès.'}, status=200)
        except Move.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Entré non trouvée.'}, status=200)
        except MoveLine.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Entré non trouvée.'}, status=200)
        except Exception as e:
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
                move_line = MoveLine.objects.create(lot_number=lot_number, product_id=product, observation=observation, move_id=move.id, create_uid=cu, write_uid=cu)
                n_lot = move_line.n_lot
                
                row_ids = [key.split('_')[1] for key in request.POST.keys() if key.startswith('warehouse_')]
                for row_id in row_ids:
                    warehouse_id = request.POST.get(f'warehouse_{row_id}')
                    emplacement_id = request.POST.get(f'emplacement_{row_id}')
                    qte = request.POST.get(f'qte_{row_id}')

                    if warehouse_id and emplacement_id and qte:
                        line_detail = LineDetail.objects.create(move_line=move_line, warehouse_id=warehouse_id, emplacement_id=emplacement_id, 
                                                                n_lot=n_lot, qte=int(qte), create_uid=request.user, write_uid=request.user)

                return JsonResponse({'success': True, 'message': 'Entrée créée avec succès.', 'new_record': move_line.id}, status=200)

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
                move_line.save()

                n_lot = move_line.n_lot

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

                return JsonResponse({'success': True, 'message': 'Entrée mise à jour avec succès.'}, status=200)
        except Move.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Entré non trouvée.'}, status=200)
        except MoveLine.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Entré non trouvée.'}, status=200)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erreur lors du traitement de la demande: {str(e)}'}, status=500)


@login_required(login_url='login')
@admin_or_gs_required
def tarnsfer_list(request):
    transfers = LineDetail.objects.filter(Q(move_line__move__gestionaire=request.user) | Q(move_line__move__line__in=request.user.lines.all().values('id')), move_line__move__is_transfer=True).order_by('-date_modified')    
    filteredData = LineDetailFilter(request.GET, queryset=transfers)
    transfers = filteredData.qs
    page_size_param = request.GET.get('page_size')
    page_size = int(page_size_param) if page_size_param else 12
    paginator = Paginator(transfers, page_size)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {'page': page, 'filteredData': filteredData}
    return render(request, 'transfer_list.html', context)


@login_required(login_url='login')
@admin_or_gs_required        
def move_line_detail(request, move_line_id):
    move_line = get_object_or_404(MoveLine, id=move_line_id)
    can_edit, can_cancel, can_confirm, can_validate, can_print = False, False, False, False, move_line.move.state == 'Validé'
    if request.user.role == 'Admin':
        can_edit = True
        can_cancel = move_line.move.state == 'Brouillon'
        can_confirm = move_line.move.state == 'Brouillon'
        can_validate = move_line.move.state == 'Confirmé'
    elif request.user.role == 'Gestionaire' and move_line.move.gestionaire == request.user:
        can_edit = move_line.move.state == 'Brouillon'
        can_cancel = move_line.move.state == 'Brouillon'
        can_confirm = move_line.move.state == 'Brouillon'
    elif request.user.role == 'Validateur' and move_line.move.site == request.user.default_site:
        can_validate = move_line.move.state == 'Confirmé'

    lines = Line.objects.all()

    context = {'move_line': move_line, 'can_edit': can_edit, 'can_cancel': can_cancel, 'can_confirm': can_confirm, 'can_validate': can_validate, 
               'can_print': can_print, 'lines': lines}
    if move_line.move.type == 'Sortie':
        return render(request, 'move_out_details.html', context)
    elif move_line.product.type == 'Matière Première':
        return render(request, 'details_move_mp.html', context)
    return render(request, 'details_move.html', context)

@login_required(login_url='login')
@admin_or_gs_required
def confirmMoveLine(request, move_line_id):
    if request.method == 'POST':
        try:
            move_line = MoveLine.objects.get(id=move_line_id)
        except MoveLine.DoesNotExist:
            messages.success(request, 'Le Move n\'existe pas')
            return JsonResponse({'success': False, 'message': 'Move n\'existe pas.'})
        success, validation = changeState(request, move_line, 'Confirmé')
        if success:
            return JsonResponse({'success': True, 'message': 'Move confirmé avec succès.', 'move_line_id': move_line_id})
        else:
            return JsonResponse({'success': False, 'message': 'Move n\'existe pas.'})
    return JsonResponse({'success': False, 'message': 'Méthode de demande non valide.'})

@login_required(login_url='login')
@admin_or_gs_required
def validateMoveLine(request, move_line_id):
    if request.method == 'POST':
        try:
            move_line = MoveLine.objects.get(id=move_line_id)
        except MoveLine.DoesNotExist:
            messages.success(request, 'Le Move n\'existe pas')
            return JsonResponse({'success': False, 'message': 'Move n\'existe pas.'})
        
        for detail in move_line.details.all():
            if not detail.emplacement.can_stock(detail.palette):
                return JsonResponse({'success': False, 'message': f'Emplacement {detail.emplacement} insuffisant pour stocker les palettes.'})
            
        success, validation = changeState(request, move_line, 'Validé')
        if success:
            adjusted, message = adjustStock(move_line)
            if not adjusted:
                return JsonResponse({'success': False, 'message': message})
            for detail in move_line.details.all():
                detail.code = f"Product:{move_line.product.id};Emplacement:{detail.emplacement.id};NLOT:{move_line.n_lot}"
                if detail.emplacement.temp:
                    TemporaryEmplacementAlert.objects.get_or_create(line_detail=detail, write_uid=request.user, create_uid=request.user)
                detail.save()
            if move_line.move.is_transfer:
                for detail in move_line.details.all():
                    source_line_detail = detail.mirrored_move
                    source_line_detail.qte -= detail.qte
                    source_line_detail.code = f"ID:{source_line_detail.id}MoveLine:{source_line_detail.move_line.id};Product:{source_line_detail.move_line.product.designation};Date:{source_line_detail.move_line.move.date};Qte:{source_line_detail.qte}"
                    source_line_detail.save()
                    if source_line_detail.emplacement.temp and source_line_detail.qte == 0:
                        TemporaryEmplacementAlert.objects.filter(line_detail=source_line_detail).delete()

            return JsonResponse({'success': True, 'message': 'Move confirmé avec succès.', 'move_line_id': move_line_id})
        else:
            return JsonResponse({'success': False, 'message': 'Move n\'existe pas.'})
    return JsonResponse({'success': False, 'message': 'Méthode de demande non valide.'})

def adjustStock(ml):
    is_entry = ml.move.type == 'Entré'
    for detail in ml.details.all():
        ds = Disponibility.objects.filter(product=ml.product, emplacement=detail.emplacement, n_lot=ml.n_lot).first()
        if is_entry:
            if ds:
                ds.qte += detail.qte
            else:
                ds = Disponibility(product=ml.product, emplacement=detail.emplacement, qte=detail.qte, create_uid=ml.create_uid, 
                                    production_date=ml.move.date, expiry_date=ml.expiry_date, write_uid=ml.create_uid,n_lot=ml.n_lot)
            ds.save()
            return True, 'Stock ajusté avec succès.'
        else:
            if ds and ds.qte >= detail.qte:
                ds.qte -= detail.qte
                ds.save()
                if ds.qte == 0:
                    ds.delete()
            elif ds.qte < detail.qte:
                return False, 'Stock insuffisant pour la sortie.'
            else:
                return False, 'Stock introuvable.'

@login_required(login_url='login')
@admin_or_gs_required
def cancelMoveLine(request, move_line_id):
    if request.method == 'POST':
        try:
            move_line = MoveLine.objects.get(id=move_line_id)
        except MoveLine.DoesNotExist:
            messages.success(request, 'Le Move n\'existe pas')
            return JsonResponse({'success': False, 'message': 'Move n\'existe pas.'})
        success, validation = changeState(request, move_line, 'Annulé')
        if success:
            return JsonResponse({'success': True, 'message': 'Move anulé avec succès.', 'move_line_id': move_line_id})
        else:
            return JsonResponse({'success': False, 'message': 'Move n\'existe pas.'})
    return JsonResponse({'success': False, 'message': 'Méthode de demande non valide.'})

def createValidation(request, move, new_state, refusal_reason=None):
    old_state = move.state
    move.state = new_state
    actor = request.user
    validation = Validation(old_state=old_state, new_state=new_state, actor=actor, refusal_reason=refusal_reason, move=move)
    move.save()
    validation.save()
    messages.success(request, f'Move set to {new_state} successfully')
    return validation

def changeState(request, move_line, action):
    move = move_line.move
    if move.state == action:
        return True, None
    reason = request.POST.get('refusal_reason', None)
    if move.state == 'Refusé' and action == 'Confirmé':
        reason = 'Correrction.'
    validation = createValidation(request, move, action, reason)
    return True, validation

@login_required(login_url='login')
@admin_or_gs_required
def transfer_quantity(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                site_id = request.POST.get('site_id')
                destination_line_id = request.POST.get('line')
                destination_warehouse_id = request.POST.get('destination_warehouse')
                destination_emplacement_id = request.POST.get('destination_emplacement')
                destination_lot_number = request.POST.get('destination_lot')
                transfer_quantity = int(request.POST.get('destination_qte', 0))
                source_id = request.POST.get('source_id')

                if not all([site_id, destination_line_id, destination_warehouse_id, destination_emplacement_id, destination_lot_number, transfer_quantity]):
                    return JsonResponse({'success': False, 'message': 'Tous les champs sont obligatoires.'}, status=200)

                if transfer_quantity <= 0:
                    return JsonResponse({'success': False, 'message': 'La quantité doit être supérieure à 0.'}, status=200)
                
                source_line_detail = LineDetail.objects.get(id=source_id)
                source_move_line = source_line_detail.move_line
                already_transferred = source_line_detail.transfers.aggregate(total=models.Sum('qte'))['total'] or 0

                if transfer_quantity > source_line_detail.qte:
                    return JsonResponse({'success': False, 'message': 'La quantité à transférer dépasse la quantité disponible.'}, status=200)
                elif already_transferred + transfer_quantity > source_line_detail.qte: 
                        return JsonResponse({'success': False, 'message': f'La quantité à transférer dépasse la quantité disponible (Brouillon inclus).'}, status=200)
                
                move_year = source_move_line.move.date.year
                existing_move_line = MoveLine.objects.filter(lot_number=destination_lot_number, move__line_id=destination_line_id, move__date__year=move_year).first()
                
                if existing_move_line:
                    if not existing_move_line.move.is_transfer:
                        return JsonResponse({'success': False, 'message': f'N° Lot {destination_lot_number} existe déjà.'}, status=200)
                    elif not existing_move_line.move.state == 'Brouillon':
                        return JsonResponse({'success': False, 'message': f'Il existe déjà un transfert validé avec le même N° Lot {destination_lot_number}, id = {existing_move_line.id}'}, status=200)
                    else:
                        LineDetail.objects.create(move_line=existing_move_line, warehouse_id=destination_warehouse_id, emplacement_id=destination_emplacement_id, 
                                              qte=transfer_quantity, write_uid=request.user, create_uid=request.user, mirrored_move=source_line_detail)
                else:
                    new_move = Move.objects.create(site_id=site_id,line_id=destination_line_id, gestionaire=request.user, date=source_move_line.move.date, 
                                                is_transfer=True, type='Entré', write_uid=request.user, 
                                                create_uid=request.user)

                    new_move_line = MoveLine.objects.create(lot_number=destination_lot_number, product=source_move_line.product, 
                                                            move=new_move, write_uid=request.user, create_uid=request.user)

                    LineDetail.objects.create(move_line=new_move_line, warehouse_id=destination_warehouse_id, emplacement_id=destination_emplacement_id, 
                                            qte=transfer_quantity, write_uid=request.user, create_uid=request.user, mirrored_move=source_line_detail)

                return JsonResponse({'success': True, 'message': 'Le transfert a été effectué avec succès.'}, status=200)

        except LineDetail.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Détail de ligne source introuvable.'}, status=200)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erreur lors du transfert : {str(e)}'}, status=200)


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
def get_emplacements_for_warehouse(request):
    warehouse_id = request.GET.get('warehouse_id')
    warehouse = Warehouse.objects.get(id=warehouse_id)
    emplacements = Emplacement.objects.filter(warehouse=warehouse)
    emplacement_data = [{'id': emplacement.id, 'name': emplacement.designation} for emplacement in emplacements]

    return JsonResponse({'emplacements': emplacement_data})

def get_transfers(request, detail_id):
    detail = get_object_or_404(LineDetail, id=detail_id)
    data = []

    for t in detail.transfers.all():
        move = t.move_line.move
        data.append({ 'site': move.line.site.designation, 'line': move.line.designation, 'magasin': t.warehouse.designation, 
                     'emplacement': t.emplacement.designation, 'qte': t.qte, 'date': move.date, 'state': move.state, 'n_lot': t.move_line.n_lot})
        
    return JsonResponse({'transfers': data})

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
