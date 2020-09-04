from django.urls import path
from apps.orders.views import SettlementView,CommentView
urlpatterns = [
    path('orders/settlement/',SettlementView.as_view()),
    path('orders/commit/',CommentView.as_view()),
]