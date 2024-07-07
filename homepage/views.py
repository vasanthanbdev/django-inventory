from django.shortcuts import render
from django.views.generic import View, TemplateView
from inventory.models import Stock
from transactions.models import SaleBill, PurchaseBill,  Supplier, PurchaseBillDetails, PurchaseItem, SaleBillDetails, SaleItem

class HomeView(View):
    template_name = "home.html"

    def get(self, request):
        selected_product = request.GET.get('product', '')
        selected_data = request.GET.get('data', 'quantity')  # Default to 'quantity' if not specified

        labels = []
        quantity_data = []
        cost_data = []  # Add this line for cost data
        sales_data = []

        stock_queryset = Stock.objects.filter(is_deleted=False).order_by('-quantity')

        if selected_product:
            stock_queryset = stock_queryset.filter(name=selected_product)

        for item in stock_queryset:
            labels.append(f"{item.name} ({item.sub_category})" if item.sub_category else item.name)
            quantity_data.append(float(item.quantity) if selected_data == 'quantity' else 0)  # Convert Decimal to float
            cost_data.append(float(item.cost) if selected_data == 'quantity' else 0)  # Convert Decimal to float
            sales_data.append(float(item.total_sales_value) if selected_data == 'quantity' else 0)

        sales = SaleBill.objects.order_by('-time')[:3]
        purchases = PurchaseBill.objects.order_by('-time')[:3]

        context = {
            'labels': labels,
            'data': quantity_data,
            'cost_data': cost_data,  # Add this line for cost data
            'sales_data': sales_data,
            'sales': sales,
            'purchases': purchases,
            'product_items': Stock.objects.filter(is_deleted=False).values('name').distinct(),
            'selected_product': selected_product,
            'selected_data': selected_data,
        }
        return render(request, self.template_name, context)





class AboutView(TemplateView):
    template_name = "about.html"


from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # Redirect to login page after successful signup
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
# from .models import YourModel

@login_required
def clear_data(request):
    if request.method == 'POST':
        try:
            # Delete all data from the backend
            Stock.objects.all().delete()
            SaleBill.objects.all().delete()
            PurchaseBill.objects.all().delete()
            Supplier.objects.all().delete()
            PurchaseItem.objects.all().delete()
            PurchaseBillDetails.objects.all().delete()
            SaleBillDetails.objects.all().delete()
            SaleItem.objects.all().delete()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        # Handle GET request or other methods if needed
        return JsonResponse({"error": "Method not allowed."}, status=405)

