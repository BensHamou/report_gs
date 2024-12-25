from .models import *
from django.utils.timezone import now, timedelta

def check_temp_emplacements():
    alerts = TemporaryEmplacementAlert.objects.all()
    for alert in alerts:
        
        alert.save()

    
