from django.contrib import admin
from  .models import *

admin.site.register(FacebookAccount)
admin.site.register(FacebookPost)
admin.site.register(FacebookAction)
admin.site.register(BlockedAccount)
admin.site.register(LoginRequiredAccount)


 