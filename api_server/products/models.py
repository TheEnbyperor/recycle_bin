from django.db import models


class Brand(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Material(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Product(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255)
    barcode = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.brand.name} {self.name}"


class ProductPart(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.product.brand.name} {self.product.name}: {self.name}"
