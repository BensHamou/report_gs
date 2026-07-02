from django.urls import path
from .api import *

urlpatterns = [
    path('api/login/', login_api, name='login_api'),
    path('api/draft-moves/', draft_move_list_api, name='draft_move_list_api'),

    path('api/send-email/', SendWarningEmail.as_view(), name='send_warning_email'),
    path('api/move-out/<int:move_id>/available-palettes/', get_available_palettes_api, name='get_available_palettes_api'),
    path('api/move-out/<int:move_id>/sync-scans/', sync_move_out_scans_api, name='sync_move_out_scans_api'),
]
