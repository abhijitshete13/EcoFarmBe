"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import (url,include,)
from django.contrib import admin
from django.conf import settings
from django.urls import path
from django.views.static import serve
from knox.views import LogoutView
from rest_framework.routers import SimpleRouter

from user.views import (UserViewSet, MeView, LogInView,
                        ChangePasswordView, SendMailView,
                        ResetPasswordView, CategoryView,
                        SearchQueryView,VerificationView,)
from vendor.views import (VendorViewSet,VendorProfileViewSet,LicenseViewSet)
from integration.views import (GetBoxTokensView, InventoryView,
                               SearchCultivars,)


router = SimpleRouter()
router.register(r'user', UserViewSet, base_name="user")
router.register(r'vendor', VendorViewSet, base_name="vendor")
router.register(r'vendor-profile', VendorProfileViewSet, base_name="vendor-profile")
router.register(r'license', LicenseViewSet, base_name="license")

urlpatterns = [
    path('admin/', admin.site.urls),
    path(r'user/me/', MeView.as_view(), name='user-me'),
    path(r'user/login/', LogInView.as_view(), name='login'),
    path(r'user/logout/', LogoutView.as_view(), name='logout'),
    path(r'user/change-password/',
         ChangePasswordView.as_view(), name='change-password'),
    path(r'user/forgot-password/', SendMailView.as_view(), name='forgot-password'),
    path(r'user/reset-password/', ResetPasswordView.as_view(), name='reset'),
    path(r'user/verify/', VerificationView.as_view(), name='verify-user'),
    path(r'category/', CategoryView.as_view(), name='category'),
    path(r'search/', SearchQueryView.as_view(), name='search'),
    path(r'integration/box/', GetBoxTokensView.as_view(), name='box'),
    path(r'inventory/item', InventoryView.as_view(), name='inventory'),
    path(r'crm/search/cultivar', SearchCultivars.as_view(), name='search_cultivar'),
] + router.urls


if not settings.DEBUG:
    urlpatterns += [
        url(r'^static\/(?P<path>.*)$', serve,
            {'document_root': settings.STATIC_ROOT})
    ]
