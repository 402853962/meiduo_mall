from django.shortcuts import render

# Create your views here.
from django.views import View
from django.http import JsonResponse
from apps.goods.models import SKU
from utils.views import LoginRequiredJsonMixin
from apps.users.models import Address
from django_redis import get_redis_connection
class SettlementView(LoginRequiredJsonMixin,View):
    def get(self,request):
        user=request.user
        addresses=Address.objects.filter(user=user,is_deleted=False)

        address_list=[]
        for address in addresses:
            address_list.append({
                'id': address.id,
                'province': address.province.name,
                'city': address.city.name,
                'district': address.district.name,
                'place': address.place,
                'receiver': address.receiver,
                'mobile': address.mobile
            })

        redis_cli=get_redis_connection('carts')
        sku_id_counts=redis_cli.hgetall('carts_%s'%user.id)
        selected_ids=redis_cli.smembers('selected_%s'%user.id)
        redis_carts={}
        # for sku_id,count in sku_id_counts.items():
        #     redis_carts[int(sku_id)]=int(count)

        skus=[]
        for sku_id in selected_ids:
            sku=SKU.objects.get(id=sku_id)
            skus.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'count': int(sku_id_counts[sku_id]),
                'price': sku.price
            })

        context = {
            'addresses':address_list,
            'skus':skus,
            'freight':10
        }

        return JsonResponse({'code':0,'errmsg':'ok','context':context})

