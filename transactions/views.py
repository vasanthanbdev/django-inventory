from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.views.generic import View, ListView, CreateView, UpdateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from datetime import datetime, timedelta
from collections import defaultdict

from .models import (
    PurchaseBill, Supplier, PurchaseItem, PurchaseBillDetails,
    SaleBill, SaleItem, SaleBillDetails
)
from .forms import (
    SelectSupplierForm, PurchaseItemFormset,
    PurchaseDetailsForm, SupplierForm,
    SaleForm, SaleItemFormset, SaleDetailsForm, PurchaseItemForm
)
from inventory.models import Stock

# Threshold and excess quantity settings
THRESHOLD_QUANTITY = 5
EXCESS_QUANTITY = 5

# Views for Suppliers
class SupplierListView(ListView):
    model = Supplier
    template_name = "suppliers/suppliers_list.html"
    queryset = Supplier.objects.filter(is_deleted=False)
    paginate_by = 10

class SupplierCreateView(SuccessMessageMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    success_url = '/transactions/suppliers'
    success_message = "Supplier has been created successfully"
    template_name = "suppliers/edit_supplier.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'New Supplier'
        context["savebtn"] = 'Add Supplier'
        return context

class SupplierUpdateView(SuccessMessageMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    success_url = '/transactions/suppliers'
    success_message = "Supplier details has been updated successfully"
    template_name = "suppliers/edit_supplier.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'Edit Supplier'
        context["savebtn"] = 'Save Changes'
        context["delbtn"] = 'Delete Supplier'
        return context

class SupplierDeleteView(View):
    template_name = "suppliers/delete_supplier.html"
    success_message = "Supplier has been deleted successfully"

    def get(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        return render(request, self.template_name, {'object': supplier})

    def post(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        supplier.is_deleted = True
        supplier.save()
        messages.success(request, self.success_message)
        return redirect('suppliers-list')

# View to show supplier profile
class SupplierView(View):
    def get(self, request, name):
        supplierobj = get_object_or_404(Supplier, name=name)
        bill_list = PurchaseBill.objects.filter(supplier=supplierobj)
        page = request.GET.get('page', 1)
        paginator = Paginator(bill_list, 10)
        try:
            bills = paginator.page(page)
        except PageNotAnInteger:
            bills = paginator.page(1)
        except EmptyPage:
            bills = paginator.page(paginator.num_pages)
        context = {
            'supplier': supplierobj,
            'bills': bills
        }
        return render(request, 'suppliers/supplier.html', context)

# Views for Purchases
class PurchaseView(ListView):
    model = PurchaseBill
    template_name = "purchases/purchases_list.html"
    context_object_name = 'bills'
    ordering = ['-time']
    paginate_by = 10

class SelectSupplierView(View):
    form_class = SelectSupplierForm
    template_name = 'purchases/select_supplier.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            supplierid = request.POST.get("supplier")
            supplier = get_object_or_404(Supplier, id=supplierid)
            return redirect('new-purchase', supplier.pk)
        return render(request, self.template_name, {'form': form})

class PurchaseCreateView(View):
    template_name = 'purchases/new_purchase.html'

    def get(self, request, pk):
        formset = PurchaseItemFormset(request.GET or None)
        supplierobj = get_object_or_404(Supplier, pk=pk)
        context = {
            'formset': formset,
            'supplier': supplierobj,
        }
        return render(request, self.template_name, context)

    def post(self, request, pk):
        formset = PurchaseItemFormset(request.POST)
        supplierobj = get_object_or_404(Supplier, pk=pk)
        if formset.is_valid():
            billobj = PurchaseBill(supplier=supplierobj)
            billobj.save()
            billdetailsobj = PurchaseBillDetails(billno=billobj)
            billdetailsobj.save()
            
            for form in formset:
                billitem = form.save(commit=False)
                billitem.billno = billobj
                stock = Stock.objects.filter(name=billitem.stock.name, sub_category=billitem.stock.sub_category).first()

                if stock is None:
                    raise Http404("Stock not found for the given name and sub_category")

                billitem.totalprice = billitem.perprice * billitem.quantity
                stock.quantity += billitem.quantity
                stock.save()
                billitem.save()
            
            messages.success(request, "Purchased items have been registered successfully")
            return redirect('purchase-bill', billno=billobj.billno)
        
        formset = PurchaseItemFormset(request.GET or None)
        context = {
            'formset': formset,
            'supplier': supplierobj
        }
        return render(request, self.template_name, context)

from django.db.models.signals import post_save
from django.dispatch import receiver, Signal
from .models import Stock

# Import the function to disconnect
# from your_app.views import check_inventory_and_create_purchase_order

class PurchaseDeleteView(SuccessMessageMixin, DeleteView):
    model = PurchaseBill
    template_name = "purchases/delete_purchase.html"
    success_url = '/transactions/purchases'
    
    def delete(self, *args, **kwargs):
        # Temporarily disconnect the post_save signal for Stock
        post_save.disconnect(check_inventory_and_create_purchase_order, sender=Stock)
        
        # Perform the deletion
        self.object = self.get_object()
        items = PurchaseItem.objects.filter(billno=self.object.billno)
        
        # Update stock quantities
        for item in items:
            stock = get_object_or_404(Stock, name=item.stock.name, sub_category=item.stock.sub_category)
            if not stock.is_deleted:
                stock.quantity -= item.quantity
                stock.save()
        
        # After deletion, reconnect the post_save signal for Stock
        post_save.connect(check_inventory_and_create_purchase_order, sender=Stock)
        
        # Display success message and perform the actual deletion
        messages.success(self.request, "Purchase bill has been deleted successfully")
        return super().delete(*args, **kwargs)


# Views for Sales
class SaleView(ListView):
    model = SaleBill
    template_name = "sales/sales_list.html"
    context_object_name = 'bills'
    ordering = ['-time']
    paginate_by = 10

class SaleCreateView(View):
    template_name = 'sales/new_sale.html'

    def get(self, request):
        form = SaleForm(request.GET or None)
        formset = SaleItemFormset(request.GET or None)
        stocks = Stock.objects.filter(is_deleted=False)
        context = {
            'form': form,
            'formset': formset,
            'stocks': stocks
        }
        return render(request, self.template_name, context)

    def post(self, request):
        form = SaleForm(request.POST)
        formset = SaleItemFormset(request.POST)
        if form.is_valid() and formset.is_valid():
            billobj = form.save(commit=False)
            billobj.save()
            billdetailsobj = SaleBillDetails(billno=billobj)
            billdetailsobj.save()
            
            for form in formset:
                billitem = form.save(commit=False)
                billitem.billno = billobj
                
                stock_name = billitem.stock.name
                stock_sub_category = billitem.stock.sub_category

                stock = get_object_or_404(Stock, name=stock_name, sub_category=stock_sub_category)
                
                billitem.totalprice = billitem.perprice * billitem.quantity
                
                # Update stock quantity based on sale
                stock.quantity -= billitem.quantity
                
                # Save the stock and bill item
                stock.save()
                billitem.save()
            
            messages.success(request, "Sold items have been registered successfully")
            return redirect('sale-bill', billno=billobj.billno)
        
        form = SaleForm(request.GET or None)
        formset = SaleItemFormset(request.GET or None)
        context = {
            'form': form,
            'formset': formset,
        }
        return render(request, self.template_name, context)

class SaleDeleteView(SuccessMessageMixin, DeleteView):
    model = SaleBill
    template_name = "sales/delete_sale.html"
    success_url = '/transactions/sales'
    
    def delete(self, *args, **kwargs):
        self.object = self.get_object()
        items = SaleItem.objects.filter(billno=self.object.billno)
        
        # Update stock quantities when sale items are deleted
        for item in items:
            stock = get_object_or_404(Stock, name=item.stock.name, sub_category=item.stock.sub_category)
            if not stock.is_deleted:
                stock.quantity += item.quantity
                stock.save()
        
        messages.success(self.request, "Sale bill has been deleted successfully")
        return super().delete(*args, **kwargs)

# Views for Purchase and Sale Bills
class PurchaseBillView(View):
    model = PurchaseBill
    template_name = "bill/purchase_bill.html"
    bill_base = "bill/bill_base.html"

    def get(self, request, billno):
        bill = PurchaseBill.objects.get(billno=billno)
        context = {
            'bill': bill,
            'items': PurchaseItem.objects.filter(billno=billno),
            'billdetails': PurchaseBillDetails.objects.get(billno=billno),
            'bill_base': self.bill_base,
            'auto_generated': bill.auto_generated  # Add auto_generated to context
        }
        return render(request, self.template_name, context)

    def post(self, request, billno):
        form = PurchaseDetailsForm(request.POST)
        if form.is_valid():
            billdetailsobj = PurchaseBillDetails.objects.get(billno=billno)
            
            billdetailsobj.eway = request.POST.get("eway")    
            billdetailsobj.veh = request.POST.get("veh")
            billdetailsobj.destination = request.POST.get("destination")
            billdetailsobj.po = request.POST.get("po")
            billdetailsobj.cgst = request.POST.get("cgst")
            billdetailsobj.sgst = request.POST.get("sgst")
            billdetailsobj.igst = request.POST.get("igst")
            billdetailsobj.cess = request.POST.get("cess")
            billdetailsobj.tcs = request.POST.get("tcs")
            billdetailsobj.total = request.POST.get("total")

            billdetailsobj.save()
            messages.success(request, "Bill details have been modified successfully")
        
        context = {
            'bill': PurchaseBill.objects.get(billno=billno),
            'items': PurchaseItem.objects.filter(billno=billno),
            'billdetails': PurchaseBillDetails.objects.get(billno=billno),
            'bill_base': self.bill_base,
        }
        return render(request, self.template_name, context)

class SaleBillView(View):
    model = SaleBill
    template_name = "bill/sale_bill.html"
    bill_base = "bill/bill_base.html"
    
    def get(self, request, billno):
        context = {
            'bill': SaleBill.objects.get(billno=billno),
            'items': SaleItem.objects.filter(billno=billno),
            'billdetails': SaleBillDetails.objects.get(billno=billno),
            'bill_base': self.bill_base,
        }
        return render(request, self.template_name, context)

    def post(self, request, billno):
        form = SaleDetailsForm(request.POST)
        if form.is_valid():
            billdetailsobj = SaleBillDetails.objects.get(billno=billno)
            
            billdetailsobj.eway = request.POST.get("eway")    
            billdetailsobj.veh = request.POST.get("veh")
            billdetailsobj.destination = request.POST.get("destination")
            billdetailsobj.po = request.POST.get("po")
            billdetailsobj.cgst = request.POST.get("cgst")
            billdetailsobj.sgst = request.POST.get("sgst")
            billdetailsobj.igst = request.POST.get("igst")
            billdetailsobj.cess = request.POST.get("cess")
            billdetailsobj.tcs = request.POST.get("tcs")
            billdetailsobj.total = request.POST.get("total")

            billdetailsobj.save()
            messages.success(request, "Bill details have been modified successfully")
        
        context = {
            'bill': SaleBill.objects.get(billno=billno),
            'items': SaleItem.objects.filter(billno=billno),
            'billdetails': SaleBillDetails.objects.get(billno=billno),
            'bill_base': self.bill_base,
        }
        return render(request, self.template_name, context)

# Product Details View for Sales data
class ProductDetailsView(View):
    template_name = 'sales/product_details.html'

    def get(self, request, product_name):
        # Retrieve the product's sales data from the database
        sales_data = SaleItem.objects.filter(stock__name=product_name)

        # Aggregate sales data by month
        aggregated_data = defaultdict(int)
        for sale in sales_data:
            month_year = sale.billno.time.strftime('%Y-%m')  # Extract month and year
            aggregated_data[month_year] += sale.quantity

        # Prepare data for graph
        months = []
        monthly_sales_data = []
        current_month = datetime.now().replace(day=1)  # Start from the beginning of the current month
        for i in range(6):
            month_year = current_month.strftime('%Y-%m')
            months.append(current_month.strftime('%b %Y'))
            monthly_sales_data.append(aggregated_data[month_year])
            current_month -= timedelta(days=1)

        # Prepare context data for rendering template
        context = {
            'product_name': product_name,
            'months': months[::-1],  # Reverse the list to display in ascending order
            'monthly_sales_data': monthly_sales_data[::-1],  # Reverse the list
        }

        return render(request, self.template_name, context)

@receiver(post_save, sender=Stock)
def check_inventory_and_create_purchase_order(sender, instance, created, **kwargs):
    if created:
        # New product added, no need to check inventory
        return

    # Check if the quantity is below the threshold
    if instance.quantity < THRESHOLD_QUANTITY:
        # Print the actual cost from the Stock instance for debugging
        print(f"Stock instance cost: {instance.cost}")
        
        # Get the first available supplier
        supplier = Supplier.objects.filter(is_deleted=False).first()
        if supplier:
            # Calculate the quantity to order
            quantity_to_order = THRESHOLD_QUANTITY - instance.quantity + EXCESS_QUANTITY

            # Create a new purchase order and set auto_generated to True
            new_purchase_order = PurchaseBill.objects.create(
                supplier=supplier,
                auto_generated=True
            )

            # Create purchase bill details
            PurchaseBillDetails.objects.create(billno=new_purchase_order)
            print(f"Stock instance cost: {instance.cost}")
            perprice = instance.cost
            totalprice = quantity_to_order * perprice


            # Create a purchase item using the actual cost from the Stock instance
            purchase_item = PurchaseItem.objects.create(
                billno=new_purchase_order,
                stock=instance,
                perprice=perprice,  # Set perprice to the actual cost from the Stock instance
                quantity=quantity_to_order,
                totalprice = totalprice,
            )
            # Update stock quantity
            instance.quantity += quantity_to_order
            instance.save()
