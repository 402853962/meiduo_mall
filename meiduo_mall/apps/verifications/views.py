from django.shortcuts import render
# Create your views here.
import re
from django.http import JsonResponse
from django.views import View

from libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from django.http import HttpResponse
class ImageCodeView(View):
    def get(self,request,key):
        text,image = captcha.generate_captcha()
        redis_cli = get_redis_connection('code')
        redis_cli.setex(key,60,text)

        return HttpResponse(image,content_type='image/jpeg')

class SmsCodeView(View):
    def get(self,request,mobile):
        image_code = request.GET.get('image_code')
        image_code_id = request.GET.get('image_code_id')

        if not all ([mobile,image_code,image_code_id]):
            return JsonResponse({'code': 400, 'errmsg': '参数不全！'})
        if not re.match('1[3-9]\d{9}',mobile):
            return JsonResponse({'code': 400, 'errmsg': '电话格式有误！'})

        redis_cli = get_redis_connection('code')
        redis_text = redis_cli.get(image_code_id)
        if redis_text is None:
            return JsonResponse({'code': 400, 'errmsg': '没有图片验证码！'})
        if image_code.lower() != redis_text.decode().lower():
            return JsonResponse({'code': 400, 'errmsg': '验证码不一致！'})

        redis_cli.delete(image_code_id)

        from random import randint
        sms_code = '%06d'%randint(0,999999)
        redis_cli.setex(mobile,300,sms_code)

        from libs.yuntongxun.sms import CCP
        ccp = CCP()
        # 注意： 测试的短信模板编号为1
        ccp.send_template_sms(mobile, [sms_code, 5], 1)
        return JsonResponse({'code':0,'errmsg':'ok'})