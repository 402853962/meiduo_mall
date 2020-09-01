from django.core.mail import send_mail
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from meiduo_mall import settings
from celery_tasks.main import app

@app.task
def celery_send_mail(email,access_token):
    subject = "美多商城邮箱验证"
    message = ''
    from_email = 'qi_rui_hua@163.com'
    recipient_list = [email]

    verify_url = 'http://www.meiduo.site:8080/success_verify_email.html?token=%s' % access_token
    html_message = '<p>尊敬的用户您好！</p>' \
                   '<p>感谢您使用美多商城。</p>' \
                   '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                   '<p><a href="%s">%s<a></p>' % (email, verify_url, verify_url)
    send_mail(subject, message, from_email, recipient_list, html_message=html_message)