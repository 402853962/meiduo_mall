from django.urls import path
from apps.oauth.views import QQLoginURLView,QQUserView

urlpatterns = [
    path('qq/authorization/',QQLoginURLView.as_view()),
    path('oauth_callback/', QQUserView.as_view()),
]