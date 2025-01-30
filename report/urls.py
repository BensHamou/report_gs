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
    path('get_warehouses_for_site/', get_warehouses_for_site, name='get_warehouses_for_site'),
    path('get_emplacements_for_warehouse/', get_emplacements_for_warehouse, name='get_emplacements_for_warehouse'),

    path('move-in/product/create/<int:product_id>/', create_move_in_view, name='move_in_pf'),
    path('move-in/product/edit/<int:move_line_id>/', edit_move_in_view, name='edit_move_line_pf'),
    path('move-line/product/create/', create_move_pf, name='create_move_pf'),
    path('move-line/product/update/<int:move_line_id>/', update_move_pf, name='update_move_pf'),

    path('move-in/primary-product/create/', create_move_in_mp_view, name='move_in_mp'),
    path('move-in/primary-product/edit/<int:move_line_id>/', edit_move_in_mp_view, name='edit_move_line_mp'),
    path('move-line/primary-product/create/', create_move_mp, name='create_move_mp'),
    path('move-line/primary-product/update/<int:move_line_id>/', update_move_mp, name='update_move_mp'),

    path('move/all/', list_move, name='moves'),
    path('', list_move, name='moves'),
    path('move/detail/<int:move_id>/', move_detail, name='move_detail'),
    path('move/delete/<int:move_id>/', delete_move, name='delete_move'),
    path('move/<int:move_id>/edit-bl/', EditMoveBLView.as_view(), name='edit_move_bl'),

    path('move/confirm/<int:move_id>/', confirmMove, name='confirm_move'),
    path('move/cancel/<int:move_id>/', cancelMove, name='cancel_move'),
    path('move/validate/<int:move_id>/', validateMove, name='validate_move'),
    
    path('generate-qr-code/<int:detail_id>/', generateQRCode, name='generate_qr_code'),

    path('stock/all/', listStockView, name='stocks'),
    path('stock/create/', createStockView, name='create_stock'),
    path('stock/edit/<int:id>/', editStockView, name='edit_stock'),
    path('stock/delete/<int:id>/', deleteStockView, name='delete_stock'),
    path('stock/extract/', extractStockView, name='extract_stock'),

]

