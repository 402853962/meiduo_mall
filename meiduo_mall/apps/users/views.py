from django.shortcuts import render
from django.views import View
from apps.users.models import User
from django.http import JsonResponse
import json
import re
# Create your views here.
class UsernameCountView(View):
    def get(self,request,username):
        # if not re.match('[a-zA-Z0-9]{5,20}',username) :
        #     return JsonResponse({'code':0,'errmsg':'username do not match the requirment'})
        count = User.objects.filter(username=username).count()
        return JsonResponse({'code':0,'errmsg':'ok','count':count})

class RegisterView(View):
    def post(self,request):
        body_str = request.body.decode()
        body_dict = json.loads(body_str)


        username = body_dict.get('username')
        password = body_dict.get('password')
        password2 = body_dict.get('password2')
        mobile = body_dict.get('mobile')
        allow = body_dict.get('allow')

        if not all([username,password2,password,mobile,allow]):
            return JsonResponse({'code':'400','errmsg':'参数不全'})

        if not re.match(r'[a-zA-Z0-9_-]{5,20}',username):
            return JsonResponse({'code':'400','errmsg':'用户名不符合规则'})

        if not re.match(r'^[a-zA-Z0-9]{8,20}$',password):
            return JsonResponse({'code':'400','errmsg':'密码不符合规则'})


        user = User.objects.create_user(username=username,password=password,mobile=mobile)
        return JsonResponse({'code':0,'errmsg':'注册成功！'})


        pass

