from django.template import loader
from meiduo_mall import settings
from apps.contents.models import ContentCategory
from utils.goods import get_categories
import os


def generic_index_html():
    categories = get_categories()
    contents = {}
    content_categories = ContentCategory.objects.all()
    for cat in content_categories:
        contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

    context = {
        'categories': categories,
        'contents': contents,
    }

    index_template=loader.get_template('index.html')
    index_html=index_template.render(context)
    index_path=os.path.join(os.path.dirname(settings.BASE_DIR),'front_end_pc/index.html')

    with open(index_path,'w') as f:
        f.write(index_html)

    pass