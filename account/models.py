from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from datetime import timedelta
from django.template.defaultfilters import slugify
from PIL import Image as PILImage
import os


class BaseModel(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    create_uid = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="created_%(class)s", on_delete=models.SET_NULL, null=True, blank=True)
    write_uid = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="modified_%(class)s", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        abstract = True

class Shift(BaseModel):
    start_time = models.TimeField()
    end_time = models.TimeField()

    @property
    def passed_time(self):
        start_datetime = timedelta(hours=self.start_time.hour, minutes=self.start_time.minute)
        end_datetime = timedelta(hours=self.end_time.hour, minutes=self.end_time.minute)
        total_time = end_datetime - start_datetime

        if total_time.total_seconds() < 0:
            total_time += timedelta(hours=24)

        return round(total_time.total_seconds() / 3600, 2)
    
    @property
    def designation(self):
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"

    def __str__(self):
        return self.designation
    
def get_site_image_filename(instance, filename):
    title = instance.designation
    slug = slugify(title)
    return f"images/site/{slug}-{filename}"

class Site(BaseModel):
    designation = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    email = models.EmailField()
    prefix_bl = models.CharField(max_length=50)
    prefix_bl_a = models.CharField(max_length=50)
    prefix_btr = models.CharField(max_length=50)
    check_for_drafts = models.BooleanField(default=False)
    image = models.ImageField(upload_to=get_site_image_filename, verbose_name='Image', blank=True, null=True)

    def get_quarantine(self):
        return Emplacement.objects.filter(warehouse__site=self, quarantine=True).first()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image and os.path.exists(self.image.path):
            img = PILImage.open(self.image.path)
            max_size = (1280, 720)
            img.thumbnail(max_size, PILImage.LANCZOS)
            img.save(self.image.path, quality=50, optimize=True)

    def __str__(self):
        return self.designation

    
def get_warehouse_image_filename(instance, filename):
    title = instance.designation
    slug = slugify(title)
    return f"images/warehouse/{slug}-{filename}"

class Warehouse(BaseModel):
    designation = models.CharField(max_length=255)
    site = models.ForeignKey(Site, related_name='warehouses', on_delete=models.CASCADE)
    image = models.ImageField(upload_to=get_warehouse_image_filename, verbose_name='Image', blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image and os.path.exists(self.image.path):
            img = PILImage.open(self.image.path)
            max_size = (1280, 720)
            img.thumbnail(max_size, PILImage.LANCZOS)
            img.save(self.image.path, quality=50, optimize=True)

    def __str__(self):
        return f'{self.designation} - {self.site}'


class Emplacement(BaseModel):
    TYPE_CHOICES = [('Surface Libre', 'Surface Libre'), ('Rayon', 'Rayon')]

    designation = models.CharField(max_length=255)
    type = models.CharField(choices=TYPE_CHOICES, max_length=30, default='Surface Libre')
    capacity = models.PositiveIntegerField()
    quarantine = models.BooleanField(default=False)
    temp = models.BooleanField(default=False)
    warehouse = models.ForeignKey(Warehouse, related_name='emplacements', on_delete=models.CASCADE)

    @property
    def available_qte(self):
        return sum([d.qte for d in self.disponibilities.all()])

    # @property
    # def available_capacity(self):
    #     return self.capacity - self.available_qte

    # def can_stock(self, palette):
    #     return True
        # return self.available_palettes + palette <= self.capacity
    
    def can_destock(self, qte):
        return self.available_qte - qte >= 0

    def __str__(self):
        return f'{self.designation} - {self.warehouse}'


class Line(BaseModel):
    designation = models.CharField(max_length=255)
    prefix_nlot = models.CharField(max_length=50)
    site = models.ForeignKey(Site, related_name='lines', on_delete=models.CASCADE)
    shifts = models.ManyToManyField(Shift, related_name='lines', blank=True)

    def __str__(self):
        return f'{self.designation} - {self.site}'


class Setting(BaseModel):
    name = models.CharField(max_length=50)
    value = models.CharField(max_length=250)

    def __str__(self):
        return f"{self.name} : {self.value}"


class User(BaseModel, AbstractUser):
    ROLE_CHOICES = [
        ('Nouveau', 'Nouveau'),
        ('Gestionaire', 'Gestionaire'),
        ('Validateur', 'Validateur'),
        ('Observateur', 'Observateur'),
        ('Admin', 'Admin')
    ]

    fullname = models.CharField(max_length=255)
    role = models.CharField(choices=ROLE_CHOICES, max_length=30)
    default_site = models.ForeignKey(Site, related_name='users', on_delete=models.SET_NULL, null=True, blank=True)
    lines = models.ManyToManyField(Line, related_name='users', blank=True)
    is_admin = models.BooleanField(default=False)
    allow_policy = models.BooleanField(default=False)

    def __str__(self):
        return self.fullname

    class Meta(AbstractUser.Meta):
        swappable = 'AUTH_USER_MODEL'
