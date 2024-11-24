from django import forms
from .models import *
from account.forms import getAttrs, BaseModelForm

class UnitForm(BaseModelForm):

    designation = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Désignation')))

    class Meta:
        model = Unit
        fields = ['designation']

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
    qte_per_pal = forms.IntegerField(widget=forms.NumberInput(attrs=getAttrs('control', 'Quantité par palette')))
    family = forms.ModelChoiceField(queryset=Family.objects.all(), widget=forms.Select(attrs=getAttrs('control')), empty_label="Famille")
    unit = forms.ModelChoiceField(queryset=Unit.objects.all(), widget=forms.Select(attrs=getAttrs('control')), empty_label="Unité")
    type = forms.ChoiceField(choices=Product.PRODUCT_CHOICES, widget=forms.Select(attrs=getAttrs('control')))
    alert_stock = forms.IntegerField(widget=forms.NumberInput(attrs=getAttrs('control', 'Alerte Stock')))

    class Meta:
        model = Product
        fields = ['designation', 'image', 'delais_expiration', 'qte_per_pal', 'family', 'unit', 'type', 'alert_stock']
        