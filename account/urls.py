from django.urls import path
from .views import *


urlpatterns = [

    path('login_success/', login_success, name='login_success'),

    path("home/", homeView, name="home"),

    path("user/new/", listNewUserView, name="new_users"),
    path("user/active/", listUserView, name="users"),
    path("user/refresh/", refreshUserList, name="refresh_users"),
    path("user/edit/<int:id>", editUserView, name="edit_user"),
    path("user/delete/<int:id>", deleteUserView, name="delete_user"),
    # path('user/profile/<int:id>', userProfileView, name='details'),
    
    path('login/', CustomLoginView.as_view(), name='login'),
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logoutView, name='logout'),

    path('site/all/', listSiteView, name='sites'),
    path("site/create/", createSiteView, name="create_site"),
    path("site/edit/<int:id>", editSiteView, name="edit_site"),
    path("site/delete/<int:id>", deleteSiteView, name="delete_site"),

    path("line/all/", listLineView, name='lines'),
    path("line/create/", createLineView, name="create_line"),
    path("line/edit/<int:id>", editLineView, name="edit_line"),
    path("line/delete/<int:id>", deleteLineView, name="delete_line"),

    path('warehouse/all/', listWarehouseView, name='warehouses'),
    path("warehouse/create/", createWarehouseView, name="create_warehouse"),
    path("warehouse/edit/<int:id>", editWarehouseView, name="edit_warehouse"),
    path("warehouse/delete/<int:id>", deleteWarehouseView, name="delete_warehouse"),

    path('zone/all/', listZoneView, name='zones'),
    path("zone/create/", createZoneView, name="create_zone"),
    path("zone/edit/<int:id>", editZoneView, name="edit_zone"),
    path("zone/delete/<int:id>", deleteZoneView, name="delete_zone"),


    path("shift/all/", listShiftView, name='shifts'),
    path("shift/create/", createShiftView, name="create_shift"),
    path("shift/edit/<int:id>", editShiftView, name="edit_shift"),
    path("shift/delete/<int:id>", deleteShiftView, name="delete_shift"),
]

