from django.core.cache import cache
from django.shortcuts import render

# Create your views here.
from django.views import View

from apps.areas.models import Area
from django.http import JsonResponse

class AreaView(View):
    def get(self,request):

        province_list=cache.get('province')
        if province_list is None:
            province = Area.objects.filter(parent__isnull=True)
            province_list = []
            for item in province:
                province_list.append({
                    'id':item.id,
                    'name':item.name
                })

            cache.set('province',province_list)
        return JsonResponse({'code':0, 'errmsg':'ok', 'province_list':province_list})

class SubsAreaView(View):
    def get(self,request,parent_id):
        sub_data = cache.get('sub_data%s'%parent_id)
        if sub_data is None:

        # 方案一，根据id拿
        # subs = Area.objects.filter(parent=parent_id)

        # 方案二，先获取parent_id,再获取下一级数据
            parent_area = Area.objects.get(id=parent_id)
            subs = parent_area.subs.all()

            sub_list = []
            for item in subs:
                sub_list.append({
                    'id':item.id,
                    'name':item.name
                })
            sub_data = {
                'id':parent_area.id,
                'name':parent_area.name,
                'subs':sub_list
            }

            cache.set('sub_data%s'%parent_id,sub_data)
        return JsonResponse({'code':0,'errmsg':'ok','sub_data':sub_data})