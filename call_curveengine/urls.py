from django.urls import path
from .views import api_health, api_bootstrap, api_discount, api_forward_rates

urlpatterns = [
    path('health', api_health.as_view(), name='health'),
    path('bootstrap', api_bootstrap.as_view(), name='bootstrapping'),
    path('discount', api_discount.as_view(), name='discount'),
    path('forwardRates', api_forward_rates.as_view(), name='discount')
]
