from . import views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import *

urlpatterns = [
    path('', index, name='index'),
    path('view/<str:device_name>', view, name='view')
]