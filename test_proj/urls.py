from django.contrib import admin
from django.urls import path

from test_proj.blog.custom_admin import custom_admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('custom_admin/', custom_admin.urls),
]
