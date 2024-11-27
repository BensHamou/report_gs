from rest_framework import serializers
from report.models import *
from .models import *

class LineDetailSerializer(serializers.ModelSerializer):
    palette = serializers.ReadOnlyField()

    class Meta:
        model = LineDetail
        fields = ['id', 'warehouse', 'zone', 'qte', 'palette']

class MoveLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.designation', read_only=True)
    expiry_date = serializers.DateField(read_only=True)
    production_date = serializers.DateField(source='move.date', read_only=True)
    details = LineDetailSerializer(many=True, read_only=True) 
    n_lot = serializers.CharField(read_only=True)

    class Meta:
        model = MoveLine
        fields = ['id',  'product_name',  'lot_number',  'code', 'expiry_date',  'production_date',  'details', 'qte', 'palette', 'n_lot']


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ['id', 'designation', 'address', 'email']

class WarehouseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Warehouse
        fields = ['id', 'designation', 'site']

class ZoneSerializer(serializers.ModelSerializer):

    class Meta:
        model = Zone
        fields = ['id', 'designation', 'quarantine', 'temp', 'warehouse']

class LineSerializer(serializers.ModelSerializer):

    class Meta:
        model = Line
        fields = ['id', 'designation', 'prefix_bl', 'prefix_bl_a', 'prefix_nlot', 'site']

class FamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = Family
        fields = ['id', 'designation', 'image']

class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ['id', 'designation']

class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = ['id', 'designation', 'image', 'type', 'family', 'unit']


class DetailAvailabilitySerializer(serializers.ModelSerializer):
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    lot_number = serializers.CharField(source='move_line.lot_number', read_only=True)
    expiry_date = serializers.DateField(source='move_line.expiry_date', read_only=True)

    class Meta:
        model = LineDetail
        fields = ['warehouse_name', 'zone_name', 'qte', 'lot_number', 'expiry_date']

class ProductAvailabilitySerializer(serializers.ModelSerializer):
    availability = LineDetailSerializer(many=True, read_only=True)
    image = serializers.ImageField(use_url=True)
    name = serializers.CharField(source='designation', read_only=True)
    qte_in_line = serializers.IntegerField(source='aggregates.total_qte', read_only=True)
    palettes_in_line = serializers.IntegerField(read_only=True)
    product_id = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = Product
        fields = ['product_id', 'name', 'qte_in_line', 'palettes_in_line', 'qte_per_pal', 'image', 'availability']