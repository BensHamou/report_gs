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


class TabletMoveScanSerializer(serializers.ModelSerializer):
    bl_str = serializers.ReadOnlyField()
    site_name = serializers.CharField(source='site.designation', default='/', read_only=True)
    type = serializers.SerializerMethodField()
    observation = serializers.SerializerMethodField()
    to_scan = serializers.SerializerMethodField()
    scanned = serializers.SerializerMethodField()

    class Meta:
        model = Move
        fields = ['id', 'bl_str', 'date', 'site_name', 'type', 'observation', 'to_scan', 'scanned']

    def get_type(self, obj):
        if obj.is_transfer and not obj.is_isolation:
            return "transfer"
        elif obj.is_transfer and obj.is_isolation:
            return "isolation"
        elif not obj.is_transfer and obj.is_isolation:
            return "consumption"
        return "normal"

    def get_observation(self, obj):
        first_line = obj.move_lines.first()
        return first_line.observation if (first_line and first_line.observation) else "/"

    def _get_scan_data(self, obj, is_scanned):
        detail_codes = DetailCode.objects.filter(line_detail__move_line__move=obj, is_scanned=is_scanned).select_related(
            'line_detail__emplacement__warehouse', 'line_detail__move_line__product')
        emplacements_map = {}
        for dc in detail_codes:
            emp = dc.line_detail.emplacement
            prod = dc.line_detail.move_line.product
            
            if emp.id not in emplacements_map:
                warehouse_name = emp.warehouse.designation if emp.warehouse else ""
                emplacements_map[emp.id] = {
                    'id': emp.id,
                    'name': f"{warehouse_name} - {emp.designation}",
                    'products': {}
                }
            
            if prod.id not in emplacements_map[emp.id]['products']:
                image_url = ""
                if prod.image:
                    request = self.context.get('request')
                    if request:
                        image_url = request.build_absolute_uri(prod.image.url)
                    else:
                        image_url = prod.image.url
                
                emplacements_map[emp.id]['products'][prod.id] = {
                    'id': prod.id,
                    'name': prod.designation,
                    'image': image_url,
                    'codes': []
                }
            
            emplacements_map[emp.id]['products'][prod.id]['codes'].append({
                'id': dc.id,
                'code': dc.code,
                'qte_to_scan': f'{dc.qte} {prod.packing.unit}',
                'qte_per_cond': f'{dc.qte / prod.qte_per_cond} {prod.packing.designation}' if prod.qte_per_cond else f'{dc.qte} {prod.packing.unit}'
            })
            
        result = []
        for emp_id, emp_data in emplacements_map.items():
            emp_data['products'] = list(emp_data['products'].values())
            result.append(emp_data)
        return result

    def get_to_scan(self, obj):
        return self._get_scan_data(obj, is_scanned=False)

    def get_scanned(self, obj):
        return self._get_scan_data(obj, is_scanned=True)


