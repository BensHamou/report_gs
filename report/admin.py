from django.contrib import admin
from .models import *

admin.site.register(Product)
admin.site.register(Family)
admin.site.register(Packing)
admin.site.register(Move)
admin.site.register(MoveLine)
admin.site.register(LineDetail)
admin.site.register(TemporaryEmplacementAlert)
admin.site.register(Validation)
admin.site.register(Disponibility)
admin.site.register(MoveBL)