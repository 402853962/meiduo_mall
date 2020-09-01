from django.urls import path
from apps.goods.views import IndexView,ListView,HotView,DetailView,GoodsVisitView,MySearchView
urlpatterns = [
    path('index/',IndexView.as_view()),
    path('list/<int:category_id>/skus/',ListView.as_view()),
    path('hot/<int:category_id>/', HotView.as_view()),
    path('detail/<int:sku_id>/',DetailView.as_view()),
    path('detail/visit/<int:cat_id>/',GoodsVisitView.as_view()),
    path('search/',MySearchView),
]