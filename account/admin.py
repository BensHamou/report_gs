from django.contrib import admin
from .models import *

admin.site.register(User)
admin.site.register(Site)
admin.site.register(Line)
admin.site.register(Zone)
admin.site.register(Warehouse)
admin.site.register(Shift)