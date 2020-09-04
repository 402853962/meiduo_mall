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
            # redis_cli.hset('carts_%s'%user.id,sku_id,count)
            redis_cli.hincrby('carts_%s'%user.id,sku_id,count)
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
                carts[int(sku_id)]={
                    'count':int(count),
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
                'selected': carts.get(sku.id).get('selected'),  # 将True，转'True'，方便json解析
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),  # 从Decimal('10.2')中取出'10.2'，方便json解析
                'amount': str(sku.price * carts.get(sku.id).get('count')),
            })

        return JsonResponse({'code':0,'errmsg':'ok','cart_skus':sku_list})

    def put(self,request):
        data=json.loads(request.body.decode())
        sku_id=data.get('sku_id')
        count=data.get('count')
        selected=data.get('selected')

        # 判断参数是否齐全
        if not all([sku_id, count]):
            return JsonResponse({'code':400,'errmsg':'缺少必传参数'})
        # 判断sku_id是否存在
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code':400,'errmsg':'商品sku_id不存在'})
        # 判断count是否为数字
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'code':400,'errmsg':'参数count有误'})

        user=request.user
        if user.is_authenticated:
            redis_cli=get_redis_connection('carts')
            redis_cli.hset('carts_%s'%user.id,sku_id,count)
            if selected:
                redis_cli.sadd('selected_%s'%user.id,sku_id)
            else:
                redis_cli.srem('selected_%s'%user.id,sku_id)

            cart_sku = {
                'id': sku_id,
                'count': count,
                'selected': selected,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'amount': sku.price * count,
            }

            return JsonResponse({'code':0,'errmsg':'ok','cart_sku':cart_sku})
        else:
            cookie_cart=request.COOKIES.get('carts')
            if cookie_cart is not None:
                carts=pickle.loads(base64.b64decode(cookie_cart))
            else:
                carts={}
            if sku_id in carts:
                carts[sku_id]={
                    'count':count,
                    'selected':selected
                }

            base64_carts = base64.b64encode(pickle.dumps(carts))


            response= JsonResponse({'code':0,'errmsg':'ok','count':count})
            response.set_cookie('carts',base64_carts.decode(),max_age=14*24*3600)
            return response

    def delete(self,request):
        data=json.loads(request.body.decode())
        sku_id=data.get('sku_id')
     # 判断sku_id是否存在
        try:
            sku=SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code':400,'errmsg':'商品不存在'})

        user=request.user
        if user.is_authenticated:
            redis_cli=get_redis_connection('carts')
            redis_cli.hdel('carts_%s'%user.id,sku_id)
            redis_cli.srem('selected_%s'%user.id,sku_id)

            return JsonResponse({'code':0,'errmsg':'ok'})
        else:
            carts_cookie=request.COOKIES.get('carts')
            if carts_cookie is not None:
                carts=pickle.loads(base64.b64decode(carts_cookie))
            else:
                carts={}

            if sku_id in carts:
                del carts[sku_id]

            base64_carts=base64.b64encode(pickle.dumps(carts))
            response=JsonResponse({'code':0,'errmsg':'ok'})

            response.set_cookie('carts',base64_carts.decode(),max_age=14*24*3600)
            return response

class CartShowAll(View):
    def put(self,request):
        data=json.loads(request.body.decode())
        selected=data.get('selected')

        user=request.user
        if user.is_authenticated:
            redis_cli=get_redis_connection('carts')
            hash_all=redis_cli.hgetall('carts_%s'%user.id)
            hash_keys=hash_all.keys()
            if selected:
                redis_cli.sadd('selected_%s'%user.id,*hash_keys)
            else:
                redis_cli.srem('selected_%s'%user.id,*hash_keys)

            return JsonResponse({'code':0,'errmsg':'ok',})
        else:
            cart=request.COOKIES.get('carts')
            if cart is not None:
                carts=pickle.loads(base64.b64decode(cart))
                for sku in carts:
                    carts[sku]['selected']=selected

                base64_carts=base64.b64encode(pickle.dumps(carts))
                response=JsonResponse({'code':0,'errmsg':'ok',})
                response.set_cookie('carts',base64_carts.decode(),max_age=14*24*3600)
                return response

class CartSimpleView(View):
    def get(self,request):
        user=request.user
        if user.is_authenticated:
            redis_cli=get_redis_connection('carts')
            sku_id_counts=redis_cli.hgetall('carts_%s'%user.id)
            sku_selected=redis_cli.smembers('selected_%s'%user.id)

            carts_dict={}
            for sku_id,count in sku_id_counts.items():
                carts_dict[int(sku_id)]={
                    'count':int(count),
                    'selected':sku_id in sku_selected
                }
        else:
            carts_cookies=request.COOKIES.get('carts')
            if carts_cookies is not None:
                carts_dict=pickle.loads(base64.b64decode(carts_cookies))
            else:
                carts_dict={}


        carts_sku=[]
        sku_ids= carts_dict.keys()
        skus=SKU.objects.filter(id__in=sku_ids)
        for sku in skus:
            carts_sku.append({
                'id': sku.id,
                'name': sku.name,
                'count': carts_dict.get(sku.id).get('count'),
                'default_image_url': sku.default_image.url
            })

        return JsonResponse({'code':0, 'errmsg':'OK', 'cart_skus':carts_sku})



