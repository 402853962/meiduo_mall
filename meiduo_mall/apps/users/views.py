from django.shortcuts import render
from django.views import View
from apps.users.models import User
from django.http import JsonResponse
import json
import re
# Create your views here.
# 1.判断是否重复注册,定义类
# 2.判断输入是否规范,建立路由转换器
# 3.在总路由中注册转换器
# 4.在子路由调用
# 5.跨域,注册应用 中间件 白名单 允许携带cookies
# 6.注册接口定义,定义视图函数
# 7.自路由注册视图函数
# 8.视图函数中，接受请求体数据，把JSON转换成字典,从字典提取参数
# 9.校验参数,齐全？用户名密码手机号规范？两次密码一致？用户协议？
# 10.保存数据,返回JSON响应

class UsernameCountView(View):
    def get(self,request,username):
        count = User.objects.filter(username=username).count()
        return JsonResponse({'code':0,'errmsg':'ok','count':count})

class MobileCountView(View):
    def get(self,request,mobile):
        count = User.objects.filter(mobile=mobile).count()
        return JsonResponse({'code':0,'errmsg':'ok','count':count})

class RegisterView(View):
    def post(self,request):
        json_str = request.body.decode()
        json_dict = json.loads(json_str)

        username = json_dict['username']
        password = json_dict['password']
        password2 = json_dict['password2']
        mobile = json_dict['mobile']
        allow = json_dict['allow']
        sms_code = json_dict['sms_code']

        if not all ([username,password,password2,mobile,allow,sms_code]):
            return JsonResponse({'code':400,'errmsg':'参数不全！'})
        if not re.match('[a-zA-Z0-9_-]{5,20}',username):
            return JsonResponse({'code':400,'errmsg':'用户名格式有误！'})
        if not re.match('1[3-9]\d{9}',mobile):
            return JsonResponse({'code': 400, 'errmsg': '电话格式有误！'})
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return JsonResponse({'code': 400, 'errmsg': 'password格式有误!'})
        if not password == password2:
            return JsonResponse({'code': 400, 'errmsg': '两次密码不相等!'})
        if allow != True:
            return JsonResponse({'code': 400, 'errmsg': 'allow格式有误!'})

        user = User.objects.create_user(username=username,password=password,mobile=mobile)
        return JsonResponse({'code':0,'errmsg':'注册成功！'})