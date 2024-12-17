from rest_framework import serializers
from report.models import *
from .models import *

class LineDetailSerializer(serializers.ModelSerializer):
    palette = serializers.ReadOnlyField()

    class Meta:
        model = LineDetail
        fields = ['id', 'warehouse', 'emplacement', 'n_lot', 'qte', 'palette']

class MoveLineSerializer(serializers.ModelSerializer):
    details = LineDetailSerializer(many=True, read_only=True)
    production_date = serializers.DateField(source='move.date', read_only=True)
    expiry_date = serializers.DateField(read_only=True)
    n_lot = serializers.CharField(read_only=True)
    gestionaire = serializers.CharField(source='move.gestionaire.fullname', read_only=True)
    state = serializers.CharField(source='move.state', read_only=True)
    bls = serializers.CharField(source='move.bl_str', read_only=True)
    type = serializers.CharField(source='move.type', read_only=True)
    is_transfer = serializers.CharField(source='move.is_transfer', read_only=True)
    is_transfer = serializers.CharField(source='move.is_transfer', read_only=True)
    line = serializers.CharField(source='move.line', read_only=True)
    site = serializers.CharField(source='move.site', read_only=True)
    shift = serializers.CharField(source='move.shift', read_only=True)

    class Meta:
        model = MoveLine
        fields = ['id',  'product', 'expiry_date',  'production_date',  'details', 'qte', 'palette', 'n_lot', 'state', 
                  'gestionaire', 'bls', 'type', 'is_transfer', 'line', 'site', 'date_created', 'shift']


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ['id', 'designation', 'address', 'email', 'prefix_bl', 'prefix_bl_a']

class WarehouseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Warehouse
        fields = ['id', 'designation', 'site']

class EmplacementSerializer(serializers.ModelSerializer):

    class Meta:
        model = Emplacement
        fields = ['id', 'designation', 'type', 'capacity', 'quarantine', 'temp', 'warehouse']

class LineSerializer(serializers.ModelSerializer):

    class Meta:
        model = Line
        fields = ['id', 'designation', 'prefix_nlot', 'site']

class FamilySerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)
    class Meta:
        model = Family
        fields = ['id', 'designation', 'image']

class PackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Packing
        fields = ['id', 'designation', 'unit']

class ProductSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = Product
        fields = ['id', 'designation', 'image', 'type', 'family', 'packing', 'delais_expiration', 'qte_per_pal', 'qte_per_cond', 'alert_stock']


class DisponibilitySerializer(serializers.ModelSerializer):
    warehouse_id = serializers.CharField(source='emplacement.warehouse.id', read_only=True)
    emplacement_id = serializers.CharField(source='emplacement.id', read_only=True)
    palette = serializers.ReadOnlyField()

    class Meta:
        model = Disponibility
        fields = ['warehouse_id', 'emplacement_id', 'n_lot', 'qte', 'palette', 'production_date', 'expiry_date']

class ProductDisponibilitySerializer(serializers.ModelSerializer):
    disponibility = DisponibilitySerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'disponibility']