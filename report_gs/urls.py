from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("puma_stock/admin/", admin.site.urls),
    path("", include('account.urls')),
    path("", include('report.urls')),
    path("", include('account.endpoints')),
]

handler404 = 'account.views.page_not_found'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)