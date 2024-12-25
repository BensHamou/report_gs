import django_filters
from django import forms
from .models import *
from django.db.models import Q
from account.forms import getAttrs

class FamilyFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search', widget=forms.TextInput(attrs=getAttrs('search', 'Rechercher..')))

    def filter_search(self, queryset, name, value):
        return queryset.filter(Q(designation__icontains=value)).distinct()

    class Meta:
        model = Family
        fields = ['search']

class PackingFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search', widget=forms.TextInput(attrs=getAttrs('search', 'Rechercher..')))

    def filter_search(self, queryset, name, value):
        return queryset.filter(Q(designation__icontains=value) | Q(unit__icontains=value)).distinct()

    class Meta:
        model = Packing
        fields = ['search']

class ProductFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search', widget=forms.TextInput(attrs=getAttrs('search', 'Rechercher..', other={'style': 'width: 100%;'})))
    family = django_filters.ModelChoiceFilter(queryset=Family.objects.all(), empty_label='Choisir Famille')
    packing = django_filters.ModelChoiceFilter(queryset=Packing.objects.all(), empty_label='Choisir Conditionnement')

    def filter_search(self, queryset, name, value):
        return queryset.filter(Q(designation__icontains=value)).distinct()

    class Meta:
        model = Product
        fields = ['search', 'family', 'packing']

class MoveFilter(django_filters.FilterSet):
    TYPE_CHOICES = [
        ('all', 'Tous'),
        ('entree', 'Entré'),
        ('entree_transfer', 'Entrée & Transfer'),
        ('transfer', 'Transfers'),
        ('sortie', 'Sortie'),
    ]

    STATE_REPORT = [
        ('Tous', 'Tous'),
        ('Brouillon', 'Brouillon'),
        ('Confirmé', 'Confirmé'),
        ('Validé', 'Validé'),
        ('Annulé', 'Annulé')
    ]
    
    type = django_filters.ChoiceFilter(method='filter_by_type', choices=TYPE_CHOICES, empty_label=None, initial='all', widget=forms.Select(attrs=getAttrs('select')))
    site = django_filters.CharFilter(field_name="move__site__designation", lookup_expr='icontains', widget=forms.TextInput(attrs=getAttrs('search2', 'Site')))
    warehouse = django_filters.CharFilter(method='filter_by_warehouse', widget=forms.TextInput(attrs=getAttrs('search2', 'Entrepôt')))
    emplacement = django_filters.CharFilter(method='filter_by_emplacement', widget=forms.TextInput(attrs=getAttrs('search2', 'Emplacement')))
    lot_number = django_filters.CharFilter(field_name="move_lines__lot_number", lookup_expr='icontains', widget=forms.TextInput(attrs=getAttrs('search2', 'Lot')))
    start_date = django_filters.DateFilter(field_name="date", lookup_expr='gte', widget=forms.DateInput(attrs=getAttrs('date', 'Date Début')))
    end_date = django_filters.DateFilter(field_name="date", lookup_expr='lte', widget=forms.DateInput(attrs=getAttrs('date', 'Date Fin')))
    product = django_filters.CharFilter(field_name="move_lines__product__designation", lookup_expr='icontains', widget=forms.TextInput(attrs=getAttrs('search2', 'Produit')))

    state = django_filters.ChoiceFilter(method='filter_by_state', choices=STATE_REPORT, empty_label=None, initial='Tous', widget=forms.Select(attrs=getAttrs('select')))

    def filter_by_state(self, queryset, name, value):
        if value == 'Tous':
            return queryset.filter(state__in=['Brouillon', 'Confirmé', 'Validé', 'Annulé'])
        else:
            return queryset.filter(state=value)
    
    def filter_by_type(self, queryset, name, value):
        if value == 'all':
            return queryset.filter(type__in=['Entré', 'Sortie'])
        elif value == 'entree':
            return queryset.filter(type='Entré', is_transfer=False)
        elif value == 'entree_transfer':
            return queryset.filter(Q(type='Entré') | Q(is_transfer=True))
        elif value == 'transfer':
            return queryset.filter(is_transfer=True)
        elif value == 'sortie':
            return queryset.filter(type='Sortie', is_transfer=False)
        return queryset

    def filter_by_warehouse(self, queryset, name, value):
        return queryset.filter(move_lines__details__warehouse__designation__icontains=value).distinct()

    def filter_by_emplacement(self, queryset, name, value):
        return queryset.filter(move_lines__details__emplacement__designation__icontains=value).distinct()

    class Meta:
        model = MoveLine
        fields = ['type', 'site', 'warehouse', 'emplacement', 'lot_number', 'start_date', 'end_date', 'product', 'state']

class LineDetailFilter(django_filters.FilterSet):

    STATE_REPORT = [
        ('Tous', 'Tous'),
        ('Brouillon', 'Brouillon'),
        ('Confirmé', 'Confirmé'),
        ('Annulé', 'Annulé')
    ]
    
    search = django_filters.CharFilter(method='filter_search', widget=forms.TextInput(attrs=getAttrs('search', 'Rechercher..', other={'style': 'width: 80%; margin-right: 10px;'})))
    state = django_filters.ChoiceFilter(method='filter_by_state', choices=STATE_REPORT, empty_label=None, initial='Tous', widget=forms.Select(attrs=getAttrs('select')))

    def filter_search(self, queryset, name, value):
        return queryset.filter(Q(move_line__product__designation__icontains=value)
                               |Q(move_line__lot_number__icontains=value)
                               |Q(move_line__move__date__icontains=value)
                               |Q(move_line__move__gestionaire__fullname__icontains=value)
                               |Q(warehouse__designation__icontains=value)
                               |Q(emplacement__designation__icontains=value)
                               ).distinct()
    
    def filter_by_state(self, queryset, name, value):
        if value == 'Tous':
            return queryset.filter(move_line__move__state__in=['Brouillon', 'Confirmé', 'Annulé'])
        else:
            return queryset.filter(move_line__move__state=value)

    class Meta:
        model = LineDetail
        fields = ['search', 'state']