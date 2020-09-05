from django.urls import path
from apps.payment.views import PayURLView,PaymentStatusView
urlpatterns = [
    path('payment/<int:order_id>/',PayURLView.as_view()),
    path('payment/status/',PaymentStatusView.as_view()),
]