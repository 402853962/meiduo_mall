
from celery_tasks.main import app
from libs.yuntongxun.sms import CCP

@app.task
def celery_send_sms(mobile,sms_code):
    CCP().send_template_sms(mobile,[sms_code,5],1)