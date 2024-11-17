from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.urls import reverse
from .filters import *
from .models import *
from .forms import *
from account.decorators import admin_required, getRedirectionURL

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

