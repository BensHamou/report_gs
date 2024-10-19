import django_filters
from django import forms
from django.db.models import Q
from .models import *
from .forms import getAttrs

class UserFilter(django_filters.FilterSet):
    
    search = django_filters.CharFilter(method='filter_search', widget=forms.TextInput(attrs=getAttrs('search', 'Rechercher..')))

    def filter_search(self, queryset, name, value):
        return queryset.filter( Q(fullname__icontains=value) | Q(username__icontains=value) | Q(role__icontains=value) | Q(usines__designation__contains=value) ).distinct()

    class Meta:
        model = User
        fields = ['search']

class ShiftFilter(django_filters.FilterSet):
    
    search = django_filters.CharFilter(method='filter_search', widget=forms.TextInput(attrs=getAttrs('search', 'Rechercher..')))

    def filter_search(self, queryset, name, value):
        return queryset.filter(Q(start_time__icontains=value) | Q(end_time__icontains=value)).distinct()

    class Meta:
        model = Shift
        fields = ['search']

class WarehouseFilter(django_filters.FilterSet):
    
    search = django_filters.CharFilter(method='filter_search', widget=forms.TextInput(attrs=getAttrs('search', 'Rechercher..')))

    def filter_search(self, queryset, name, value):
        return queryset.filter(Q(designation__icontains=value)).distinct()

    class Meta:
        model = Warehouse
        fields = ['search']

class LineFilter(django_filters.FilterSet):
    
    search = django_filters.CharFilter(method='filter_search', widget=forms.TextInput(attrs=getAttrs('search', 'Rechercher..')))

    def filter_search(self, queryset, name, value):
        return queryset.filter(Q(designation__icontains=value)).distinct()

    class Meta:
        model = Line
        fields = ['search']

class ZoneFilter(django_filters.FilterSet):
    
    search = django_filters.CharFilter(method='filter_search', widget=forms.TextInput(attrs=getAttrs('search', 'Rechercher..')))

    def filter_search(self, queryset, name, value):
        return queryset.filter(Q(designation__icontains=value)).distinct()

    class Meta:
        model = Zone
        fields = ['search']

class SiteFilter(django_filters.FilterSet): 
    
    search = django_filters.CharFilter(method='filter_search', widget=forms.TextInput(attrs=getAttrs('search', 'Rechercher..')))

    def filter_search(self, queryset, name, value):
        return queryset.filter(Q(designation__contains=value)).distinct()

    class Meta:
        model = Site 
        fields = ['search']
