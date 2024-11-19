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

    path('families/', families_view, name='families_view'),  
    path('products/<int:family_id>/', products_view, name='products_view'),  
    path('move-in/form/<int:product_id>/', move_in_form_view, name='move_in_form'),
    path('get_shifts_and_users_for_line/', get_shifts_and_users_for_line, name='get_shifts_and_users_for_line'),
    path('get_warehouses_for_line/', get_warehouses_for_line, name='get_warehouses_for_line'),
    path('get_zones_for_warehouse/', get_zones_for_warehouse, name='get_zones_for_warehouse'),

    path('move-lines/', move_list, name='move_lines'),
    path('move-line/edit/<int:move_line_id>/', move_edit, name='edit_move_line'),
    path('move-line/delete/<int:move_line_id>/', move_delete, name='delete_move_line'),
]

