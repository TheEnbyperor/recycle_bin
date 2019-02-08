import graphene
from graphene_django.types import DjangoObjectType
from . import models


class BrandType(DjangoObjectType):
    class Meta:
        model = models.Brand


class MaterialType(DjangoObjectType):
    class Meta:
        model = models.Material


class ProductType(DjangoObjectType):
    class Meta:
        model = models.Product


class ProductPartType(DjangoObjectType):
    class Meta:
        model = models.ProductPart


class Query:
    product = graphene.Field(ProductType, barcode=graphene.NonNull(graphene.String))

    def resolve_product(self, info, barcode):
        return models.Product.objects.get(barcode=barcode)
