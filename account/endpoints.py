from django.urls import path
from .api import *

urlpatterns = [
    path('api/login/', login_api, name='login_api'),
    path('api/draft-moves/', draft_move_list_api, name='draft_move_list_api'),
    path('api/save-progress/', save_scan_progress_api, name='save_scan_progress_api'),
    path('api/send-email/', SendWarningEmail.as_view(), name='send_warning_email')
]
