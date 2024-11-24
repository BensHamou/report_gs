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

class UnitFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search', widget=forms.TextInput(attrs=getAttrs('search', 'Rechercher..')))

    def filter_search(self, queryset, name, value):
        return queryset.filter(Q(designation__icontains=value)).distinct()

    class Meta:
        model = Unit
        fields = ['search']

class ProductFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search', widget=forms.TextInput(attrs=getAttrs('search', 'Rechercher..')))
    family = django_filters.ModelChoiceFilter(queryset=Family.objects.all(), empty_label='Choisir Famille')
    unit = django_filters.ModelChoiceFilter(queryset=Unit.objects.all(), empty_label='Choisir Unité')

    def filter_search(self, queryset, name, value):
        return queryset.filter(Q(designation__icontains=value)).distinct()

    class Meta:
        model = Product
        fields = ['search', 'family', 'unit']

class MoveLineFilter(django_filters.FilterSet):
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
        ('Annulé', 'Annulé')
    ]
    
    search = django_filters.CharFilter(method='filter_search', widget=forms.TextInput(attrs=getAttrs('search', 'Rechercher..')))
    type = django_filters.ChoiceFilter(method='filter_by_type', choices=TYPE_CHOICES, empty_label=None, initial='all', widget=forms.Select(attrs=getAttrs('select')))
    state = django_filters.ChoiceFilter(method='filter_by_state', choices=STATE_REPORT, empty_label=None, initial='Tous', widget=forms.Select(attrs=getAttrs('select')))

    def filter_search(self, queryset, name, value):
        return queryset.filter(Q(product__designation__icontains=value)
                               |Q(lot_number__icontains=value)
                               |Q(move__date__icontains=value)
                               |Q(move__gestionaire__fullname__icontains=value)
                               ).distinct()
    
    def filter_by_state(self, queryset, name, value):
        if value == 'Tous':
            return queryset.filter(move__state__in=['Brouillon', 'Confirmé', 'Annulé'])
        else:
            return queryset.filter(move__state=value)
    
    def filter_by_type(self, queryset, name, value):
        if value == 'all':
            return queryset.filter(move__type__in=['Entré', 'Sortie'])
        elif value == 'entree':
            return queryset.filter(move__type='Entré', move__is_transfer=False)
        elif value == 'entree_transfer':
            return queryset.filter(Q(move__type='Entré') | Q(move__is_transfer=True))
        elif value == 'transfer':
            return queryset.filter(move__is_transfer=True)
        elif value == 'sortie':
            return queryset.filter(move__type='Sortie', move__is_transfer=False)
        return queryset

    class Meta:
        model = MoveLine
        fields = ['search', 'type', 'state']
