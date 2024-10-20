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
        'search': {'class': 'form-control form-input', 'style': 'background-color: #ffffff; border-color: transparent; color: #133356; height: 40px; text-indent: 33px; border-radius: 5px;', 'type': 'search', 'placeholder': '', 'id': 'search'},
        'select': {'class': 'form-select', 'style': 'background-color: #ffffff; padding-left: 30px;'},
        'select2': {'class': 'form-select', 'style': 'background-color: #ffffff; padding-left: 30px; width: 100%;'},
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
        fields = ['username', 'email', 'is_admin', 'first_name', 'last_name', 'role', 'lines']

    username = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Nom d\'utilisateur')))
    last_name = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Nom de famille')))
    first_name = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Prénom')))
    email = forms.EmailField(widget=forms.EmailInput(attrs=getAttrs('control', 'Email')))
    lines = forms.SelectMultiple(attrs=getAttrs('select'))
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
        fields = ['designation', 'address', 'email']

    designation = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Désignation')))
    address = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Adresse')))
    email = forms.EmailField(widget=forms.EmailInput(attrs=getAttrs('control', 'Email')))

class LineForm(BaseModelForm):
    class Meta:
        model = Line
        fields = ['designation', 'prefix_bl', 'prefix_bl_a', 'prefix_nlot', 'shifts']

    designation = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Désignation')))
    prefix_bl = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Préfixe BL')))
    prefix_bl_a = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Préfixe BL Annex')))
    prefix_nlot = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Préfixe N° Lot')))
    shifts = forms.SelectMultiple(attrs=getAttrs('select'))

class WarehouseForm(BaseModelForm):
    class Meta:
        model = Warehouse
        fields = ['designation', 'site']

    designation = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Désignation')))
    site = forms.Select(attrs=getAttrs('select'))

class ZoneForm(BaseModelForm):
    class Meta:
        model = Zone
        fields = ['designation', 'quarantine', 'temp', 'warehouse']

    designation = forms.CharField(widget=forms.TextInput(attrs=getAttrs('control', 'Désignation')))
    quarantine = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'type': 'checkbox', 
        'data-onstyle': 'secondary', 
        'data-toggle': 'switchbutton'
    }))
    temp = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'type': 'checkbox', 
        'data-onstyle': 'secondary', 
        'data-toggle': 'switchbutton'
    }))
    warehouse = forms.Select(attrs=getAttrs('select'))

class ShiftForm(BaseModelForm):
    class Meta:
        model = Shift
        fields = ['start_time', 'end_time']

    start_time = forms.TimeField(label='Heure de début', widget=forms.TimeInput(attrs=getAttrs('time', 'Heure de début')))
    end_time = forms.TimeField(label='Heure de fin', widget=forms.TimeInput(attrs=getAttrs('time', 'Heure de fin')))


class CustomLoginForm(AuthenticationForm):
    
    username = forms.CharField(label="Email / AD 2000", widget=forms.TextInput(attrs=getAttrs('login', 'Adresse e-mail', {'autofocus': True})))
    password = forms.CharField(widget=forms.PasswordInput(attrs=getAttrs('login', 'Mot de passe')))
