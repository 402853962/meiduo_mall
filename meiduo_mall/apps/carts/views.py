from django.shortcuts import render

# Create your views here.
from django.views import View
import json
from django.shortcuts import render
from django.http import JsonResponse,HttpResponse
from django_redis import get_redis_connection
import base64
import pickle

from apps.goods.models import SKU


class CartView(View):
    def post(self,request):
        data=json.loads(request.body.decode())
        sku_id=data.get('sku_id')
        count=data.get('count')

        try:
            sku=SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code':400,'errmsg':'没有商品'})

        try:
            count=int(count)
        except Exception:
            count=1

        user=request.user
        if user.is_authenticated:
            redis_cli = get_redis_connection('carts')
            redis_cli.hset('carts_%s'%user.id,sku_id,count)
            redis_cli.sadd('selected_%s'%user.id,sku_id)

            return JsonResponse({'code':0,'errmsg':'ok'})
        else:
            cookie_carts=request.COOKIES.get('carts')
            if cookie_carts is None:
                carts={}
            else:
                carts=pickle.loads(base64.b64decode(cookie_carts))

            if sku_id in carts:
                origin_count=carts[sku_id]['count']
                count += origin_count

            carts[sku_id] = {
                'count':count,
                'selected':True,
            }

            carts_bytes=pickle.dumps(carts)
            carts_base64=base64.b64encode(carts_bytes)
            response=JsonResponse({'code':0,'errmsg':'ok'})

            response.set_cookie(key='carts',value=carts_base64.decode(),max_age=14*24*3600)
            return response

    def get(self,request):
        user=request.user
        if user.is_authenticated:
            redis_cli=get_redis_connection('carts')
            selected_ids=redis_cli.smembers('selected_%s'%user.id)
            sku_id_counts=redis_cli.hgetall('carts_%s'%user.id)
            carts={}
            for sku_id,count in sku_id_counts.items():
                carts[sku_id]={
                    'count':count,
                    'selected':sku_id in selected_ids
                }

        else:
            cookie_carts=request.COOKIES.get('carts')
            if cookie_carts is not None:
                carts=pickle.loads(base64.b64decode(cookie_carts))
            else:
                carts={}

        ids=carts.keys()
        skus=SKU.objects.filter(id__in=ids)
        sku_list=[]
        for sku in skus:
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'count': carts.get(sku.id).get('count'),
                'selected': str(carts.get(sku.id).get('selected')),  # 将True，转'True'，方便json解析
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),  # 从Decimal('10.2')中取出'10.2'，方便json解析
                'amount': str(sku.price * carts.get(sku.id).get('count')),
            })

        return JsonResponse({'code':0,'errmsg':'ok','cart_skus':sku_list})
