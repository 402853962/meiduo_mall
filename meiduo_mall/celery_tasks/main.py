import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo_mall.settings")


from celery import Celery
# 1.创建celery实例
# 2.生产者

app=Celery('celery_tasks')
app.config_from_object('celery_tasks.config')
app.autodiscover_tasks(['celery_tasks.sms','celery_tasks.email'])


# app=Celery('celery_tasks')
# app.config_from_object('celery_tasks.config')
#
# app.autodiscover_tasks(['celery_tasks.sms'])

