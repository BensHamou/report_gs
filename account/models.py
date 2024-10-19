from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from datetime import timedelta


class BaseModel(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    create_uid = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="created_%(class)s", on_delete=models.SET_NULL, null=True, blank=True)
    write_uid = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="modified_%(class)s", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if not self.pk and user:
            self.create_uid = user
        self.write_uid = user
        super(BaseModel, self).save(*args, **kwargs)


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

    def __str__(self):
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"


class Site(BaseModel):
    designation = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    email = models.EmailField()

    def __str__(self):
        return self.designation


class Warehouse(BaseModel):
    designation = models.CharField(max_length=255)
    site = models.ForeignKey(Site, related_name='warehouses', on_delete=models.CASCADE)

    def __str__(self):
        return self.designation


class Zone(BaseModel):
    designation = models.CharField(max_length=255)
    quarantine = models.BooleanField(default=False)
    temp = models.BooleanField(default=False)
    warehouse = models.ForeignKey(Warehouse, related_name='zones', on_delete=models.CASCADE)

    def __str__(self):
        return self.designation


class Line(BaseModel):
    designation = models.CharField(max_length=255)
    prefix_bl = models.CharField(max_length=50)
    prefix_bl_a = models.CharField(max_length=50)
    prefix_nlot = models.CharField(max_length=50)
    shifts = models.ManyToManyField(Shift, related_name='lines', blank=True)

    def __str__(self):
        return self.designation


class Setting(BaseModel):
    name = models.CharField(max_length=50)
    value = models.CharField(max_length=250)

    def __str__(self):
        return f"{self.name} : {self.value}"


class User(BaseModel, AbstractUser):
    ROLE_CHOICES = [
        ('Nouveau', 'Nouveau'),
        ('Gestionaire', 'Gestionaire'),
        ('Observateur', 'Observateur'),
        ('Admin', 'Admin')
    ]

    fullname = models.CharField(max_length=255)
    role = models.CharField(choices=ROLE_CHOICES, max_length=30)
    lines = models.ManyToManyField(Line, related_name='users', blank=True)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.fullname

    class Meta(AbstractUser.Meta):
        swappable = 'AUTH_USER_MODEL'
