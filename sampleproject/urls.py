from django.contrib import admin
from django import VERSION

if VERSION[0] >= 2:
    from django.urls import path, include
    urlpatterns = [
        path('admin/', admin.site.urls),
    ]
else:
    from django.conf.urls import include, url
    urlpatterns = [
        url(r'^admin/', include(admin.site.urls)),
    ]
