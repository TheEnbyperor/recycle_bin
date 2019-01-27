from django.contrib import admin
from . import models

admin.site.register(models.Brand)
admin.site.register(models.Product)
admin.site.register(models.Material)
admin.site.register(models.ProductPart)
