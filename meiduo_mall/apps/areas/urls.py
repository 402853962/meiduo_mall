from django.urls import path
from apps.areas.views import AreaView,SubsAreaView
urlpatterns =[
    path('areas/',AreaView.as_view()),
    path('areas/<int:parent_id>/', SubsAreaView.as_view()),
]