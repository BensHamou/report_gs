from django import forms
from .models import *
from account.forms import getAttrs, BaseModelForm

class PackingForm(BaseModelForm):

    designation = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Désignation')))
    unit = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Unité')))

    class Meta:
        model = Packing
        fields = ['designation', 'unit']

class FamilyForm(BaseModelForm):

    designation = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Désignation')))
    image = forms.ImageField(widget=forms.ClearableFileInput(attrs={'class': 'custom-file-input','accept': 'image/*'}))

    class Meta:
        model = Family
        fields = ['designation', 'image']  

class ProductForm(BaseModelForm):
    
    designation = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Désignation')))
    image = forms.ImageField(widget=forms.ClearableFileInput(attrs={'class': 'custom-file-input', 'accept': 'image/*'}))
    delais_expiration = forms.IntegerField(widget=forms.NumberInput(attrs=getAttrs('control', 'Délais d\'expiration')))
    qte_per_cond = forms.IntegerField(widget=forms.NumberInput(attrs=getAttrs('control', 'Quantité par unité')))
    qte_per_pal = forms.IntegerField(widget=forms.NumberInput(attrs=getAttrs('control', 'Quantité par palette')))
    family = forms.ModelChoiceField(queryset=Family.objects.all(), widget=forms.Select(attrs=getAttrs('control')), empty_label="Famille")
    packing = forms.ModelChoiceField(queryset=Packing.objects.all(), widget=forms.Select(attrs=getAttrs('control')), empty_label="Conditionnement")
    alert_stock = forms.IntegerField(widget=forms.NumberInput(attrs=getAttrs('control', 'Alerte Stock')))

    class Meta:
        model = Product
        fields = ['designation', 'image', 'delais_expiration', 'qte_per_pal', 'qte_per_cond', 'family', 'packing', 'alert_stock']
        
class MProductForm(BaseModelForm):
    
    qte_per_cond = forms.IntegerField(widget=forms.NumberInput(attrs=getAttrs('control', 'Quantité par copnditionnement')))
    qte_per_pal = forms.IntegerField(widget=forms.NumberInput(attrs=getAttrs('control', 'Quantité par palette')))
    packing = forms.ModelChoiceField(queryset=Packing.objects.all(), widget=forms.Select(attrs=getAttrs('control')), empty_label="Conditionnement")
    alert_stock = forms.IntegerField(widget=forms.NumberInput(attrs=getAttrs('control', 'Alerte Stock')))

    class Meta:
        model = Product
        fields = ['qte_per_pal', 'qte_per_cond', 'packing', 'alert_stock']

class DisponibilityForm(BaseModelForm):
    
    emplacement = forms.ModelChoiceField(queryset=Emplacement.objects.all(), widget=forms.Select(attrs=getAttrs('select3')), empty_label="Emplacement")
    product = forms.ModelChoiceField(queryset=Product.objects.all(), widget=forms.Select(attrs=getAttrs('select3')), empty_label="Produit")
    n_lot = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'N° Lot')))
    qte = forms.IntegerField(widget=forms.NumberInput(attrs=getAttrs('control', 'Quantité')))
    palette = forms.IntegerField(widget=forms.NumberInput(attrs=getAttrs('control', 'Palette')))
    production_date = forms.DateField(widget=forms.DateInput(attrs=getAttrs('control', 'Date de Production')))
    expiry_date = forms.DateField(widget=forms.DateInput(attrs=getAttrs('control', 'Date d\'expiration')))

    class Meta:
        model = Disponibility
        fields = ['emplacement', 'product', 'n_lot', 'qte', 'palette', 'production_date', 'expiry_date']