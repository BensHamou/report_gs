from django.urls import path
from .api import *

urlpatterns = [
    path('api/login/', login_api, name='login_api'),
    path('api/moves/', move_list_api, name='move_list_api'),
    path('api/families/', FamilyListView.as_view(), name='family-list'),
    path('api/products/<int:family_id>/', ProductListView.as_view(), name='product-list'),
    path('api/move-out-details/', MoveOutDetailsView.as_view(), name='move-out-details'),
]
