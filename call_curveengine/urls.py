from django.urls import path
from .views import api_health, api_bootstrap

urlpatterns = [
    path('health/', api_health.as_view(), name='health'),
    path('bootstrap/', api_bootstrap.as_view(), name='bootstrapping')
]
