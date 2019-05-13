import graphene.relay
from graphene_django.types import DjangoObjectType
from graphql_relay import from_global_id
from . import models


class LocalAuthorityType(DjangoObjectType):
    class Meta:
        model = models.Authority
        interfaces = (graphene.relay.Node, )


class BinType(DjangoObjectType):
    class Meta:
        model = models.Bin
        interfaces = (graphene.relay.Node, )


class MaterialBinType(DjangoObjectType):
    class Meta:
        model = models.MaterialBin
        interfaces = (graphene.relay.Node, )


class Query:
    local_authorities = graphene.NonNull(graphene.List(graphene.NonNull(LocalAuthorityType)))
    local_authority = graphene.Field(LocalAuthorityType, id=graphene.NonNull(graphene.ID))

    def resolve_local_authorities(self, info):
        return models.Authority.objects.all()

    def resolve_local_authority(self, info, id):
        id = from_global_id(id)
        if id[0] != "LocalAuthorityType":
            return None
        return models.Authority.objects.get(id=id[1])
