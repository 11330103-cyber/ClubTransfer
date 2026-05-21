from django.contrib import admin
from .models import Club, TransferRequest, UserProfile

admin.site.register(Club)
admin.site.register(TransferRequest)
admin.site.register(UserProfile)