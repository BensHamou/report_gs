from rest_framework import serializers
from report.models import *
from .models import *

class LineDetailSerializer(serializers.ModelSerializer):
    package = serializers.ReadOnlyField()

    class Meta:
        model = LineDetail
        fields = ['id', 'warehouse', 'emplacement', 'n_lot', 'qte', 'palette', 'package']

class MoveLineSerializer(serializers.ModelSerializer):
    n_lot = serializers.ReadOnlyField()
    expiry_date = serializers.ReadOnlyField()
    qte = serializers.ReadOnlyField()
    palette = serializers.ReadOnlyField()
    observation = serializers.ReadOnlyField()
    details = LineDetailSerializer(many=True, read_only=True)

    class Meta:
        model = MoveLine
        fields = ['id',  'product', 'expiry_date',  'details', 'qte', 'palette', 'n_lot', 'observation']
        
class MoveSerializer(serializers.ModelSerializer):
    n_lots = serializers.ReadOnlyField()
    gestionaire = serializers.CharField(source='gestionaire.fullname', read_only=True)
    qte = serializers.ReadOnlyField()
    palette = serializers.ReadOnlyField()
    bl_str = serializers.ReadOnlyField()
    move_lines = MoveLineSerializer(many=True, read_only=True)
    display_type = serializers.ReadOnlyField()
    date = serializers.ReadOnlyField()
    product_display = serializers.ReadOnlyField()

    class Meta:
        model = Move
        fields = ['id', 'date', 'move_lines', 'qte', 'palette', 'n_lots', 'state', 'product_display', 'transfer_to',
                  'gestionaire', 'bl_str', 'display_type', 'is_transfer', 'is_inventory', 'is_isolation', 'line', 'site', 'date_created', 'shift']

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
        fields = ['id', 'designation', 'image', 'for_mp', 'is_expiring', 'sequence']

class PackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Packing
        fields = ['id', 'designation', 'unit']

class ProductSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = Product
        fields = ['id', 'designation', 'image', 'type', 'family', 'packing', 'delais_expiration', 'qte_per_pal', 'qte_per_cond', 'alert_stock', 'alert_stock_max', 'alert_expiration']


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


class LightMoveSerializer(serializers.ModelSerializer):
    bl_str = serializers.ReadOnlyField()
    site_name = serializers.CharField(source='site.designation', default='/', read_only=True)
    product_display_pda = serializers.ReadOnlyField()
    type = serializers.SerializerMethodField()
    expected_qte = serializers.SerializerMethodField()
    expected_plt = serializers.SerializerMethodField()
    date = serializers.ReadOnlyField()

    class Meta:
        model = Move
        fields = ['id', 'bl_str', 'date', 'site_name', 'product_display_pda', 'expected_qte', 'expected_plt', 'type']

    def get_type(self, obj):
        if obj.is_transfer and not obj.is_isolation:
            return "transfer"
        elif obj.is_transfer and obj.is_isolation:
            return "isolation"
        elif not obj.is_transfer and obj.is_isolation:
            return "consumption"
        return "normal"

    def get_expected_qte(self, obj):
        return sum((ml.initial_qte or 0) for ml in obj.move_lines.all())

    def get_expected_plt(self, obj):
        import math
        total_plt = 0
        for ml in obj.move_lines.all():
            qte = ml.initial_qte or 0
            if ml.product.qte_per_pal and ml.product.qte_per_pal > 0:
                total_plt += math.ceil(qte / ml.product.qte_per_pal)
        return total_plt
