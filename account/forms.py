from django.forms import ModelForm
from django import forms
from .models import *
from django.contrib.auth.forms import AuthenticationForm

def getAttrs(type, placeholder='', other={}):
    ATTRIBUTES = {
        'control': {'class': 'form-control', 'style': 'background-color: #ffffff; padding-left: 30px;', 'placeholder': ''},
        'login': {'class': 'form-control', 'style': 'background-color: white; height: 45px; border: 1px solid #ccc; border-radius: 10px;', 'placeholder': ''},
        'controlID': {'class': 'form-control search-input-id', 'autocomplete': "off", 'style': 'background-color: #ffffff; border-color: #ffffff;', 'placeholder': ''},
        'controlSearch': {'class': 'form-control search-input', 'autocomplete': "off", 'style': 'background-color: #ffffff; border-color: #ffffff;', 'placeholder': ''},
        'search': {'class': 'form-control', 'style': 'width: 40%; margin-right: 10px;', 'type': 'text', 'placeholder': '', 'id': 'search'},
        'search2': {'class': 'form-control', 'style': 'margin-right: 10px;', 'type': 'text', 'placeholder': '', 'id': 'search'},
        'select': {'class': 'form-select', 'style': 'background-color: #ffffff; padding-left: 30px;'},
        'select2': {'class': 'form-select select2', 'style': 'background-color: #ffffff; padding-left: 30px; width: 100%;'},
        'select3': {'class': 'form-select select3', 'style': 'background-color: #ffffff; padding-left: 30px; width: 100%;'},
        'date': {'type': 'date', 'class': 'form-control dateinput','style': 'background-color: #ffffff;'},
        'time': {'type': 'time', 'class': 'form-control timeinput', 'style': 'background-color: #ffffff; padding-left: 30px;', 'placeholder': ''},
        'textarea': {"rows": "3", 'style': 'width: 100%', 'class': 'form-control', 'placeholder': '', 'style': 'background-color: #ffffff;'}
    }

    if type in ATTRIBUTES:
        attributes = ATTRIBUTES[type]
        if 'placeholder' in attributes:
            attributes['placeholder'] = placeholder
        if other:
            attributes.update(other)
        return attributes
    else:
        return {}
    
class BaseModelForm(ModelForm):
    def save(self, commit=True, user=None):
        instance = super(BaseModelForm, self).save(commit=False)
        if user:
            if not instance.pk:
                instance.create_uid = user
            instance.write_uid = user
        if commit:
            instance.save()
        return instance
    
class UserForm(BaseModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'is_admin', 'first_name', 'last_name', 'role', 'lines', 'default_site']

    username = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Nom d\'utilisateur')), disabled=True)
    last_name = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Nom de famille')), disabled=True)
    first_name = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Prénom')), disabled=True)
    email = forms.EmailField(widget=forms.EmailInput(attrs=getAttrs('control', 'Email')), disabled=True)
    default_site = forms.ModelChoiceField(queryset=Site.objects.all(), widget=forms.Select(attrs=getAttrs('select3')), empty_label="Site")
    lines = forms.ModelMultipleChoiceField(queryset=Line.objects.all(), widget=forms.SelectMultiple(attrs={'class': 'form-select select3'}), required=False)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, widget=forms.Select(attrs=getAttrs('select')))
    is_admin = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'type': 'checkbox',
        'data-onstyle': 'primary',
        'data-toggle': 'switchbutton',
        'data-onlabel': "Admin", 
        'data-offlabel': "User"
    }))

class SiteForm(BaseModelForm):
    class Meta:
        model = Site
        fields = ['designation', 'address', 'email', 'prefix_bl', 'prefix_bl_a']

    designation = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Désignation')))
    address = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Adresse')))
    email = forms.EmailField(widget=forms.EmailInput(attrs=getAttrs('control', 'Email')))
    prefix_bl = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Préfixe BL')))
    prefix_bl_a = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Préfixe BL Annex')))

class LineForm(BaseModelForm):
    class Meta:
        model = Line
        fields = ['designation', 'site', 'prefix_nlot', 'shifts']

    designation = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Désignation')))
    prefix_nlot = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Préfixe N° Lot')))
    site = forms.ModelChoiceField(queryset=Site.objects.all(), widget=forms.Select(attrs=getAttrs('select3')), empty_label="Site")
    shifts = forms.ModelMultipleChoiceField(queryset=Shift.objects.all(), widget=forms.SelectMultiple(attrs=getAttrs('select3')), required=False)

class WarehouseForm(BaseModelForm):
    class Meta:
        model = Warehouse
        fields = ['designation', 'site']

    designation = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Désignation')))
    site = forms.ModelChoiceField(queryset=Site.objects.all(), widget=forms.Select(attrs=getAttrs('select2')), empty_label="Site")


class ZoneForm(BaseModelForm):
    class Meta:
        model = Zone
        fields = ['designation', 'quarantine', 'temp', 'warehouse']

    designation = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Désignation')))
    quarantine = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'type': 'checkbox', 
        'data-onstyle': 'secondary', 
        'data-toggle': 'switchbutton',
        'data-onlabel': "Oui", 
        'data-offlabel': "Non"
    }))
    temp = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'type': 'checkbox', 
        'data-onstyle': 'secondary', 
        'data-toggle': 'switchbutton',
        'data-onlabel': "Oui", 
        'data-offlabel': "Non"
    }))
    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all(), widget=forms.Select(attrs=getAttrs('select2')), empty_label="Magasins")

class ShiftForm(BaseModelForm):
    class Meta:
        model = Shift
        fields = ['start_time', 'end_time']

    start_time = forms.TimeField(label='Heure de début', widget=forms.TimeInput(attrs=getAttrs('time', 'Heure de début')))
    end_time = forms.TimeField(label='Heure de fin', widget=forms.TimeInput(attrs=getAttrs('time', 'Heure de fin')))


class CustomLoginForm(AuthenticationForm):
    
    username = forms.CharField(label="Email / AD 2000", widget=forms.TextInput(attrs=getAttrs('login', 'Adresse e-mail', {'autofocus': True})))
    password = forms.CharField(widget=forms.PasswordInput(attrs=getAttrs('login', 'Mot de passe')))
