from django.urls import path
from apps.orders.views import SettlementView
urlpatterns = [
    path('orders/settlement/',SettlementView.as_view()),
]