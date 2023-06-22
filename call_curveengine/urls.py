from django.urls import path
from .views import api_health, api_bootstrap, api_discount

urlpatterns = [
    path('health/', api_health.as_view(), name='health'),
    path('bootstrap/', api_bootstrap.as_view(), name='bootstrapping'),
    path('discount/', api_discount.as_view(), name='discount')
]
