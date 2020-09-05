from django.shortcuts import render

# Create your views here.
from django.views import View

from apps.orders.models import OrderInfo
from utils.views import LoginRequiredJsonMixin
from django.http import JsonResponse
from alipay import AliPay
from meiduo_mall import settings
from apps.payment.models import Payment

class PayURLView(LoginRequiredJsonMixin,View):
    def get(self,request,order_id):
        try:
            order=OrderInfo.objects.get(order_id=order_id,status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'],user=request.user)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'code':400,'errmsg':'订单不存在'})

        app_private_key_string = open(settings.APP_PRIVATE_KEY_PATH).read()
        alipay_public_key_string = open(settings.ALIPAY_PUBLIC_KEY_PATH).read()


        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug = False  # 默认False
        )

        # 如果你是 Python 3的用户，使用默认的字符串即可
        subject = "美多商城"

        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),
            subject=subject,
            return_url=settings.ALIPAY_RETURN_URL,
            notify_url="https://example.com/notify"  # 可选, 不填则使用默认notify url
        )

        alipay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string

        return JsonResponse({'code':0,'errmsg':'ok','alipay_url':alipay_url})

class PaymentStatusView(LoginRequiredJsonMixin,View):
    def put(self,request):
        data=request.GET.dict()
        signature=data.pop('sign')

        app_private_key_string = open(settings.APP_PRIVATE_KEY_PATH).read()
        alipay_public_key_string = open(settings.ALIPAY_PUBLIC_KEY_PATH).read()

        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=False  # 默认False
        )

        success = alipay.verify(data, signature)
        if success:
            trade_no=data.get('trade_no')
            out_trade_no=data.get('out_trade_no')

            Payment.objects.create(
                order_id=out_trade_no,
                trade_id=trade_no
            )

            OrderInfo.objects.filter(order_id=out_trade_no).update(status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'])

            return JsonResponse({'code':0,'errmsg':'ok','trade_id':trade_no})

        return JsonResponse({'code':400,'errmsg':'请稍后再试'})