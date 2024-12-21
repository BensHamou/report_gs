from django.urls import path
from .api import *

urlpatterns = [
    path('api/login/', login_api, name='login_api'),
    path('api/moves/', move_list_api, name='move_list_api'),
    path('api/sync-data/', SyncDataView.as_view(), name='sync-data'),
    path('api/product-availibility/', ProductAvalibilityView.as_view(), name='get_product_availibility'),
    path('api/create-move-out/', CreateMoveOut.as_view(), name='create_move_out'),
    path('api/confirm-move-out/', ConfirmMoveOut.as_view(), name='confirm_move_out'),
    path('api/cancel-move-out/', CancelMoveOut.as_view(), name='cancel_move_out'),
    path('api/validate-move-out/', ValidateMoveOut.as_view(), name='validate_move_out')
]
