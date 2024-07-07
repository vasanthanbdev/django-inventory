from django.urls import path
from . import views

urlpatterns = [
    path('', views.StockListView.as_view(), name='inventory'),
    path('new', views.StockCreateView.as_view(), name='new-stock'),
    path('stock/<pk>/edit', views.StockUpdateView.as_view(), name='edit-stock'),
    path('stock/<pk>/delete', views.StockDeleteView.as_view(), name='delete-stock'),
    path('reorder-products/', views.ReorderProductsView.as_view(), name='reorder-products'),
    path('editable-table/', views.EditableTableView.as_view(), name='editable-table'),
    path('product-table/<int:product_id>/', views.ProductTableView.as_view(), name='product-table'),
     path('editable-table/<int:pk>/', views.EditableTableView.as_view(), name='editable-table'),
]
