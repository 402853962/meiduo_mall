import json

from django.contrib.auth import login
from django.shortcuts import render
from django.http import JsonResponse
from apps.users.models import User
# Create your views here.
from django.views import View

from apps.oauth.models import OAuthQQUser


class QQLoginURLView(View):
    def get(self,request):
        next = request.GET.get('next')
        from QQLoginTool.QQtool import OAuthQQ
        from meiduo_mall import settings
        qqlogin = OAuthQQ( client_id=settings.QQ_CLIENT_ID,
                           client_secret=settings.QQ_CLIENT_SECRET,
                           redirect_uri=settings.QQ_REDIRECT_URI,
                           state=next)

        login_url = qqlogin.get_qq_url()

        return JsonResponse({'code':0, 'errmsg':'ok', 'login_url' : login_url})

class QQUserView(View):
    def get(self,request):


        code = request.GET.get('code')
        if code is None:
            return JsonResponse({'code':400, 'errmsg':'缺少参数！'})
        from QQLoginTool.QQtool import OAuthQQ
        from meiduo_mall import settings
        oauthqq = OAuthQQ( client_id=settings.QQ_CLIENT_ID,
                           client_secret=settings.QQ_CLIENT_SECRET,
                           redirect_uri=settings.QQ_REDIRECT_URI,
                           state=None)
        token = oauthqq.get_access_token(code)
        openid = oauthqq.get_open_id(token)

        try:
            qquser = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            from apps.oauth.utils import generate_access_token
            openid_token = generate_access_token(openid)
            return JsonResponse({'code':300, 'access_token' : openid_token})
        else:

            login(request,qquser.user)
            response = JsonResponse({'code':0, 'errmsg':'ok'})

            response.set_cookie('username',qquser.user.username,max_age=14*24*60*60)
            return response

    def post(self,request):
        data = request.body.decode()
        data_dict = json.loads(data)
        mobile = data_dict.get('mobile')
        password = data_dict.get('password')
        openid_token = data_dict.get('access_token')
        sms_code = data_dict.get('sms_code')

        from apps.oauth.utils import check_access_token
        openid = check_access_token(openid_token)
        if openid is None:
            return JsonResponse({'code':400, 'errmsg':'token过期了'})

        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            user = User.objects.create_user(username=mobile,mobile=mobile,password=password)
        else:
            if not user.check_password(password):
                return JsonResponse({'code':400, 'errmsg':'密码不正确！'})

        OAuthQQUser.objects.create(user=user,openid=openid)

        login(request,user)

        response = JsonResponse({'code':0,'errmsg':'ok'})
        response.set_cookie('username',user.username,max_age=14*24*60*60)
        return response


from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.conf import settings

# serializer = Serializer(秘钥, 有效期秒)
serializer = Serializer(settings.SECRET_KEY, 300)
# serializer.dumps(数据), 返回bytes类型
token = serializer.dumps({'mobile': '18512345678'})
token = token.decode()

# 检验token
# 验证失败，会抛出itsdangerous.BadData异常
# serializer = Serializer(settings.SECRET_KEY, 300)
# try:
#     data = serializer.loads(token)
# # except BadData:
# #     return None


