from django.urls import path
from apps.carts.views import CartView,CartShowAll
urlpatterns = [
    path('carts/',CartView.as_view()),
    path('carts/selection/',CartShowAll.as_view()),
]