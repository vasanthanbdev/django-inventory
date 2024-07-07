from django import forms
from .models import Stock

class StockForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'class': 'textinput form-control'})
        self.fields['quantity'].widget.attrs.update({'class': 'textinput form-control', 'min': '0'})
        self.fields['cost'].widget.attrs.update({'class': 'textinput form-control', 'min': '0'})

        # If you want to exclude reorder_point from the form, you can do:
        if 'reorder_point' in self.fields:
            del self.fields['reorder_point']

    class Meta:
        model = Stock
        fields = ['name', 'quantity', 'cost', 'sub_category']
