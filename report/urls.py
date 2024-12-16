from django.urls import path
from .views import *


urlpatterns = [
    path('family/all/', listFamilyView, name='families'),
    path('family/create/', createFamilyView, name='create_family'),
    path('family/edit/<int:id>/', editFamilyView, name='edit_family'),
    path('family/delete/<int:id>/', deleteFamilyView, name='delete_family'),

    path('packing/all/', listPackingView, name='packings'),
    path('packing/create/', createPackingView, name='create_packing'),
    path('packing/edit/<int:id>/', editPackingView, name='edit_packing'),
    path('packing/delete/<int:id>/', deletePackingView, name='delete_packing'),

    path('product/all/', listProductView, name='products'),
    path('product/create/', createProductView, name='create_product'),
    path('product/edit/<int:id>/', editProductView, name='edit_product'),
    path('product/delete/<int:id>/', deleteProductView, name='delete_product'),

    path('categories/', categories_view, name='select_c'),  
    path('move-in/primary-product/', primary_products_view, name='move_in_mp'),
    path('families/', families_view, name='select_f'),  
    path('products/<int:family_id>/', products_view, name='select_p'),    
    path('move-in/form/<int:product_id>/', move_in_form_view, name='move_in_form'),
    path('get_shifts_and_users_for_line/', get_shifts_and_users_for_line, name='get_shifts_and_users_for_line'),
    path('get_warehouses_for_line/', get_warehouses_for_line, name='get_warehouses_for_line'),
    path('get_emplacements_for_warehouse/', get_emplacements_for_warehouse, name='get_emplacements_for_warehouse'),

    path('move-lines/', move_list, name='move_lines'),
    path('', move_list, name='move_lines'),
    path('transfer-lines/', tarnsfer_list, name='tarnsfer_list'),
    path('move-line/edit/<int:move_line_id>/', move_edit, name='edit_move_line'),
    path('move-line/delete/<int:move_line_id>/', move_delete, name='delete_move_line'),
    path('move-line/create/', create_move, name='create_move'),
    path('move-line/update/<int:move_line_id>/', update_move, name='update_move_line'),
    path('move-line/detail/<int:move_line_id>/', move_line_detail, name='move_line_detail'),

    path('move-line/confirm/<int:move_line_id>/', confirmMoveLine, name='confirm_move_line'),
    path('move-line/cancel/<int:move_line_id>/', cancelMoveLine, name='cancel_move_line'),
    
    path('generate-qr-code/<int:detail_id>/', generateQRCode, name='generate_qr_code'),

    path('transfer-move-line/', transfer_quantity, name='transfer_move_line'),
    path('get-detail-transfers/<int:detail_id>/', get_transfers, name='get_transfers'),


]

