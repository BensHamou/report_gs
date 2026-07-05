from rest_framework import serializers
from report.models import *
from .models import *


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
