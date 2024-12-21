from account.models import BaseModel, Line, Emplacement, Warehouse, Shift, Site
from django.template.defaultfilters import slugify
from django.db.models import Sum, Q
from PIL import Image as PILImage
from django.utils import timezone
from datetime import timedelta
from django.db import models
import math
import os

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

class Packing(BaseModel):
    designation = models.CharField(max_length=255)
    unit = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.designation} en {self.unit}'

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

    family = models.ForeignKey(Family, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    packing = models.ForeignKey(Packing, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    delais_expiration = models.PositiveIntegerField(null=True, blank=True)
    qte_per_pal = models.PositiveIntegerField(null=True, blank=True)
    qte_per_cond = models.PositiveIntegerField(null=True, blank=True)
    alert_stock = models.PositiveIntegerField(null=True, blank=True)
    lines = models.ManyToManyField(Line, related_name='products', blank=True)
    odoo_id = models.PositiveIntegerField(null=True, blank=True)

    def unit_qte(self, site_id):
        return self.disponibilities.filter(emplacement__warehouse__site_id=site_id).aggregate(total=Sum('qte'))['total'] or 0

    def state_in_site(self, site_id):
        return self.disponibilities.filter(emplacement__warehouse__site_id=site_id)

    def tn_qte(self, site_id):
        return round(self.unit_qte(site_id) / 1000, 2)

    def state_stock(self, site_id):
        qte = self.unit_qte(site_id)
        if not self.alert_stock:
            return 'Non défini'
        if qte > self.alert_stock:
            return 'En stock'
        elif qte < self.alert_stock and qte > 0:
            return 'Stock bas'
        return 'Rupture'
    
    def last_entry_date(self, site_id):
        last_entry = MoveLine.objects.filter(product=self, move__type='Entré', move__state='Confirmé', move__site_id=site_id).order_by('-move__date').first()
        return last_entry.move.date if last_entry else None
    
    def __str__(self):
        return self.designation

class Move(BaseModel):

    MOVE_STATE = [
        ('Brouillon', 'Brouillon'),
        ('Confirmé', 'Confirmé'),
        ('Validé', 'Validé'),
        ('Annulé', 'Annulé')
    ]
    MOVE_TYPE = [('Entré', 'Entré'), ('Sortie', 'Sortie')]

    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='moves')
    line = models.ForeignKey(Line, on_delete=models.SET_NULL, null=True, blank=True, related_name='moves')
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, blank=True, related_name='moves')
    gestionaire = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='moves', limit_choices_to=Q(role='Gestionaire') | Q(role='Admin'))

    date = models.DateField(default=timezone.now, null=True, blank=True)
    is_transfer = models.BooleanField(default=False)
    stayed_in_temp = models.PositiveIntegerField(default=0, null=True, blank=True)

    state = models.CharField(choices=MOVE_STATE, max_length=15, default='Brouillon')
    type = models.CharField(choices=MOVE_TYPE, max_length=6, default='Entré')
    mirror = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='transferred_move', null=True, blank=True)

    @property
    def bl_str(self):
        return ', '.join([bl.num for bl in self.bls.all()])
    
    def changeState(self, actor_id, new_state):
        if self.state == new_state:
            return True
        Validation.objects.create(old_state=self.state, new_state=new_state, actor_id=actor_id, move=self)
        self.state = new_state
        self.save()
        return True
        
    def can_validate(self):
        def check_emplacement(detail, operation):
            if operation == 'stock' and not detail.emplacement.can_stock(detail.palette):
                return False, f'Emplacement {detail.emplacement} n\'a pas la capacité suffisante pour stocker cette quantité de palettes'
            elif operation == 'destock' and not detail.emplacement.can_destock(detail.palette):
                return False, f"Ajustement entraînerait un stock négatif pour l'emplacement {detail.emplacement}."
            return True, None

        operation = 'stock' if self.type == 'Entré' else 'destock'
        for ml in self.move_lines.all():
            for detail in ml.details.all():
                is_valid, error_message = check_emplacement(detail, operation)
                if not is_valid:
                    raise ValueError(f"{ml.n_lot} - {error_message}")
        return True, 'Can stock'
    
    def integrate_in_stock(self):
        is_entry = self.type == 'Entré'
        for ml in self.move_lines.all():
            for detail in ml.details.all():
                ds = Disponibility.objects.filter(product=ml.product,emplacement=detail.emplacement, n_lot=ml.n_lot).first()
                if is_entry:
                    if ds:
                        ds.qte += detail.qte
                        ds.write_uid = ml.create_uid
                    else:
                        ds = Disponibility(product=ml.product, emplacement=detail.emplacement, qte=detail.qte, create_uid=ml.create_uid, 
                                        production_date=ml.move.date, expiry_date=ml.expiry_date, write_uid=ml.create_uid, n_lot=ml.n_lot )
                else:
                    if not ds:
                        raise ValueError(f"{ml.n_lot} - Stock introuvable.")
                    ds.qte -= detail.qte
                if ds.qte > 0:
                    ds.save()
                else:
                    ds.delete()
        return True, 'Stock ajusté avec succès.'

    def do_after_validation(self, user):
        if not self.integrate_in_stock():
            raise ValueError(f"{ml.n_lot} - Échec d\'ajuster le stock.")
        for ml in self.move_lines.all():
            for detail in ml.details.all():
                if not detail.generateCode(user):
                    raise ValueError(f"{ml.n_lot} - Échec de la génération du code QR pour l'emplacement {detail.emplacement}.")
        return True, 'Stock ajusté et codes QR générés avec succès.'
    
    def create_mirror(self):
        if self.type == 'Sortie' and self.state == 'Validé' and self.is_transfer:
            try:
                mirror = Move.objects.create(site=self.site, gestionaire=self.gestionaire, date=self.date, type='Entré', is_transfer=True, state='Brouillon', mirror=self)
                self.mirror = mirror
                self.save()
                for ml in self.move_lines.all():
                    move_mirror = MoveLine.objects.create(lot_number=ml.n_lot, product=ml.product, mirror=ml, move=mirror, transfered_qte=ml.qte)
                    ml.mirror = move_mirror
                    ml.save()
            except Exception as e:
                raise RuntimeError(f"Error during mirror creation: {e}")

    def __str__(self):
        if not self.line:  
            return f"[{self.id}] {self.site} - {self.date}"
        return f"[{self.id}] {self.line.designation} - {self.date}"
    
class MoveLine(BaseModel):
    lot_number = models.CharField(max_length=255)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='move_lines')
    move = models.ForeignKey(Move, on_delete=models.CASCADE, related_name='move_lines')
    mirror = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='transferred_line', null=True, blank=True)
    observation = models.TextField(blank=True, null=True)
    transfered_qte = models.PositiveIntegerField(default=0, null=True, blank=True)

    @property
    def qte(self):
        return self.details.aggregate(total=models.Sum('qte'))['total'] or 0

    @property
    def expiry_date(self):
        if self.product.type == 'Produit Fini':
            return self.move.date + timedelta(days=self.product.delais_expiration) 
        else:
            return None

    @property
    def package(self):
        return sum(detail.package for detail in self.details.all()) or 0

    @property
    def palette(self):
        return sum(detail.palette for detail in self.details.all()) or 0

    @property
    def n_lot(self):
        if self.move.type == 'Entré':
            if self.product.type == 'Produit Fini':
                return f'{self.move.line.prefix_nlot}-{self.lot_number.zfill(5)}/{str(self.move.date.year)[-2:]}'
            else:
                return self.lot_number
        else:
            return '/'
        
    def __str__(self):
        return f"[{self.id}] {self.product} - {self.qte}"
    
class LineDetail(BaseModel):
    move_line = models.ForeignKey(MoveLine, on_delete=models.CASCADE, related_name='details')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='details')
    emplacement = models.ForeignKey(Emplacement, on_delete=models.CASCADE, related_name='details')
    qte = models.PositiveIntegerField()
    code = models.CharField(max_length=255, null=True, blank=True)
    n_lot = models.CharField(max_length=255, null=True, blank=True)

    @property
    def palette(self):
        if self.move_line.product.qte_per_pal and self.qte:
            return math.ceil(self.qte / self.move_line.product.qte_per_pal)
        return 0

    @property
    def package(self):
        if self.move_line.product.qte_per_cond and self.qte:
            return math.ceil(self.qte / self.move_line.product.qte_per_cond)
        return 0
        
    def generateCode(self, user):
        try:
            self.code = f"Product:{self.move_line.product.id};Emplacement:{self.emplacement.id};NLOT:{self.move_line.n_lot}"
            if self.emplacement.temp:
                TemporaryEmplacementAlert.objects.get_or_create(line_detail=self, write_uid=user, create_uid=user)
            self.save()

            return True
        except Exception as e:
            print(f'Error lors de génération de code : {e}')
            return False

    class Meta:
        constraints = [models.CheckConstraint(check=models.Q(qte__gte=0), name="qte_positive")]

    def __str__(self):
        return f"{self.move_line.product} - {self.qte}"

class TemporaryEmplacementAlert(BaseModel):
    line_detail = models.OneToOneField(LineDetail, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    email_sent = models.BooleanField(default=False)

class MoveBL(BaseModel):
    move = models.ForeignKey(Move, on_delete=models.CASCADE, related_name='bls')
    is_annexe = models.BooleanField(default=False)
    numero = models.PositiveIntegerField()

    @property
    def num(self):
        if self.is_annexe:
            return f'{self.move.site.prefix_bl_a}{str(self.numero).zfill(5)}/{str(self.move.date.year)[-2:]}'
        else:
            return f'{self.move.site.prefix_bl}{str(self.numero).zfill(5)}/{str(self.move.date.year)[-2:]}'
    
    def __str__(self):
        return f"{self.move} - {self.numero}"

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
    move = models.ForeignKey(Move, on_delete=models.CASCADE, related_name='validations')

    def __str__(self):
        return f"Validation - {str(str(self.move.id).zfill(4))} - {str(self.date)} ({self.old_state} -> {self.new_state})" 
    
class Disponibility(BaseModel):
    emplacement = models.ForeignKey(Emplacement, related_name='disponibilities', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='disponibilities', on_delete=models.CASCADE)
    n_lot = models.CharField(max_length=50)
    qte = models.PositiveIntegerField()
    production_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    @property
    def palette(self):
        if self.product.qte_per_pal and self.qte:
            return math.ceil(self.qte / self.product.qte_per_pal)
        return 0
    