from django.urls import path
from apps.users.views import UsernameCountView,MobileCountView,RegisterView,LoginView,LogoutView,UserCenterView,EmailView,EmailVerificationView,AddressCreateView,AddressesView,VerifyAddressView,DefaultSetView,TitleSetView,UserHistoryView
urlpatterns = [
    path('usernames/<username:username>/count/',UsernameCountView.as_view()),
    path('mobiles/<mobile:mobile>/count/',MobileCountView.as_view()),
    path('register/',RegisterView.as_view()),
    path('login/',LoginView.as_view()),
    path('logout/',LogoutView.as_view()),
    path('info/',UserCenterView.as_view()),
    path('emails/',EmailView.as_view()),
    path('emails/verification/',EmailVerificationView.as_view()),
    path('addresses/create/',AddressCreateView.as_view()),
    path('addresses/', AddressesView.as_view()),
    path('addresses/<int:address_id>/',VerifyAddressView.as_view()),
    path('addresses/<int:address_id>/default/',DefaultSetView.as_view()),
    path('addresses/<int:address_id>/title/',TitleSetView.as_view()),
    path('browse_histories/',UserHistoryView.as_view()),
]