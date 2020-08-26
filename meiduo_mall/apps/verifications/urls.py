from django.urls import path
from apps.verifications.views import SmsCodeView,ImageCodeView
urlpatterns = [
    path('image_codes/<key:key>/',ImageCodeView.as_view()),
    path('sms_codes/<mobile:mobile>/',SmsCodeView.as_view()),
]