from django.shortcuts import render
# Create your views here.
import re
from django.http import JsonResponse
from django.views import View
from django_redis import get_redis_connection
from libs.captcha.captcha import captcha
from django.http import HttpResponse

# 图片验证流程：
# 1.定义视图,获取uuid
# 2.url注册
# 3.定义转换器,正则判断
# 4.注册redis数据库
# 5.图片验证码生成,保存,响应
class ImageCodeView(View):
    def get(self,request,key):
        text,image = captcha.generate_captcha()

        redis_conn = get_redis_connection('code')
        redis_conn.setex(key,300,text)

        return HttpResponse(image,content_type='image/jpeg')

# 短信验证流程:
# 1.定义视图,接收mobile
# 2.接收数据,电话,图形验证码,uuid
# 3.链接redis,提取后端保存的图形验证码
# 4.校验数据(数据齐全？电话号码规范？图形验证码匹配？)
# 5.校验结束删除接收的图形验证码
# 6.生成短信校验码
# 7.发送校验码
# 8.返回响应

class SmsCodeView(View):
    def get(self,request,mobile):
        image_code = request.GET.get('image_code')
        image_code_id = request.GET.get('image_code_id')

        redis_cli = get_redis_connection('code')
        redis_text = redis_cli.get(image_code_id)

        if not all ([image_code,image_code_id,mobile]):
            return JsonResponse({'code':400, 'errmsg':'参数不全！'})
        if  not re.match('1[3-9]\d{9}',mobile):
            return JsonResponse({'code':400, 'errmsg':'电话号码不规范！'})

        if redis_text is None:
            return JsonResponse({'code':400, 'errmsg':'图形码不存在！'})
        if image_code.lower() != redis_text.decode().lower():
            return JsonResponse({'code':400, 'errmsg':'图形码不一致！'})

        redis_cli.delete(image_code_id)

        send_flag = redis_cli.get('send_flag_%s'%mobile)
        if send_flag:
            return JsonResponse({'code':400, 'errmsg':'短信申请频繁！'})

        from random import randint
        sms_code = '%06d' % randint(0,999999)

        pipeline = redis_cli.pipeline()


        pipeline.setex(mobile,300,sms_code)

        # from libs.yuntongxun.sms import CCP
        # ccp = CCP()
        # 注意： 测试的短信模板编号为1

        from celery_tasks.sms.tasks import celery_send_sms

        celery_send_sms.delay(mobile,sms_code)

        pipeline.setex('send_flag_%s'%mobile,60,1)
        pipeline.excute()

        return JsonResponse({'code':0,'errmsg':'ok'})
