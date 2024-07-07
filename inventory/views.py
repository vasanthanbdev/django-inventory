# views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import (
    View,
    CreateView, 
    UpdateView,
    TemplateView
)
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from .models import Stock
from .forms import StockForm
from django_filters.views import FilterView
from .filters import StockFilter
from django.views.generic import ListView
from .models import Stock

class StockListView(FilterView):
    filterset_class = StockFilter
    queryset = Stock.objects.filter(is_deleted=False)
    template_name = 'inventory.html'
    paginate_by = 10

class ProductTableView(TemplateView):
    template_name = 'product_table.html'

    def get_context_data(self, **kwargs):
        product_id = self.kwargs.get('product_id')
        product = get_object_or_404(Stock, pk=product_id)
        context = super().get_context_data(**kwargs)
        context['product'] = product
        return context


class ReorderProductsView(ListView):
    template_name = 'reorder.html'
    model = Stock
    context_object_name = 'reorder_products'
    REORDER_POINT = 5

    def get_queryset(self):
        # Filter out deleted items and items above the reorder point
        return Stock.objects.filter(
            is_deleted=False,
            quantity__lt=self.REORDER_POINT
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Reorder Products'
        return context
    

class StockCreateView(SuccessMessageMixin, CreateView):
    model = Stock
    form_class = StockForm
    template_name = "edit_stock.html"
    success_url = '/inventory'
    success_message = "Stock has been created successfully"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'New Stock'
        context["savebtn"] = 'Add to Inventory'
        return context

    def form_valid(self, form):
        # Set the ReorderPoint to a default value or handle it in your model's save method
        form.instance.reorder_point = 0  # Change the value accordingly
        response = super().form_valid(form)
        messages.success(self.request, self.success_message)
        return response      

class StockUpdateView(SuccessMessageMixin, UpdateView):
    model = Stock
    form_class = StockForm
    template_name = "edit_stock.html"
    success_url = '/inventory'
    success_message = "Stock has been updated successfully"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'Edit Stock'
        context["savebtn"] = 'Update Stock'
        context["delbtn"] = 'Delete Stock'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.success_message)
        return response

class StockDeleteView(View):
    template_name = "delete_stock.html"
    success_message = "Stock has been deleted successfully"

    def get(self, request, pk):
        stock = get_object_or_404(Stock, pk=pk)
        return render(request, self.template_name, {'object' : stock})

    def post(self, request, pk):  
        stock = get_object_or_404(Stock, pk=pk)
        stock.is_deleted = True
        stock.save()                                               
        messages.success(request, self.success_message)
        return redirect('inventory')

# views.py

class EditableTableView(View):
    template_name = 'editable_table.html'

    def get(self, request, pk):
        # Assuming pk is the primary key of the product
        product = Stock.objects.get(pk=pk)

        related_products = Stock.objects.filter(name=product.name)

        context = {
            'product': product,
            'related_products': related_products,
        }

        return render(request, self.template_name, context)
