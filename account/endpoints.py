from django.urls import path
from .api import *

urlpatterns = [
    path('api/login/', login_api, name='login_api'),
    path('api/moves/', move_list_api, name='move_list_api'),
    path('api/sync-data/', SyncDataView.as_view(), name='sync-data'),
    path('api/product-availibility/', ProductAvalibilityView.as_view(), name='get_product_availibility'),
]
