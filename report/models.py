from account.models import BaseModel, Line, Emplacement, Warehouse, Shift, Site
from django.template.defaultfilters import slugify
from django.db.models import Sum, Q
from PIL import Image as PILImage
import datetime
from django.db import models
import math
import os
from django.utils import timezone
from datetime import timedelta

def get_family_image_filename(instance, filename):
    title = instance.designation
    slug = slugify(title)
    return f"images/family/{slug}-{filename}"

class Family(BaseModel):
    designation = models.CharField(max_length=255)
    image = models.ImageField(upload_to=get_family_image_filename, verbose_name='Image', blank=True, null=True)
    for_mp = models.BooleanField(default=False)
    nb_days_min = models.PositiveIntegerField(null=True, blank=True, default=10)
    nb_days_max = models.PositiveIntegerField(null=True, blank=True, default=20)
    nb_min_btr = models.PositiveIntegerField(null=True, blank=True, default=10)
    is_expiring = models.BooleanField(default=False)
    sequence = models.PositiveIntegerField(default=99)

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
    qte_per_pal = models.FloatField(null=True, blank=True)
    qte_per_cond = models.FloatField(null=True, blank=True)
    alert_stock = models.PositiveIntegerField(null=True, blank=True, default=0)
    alert_stock_max = models.PositiveIntegerField(null=True, blank=True, default=0)
    alert_expiration = models.PositiveIntegerField(null=True, blank=True, default=150)
    lines = models.ManyToManyField(Line, related_name='products', blank=True)
    check_minmax = models.BooleanField(default=True)
    odoo_id = models.PositiveIntegerField(null=True, blank=True)

    def unit_qte(self, site_id):
        return self.disponibilities.filter(emplacement__warehouse__site_id=site_id).aggregate(total=Sum('qte'))['total'] or 0

    def state_in_site(self, site_id, move_type='normal'):
        queryset = self.disponibilities.filter(emplacement__warehouse__site_id=site_id)
        if move_type == 'normal':
            queryset = queryset.filter(emplacement__quarantine=False, emplacement__temp=False).order_by('expiry_date', 'n_lot')
        elif move_type == 'isolation':
            queryset = queryset.filter(emplacement__quarantine=False)
        elif move_type == 'consumption':
            queryset = queryset.filter(emplacement__quarantine=True)
        return queryset

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
        last_entry = MoveLine.objects.filter(product=self, move__type='Entré', move__state='Validé', move__site_id=site_id).order_by('-move__date').first()
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
    gestionaire = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='moves', limit_choices_to=Q(role='Gestionaire') | Q(role='Validateur') | Q(role='Admin'))

    date = models.DateField(default=datetime.date.today, null=True, blank=True)
    is_transfer = models.BooleanField(default=False)
    is_isolation = models.BooleanField(default=False)
    is_inventory = models.BooleanField(default=False)
    stayed_in_temp = models.PositiveIntegerField(default=0, null=True, blank=True) 


    state = models.CharField(choices=MOVE_STATE, max_length=15, default='Brouillon')
    type = models.CharField(choices=MOVE_TYPE, max_length=6, default='Entré')
    transfer_to = models.ForeignKey(Site, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfers')
    mirror = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='transferred_move', null=True, blank=True)

    @property
    def palette(self):
        return sum(ml.palette for ml in self.move_lines.all()) or 0
    
    @property
    def qte(self):
        return sum(ml.qte for ml in self.move_lines.all()) or 0.0
    
    @property
    def bl_str(self):
        return ', '.join([bl.num for bl in self.bls.all()])
    
    def changeState(self, actor_id, new_state):
        if self.state == new_state:
            return True
        Validation.objects.create(old_state=self.state, new_state=new_state, actor_id=actor_id, move=self)
        self.state = new_state
        self.save()
        
        if new_state == 'Annulé':
            for ml in self.move_lines.all():
                for detail in ml.details.all():
                    for dc in detail.detail_codes.all():
                        DisponibilityLine.objects.filter(code=dc.code, status__in=['Sortie', 'Partialement Sortie']).update(status='Valide')
        return True

    def delete(self, *args, **kwargs):
        for ml in self.move_lines.all():
            for detail in ml.details.all():
                for dc in detail.detail_codes.all():
                    DisponibilityLine.objects.filter(code=dc.code, status__in=['Sortie', 'Partialement Sortie']).update(status='Valide')
        super().delete(*args, **kwargs)
        
    def can_validate(self):
        def check_emplacement(detail, operation):
            if operation == 'destock' and not detail.emplacement.can_destock(detail.qte):
                return False, f"Ajustement entraînerait un stock négatif pour l'emplacement {detail.emplacement}."
            return True, None

        operation = 'stock' if self.type == 'Entré' else 'destock'
        for ml in self.move_lines.all():
            for detail in ml.details.all():
                is_valid, error_message = check_emplacement(detail, operation)
                if not is_valid:
                    raise ValueError(f"{detail.n_lot} - {error_message}")
                
                if operation == 'destock':
                    detail_codes = detail.detail_codes.all()
                    if detail_codes.exists():
                        for dc in detail_codes:
                            dl = DisponibilityLine.objects.filter(code=dc.code).first()
                            if not dl:
                                raise ValueError(f"Code QR {dc.code} introuvable en stock.")
                            if dl.qte < dc.qte:
                                raise ValueError(f"Quantité insuffisante sur la palette {dc.code} (Requis: {dc.qte}, Dispo: {dl.qte}).")
                    else:
                        ds = Disponibility.objects.filter(product=ml.product, emplacement=detail.emplacement, n_lot=detail.n_lot).first()
                        if not ds:
                            raise ValueError(f"{detail.n_lot} - Stock introuvable dans {detail.emplacement.designation} pour le produit {ml.product}.")
                        if ds.qte < detail.qte:
                            raise ValueError(f"{detail.n_lot} - Quantité en stock insuffisante pour le produit {ml.product} dans {detail.emplacement.designation}.")
        return True, 'Can stock'
    
    def integrate_in_stock(self):
        is_entry = self.type == 'Entré'
        for ml in self.move_lines.all():
            for detail in ml.details.all():
                if is_entry:
                    ds = Disponibility.objects.filter(product=ml.product, emplacement=detail.emplacement, n_lot=detail.n_lot).first()
                    if ds:
                        ds.qte += detail.qte
                        ds.palette += detail.palette
                        ds.write_uid = ml.create_uid
                    else:
                        ds = Disponibility(product=ml.product, emplacement=detail.emplacement, qte=detail.qte, palette=detail.palette, create_uid=ml.create_uid, 
                                           production_date=ml.move.date, expiry_date=ml.expiry_date, write_uid=ml.create_uid, n_lot=detail.n_lot)
                    
                    if detail.emplacement.temp:
                        ds.save()
                        TemporaryEmplacementAlert.objects.get_or_create(dispo=ds, write_uid=detail.create_uid, create_uid=detail.create_uid, type='Temporaire')
                    else:
                        ds.save()
                else:
                    detail_codes = detail.detail_codes.all()
                    if detail_codes.exists():
                        for dc in detail_codes:
                            dl = DisponibilityLine.objects.filter(code=dc.code).first()
                            if not dl:
                                raise ValueError(f"Palette {dc.code} introuvable en stock.")
                            
                            ds = dl.disponibility
                            dl.qte -= dc.qte
                            ds.qte -= dc.qte
                            
                            if ml.product.type == 'Produit Fini':
                                if dl.qte <= 0:
                                    ds.palette = max(ds.palette - 1, 0)
                            else:
                                ds.palette = max(ds.palette - dc.palette, 0)
                                dl.palette = max(dl.palette - dc.palette, 0)
                            
                            if dl.qte <= 0:
                                dl.delete()
                            else:
                                dl.status = 'Valide'
                                dl.save()
                            
                            if ds.qte <= 0:
                                ds.delete()
                            else:
                                ds.save()
                    else:
                        # Legacy/fallback bulk deduction
                        ds = Disponibility.objects.filter(product=ml.product, emplacement=detail.emplacement, n_lot=detail.n_lot).first()
                        if not ds:
                            raise ValueError(f"{detail.n_lot} - Stock introuvable dans {detail.emplacement.designation} pour le produit {ml.product}.")
                        ds.qte -= detail.qte
                        ds.palette = max(ds.palette - detail.palette, 0)
                        if ds.qte <= 0:
                            ds.delete()
                        else:
                            ds.save()
        return True, 'Stock ajusté avec succès.'


    def do_after_validation(self, user):
        success, msg = self.integrate_in_stock()
        if not success:
            raise ValueError(msg)
        
        if self.is_transfer and not self.is_isolation and self.type == 'Sortie':
            self.create_mirror()
            return True, 'Stock ajusté et Transfer miroire créé avec succès.'
        
        elif self.is_transfer and self.is_isolation and self.type == 'Sortie':
            self.create_isolation()
            return True, 'Stock ajusté créé avec succès.'
        
        elif self.type == 'Entré':
            for ml in self.move_lines.all():
                for detail in ml.details.all():
                    if not detail.generateCode():
                        raise ValueError(f"{ml.n_lot} - Échec de la génération du code QR pour l'emplacement {detail.emplacement}.")
        
        if self.type == 'Sortie':
            return True, 'Stock ajusté avec succès.'
        return True, 'Stock ajusté et codes QR générés avec succès.'
    
    def create_mirror(self):
        if self.type == 'Sortie' and self.state == 'Validé' and self.is_transfer and not self.is_isolation:
            try:
                mirror = Move.objects.create(site=self.transfer_to, gestionaire=self.gestionaire, shift=self.shift, date=self.date, type='Entré', 
                                             is_transfer=self.is_transfer, is_isolation=self.is_isolation, state='Brouillon', mirror=self)
                self.mirror = mirror
                self.save()
                for ml in self.move_lines.all():
                    for d in ml.details.all():
                        move_mirror = MoveLine.objects.create(lot_number=d.n_lot, product=ml.product, expiry_date=d.expiry_date, mirror=d, 
                                                              move=mirror, transfered_qte=d.qte, create_uid=ml.create_uid, write_uid=ml.create_uid)
                        ml.mirror = d
                        ml.save()
                TemporaryEmplacementAlert.objects.get_or_create(mirror=mirror, write_uid=mirror.create_uid, create_uid=mirror.create_uid, type='Transfer')
                for bl in self.bls.all():
                    MoveBL.objects.create(move=mirror, numero=bl.numero)
            except Exception as e:
                raise RuntimeError(f"Erreur lors de la création du miroir: {e}")
    
    def create_isolation(self):
        if self.type == 'Sortie' and self.state == 'Validé' and self.is_transfer and self.is_isolation:
            try:
                emp = self.site.get_quarantine()
                mirror = Move.objects.create(site=self.site, gestionaire=self.gestionaire, shift=self.shift, date=self.date, type='Entré', 
                                             is_isolation=self.is_isolation, is_transfer=self.is_isolation, state='Brouillon', mirror=self)
                self.mirror = mirror
                self.save()
                for ml in self.move_lines.all():
                    for d in ml.details.all():
                        move_mirror = MoveLine.objects.create(lot_number=d.n_lot, product=ml.product, move=mirror, expiry_date=d.expiry_date, 
                                                          create_uid=ml.create_uid, write_uid=ml.write_uid, mirror=d)
                        LineDetail.objects.create(move_line=move_mirror, warehouse=emp.warehouse, emplacement=emp, 
                                                  qte=d.qte, palette=d.palette, expiry_date=d.expiry_date, code=d.code, n_lot=d.n_lot)
                for bl in self.bls.all():
                    MoveBL.objects.create(move=mirror, numero=bl.numero)
                
            except Exception as e:
                raise RuntimeError(f"Erreur lors de la création de l'isolation: {e}")
            
    def cancel_transfer(self):
        try:
            if self.is_transfer and not self.is_isolation and self.state == 'Annulé' and self.mirror and self.type == 'Entré':
                for ml in self.move_lines.all():
                    pal = ml.product.qte_per_pal
                    if pal == 0:
                        pal = 99999999
                    ds = Disponibility.objects.filter(product=ml.product, emplacement=ml.mirror.emplacement, n_lot=ml.mirror.n_lot).first()
                    if not ds:
                        Disponibility(product=ml.product, emplacement=ml.mirror.emplacement, qte=ml.mirror.qte, palette=ml.mirror.palette, 
                                n_lot=ml.mirror.n_lot, production_date=ml.move.date, expiry_date=ml.mirror.expiry_date).save()
                    else:
                        ds.qte += ml.mirror.qte
                        ds.nqte -= ml.mirror.qte
                        ds.palette = max(math.ceil(ds.qte / pal), 1)
                        ds.save()
                self.mirror.save()
                return True, 'Transfer annulé avec succès.'
        except Exception as e:
            raise RuntimeError(f'Erreur lors de l\'annulation du transfer: {e}')

    def check_can_confirm(self):
        if not self.move_lines.all():
            raise ValueError('Aucune ligne de mouvement.')
        for ml in self.move_lines.all():
            if not ml.details.all():
                raise ValueError(f'Aucun détail de ligne de mouvement - N LOT {ml.n_lot}.')
        return True
    
    @property
    def display_type(self):
        if self.is_isolation and self.is_transfer:
            return 'Isolation Entrant' if self.type == 'Entré' else 'Isolation Sortant'
        elif self.is_transfer:
            return 'Transfer Entrant' if self.type == 'Entré' else 'Transfer Sortant'
        elif self.is_isolation and self.type == 'Sortie':
            return 'Consomation'
        elif self.is_inventory and self.type == 'Sortie':
            return 'Inverntaire Sortant'
        elif self.is_inventory and self.type == 'Entré':
            return 'Inverntaire Entrant'
        else:
            return self.type

    @property
    def product_display(self):
        first_move_line = self.move_lines.first()
        if not first_move_line:
            return '/'
        if len(self.move_lines.all()) > 1:
            return f"{first_move_line.product}, ..."
        return f'{first_move_line.product.designation}'
    
    def is_in_mp(self):
        return all([ml.product.type == 'Matière Première' for ml in self.move_lines.all()]) and not self.is_transfer and self.type == 'Entré'
    
    @property
    def n_lots(self):
        if self.is_transfer or self.type == 'Sortie':
            return '/'
        return ', '.join([ml.n_lot for ml in self.move_lines.all()])

    def __str__(self):
        if not self.line:  
            return f"[{self.id}] {self.site} - {self.date}"
        return f"[{self.id}] {self.line.designation} - {self.date}"
    
class MoveLine(BaseModel):
    lot_number = models.CharField(max_length=255)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='move_lines')
    move = models.ForeignKey(Move, on_delete=models.CASCADE, related_name='move_lines')
    mirror = models.ForeignKey('LineDetail', on_delete=models.SET_NULL, related_name='transferred_line', null=True, blank=True)
    observation = models.TextField(blank=True, null=True)
    transfered_qte = models.FloatField(default=0, null=True, blank=True)
    diff_qte = models.FloatField(default=0, null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    @property
    def qte(self):
        return self.details.aggregate(total=models.Sum('qte'))['total'] or 0.0

    @property
    def package(self):
        return sum(detail.package for detail in self.details.all()) or 0

    @property
    def palette(self):
        return sum(detail.palette for detail in self.details.all()) or 0

    @property
    def is_out(self):
        return self.move.type == 'Sortie'

    @property
    def n_lot(self):
        if self.move.is_transfer:
            return self.lot_number
        if self.move.is_isolation:
            return self.lot_number
        if self.move.type == 'Entré':
            if self.product.type == 'Produit Fini':
                return f'{self.move.line.prefix_nlot}-{self.lot_number.zfill(4)}/{str(self.move.date.year)[-2:]}' or '/'
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
    qte = models.FloatField()
    palette = models.PositiveIntegerField(default=0)
    expiry_date = models.DateField(null=True, blank=True)
    code = models.CharField(max_length=255, null=True, blank=True)
    n_lot = models.CharField(max_length=255, null=True, blank=True)

    @property
    def has_unprinted_codes(self):
        return self.detail_codes.filter(is_printed=False).exists()

    @property
    def package(self):
        if self.move_line.product.qte_per_cond and self.qte:
            return math.ceil(self.qte / self.move_line.product.qte_per_cond)
        return 0
        
    def generateCode(self):
        try:
            self.expiry_date = self.move_line.expiry_date
            self.save()
            
            dispo = Disponibility.objects.filter(
                product=self.move_line.product,
                emplacement=self.emplacement,
                n_lot=self.n_lot
            ).first()

            if not dispo:
                raise ValueError("Matching stock Disponibility not found.")

            max_dl = dispo.lines.aggregate(models.Max('sequence'))['sequence__max'] or 0
            next_seq = max_dl + 1

            if self.move_line.mirror and self.move_line.mirror.detail_codes.count() == (self.palette if self.palette > 0 else 1):
                first_code = None
                idx = 0
                for original_dc in self.move_line.mirror.detail_codes.all():
                    seq_num = next_seq + idx
                    unique_code = f"Product:{self.move_line.product.id};Emplacement:{self.emplacement.id};NLOT:{self.n_lot};PAL:{seq_num}"
                    if idx == 0:
                        first_code = unique_code

                    DetailCode.objects.create(line_detail=self, code=unique_code, qte=original_dc.qte, palette=1)
                    DisponibilityLine.objects.create(disponibility=dispo, code=unique_code, qte=original_dc.qte, 
                                                     palette=1, sequence=seq_num, shift=self.move_line.move.shift)
                    idx += 1
                self.code = first_code

            elif self.move_line.product.type == 'Matière Première':
                unique_code = f"Product:{self.move_line.product.id};Emplacement:{self.emplacement.id};NLOT:{self.n_lot};PAL:{next_seq}"
                DetailCode.objects.create(
                    line_detail=self,
                    code=unique_code,
                    qte=self.qte,
                    palette=self.palette if self.palette > 0 else 1
                )
                DisponibilityLine.objects.create(
                    disponibility=dispo,
                    code=unique_code,
                    qte=self.qte,
                    palette=self.palette if self.palette > 0 else 1,
                    sequence=next_seq,
                    shift=self.move_line.move.shift
                )
                self.code = unique_code
            else:
                num_palettes = self.palette if self.palette > 0 else 1
                qte_per_pal = self.move_line.product.qte_per_pal
                if not qte_per_pal or qte_per_pal <= 0:
                    qte_per_pal = self.qte / num_palettes

                distributed_qte = 0.0
                first_code = None

                for idx in range(num_palettes):
                    seq_num = next_seq + idx
                    unique_code = f"Product:{self.move_line.product.id};Emplacement:{self.emplacement.id};NLOT:{self.n_lot};PAL:{seq_num}"
                    if idx == 0:
                        first_code = unique_code
                    
                    if idx == num_palettes - 1:
                        palette_qte = max(self.qte - distributed_qte, 0.0)
                    else:
                        palette_qte = min(qte_per_pal, max(self.qte - distributed_qte, 0.0))

                    distributed_qte += palette_qte

                    DetailCode.objects.create(
                        line_detail=self,
                        code=unique_code,
                        qte=palette_qte,
                        palette=1
                    )
                    DisponibilityLine.objects.create(
                        disponibility=dispo,
                        code=unique_code,
                        qte=palette_qte,
                        palette=1,
                        sequence=seq_num,
                        shift=self.move_line.move.shift
                    )
                self.code = first_code

            self.save()
            return True
        except Exception as e:
            print(f'Error lors de génération de code : {e}')
            return False

    class Meta:
        constraints = [models.CheckConstraint(check=models.Q(qte__gte=0), name="qte_positive")]

    def __str__(self):
        return f"{self.move_line.product} - {self.qte}"

class DetailCode(BaseModel):
    line_detail = models.ForeignKey(LineDetail, on_delete=models.CASCADE, related_name='detail_codes')
    code = models.CharField(max_length=255)
    qte = models.FloatField()
    palette = models.PositiveIntegerField(default=1)
    is_printed = models.BooleanField(default=False)
    is_scanned = models.BooleanField(default=False)


    @property
    def package(self):
        import math
        if self.line_detail.move_line.product.qte_per_cond and self.qte:
            return math.ceil(self.qte / self.line_detail.move_line.product.qte_per_cond)
        return 0

    @property
    def sequence(self):
        try:
            parts = self.code.split(';')
            for part in parts:
                if part.startswith('PAL:'):
                    return part.split(':')[1]
        except Exception:
            pass
        return '/'

    @property
    def location_info(self):
        try:
            parts = self.code.split(';')
            emp_id = None
            pal_seq = '/'
            for part in parts:
                if part.startswith('Emplacement:'):
                    emp_id = int(part.split(':')[1])
                elif part.startswith('PAL:'):
                    pal_seq = part.split(':')[1]
            
            if emp_id:
                from account.models import Emplacement
                emp = Emplacement.objects.filter(id=emp_id).first()
                if emp:
                    site_name = emp.warehouse.site.designation
                    wh_name = emp.warehouse.designation
                    zone_name = emp.designation
                    return f"{site_name} - {wh_name} - {zone_name} - N°{pal_seq} / {self.qte} Kg"
        except Exception:
            pass
        return f"{self.code} / {self.qte} Kg"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.qte}"

class DisponibilityLine(BaseModel):
    disponibility = models.ForeignKey('Disponibility', on_delete=models.CASCADE, related_name='lines')
    code = models.CharField(max_length=255, unique=True)
    qte = models.FloatField()
    nqte = models.FloatField(default=0)
    palette = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=30,
        default='Valide',
        choices=[
            ('Valide', 'Valide'),
            ('Sortie', 'Sortie'),
            ('Partialement Sortie', 'Partialement Sortie'),
            ('Détruit', 'Détruit')
        ]
    )
    sequence = models.IntegerField(default=1)
    is_printed = models.BooleanField(default=False)
    shift = models.ForeignKey('account.Shift', on_delete=models.SET_NULL, null=True, blank=True, related_name='dispo_lines')

    @property
    def package(self):
        import math
        if self.disponibility.product.qte_per_cond and self.qte:
            return math.ceil(self.qte / self.disponibility.product.qte_per_cond)
        return 0

    def replace_damaged(self):
        if self.status != 'Valide':
            raise ValueError("Seules les palettes actives peuvent être remplacées.")
        
        import uuid
        from django.db.models import Sum
        base_code = self.code
        if ";REP:" in base_code:
            base_code = base_code.split(";REP:")[0]
        
        new_code = f"{base_code};REP:{uuid.uuid4().hex[:6]}"
        while DisponibilityLine.objects.filter(code=new_code).exists():
            new_code = f"{base_code};REP:{uuid.uuid4().hex[:6]}"
        
        reserved_qte = DetailCode.objects.filter(
            code=self.code,
            line_detail__move_line__move__state__in=['Brouillon', 'Confirmé']
        ).aggregate(total=Sum('qte'))['total'] or 0.0
        
        if reserved_qte > 0:
            if reserved_qte >= self.qte:
                old_qte = self.qte
                self.status = 'Détruit'
                self.qte = 0.0
                self.save()
                
                DetailCode.objects.filter(code=self.code).update(code=new_code)
                
                new_line = DisponibilityLine.objects.create(
                    disponibility=self.disponibility,
                    code=new_code,
                    qte=old_qte,
                    nqte=self.nqte,
                    palette=self.palette,
                    sequence=self.sequence,
                    status='Valide',
                    shift=self.shift
                )
                return new_line
            else:
                # Partially reserved
                # The reserved part remains with the old code (so the draft move out can deduct it on validation),
                # and the left (remaining) part is replaced with the new code and becomes 'Valide' in stock.
                left_qte = self.qte - reserved_qte
                
                # Keep the reserved part with the old code as 'Valide'
                self.status = 'Valide'
                self.qte = reserved_qte
                self.save()
                
                # Create a new line for the left (remaining) quantity in stock with the new code
                new_line = DisponibilityLine.objects.create(
                    disponibility=self.disponibility,
                    code=new_code,
                    qte=left_qte,
                    nqte=self.nqte,
                    palette=self.palette,
                    sequence=self.sequence,
                    status='Valide',
                    shift=self.shift
                )
                return new_line
        else:
            # Not reserved (Valide)
            old_qte = self.qte
            self.status = 'Détruit'
            self.qte = 0.0
            self.save()
            
            new_line = DisponibilityLine.objects.create(
                disponibility=self.disponibility,
                code=new_code,
                qte=old_qte,
                nqte=self.nqte,
                palette=self.palette,
                sequence=self.sequence,
                status='Valide',
                shift=self.shift
            )
            return new_line

    def __str__(self):
        return f"{self.code} - {self.qte}"

class MoveBL(BaseModel):
    move = models.ForeignKey(Move, on_delete=models.CASCADE, related_name='bls')
    is_annexe = models.BooleanField(default=False)
    numero = models.PositiveIntegerField()

    @property
    def num(self):
        if self.move.is_transfer:
            return f'{self.move.site.prefix_btr}{str(self.numero).zfill(4)}/{str(self.move.date.year)[-2:]}'
        elif self.is_annexe:
            return f'{self.move.site.prefix_bl_a}{str(self.numero).zfill(4)}/{str(self.move.date.year)[-2:]}'
        else:
            return f'{self.move.site.prefix_bl}{str(self.numero).zfill(4)}/{str(self.move.date.year)[-2:]}'
    
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
    qte = models.FloatField()
    nqte = models.FloatField(default=0)
    palette = models.PositiveIntegerField(default=0)
    production_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    @property
    def sorted_lines(self):
        from django.db.models import Case, When, Value, IntegerField
        return self.lines.all().annotate(
            status_order=Case(
                When(status='Valide', then=Value(1)),
                When(status='Partialement Sortie', then=Value(2)),
                When(status='Sortie', then=Value(3)),
                When(status='Détruit', then=Value(4)),
                default=Value(5),
                output_field=IntegerField(),
            )
        ).order_by('status_order', 'sequence', 'id')

class TemporaryEmplacementAlert(BaseModel):

    ALERT_TYPE = [('Temporaire', 'Temporaire'), ('Transfer', 'Transfer')]

    dispo = models.ForeignKey(Disponibility, on_delete=models.SET_NULL, null=True, blank=True, related_name='alert_dispo')
    mirror = models.ForeignKey(Move, on_delete=models.SET_NULL, null=True, blank=True, related_name='alert_mirror')
    start_time = models.DateTimeField(auto_now_add=True)
    email_sent = models.BooleanField(default=False)
    type = models.CharField(choices=ALERT_TYPE, max_length=25, default='Temporaire')

class ExpiryAlertLog(models.Model):
    dispo = models.ForeignKey(Disponibility, related_name='alerts', on_delete=models.CASCADE)
    sent_at = models.DateField(auto_now_add=True)
