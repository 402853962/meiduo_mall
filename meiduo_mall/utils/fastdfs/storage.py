from django.core.files.storage import Storage

class MyStorage(Storage):
    # def __init__(self, option=None):
    #     if not option:
    #         option = settings.CUSTOM_STORAGE_OPTIONS
    def __open(self,name,mode='rb'):
        pass

    def __save(self,name,content,max_length=None):
        pass

    def url(self, name):
        return 'http://192.168.112.146:8888/' + name