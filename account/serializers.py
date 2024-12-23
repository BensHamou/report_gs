from rest_framework import serializers
from report.models import *
from .models import *

class LineDetailSerializer(serializers.ModelSerializer):
    palette = serializers.ReadOnlyField()

    class Meta:
        model = LineDetail
        fields = ['id', 'warehouse', 'emplacement', 'n_lot', 'qte', 'palette']

class MoveLineSerializer(serializers.ModelSerializer):
    n_lot = serializers.ReadOnlyField()
    expiry_date = serializers.ReadOnlyField()
    qte = serializers.ReadOnlyField()
    palette = serializers.ReadOnlyField()
    details = LineDetailSerializer(many=True, read_only=True)

    class Meta:
        model = MoveLine
        fields = ['id',  'product', 'expiry_date',  'details', 'qte', 'palette', 'n_lot']
        
class MoveSerializer(serializers.ModelSerializer):
    n_lots = serializers.ReadOnlyField()
    gestionaire = serializers.CharField(source='gestionaire.fullname', read_only=True)
    qte = serializers.ReadOnlyField()
    palette = serializers.ReadOnlyField()
    move_lines = MoveLineSerializer(many=True, read_only=True)

    class Meta:
        model = Move
        fields = ['id', 'date',  'move_lines', 'qte', 'palette', 'n_lots', 'state', 
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

