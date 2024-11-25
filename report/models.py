from account.models import BaseModel, Line, Zone, Warehouse, Shift
from django.template.defaultfilters import slugify
from PIL import Image as PILImage
from django.utils import timezone
from django.db.models import Sum, Q
from django.db import models
import os
import math
from datetime import timedelta

def get_family_image_filename(instance, filename):
    title = instance.designation
    slug = slugify(title)
    return f"images/family/{slug}-{filename}"

class Family(BaseModel):
    designation = models.CharField(max_length=255)
    image = models.ImageField(upload_to=get_family_image_filename, verbose_name='Image', blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image and os.path.exists(self.image.path):
            img = PILImage.open(self.image.path)
            max_size = (1280, 720)
            img.thumbnail(max_size, PILImage.LANCZOS)
            img.save(self.image.path, quality=50, optimize=True)

    def __str__(self):
        return self.designation

class Unit(BaseModel):
    designation = models.CharField(max_length=255)

    def __str__(self):
        return self.designation

def get_product_image_filename(instance, filename):
    title = instance.designation
    slug = slugify(title)
    return f"images/product/{slug}-{filename}"

class Product(BaseModel):
    PRODUCT_CHOICES = [
        ('Produit Fini', 'Produit Fini'),
        ('Matière Première', 'Matière Première')
    ]

    designation = models.CharField(max_length=255)
    image = models.ImageField(upload_to=get_product_image_filename, verbose_name='Image', blank=True, null=True)
    type = models.CharField(choices=PRODUCT_CHOICES, max_length=50, default='Produit Fini')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image and os.path.exists(self.image.path):
            img = PILImage.open(self.image.path)
            max_size = (1280, 720)
            img.thumbnail(max_size, PILImage.LANCZOS)
            img.save(self.image.path, quality=50, optimize=True)

    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='products')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='products')
    delais_expiration = models.PositiveIntegerField()
    qte_per_pal = models.PositiveIntegerField()
    alert_stock = models.PositiveIntegerField()
    lines = models.ManyToManyField(Line, related_name='products', blank=True)

    def get_stock_details(self, site):
        move_lines = MoveLine.objects.filter(product=self, move__state='Confirmé', move__line__site=site)
        stock_aggregate = move_lines.filter(move__type='Entré').aggregate(total_in=Sum('details__qte'))
        stock_aggregate.update(move_lines.filter(move__type='Sortie').aggregate(total_out=Sum('details__qte')))
        net_stock = (stock_aggregate['total_in'] or 0) - (stock_aggregate['total_out'] or 0)

        valid_zones = Zone.objects.filter(temp=False, quarantine=False, warehouse__site=site)
        
        availability = (
            LineDetail.objects.filter(move_line__product=self, move_line__move__state='Confirmé', zone__in=valid_zones)
            .values('warehouse__designation', 'zone__designation', 'warehouse__id', 'zone__id')
            .annotate(qte_in=Sum('qte', filter=Q(move_line__move__type='Entré')), qte_out=Sum('qte', filter=Q(move_line__move__type='Sortie')))
            .annotate(net_qte=(models.F('qte_in') or 0 - models.F('qte_out') or 0))
            .filter(net_qte__gt=0)
        )

        return {'net_stock': net_stock, 'availability': list(availability)}

    def qte_in_stock(self, site):
        return self.get_stock_details(site)['net_stock'] / 1000

    def state_stock(self, site):
        qte = self.qte_in_stock(site)
        if qte > self.alert_stock / 1000:
            return 'En stock'
        elif qte < self.alert_stock / 1000 and qte > 0:
            return 'Stock bas'
        return 'Rupture'
    
    def last_entry_date(self, site):
        last_entry = MoveLine.objects.filter(product=self, move__type='Entré', move__state='Confirmé', move__line__site=site).order_by('-move__date').first()
        return last_entry.move.date if last_entry else None
    
    def __str__(self):
        return self.designation

class Move(BaseModel):

    MOVE_STATE = [
        ('Brouillon', 'Brouillon'),
        ('Confirmé', 'Confirmé'),
        ('Annulé', 'Annulé')
    ]
    MOVE_TYPE = [('Entré', 'Entré'), ('Sortie', 'Sortie')]

    line = models.ForeignKey(Line, on_delete=models.CASCADE, related_name='moves')
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, blank=True, related_name='moves')
    gestionaire = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='moves', limit_choices_to=Q(role='Gestionaire') | Q(role='Admin'))

    date = models.DateField(default=timezone.now)
    n_bl_1 = models.PositiveIntegerField(blank=True, null=True)
    n_bl_2 = models.PositiveIntegerField(blank=True, null=True)
    n_bl_3 = models.PositiveIntegerField(blank=True, null=True)
    n_bl_a = models.PositiveIntegerField(blank=True, null=True)
    is_transfer = models.BooleanField(default=False)
    stayed_in_temp = models.PositiveIntegerField(default=0)

    state = models.CharField(choices=MOVE_STATE, max_length=15, default='Brouillon')
    type = models.CharField(choices=MOVE_TYPE, max_length=6, default='Entré')

    def __str__(self):
        return f"{self.line.designation} - {self.date}"
    
class MoveLine(BaseModel):
    lot_number = models.CharField(max_length=255)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='move_lines')
    move = models.ForeignKey(Move, on_delete=models.CASCADE, related_name='move_lines')

    @property
    def qte(self):
        return self.details.aggregate(total=models.Sum('qte'))['total'] or 0

    @property
    def expiry_date(self):
        return self.move.date + timedelta(days=self.product.delais_expiration) 

    @property
    def palette(self):
        return sum(detail.palette for detail in self.details.all()) or 0

    @property
    def n_lot(self):
        return f'{self.move.line.prefix_nlot}-{self.lot_number.zfill(5)}/{self.move.date.year}'
    
    def __str__(self):
        return f"{self.product} - {self.qte} - {self.lot_number}"
    
class LineDetail(BaseModel):
    move_line = models.ForeignKey(MoveLine, on_delete=models.CASCADE, related_name='details')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='details')
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='details')
    qte = models.PositiveIntegerField()
    code = models.CharField(max_length=255, null=True, blank=True)
    mirrored_move = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='transfers', blank=True, null=True)

    @property
    def palette(self):
        if self.move_line.product.qte_per_pal and self.qte:
            return math.ceil(self.qte / self.move_line.product.qte_per_pal)
        return 0

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(qte__gte=0), name="qte_positive"),
        ]

    def __str__(self):
        return f"{self.move_line.product} - {self.qte}"


class Validation(BaseModel):
    MOVE_STATE = [
        ('Brouillon', 'Brouillon'),
        ('Confirmé', 'Confirmé'),
        ('Annulé', 'Annulé')
    ]
    old_state = models.CharField(choices=MOVE_STATE, max_length=40)
    new_state = models.CharField(choices=MOVE_STATE, max_length=40)
    date = models.DateTimeField(auto_now_add=True) 
    actor = models.ForeignKey('account.User', on_delete=models.SET_NULL, null=True, related_name='validations', limit_choices_to=Q(role='Gestionaire') | Q(role='Admin'))
    refusal_reason = models.TextField(blank=True, null=True)
    move = models.ForeignKey(Move, on_delete=models.CASCADE, related_name='validations')

    def __str__(self):
        return f"Validation - {str(str(self.move.id).zfill(4))} - {str(self.date)} ({self.old_state} -> {self.new_state})" 
    