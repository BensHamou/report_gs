from django.urls import path
from .views import *


urlpatterns = [
    path('family/all/', listFamilyView, name='families'),
    path('family/create/', createFamilyView, name='create_family'),
    path('family/edit/<int:id>/', editFamilyView, name='edit_family'),
    path('family/delete/<int:id>/', deleteFamilyView, name='delete_family'),

    path('unit/all/', listUnitView, name='units'),
    path('unit/create/', createUnitView, name='create_unit'),
    path('unit/edit/<int:id>/', editUnitView, name='edit_unit'),
    path('unit/delete/<int:id>/', deleteUnitView, name='delete_unit'),

    path('product/all/', listProductView, name='products'),
    path('product/create/', createProductView, name='create_product'),
    path('product/edit/<int:id>/', editProductView, name='edit_product'),
    path('product/delete/<int:id>/', deleteProductView, name='delete_product'),
]

