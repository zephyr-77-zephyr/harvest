from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from rest_framework import generics

from .forms import CheckoutForm, ProductForm, ReviewForm, UserRegistrationForm
from .models import Cart, CartItem, Category, Order, OrderItem, Product, Review
from .serializers import CategorySerializer, OrderSerializer, ProductSerializer


def signup(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            raw_password = form.cleaned_data["password1"]
            authenticated_user = authenticate(username=user.username, password=raw_password)
            if authenticated_user:
                login(request, authenticated_user)
            messages.success(request, "Welcome to Harvest Helper!")
            return redirect("home")
    else:
        form = UserRegistrationForm()
    return render(request, "accounts/signup.html", {"form": form})


def home(request):
    featured_products = Product.objects.filter(is_featured=True)[:8]
    latest_products = Product.objects.all()[:12]
    return render(
        request,
        "home.html",
        {
            "featured_products": featured_products,
            "latest_products": latest_products,
        },
    )


def product_list(request):
    products = Product.objects.select_related("category", "seller")
    query = request.GET.get("q")
    category_slug = request.GET.get("category")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")

    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category_slug:
        products = products.filter(category__slug=category_slug)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    return render(
        request,
        "products/product_list.html",
        {"products": products, "active_category": category_slug, "query": query},
    )


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related("category", "seller"), slug=slug)
    reviews = product.reviews.select_related("user")
    form = ReviewForm()
    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to leave a review.")
            return redirect("login")
        form = ReviewForm(request.POST)
        if form.is_valid():
            Review.objects.update_or_create(
                product=product,
                user=request.user,
                defaults={
                    "rating": form.cleaned_data["rating"],
                    "comment": form.cleaned_data["comment"],
                },
            )
            messages.success(request, "Your review has been saved.")
            return redirect("product_detail", slug=slug)
    return render(request, "products/product_detail.html", {"product": product, "reviews": reviews, "form": form})


def _get_user_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


@login_required
def add_to_cart(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if product.stock <= 0:
        messages.error(request, "This product is currently out of stock.")
        return redirect("product_detail", slug=slug)
    cart = _get_user_cart(request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        if item.quantity >= product.stock:
            messages.warning(request, "You've added the maximum available stock.")
            return redirect("product_detail", slug=slug)
        item.quantity += 1
        item.save()
    messages.success(request, f"{product.name} added to your cart.")
    return redirect("product_detail", slug=slug)


@login_required
def view_cart(request):
    cart = _get_user_cart(request.user)
    items = cart.items.select_related("product")
    return render(request, "orders/cart.html", {"cart": cart, "items": items})


@login_required
def remove_cart_item(request, item_id):
    cart = _get_user_cart(request.user)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    item.delete()
    messages.info(request, "Item removed from cart.")
    return redirect("view_cart")


@login_required
def update_cart_item(request, item_id):
    cart = _get_user_cart(request.user)
    item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    quantity = int(request.POST.get("quantity", item.quantity))
    if quantity <= 0:
        item.delete()
    else:
        max_allowed = item.product.stock
        if quantity > max_allowed:
            quantity = max_allowed
            messages.warning(request, "Quantity adjusted based on stock availability.")
        item.quantity = quantity
        item.save()
    messages.success(request, "Cart updated.")
    return redirect("view_cart")


@login_required
def checkout(request):
    cart = _get_user_cart(request.user)
    items = cart.items.select_related("product")
    if not items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect("product_list")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(
                user=request.user,
                full_name=form.cleaned_data["full_name"],
                shipping_address=form.cleaned_data["shipping_address"],
                contact_number=form.cleaned_data["contact_number"],
                payment_method=form.cleaned_data["payment_method"],
                payment_status=Order.PAYMENT_STATUS_PAID if form.cleaned_data["payment_method"] == Order.PAYMENT_METHOD_PICKUP else Order.PAYMENT_STATUS_PENDING
            )
            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price,
                )
                item.product.stock = max(0, item.product.stock - item.quantity)
                item.product.save(update_fields=["stock"])
            cart.items.all().delete()
            order.recalculate_total()
            messages.success(request, "Order placed successfully!")
            return redirect("order_list")
    else:
        form = CheckoutForm(initial={"full_name": request.user.get_full_name()})
    return render(request, "orders/checkout.html", {"cart": cart, "items": items, "form": form})


@login_required
def order_list(request):
    orders = request.user.orders.prefetch_related("items__product")
    return render(request, "orders/order_list.html", {"orders": orders})


@login_required
def seller_dashboard(request):
    profile = getattr(request.user, "profile", None)
    if not profile or not profile.is_seller:
        messages.error(request, "Seller access required.")
        return redirect("home")

    products = request.user.products.all()
    orders = Order.objects.filter(items__product__seller=request.user).distinct()
    categories = Category.objects.all()  # Get all categories
    stats = {
        "total_products": products.count(),
        "total_orders": orders.count(),
        "total_revenue": orders.aggregate(total=Sum("total"))["total"] or 0,
    }
    
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            product.save()
            messages.success(request, "Product saved successfully!")
            return redirect("seller_dashboard")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # Initialize the form with categories
        form = ProductForm()
        # Set the category field queryset to include all categories
        form.fields['category'].queryset = Category.objects.all()
        
    return render(
        request,
        "dashboard/seller_dashboard.html",
        {
            "products": products, 
            "orders": orders, 
            "stats": stats, 
            "form": form,
            "categories": categories,  # Add categories to context
        },
    )


class ProductListAPI(generics.ListAPIView):
    queryset = Product.objects.select_related("category", "seller")
    serializer_class = ProductSerializer


class CategoryListAPI(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class OrderHistoryAPI(generics.ListAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return user.orders.prefetch_related("items__product")
        return Order.objects.none()
