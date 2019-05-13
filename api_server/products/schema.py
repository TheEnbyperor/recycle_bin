import graphene.relay
from graphene_django.types import DjangoObjectType
from graphql_relay import from_global_id
import local_authorities.models
import local_authorities.schema
from . import models


class BrandType(DjangoObjectType):
    class Meta:
        model = models.Brand
        interfaces = (graphene.relay.Node, )


class MaterialType(DjangoObjectType):
    class Meta:
        model = models.Material
        interfaces = (graphene.relay.Node, )

    bin = graphene.NonNull(local_authorities.schema.BinType, authority=graphene.NonNull(graphene.ID))

    def resolve_bin(self, info, authority):
        id = from_global_id(authority)
        if id[0] != "LocalAuthorityType":
            return None
        material_bin = local_authorities.models.MaterialBin.objects.get(material=self, bin__authority_id=id[1])
        return material_bin.bin


class ProductType(DjangoObjectType):
    class Meta:
        model = models.Product
        interfaces = (graphene.relay.Node, )


class ProductPartType(DjangoObjectType):
    class Meta:
        model = models.ProductPart
        interfaces = (graphene.relay.Node, )


class Query:
    product = graphene.Field(ProductType, barcode=graphene.NonNull(graphene.String))

    def resolve_product(self, info, barcode):
        return models.Product.objects.get(barcode=barcode)
