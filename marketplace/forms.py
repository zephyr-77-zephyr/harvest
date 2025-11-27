from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Product, Review, UserProfile

User = get_user_model()


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    account_type = forms.ChoiceField(
        choices=(("buyer", "Buyer"), ("seller", "Seller")),
        widget=forms.RadioSelect,
        initial="buyer",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "account_type")

    def save(self, commit=True):
        user = super().save(commit=commit)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.is_seller = self.cleaned_data["account_type"] == "seller"
            profile.save()
        return user


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ("category", "name", "description", "price", "stock", "image", "is_featured")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4, "class": "w-full p-2 border rounded-lg"}),
            "category": forms.Select(attrs={"class": "w-full p-2 border rounded-lg"}),
            "name": forms.TextInput(attrs={"class": "w-full p-2 border rounded-lg"}),
            "price": forms.NumberInput(attrs={"class": "w-full p-2 border rounded-lg", "step": "0.01"}),
            "stock": forms.NumberInput(attrs={"class": "w-full p-2 border rounded-lg"}),
            "image": forms.FileInput(attrs={"class": "w-full p-2 border rounded-lg"}),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("rating", "comment")
        widgets = {
            "rating": forms.NumberInput(attrs={"min": 1, "max": 5}),
            "comment": forms.Textarea(attrs={"rows": 3}),
        }


from .models import Order

class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    shipping_address = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))
    contact_number = forms.CharField(max_length=30)
    payment_method = forms.ChoiceField(
        choices=Order.PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect(),
        initial=Order.PAYMENT_METHOD_CASH
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_method'].widget.attrs.update({
            'class': 'space-y-3'
        })

