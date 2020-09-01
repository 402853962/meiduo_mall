from django.shortcuts import render
from django.views import View
from apps.users.models import User
from django.http import JsonResponse
from django_redis import get_redis_connection
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
# 验证短信验证码逻辑:
# 1.获取用户输入的code
# 2.从redis中获取保存的sms_code
# 3.对比是否一致，code是否过期，返回json
        sms_code = request.POST.get('sms_code')
        redis_conn = get_redis_connection('code')
        sms_code_server = redis_conn.get('key')
        if not sms_code_server:
            return JsonResponse({'code':400, 'errmsg':'短信验证码已过期！'})
        if sms_code != sms_code_server.decode():
            return JsonResponse({'code':400, 'errmsg':'短信验证码不一致！'})


        user = User.objects.create_user(username=username,password=password,mobile=mobile)
        #状态保持session技术
        from django.contrib.auth import login
        login(request,user)

        return JsonResponse({'code':0,'errmsg':'注册成功！'})


# 登录视图
class LoginView(View):
    def post(self,request):
        json_info = request.body.decode()
        json_dict = json.loads(json_info)
        username = json_dict.get('username')
        password = json_dict.get('password')
        remembered = json_dict.get('remembered')
        if not all([username,password]):
            return JsonResponse({'code':400, 'errmsg':'参数不全！'})

        from django.contrib.auth import authenticate,login
        if re.match('1[3-9]\d{9}',username):
            User.USERNAME_FIELD='mobile'
        else:
            User.USERNAME_FIELD='username'

        user = authenticate(username=username,password=password)
        if user is None:
            return JsonResponse({'code':400, 'errmsg':'用户名或密码不正确'})

        login(request,user)
        if remembered:
            request.session.set_expiry(None)
        else:
            request.session.set_expiry(0)

        response = JsonResponse({'code':0,'errmsg':'ok'})
        response.set_cookie('username',user.username,max_age=14*24*60*60)

        return response

# 退出登录视图
class LogoutView(View):
    def delete(self,request):
        from django.contrib.auth import logout
        logout(request)

        response = JsonResponse({'code':0, 'errmsg':'ok'})
        response.delete_cookie('username')
        return response


#用户中心
# from django.contrib.auth.mixins import LoginRequiredMixin
from utils.views import LoginRequiredJsonMixin
class UserCenterView(LoginRequiredJsonMixin,View):
    def get(self,request):
        info_data = {
            'username' : request.user.username,
            'mobile' : request.user.mobile,
            'email' : request.user.email,
            'email_active' : request.user.email_active,
        }

        return JsonResponse({'code':0,'errmsg':'ok','info_data':info_data})

from utils.views import LoginRequiredJsonMixin
class EmailView(LoginRequiredJsonMixin,View):
    def put(self,request):
        data = json.loads(request.body.decode())
        email = data.get('email')
        if not email:
            return JsonResponse({'code': 400, 'errmsg': '缺少email参数'})
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return JsonResponse({'code': 400, 'errmsg': '参数email有误'})

        request.user.email = email
        request.user.save()

        # from django.core.mail import send_mail
        # subject='wzx测试邮件'
        # message='测试测试测试'
        # from_email='qi_rui_hua@163.com'
        # recipient_list=[email]
        #
        # from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
        # from meiduo_mall import settings
        # s = Serializer(secret_key=settings.SECRET_KEY, expires_in=24*60*60)
        # toekn = s.dumps({
        #     'id':request.user.id,
        #     'email':email
        # })
        # from apps.users.utils import generic_email_access_token
        # access_token=generic_email_access_token(request.user.id,email)
        # verify_url = 'http://www.meiduo.site:8080/success_verify_email.html/?token=%s'%access_token
        # html_message= '<a href="http://www.meiduo.site/?user_id=1">点我激活</a>'
        # send_mail(subject, message, from_email, recipient_list, html_message)

        from apps.users.utils import generic_email_access_token
        access_token=generic_email_access_token(request.user.id,email)

        from celery_tasks.email.tasks import celery_send_mail
        celery_send_mail.delay(email,access_token)

        return JsonResponse({'code':0, 'errmsg':'邮件保存成功！'})

class EmailVerificationView(View):
    def put(self,request):
        token = request.GET.get('token')
        if token is None:
            return JsonResponse({'code':400, 'errmsg':'缺少必要参数'})
        from apps.users.utils import check_email_token
        data = check_email_token(token)
        if data is None:
            return JsonResponse({'code':400, 'errmsg':'缺少必要参数'})

        user_id = data.get('id')
        email = data.get('email')

        try:
            user=User.objects.get(id=user_id,email=email)
        except User.DoesNotExist:
            return JsonResponse({'code':400, 'errmsg':'用户名不存在'})

        user.email_active=True
        user.save()

        return JsonResponse({'code':0 ,'errmsg':'ok'})

from apps.users.models import Address
from utils.views import LoginRequiredJsonMixin
class AddressCreateView(LoginRequiredJsonMixin,View):
    def post(self,request):
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        address = Address.objects.create(
            user=request.user,
            title=receiver,
            receiver=receiver,
            province_id=province_id,
            city_id=city_id,
            district_id=district_id,
            place=place,
            mobile=mobile,
            tel=tel,
            email=email
        )

        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({'code':400,'errmsg':'参数不全'})
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code':400,'errmsg':'参数mobile有误'})
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code': 400, 'errmsg': '参数tel有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400, 'errmsg': '参数email有误'})

        if not request.user.default_address:
            request.user.default_address=address
            request.user.save()

        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        return JsonResponse({'code':0,'errmsg':'ok','address':address_dict})

class AddressesView(LoginRequiredJsonMixin,View):
    def get(self,request):
        addresses = Address.objects.filter(user=request.user,is_deleted=False)
        addresses.dict = []
        for address in addresses:
            addresses.dict.append({
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "city": address.city.name,
                "district": address.district.name,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            })

        return JsonResponse({'code':0,'errmsg':'ok','addresses':addresses.dict})

# 修改地址
# 1.获取用户信息
# 2.校验信息，齐全？电话？固定电话？邮箱？
# 3.update信息
# 4.返回新的dict

class VerifyAddressView(LoginRequiredJsonMixin,View):
    def put(self,request,address_id):
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        if not all([receiver,province_id,city_id,district_id,place,mobile,tel,email]):
            return JsonResponse({'code':400,'errmsg':'参数不全'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code':400, 'errmsg':'电话参数有误'})

        if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$',tel):
            return JsonResponse({'code':400, 'errmsg':'固定电话参数有误'})

        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return JsonResponse({'code':400, 'errmsg':'邮箱地址有误'})

        Address.objects.filter(id=address_id).update(
            user=request.user,
            title=receiver,
            receiver=receiver,
            province_id=province_id,
            city_id=city_id,
            district_id=district_id,
            place=place,
            mobile=mobile,
            tel=tel,
            email=email
        )

        address = Address.objects.get(id=address_id)
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        return JsonResponse({'code':0,'errmsg':'ok','address':address_dict})

    def delete(self,request,address_id):
        address = Address.objects.get(id=address_id)

        address.is_deleted = True
        address.save()

        return JsonResponse({'code':0,'errmsg':'ok'})

class DefaultSetView(LoginRequiredJsonMixin,View):
    def put(self,request,address_id):
        address = Address.objects.get(id=address_id)
        request.user.default_address=address
        request.user.save()


        return JsonResponse({'code':0,'errmsg':'ok'})

class TitleSetView(LoginRequiredJsonMixin,View):
    def put(self,request,address_id):
        address=Address.objects.get(id=address_id)
        json_dict=json.loads(request.body.decode())
        title=json_dict.get('title')

        address.title = title
        address.save()

        return JsonResponse({'code':0,'errmsg':'ok'})

from apps.goods.models import SKU
from django_redis import get_redis_connection
class UserHistoryView(LoginRequiredJsonMixin,View):
    def post(self,request):
        data = json.loads(request.body.decode())
        sku_id=data.get('sku_id')

        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code':400,'errmsg':'商品不存在'})

        redis_cli=get_redis_connection('history')
        pl = redis_cli.pipeline()
        pl.lrem('history_%s'%request.user.id,0,sku_id)
        pl.lpush('history_%s'%request.user.id,sku_id)
        pl.ltrim('history_%s'%request.user.id,0,4)
        pl.execute()

        return JsonResponse({'code':0,'errmsg':'ok'})

    def get(self,request):
        user=request.user
        redis_cli=get_redis_connection('history')
        sku_ids=redis_cli.lrange('history_%s'%user.id,0,-1)

        sku_list=[]
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price
            })

        return JsonResponse({'code': 0, 'errmsg': 'OK', 'skus': sku_list})