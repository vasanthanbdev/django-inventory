from django.db import models

class Stock(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30)
    sub_category = models.CharField(max_length=30, blank=True)  # Allow blank for non-mandatory sub_category
    quantity = models.IntegerField(default=1)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    is_deleted = models.BooleanField(default=False)
    is_selected = models.BooleanField(default=False)
    total_sales_value = models.IntegerField(default=0) 

    reorder_point = models.IntegerField(default=0)

    class Meta:
        unique_together = ('name', 'sub_category')

    def __str__(self):
        return f"{self.name} - {self.sub_category}" if self.sub_category else self.name
