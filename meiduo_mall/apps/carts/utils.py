import pickle
import base64
from django_redis import get_redis_connection
from django.http import JsonResponse

def merge_cookie_to_redis(request,response):
    cookie_carts=request.COOKIES.get('carts')
    if cookie_carts=={}:
        pass
    elif cookie_carts is not None:
        carts=pickle.loads(base64.b64decode(cookie_carts))


        new_carts={}
        new_unselected_ids=[]
        new_selected_ids=[]

        for sku_id,count_selected_dict in carts.items():
            new_carts[sku_id]=count_selected_dict['count']

            if count_selected_dict['selected']:
                new_selected_ids.append(sku_id)
            else:
                new_unselected_ids.append(sku_id)

        redis_cli=get_redis_connection('carts')
        pipeline=redis_cli.pipeline()
        pipeline.hmset('carts_%s'%request.user.id,new_carts)

        if len(new_selected_ids)>0:
            pipeline.sadd('selected_%s'%request.user.id,*new_selected_ids)
        if len(new_unselected_ids)>0:
            pipeline.srem('selected_%s'%request.user.id,*new_unselected_ids)
        pipeline.execute()
        response.delete_cookie('carts')


    return response