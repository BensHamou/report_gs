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

class MoveFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search', widget=forms.TextInput(attrs=getAttrs('search', 'Rechercher..')))

    def filter_search(self, queryset, name, value):
        return queryset.filter(Q(n_bl_1__icontains=value)).distinct()

    class Meta:
        model = Unit
        fields = ['search']
