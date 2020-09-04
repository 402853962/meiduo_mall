from django.shortcuts import render

# Create your views here.
from django.views import View
from django.http import JsonResponse
from apps.goods.models import SKU
from apps.orders.models import OrderInfo, OrderGoods
from utils.views import LoginRequiredJsonMixin
from apps.users.models import Address
from django_redis import get_redis_connection
from django.utils import timezone
from decimal import Decimal

import json

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

class CommentView(LoginRequiredJsonMixin,View):
    def post(self,request):
        # 一。接收数据
        data=json.loads(request.body.decode())
        # 地址id
        address_id=data.get('address_id')
        # 支付方式
        pay_method=data.get('pay_method')
        # 二。验证数据
        if not all([address_id,pay_method]):
            return JsonResponse({'code':400,'errmsg':'参数不全'})
        try:
            address=Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return JsonResponse({'code':400,'errmsg':'地址错误'})

        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'],OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return JsonResponse({'code':400,'errmsg':'付款方式有误'})

        # 三。数据入库
        #     1.OrderInfo -- 订单基本信息
        #         1.1 获取用户信息
        user=request.user
        #         1.2 我们自己生成一个订单id（不用系统的自增）
        order_id=timezone.localtime().strftime('%Y%m%d%H%M%S')+('%09d'%user.id)
        #         1.3 价格数量运费新 -- 价格和总数量需要在新增订单商品的时候累加
        freight=Decimal('10')
        total_price=Decimal('0')
        total_count=Decimal('0')
        #         1.4 订单状态 -- 订单状态和支付方式有关系
        if pay_method==OrderInfo.PAY_METHODS_ENUM['CASH']:
            status=OrderInfo.ORDER_STATUS_ENUM['UNSEND']
        else:
            status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']

        order = OrderInfo.objects.create(
            order_id=order_id,
            user=user,
            address=address,
            total_count=total_count,
            total_amount=total_price,
            freight=freight,
            pay_method=pay_method,
            status=status
        )
        #     2.OrderGoods -- 订单商品信息
        #         2.1 连接redis
        redis_cli=get_redis_connection('carts')
        #         2.2 获取hash
        sku_id_counts=redis_cli.hgetall('carts_%s'%user.id)
        #         2.3 获取set数据 -- 选中的id
        sku_selected=redis_cli.smembers('selected_%s'%user.id)
        #         2.4 遍历选中的商品id
        selected_carts={}
        for sku_id in sku_selected:
            selected_carts[int(sku_id)]=int(sku_id_counts[sku_id])

        ids=selected_carts.keys()
        for id in ids:
        #         2.5 根据商品id查询商品信息
            sku = SKU.objects.get(id=id)
            custom_count = selected_carts[id]
        #         2.6 判断库存是否充足
            if custom_count>sku.stock:
                return JsonResponse({'code':400,'errmsg':'库存不足'})
        #         2.7 如果充足，减少库存，增加销量
            else:
                sku.stock -= custom_count
                sku.sales += custom_count
                sku.save()
        #         2.8 保存订单商品信息
            OrderGoods.objects.create(
                order=order,
                sku=sku,
                count=custom_count,
                price=sku.price
            )
        #         2.9 计算 订单的价格和总数量
            order.total_count+=custom_count
            order.total_amount+=(custom_count*sku.price)
        #     3. 更新订单总价格和总数量
        order.save()
        #     4. 删除redis中选中的数据
        redis_cli.hdel('carts_%s'%user.id,*ids)
        redis_cli.srem('selected_%s'%user.id,*ids)

        # 四。返回响应
        return JsonResponse({'code':0,'errmsg':'ok','order_id':order.order_id})
