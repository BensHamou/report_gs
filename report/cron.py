from .models import *
from django.utils.timezone import now, timedelta

def check_temp_zones():
    alerts = TemporaryZoneAlert.objects.all()
    for alert in alerts:
        print('TEST')
        alert.email_sent = True
        alert.save()

    
