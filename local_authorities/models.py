from django.db import models
import products.models


class Authority(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = "Authorities"

    def __str__(self):
        return self.name


class Bin(models.Model):
    authority = models.ForeignKey(Authority, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.authority.name}: {self.name}"


class MaterialBin(models.Model):
    material = models.ForeignKey(products.models.Material, on_delete=models.SET_NULL, null=True)
    bin = models.ForeignKey(Bin, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.bin.authority.name}: {self.material.name}"
