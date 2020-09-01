from django.shortcuts import render

# Create your views here.

##############################
# from fdfs_client.client import Fdfs_client
# client = Fdfs_client('utils/fastdfs/client.conf')
#
# client.upload_by_filename('/home/ubuntu/Desktop/001.jpg')
from django.views import View
from utils.goods import get_categories
from apps.contents.models import ContentCategory
class IndexView(View):
    def get(self,request):

        categories = get_categories()
        contents = {}
        content_categories = ContentCategory.objects.all()
        for cat in content_categories:
            contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

        context = {
            'categories': categories,
            'contents': contents,
        }

        return render(request,'index.html',context=context)

from utils.goods import get_breadcrumb
from apps.goods.models import GoodsCategory,SKU
from django.http import JsonResponse
from django.core.paginator import Paginator
class ListView(View):
    def get(self,request,category_id):
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return JsonResponse({'code':400, 'errmsg':'商品不存在'})

        breadcrumb = get_breadcrumb(category)
        ordering=request.GET.get('ordering')
        page=request.GET.get('page')
        page_size=request.GET.get('page_size')

        skus=SKU.objects.filter(category=category,is_launched=True).order_by(ordering)

        paginator = Paginator(skus,per_page=page_size)

        page_sku = paginator.page(page)
        total_page = paginator.num_pages

        sku_list=[]
        for sku in skus:
            sku_list.append({
                'id':sku.id,
                'name':sku.name,
                'prcie':sku.price,
                'default_image_url':sku.default_image.url,
            })

        return JsonResponse({'code': 0, 'errmsg': 'ok', 'breadcrumb':breadcrumb,'list':sku_list, 'count':total_page})

class HotView(View):
    def get(self,request,category_id):
        skus= SKU.objects.filter(category_id=category_id,is_launched=True).order_by('-sales')[0:2]
        hot_skus=[]
        for sku in skus:
            hot_skus.append({
                'id':sku.id,
                'name': sku.name,
                'prcie': sku.price,
                'default_image_url': sku.default_image.url,
            })
        return JsonResponse({'code': 0, 'errmsg': 'ok','hot_skus': hot_skus})

from utils.goods import get_goods_specs
class DetailView(View):
    def get(self,request,sku_id):
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            pass

        categories = get_categories()
        breadcrumb = get_breadcrumb(sku.category)
        specs = get_goods_specs(sku)
        context= {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'sku': sku,
            'specs': specs,
        }

        return render(request,'detail.html',context)

from apps.goods.models import GoodsVisitCount
class GoodsVisitView(View):
    def post(self,request,cat_id):
        try:
            category=GoodsCategory.objects.get(id=cat_id)
        except GoodsCategory.DoesNotExist:
            return JsonResponse({'code':400,'errmsg':'没有商品'})

        from datetime import date
        today=date.today()
        try:
            today_data=GoodsVisitCount.objects.get(category=category,date=today)
        except GoodsVisitCount.DoesNotExist:
            GoodsVisitCount.objects.create(
                category=category,
                date=today,
                count=1
            )
        else:
            today_data.count += 1
            today_data.save()

        return JsonResponse({'code':0,'errmsg':'ok'})

from haystack.views import SearchView

class MySearchView(SearchView):
    '''重写SearchView类'''
    def create_response(self):
        page = self.request.GET.get('page')
        # 获取搜索结果
        context = self.get_context()
        data_list = []
        for sku in context['page'].object_list:
            data_list.append({
                'id':sku.object.id,
                'name':sku.object.name,
                'price':sku.object.price,
                'default_image_url':sku.object.default_image.url,
                'searchkey':context.get('query'),
                'page_size':context['page'].paginator.num_pages,
                'count':context['page'].paginator.count
            })
        # 拼接参数, 返回
        return JsonResponse(data_list, safe=False)