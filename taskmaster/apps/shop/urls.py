from django.urls import path
from .views import ShopView, buy_item, apply_item

app_name = 'shop'

urlpatterns = [
    path('', ShopView.as_view(), name='shop'),
    path('buy/<int:item_id>/', buy_item, name='buy'),
    path('apply/<int:item_id>/', apply_item, name='apply'),
]
