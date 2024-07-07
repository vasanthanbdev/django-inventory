from django.db import models
from inventory.models import Stock

class Supplier(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=12, unique=True)
    address = models.CharField(max_length=200)
    email = models.EmailField(max_length=254, unique=True)
    gstin = models.CharField(max_length=15, unique=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class PurchaseBill(models.Model):
    billno = models.AutoField(primary_key=True)
    time = models.DateTimeField(auto_now=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchasesupplier')
    auto_generated = models.BooleanField(default=False)

    def __str__(self):
        return f"Bill no: {self.billno}"

    def get_items_list(self):
        return PurchaseItem.objects.filter(billno=self)

    def get_total_price(self):
        purchaseitems = PurchaseItem.objects.filter(billno=self)
        total = 0
        for item in purchaseitems:
            total += item.totalprice

class PurchaseItem(models.Model):
    billno = models.ForeignKey(PurchaseBill, on_delete=models.CASCADE, related_name='purchasebillno')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='purchaseitem')
    quantity = models.IntegerField(default=1)
    perprice = models.IntegerField(default=1)
    totalprice = models.IntegerField(default=1)

    def __str__(self):
        return f"Bill no: {self.billno.billno}, Item = {self.stock.get_full_name()}"

class PurchaseBillDetails(models.Model):
    billno = models.ForeignKey(PurchaseBill, on_delete=models.CASCADE, related_name='purchasedetailsbillno')

    eway = models.CharField(max_length=50, blank=True, null=True)
    veh = models.CharField(max_length=50, blank=True, null=True)
    destination = models.CharField(max_length=50, blank=True, null=True)
    po = models.CharField(max_length=50, blank=True, null=True)

    cgst = models.CharField(max_length=50, blank=True, null=True)
    sgst = models.CharField(max_length=50, blank=True, null=True)
    igst = models.CharField(max_length=50, blank=True, null=True)
    cess = models.CharField(max_length=50, blank=True, null=True)
    tcs = models.CharField(max_length=50, blank=True, null=True)
    total = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Bill no: {self.billno.billno}"

class SaleBill(models.Model):
    billno = models.AutoField(primary_key=True)
    time = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=12)
    address = models.CharField(max_length=200)
    email = models.EmailField(max_length=254)
    gstin = models.CharField(max_length=15)

    def __str__(self):
        return f"Bill no: {self.billno}"

    def get_items_list(self):
        return SaleItem.objects.filter(billno=self)

    def get_total_price(self):
        saleitems = SaleItem.objects.filter(billno=self)
        total = 0
        for item in saleitems:
            total += item.totalprice
        return total

from django.db import models
from inventory.models import Stock

class SaleItem(models.Model):
    billno = models.ForeignKey(SaleBill, on_delete=models.CASCADE, related_name='salebillno')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='saleitem')
    quantity = models.IntegerField(default=1)
    perprice = models.IntegerField(default=1)
    totalprice = models.IntegerField(default=1)
    total_sales_value = models.IntegerField(default=0)  # New field for total sales value

    def __str__(self):
        return f"Bill no: {self.billno.billno}, Item = {self.stock.get_full_name()}"

class SaleBillDetails(models.Model):
    billno = models.ForeignKey(SaleBill, on_delete=models.CASCADE, related_name='saledetailsbillno')

    eway = models.CharField(max_length=50, blank=True, null=True)
    veh = models.CharField(max_length=50, blank=True, null=True)
    destination = models.CharField(max_length=50, blank=True, null=True)
    po = models.CharField(max_length=50, blank=True, null=True)

    cgst = models.CharField(max_length=50, blank=True, null=True)
    sgst = models.CharField(max_length=50, blank=True, null=True)
    igst = models.CharField(max_length=50, blank=True, null=True)
    cess = models.CharField(max_length=50, blank=True, null=True)
    tcs = models.CharField(max_length=50, blank=True, null=True)
    total = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Bill no: {self.billno.billno}"
