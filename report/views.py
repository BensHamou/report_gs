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
from .forms import *
import qrcode

# UNIT

@login_required(login_url='login')
@admin_required
def listUnitView(request):
    units = Unit.objects.all().order_by('-date_modified')
    filteredData = UnitFilter(request.GET, queryset=units)
    units = filteredData.qs
    paginator = Paginator(units, request.GET.get('page_size', 12))
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    
    context = {'page': page, 'filteredData': filteredData}
    return render(request, 'list_units.html', context)

@login_required(login_url='login')
@admin_required
def deleteUnitView(request, id):
    unit = get_object_or_404(Unit, id=id)
    try:
        unit.delete()
        url_path = reverse('units')  # Adjust the URL name accordingly
        return redirect(getRedirectionURL(request, url_path))
    except Exception as e:
        messages.error(request, f"Erreur lors de la suppression de l'unité : {e}")
        return redirect(getRedirectionURL(request, reverse('units')))  # Adjust the URL name accordingly

@login_required(login_url='login')
@admin_required
def createUnitView(request):
    form = UnitForm()
    if request.method == 'POST':
        form = UnitForm(request.POST)
        if form.is_valid():
            form.save()
            url_path = reverse('units')  # Adjust the URL name accordingly
            return redirect(getRedirectionURL(request, url_path))
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    
    context = {'form': form}
    return render(request, 'unit_form.html', context)

@login_required(login_url='login')
@admin_required
def editUnitView(request, id):
    unit = get_object_or_404(Unit, id=id)
    form = UnitForm(instance=unit)
    
    if request.method == 'POST':
        form = UnitForm(request.POST, instance=unit)
        if form.is_valid():
            form.save()
            url_path = reverse('units')  # Adjust the URL name accordingly
            return redirect(getRedirectionURL(request, url_path))
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    
    context = {'form': form, 'unit': unit}
    return render(request, 'unit_form.html', context)

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
    products = Product.objects.all().order_by('-date_modified')
    filteredData = ProductFilter(request.GET, queryset=products)
    products = filteredData.qs
    page_size_param = request.GET.get('page_size')
    page_size = int(page_size_param) if page_size_param else 12
    paginator = Paginator(products, page_size)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {'page': page, 'filteredData': filteredData}
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
    
    context = {'form': form}
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
    
    context = {'form': form, 'product': product}
    return render(request, 'product_form.html', context)


# MOVES


@login_required(login_url='login')
@admin_or_gs_required
def families_view(request):
    families = Family.objects.all()
    return render(request, 'families.html', {'families': families})

@login_required(login_url='login')
@admin_or_gs_required
def products_view(request, family_id):
    family = get_object_or_404(Family, id=family_id)
    products = Product.objects.filter(family=family)
    return render(request, 'products.html', {'products': products, 'family': family})

@login_required(login_url='login')
@admin_or_gs_required
def move_in_form_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    MoveLineDetailFormSet = modelformset_factory(LineDetail, fields=('warehouse', 'zone', 'qte'), extra=1)
    
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

    return render(
        request,
        'form.html',
        {
            'product': product,
            'formset': formset,
            'lines': user_lines if show_line_field else None,
            'gestionaires': gestionaires,
            'default_line': default_line,
            'is_admin': is_admin,
            'show_line_field': show_line_field,
        },
    )

@login_required(login_url='login')
@admin_or_gs_required
def get_shifts_and_users_for_line(request):
    line_id = request.GET.get('line_id')
    line = get_object_or_404(Line, id=line_id)
    
    shifts = line.shifts.all()
    users = line.users.filter(Q(role='Gestionaire') | Q(role='Admin'))
    
    shift_data = [{'id': shift.id, 'name': shift.designation} for shift in shifts]
    user_data = [{'id': user.id, 'name': user.fullname} for user in users]
    
    return JsonResponse({'shifts': shift_data, 'users': user_data})

@login_required(login_url='login')
@admin_or_gs_required
def get_warehouses_for_line(request):
    line_id = request.GET.get('line_id')
    line = Line.objects.get(id=line_id)
    warehouses = Warehouse.objects.filter(site=line.site)
    warehouse_data = [{'id': warehouse.id, 'name': warehouse.designation} for warehouse in warehouses]

    return JsonResponse({'warehouses': warehouse_data})

@login_required(login_url='login')
@admin_or_gs_required
def get_zones_for_warehouse(request):
    warehouse_id = request.GET.get('warehouse_id')
    warehouse = Warehouse.objects.get(id=warehouse_id)
    zones = Zone.objects.filter(warehouse=warehouse)
    zone_data = [{'id': zone.id, 'name': zone.designation} for zone in zones]

    return JsonResponse({'zones': zone_data})

@login_required(login_url='login')
@admin_or_gs_required
def move_list(request):
    moves = MoveLine.objects.filter(move__line__in=request.user.lines.all().values('id')).order_by('-date_modified')    
    filteredData = MoveLineFilter(request.GET, queryset=moves)
    moves = filteredData.qs
    page_size_param = request.GET.get('page_size')
    page_size = int(page_size_param) if page_size_param else 12
    paginator = Paginator(moves, page_size)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {'page': page, 'filteredData': filteredData}
    return render(request, 'move_list.html', context)

@login_required(login_url='login')
@admin_or_gs_required
def move_edit(request, move_line_id):
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
        'zones': Zone.objects.all(),
    }
    return render(request, 'edit_move.html', context)

@login_required(login_url='login')
@admin_or_gs_required
def move_delete(request, move_line_id):
    move = get_object_or_404(MoveLine, id=move_line_id)
    try:
        move.delete()
        messages.success(request, "Move supprimée avec succès.")
    except Exception as e:
        messages.error(request, f"Erreur lors de la suppression du move : {e}")
    return redirect(getRedirectionURL(request, reverse('move_lines')))

@login_required(login_url='login')
@admin_or_gs_required
def create_move(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                line_id = request.POST.get('line')
                shift_id = request.POST.get('shift')
                gestionaire_id = request.POST.get('gestionaire')
                lot_number = request.POST.get('lot_number')
                production_date = request.POST.get('production_date')
                product = request.POST.get('product')
                print()

                if not (line_id and shift_id and gestionaire_id):
                    return JsonResponse({'success': False, 'message': 'Les champs Ligne, Shift, Date et Gestionaire sont obligatoires.'}, status=200)

                existing_move_line = MoveLine.objects.filter(lot_number=lot_number)
                if existing_move_line.exists():
                    return JsonResponse({'success': False, 'message': f'N° Lot {lot_number} existe déjà.'}, status=200)

                move = Move.objects.create(line_id=line_id, shift_id=shift_id, gestionaire_id=gestionaire_id, date=production_date,  
                                           state='Brouillon',  type='Entré',  create_uid=request.user, write_uid=request.user)
                
                move_line = MoveLine.objects.create(lot_number=lot_number, product_id=product, move=move, 
                                                    create_uid=request.user, write_uid=request.user)

                row_ids = [key.split('_')[1] for key in request.POST.keys() if key.startswith('warehouse_')]
                for row_id in row_ids:
                    warehouse_id = request.POST.get(f'warehouse_{row_id}')
                    zone_id = request.POST.get(f'zone_{row_id}')
                    qte = request.POST.get(f'qte_{row_id}')

                    if warehouse_id and zone_id and qte:
                        LineDetail.objects.create(move_line=move_line, warehouse_id=warehouse_id, zone_id=zone_id, 
                                                  qte=int(qte), create_uid=request.user, write_uid=request.user)

                return JsonResponse({'success': True, 'message': 'Entrée créée avec succès.'}, status=200)

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erreur lors du traitement de la demande: {str(e)}'}, status=500)

@login_required(login_url='login')
@admin_or_gs_required
def update_move(request, move_line_id):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                line_id = request.POST.get('line')
                shift_id = request.POST.get('shift')
                gestionaire_id = request.POST.get('gestionaire')
                lot_number = request.POST.get('lot_number')
                production_date = request.POST.get('production_date')

                if not (line_id and shift_id and gestionaire_id):
                    return JsonResponse({'success': False, 'message': 'Les champs Ligne, Shift, Date et Gestionaire sont obligatoire.'}, status=200)

                move_line = MoveLine.objects.get(id=move_line_id)

                existing_move_line = MoveLine.objects.filter(lot_number=lot_number, move__line=move_line.move.line).exclude(id=move_line_id)
                if existing_move_line.exists():
                    return JsonResponse({'success': False, 'message': f'N° Lot {lot_number} existe déjà.'}, status=200)

                move = Move.objects.get(id=move_line.move.id)

                move.line_id = line_id
                move.shift_id = shift_id
                move.gestionaire_id = gestionaire_id
                move.date = production_date
                move.write_uid = request.user
                move.save()

                move_line.lot_number = lot_number
                move_line.write_uid = request.user
                move_line.save()

                LineDetail.objects.filter(move_line=move_line).delete()

                row_ids = [key.split('_')[1] for key in request.POST.keys() if key.startswith('warehouse_')]
                for row_id in row_ids:
                    warehouse_id = request.POST.get(f'warehouse_{row_id}')
                    zone_id = request.POST.get(f'zone_{row_id}')
                    qte = request.POST.get(f'qte_{row_id}')

                    if warehouse_id and zone_id and qte:
                        LineDetail.objects.create(move_line=move_line, warehouse_id=warehouse_id, zone_id=zone_id, write_uid=request.user, 
                                                  create_uid=move_line.create_uid, date_created=move_line.date_created, qte=int(qte))

                return JsonResponse({'success': True, 'message': 'Entrée mise à jour avec succès.'}, status=200)
        except Move.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Entré non trouvée.'}, status=200)
        except MoveLine.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Entré non trouvée.'}, status=200)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erreur lors du traitement de la demande: {str(e)}'}, status=500)

@login_required(login_url='login')
@admin_or_gs_required        
def move_line_detail(request, move_line_id):
    move_line = get_object_or_404(MoveLine, id=move_line_id)

    can_edit, can_cancel, can_confirm, can_print = False, False, False, move_line.move.state == 'Confirmé'

    if request.user.role == 'Admin':
        can_edit = True
        can_cancel = move_line.move.state == 'Brouillon'
        can_confirm = move_line.move.state == 'Brouillon'
    elif request.user.role == 'Gestionaire' and move_line.move.gestionaire == request.user:
        can_edit = move_line.move.state == 'Brouillon'
        can_cancel = move_line.move.state == 'Brouillon'
        can_confirm = move_line.move.state == 'Brouillon'

    lines = Line.objects.all()


    context = {'move_line': move_line, 'can_edit': can_edit, 'can_cancel': can_cancel, 'can_confirm': can_confirm, 'can_print': can_print, 'lines': lines}
    
    return render(request, 'details_move.html', context)

@login_required(login_url='login')
@admin_or_gs_required
def confirmMoveLine(request, move_line_id):
    if request.method == 'POST':
        move_line, success, validation = changeState(request, move_line_id, 'Confirmé')
        if success:
            for detail in move_line.details.all():
                detail.code = f"ID:{detail.id}MoveLine:{move_line.id};Product:{move_line.product.designation};Date:{move_line.move.date};Qte:{detail.qte}"
                detail.save()
            if move_line.move.is_transfer:
                for detail in move_line.details.all():
                    source_line_detail = detail.mirrored_move
                    source_line_detail.qte -= detail.qte
                    source_line_detail.code = f"ID:{source_line_detail.id}MoveLine:{source_line_detail.move_line.id};Product:{source_line_detail.move_line.product.designation};Date:{source_line_detail.move_line.move.date};Qte:{source_line_detail.qte}"
                    source_line_detail.save()

            return JsonResponse({'success': True, 'message': 'Move confirmé avec succès.', 'move_line_id': move_line.id})
        else:
            return JsonResponse({'success': False, 'message': 'Move n\'existe pas.'})
    return JsonResponse({'success': False, 'message': 'Méthode de demande non valide.'})

@login_required(login_url='login')
@admin_or_gs_required
def cancelMoveLine(request, move_line_id):
    if request.method == 'POST':
        move_line, success, validation = changeState(request, move_line_id, 'Annulé')
        if success:
            return JsonResponse({'success': True, 'message': 'Move anulé avec succès.', 'move_line_id': move_line.id})
        else:
            return JsonResponse({'success': False, 'message': 'Move n\'existe pas.'})
    return JsonResponse({'success': False, 'message': 'Méthode de demande non valide.'})

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

def createValidation(request, move, new_state, refusal_reason=None):
    old_state = move.state
    move.state = new_state
    actor = request.user
    validation = Validation(old_state=old_state, new_state=new_state, actor=actor, refusal_reason=refusal_reason, move=move)
    move.save()
    validation.save()
    messages.success(request, f'Move set to {new_state} successfully')
    return validation

def changeState(request, pk, action):
    try:
        move_line = MoveLine.objects.get(id=pk)
        move = Move.objects.get(id=move_line.move.id)
    except MoveLine.DoesNotExist:
        messages.success(request, 'Le Move n\'existe pas')
        return move_line, False, None
    if move.state == action:
        return move_line, True, None
    reason = request.POST.get('refusal_reason', None)
    if move.state == 'Refusé' and action == 'Confirmé':
        reason = 'Correrction.'
    validation = createValidation(request, move, action, reason)
    return move_line, True, validation

@login_required(login_url='login')
@admin_or_gs_required
def transfer_quantity(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                destination_line_id = request.POST.get('line')
                destination_warehouse_id = request.POST.get('destination_warehouse')
                destination_zone_id = request.POST.get('destination_zone')
                destination_lot_number = request.POST.get('destination_lot')
                transfer_quantity = int(request.POST.get('destination_qte', 0))
                source_id = request.POST.get('source_id')

                if not all([destination_line_id, destination_warehouse_id, destination_zone_id, destination_lot_number, transfer_quantity]):
                    return JsonResponse({'success': False, 'message': 'Tous les champs sont obligatoires.'}, status=400)

                if transfer_quantity <= 0:
                    return JsonResponse({'success': False, 'message': 'La quantité doit être supérieure à 0.'}, status=400)
                
                source_line_detail = LineDetail.objects.get(id=source_id)
                source_move_line = source_line_detail.move_line

                if transfer_quantity > source_line_detail.qte:
                    return JsonResponse({'success': False, 'message': 'La quantité à transférer dépasse la quantité disponible.'}, status=400)
                
                existing_move_line = MoveLine.objects.filter(lot_number=destination_lot_number, move__line_id=destination_line_id, move__is_transfer=True, 
                                                             move__state='Brouillon').first()

                if existing_move_line:
                    LineDetail.objects.create(move_line=existing_move_line, warehouse_id=destination_warehouse_id, zone_id=destination_zone_id, 
                                              qte=transfer_quantity, write_uid=request.user, create_uid=request.user, mirrored_move=source_line_detail)
                else:
                    new_move = Move.objects.create(line_id=destination_line_id, gestionaire=request.user, date=source_move_line.move.date, 
                                                is_transfer=True, type='Entré', write_uid=request.user, 
                                                create_uid=request.user)

                    new_move_line = MoveLine.objects.create(lot_number=destination_lot_number, product=source_move_line.product, 
                                                            move=new_move, write_uid=request.user, create_uid=request.user)

                    LineDetail.objects.create(move_line=new_move_line, warehouse_id=destination_warehouse_id, zone_id=destination_zone_id, 
                                            qte=transfer_quantity, write_uid=request.user, create_uid=request.user, mirrored_move=source_line_detail)

                return JsonResponse({'success': True, 'message': 'Le transfert a été effectué avec succès.'}, status=200)

        except LineDetail.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Détail de ligne source introuvable.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erreur lors du transfert : {str(e)}'}, status=500)

def get_transfers(request, detail_id):
    detail = get_object_or_404(LineDetail, id=detail_id)

    data = []

    for t in detail.transfers.all():
        move = t.move_line.move
        data.append({ 'site': move.line.site.designation, 'line': move.line.designation, 'magasin': t.warehouse.designation, 
                     'zone': t.zone.designation, 'qte': t.qte, 'date': move.date, 'state': move.state})
        
    return JsonResponse({'transfers': data})
