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

    for_mp = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'type': 'checkbox',
        'data-onstyle': 'primary',
        'data-toggle': 'switchbutton',
        'data-onlabel': "Oui",
        'data-offlabel': "Non" 
    }))
    
    nb_days_min = forms.IntegerField(widget=forms.NumberInput(attrs=getAttrs('control', 'Nombre de jours (Min)')))
    nb_days_max = forms.IntegerField(widget=forms.NumberInput(attrs=getAttrs('control', 'Nombre de jours (Max)')))

    is_expiring = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'type': 'checkbox',
        'data-onstyle': 'primary',
        'data-toggle': 'switchbutton',
        'data-onlabel': "Oui",
        'data-offlabel': "Non" 
    }))

    class Meta:
        model = Family
        fields = ['designation', 'image', 'for_mp', 'nb_days_min', 'nb_days_max', 'is_expiring']  

class ProductForm(BaseModelForm):
    
    designation = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Désignation')))
    image = forms.ImageField(widget=forms.ClearableFileInput(attrs={'class': 'custom-file-input', 'accept': 'image/*'}), required=False)
    delais_expiration = forms.IntegerField(widget=forms.NumberInput(attrs=getAttrs('control', 'Délais d\'expiration (Jours)')))
    qte_per_cond = forms.FloatField(widget=forms.NumberInput(attrs=getAttrs('control', 'Quantité par unité')))
    qte_per_pal = forms.FloatField(widget=forms.NumberInput(attrs=getAttrs('control', 'Quantité par palette')))
    family = forms.ModelChoiceField(queryset=Family.objects.filter(for_mp=False), widget=forms.Select(attrs=getAttrs('control')), empty_label="Famille")
    packing = forms.ModelChoiceField(queryset=Packing.objects.all(), widget=forms.Select(attrs=getAttrs('control')), empty_label="Conditionnement")
    alert_stock = forms.IntegerField(widget=forms.NumberInput(attrs=getAttrs('control', 'Alerte Stock (Min)')))
    alert_stock_max = forms.IntegerField(widget=forms.NumberInput(attrs=getAttrs('control', 'Alerte Stock (Max)')))
    alert_expiration = forms.IntegerField(widget=forms.NumberInput(attrs=getAttrs('control', 'Alerte Expiration (Jours)')))

    check_minmax = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'type': 'checkbox',
        'data-onstyle': 'primary',
        'data-toggle': 'switchbutton',
        'data-onlabel': "Oui",
        'data-offlabel': "Non" 
    }))

    class Meta:
        model = Product
        fields = ['designation', 'image', 'delais_expiration', 'qte_per_pal', 'qte_per_cond', 'family', 'packing', 'alert_stock', 'alert_stock_max', 'alert_expiration', 'check_minmax']
        
class MProductForm(BaseModelForm):
    
    qte_per_cond = forms.FloatField(widget=forms.NumberInput(attrs=getAttrs('control', 'Quantité par copnditionnement')))
    qte_per_pal = forms.FloatField(widget=forms.NumberInput(attrs=getAttrs('control', 'Quantité par palette')))
    packing = forms.ModelChoiceField(queryset=Packing.objects.all(), widget=forms.Select(attrs=getAttrs('control')), empty_label="Conditionnement")
    family = forms.ModelChoiceField(queryset=Family.objects.filter(for_mp=True), widget=forms.Select(attrs=getAttrs('control')), empty_label="Famille")
    alert_stock = forms.IntegerField(widget=forms.NumberInput(attrs=getAttrs('control', 'Alerte Stock (Min)')))
    alert_stock_max = forms.IntegerField(widget=forms.NumberInput(attrs=getAttrs('control', 'Alerte Stock (Max)')))
    alert_expiration = forms.IntegerField(widget=forms.NumberInput(attrs=getAttrs('control', 'Alerte Expiration')))

    check_minmax = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'type': 'checkbox',
        'data-onstyle': 'primary',
        'data-toggle': 'switchbutton',
        'data-onlabel': "Oui",
        'data-offlabel': "Non" 
    }))

    class Meta:
        model = Product
        fields = ['qte_per_pal', 'qte_per_cond', 'family', 'packing', 'alert_stock', 'alert_stock_max', 'alert_expiration', 'check_minmax']

class DisponibilityForm(BaseModelForm):
    
    emplacement = forms.ModelChoiceField(queryset=Emplacement.objects.all(), widget=forms.Select(attrs=getAttrs('select3')), empty_label="Emplacement")
    product = forms.ModelChoiceField(queryset=Product.objects.all(), widget=forms.Select(attrs=getAttrs('select3')), empty_label="Produit")
    n_lot = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'N° Lot')))
    qte = forms.FloatField(widget=forms.NumberInput(attrs=getAttrs('control', 'Quantité')))
    palette = forms.IntegerField(widget=forms.NumberInput(attrs=getAttrs('control', 'Palette')))
    production_date = forms.DateField(widget=forms.DateInput(attrs=getAttrs('date'), format='%Y-%m-%d'), required=False)
    expiry_date = forms.DateField(widget=forms.DateInput(attrs=getAttrs('date'), format='%Y-%m-%d'), required=False)

    class Meta:
        model = Disponibility
        fields = ['emplacement', 'product', 'n_lot', 'qte', 'palette', 'production_date', 'expiry_date']

    def clean(self):
        cleaned_data = super().clean()
        emplacement = cleaned_data.get('emplacement')
        product = cleaned_data.get('product')
        n_lot = cleaned_data.get('n_lot')
        production_date = cleaned_data.get('production_date')

        if emplacement and product and n_lot:
            existing_dispo = Disponibility.objects.filter(emplacement=emplacement, product=product, n_lot=n_lot)
            
            if self.instance and self.instance.pk:
                existing_dispo = existing_dispo.exclude(pk=self.instance.pk)

            if production_date:
                production_year = production_date.year
                existing_dispo = existing_dispo.filter(production_date__year=production_year)

            if existing_dispo.exists():
                error_message = "Une autre entrée avec le même emplacement, produit et N° Lot existe pour l'année de production spécifiée."
                self.add_error('n_lot', error_message)
                self.add_error('emplacement', error_message)
                self.add_error('product', error_message)

        return cleaned_data
    
class MoveBLForm(forms.ModelForm):
    class Meta:
        model = MoveBL
        fields = ['numero', 'is_annexe']
        widgets = {
            'numero': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_annexe': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }