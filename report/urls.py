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
    path('raw-product/all/', listMProductView, name='mproducts'),
    path('raw-product/edit/<int:id>/', editMProductView, name='edit_mproduct'),
    path('raw-product/sync/', syncMProducts, name='sync_mproducts'),

    path('categories/', categories_view, name='select_c'),  
    path('families/', families_view, name='select_f'),  
    path('products/<int:family_id>/', products_view, name='select_p'),
    path('get_shifts_and_users_for_line/', get_shifts_and_users_for_line, name='get_shifts_and_users_for_line'),
    path('get_warehouses_for_line/', get_warehouses_for_line, name='get_warehouses_for_line'),
    path('get_emplacements_for_warehouse/', get_emplacements_for_warehouse, name='get_emplacements_for_warehouse'),

    path('move-line/all/', list_move, name='move_lines'),
    path('', list_move, name='move_lines'),

    path('move-in/product/create/<int:product_id>/', create_move_in_view, name='move_in_pf'),
    path('move-in/product/edit/<int:move_line_id>/', edit_move_in_view, name='edit_move_line_pf'),
    path('move-line/product/create/', create_move_pf, name='create_move_pf'),
    path('move-line/product/update/<int:move_line_id>/', update_move_pf, name='update_move_pf'),

    path('move-in/primary-product/create/', create_move_in_mp_view, name='move_in_mp'),
    path('move-in/primary-product/edit/<int:move_line_id>/', edit_move_in_mp_view, name='edit_move_line_mp'),
    path('move-line/primary-product/create/', create_move_mp, name='create_move_mp'),
    path('move-line/primary-product/update/<int:move_line_id>/', update_move_mp, name='update_move_mp'),

    path('move-line/delete/<int:move_line_id>/', delete_move, name='delete_move'),
    path('move-line/detail/<int:move_line_id>/', move_line_detail, name='move_line_detail'),

    path('move-line/confirm/<int:move_line_id>/', confirmMoveIn, name='confirm_move_line'),
    path('move-line/cancel/<int:move_line_id>/', cancelMoveLine, name='cancel_move_line'),
    path('move-line/validate/<int:move_line_id>/', validateMoveLine, name='validate_move_line'),
    
    path('generate-qr-code/<int:detail_id>/', generateQRCode, name='generate_qr_code'),

]

