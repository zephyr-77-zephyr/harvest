from .models import Cart, Category, UserProfile


def global_context(request):
    categories = Category.objects.all()
    cart_count = 0
    profile = None
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_count = cart.total_items
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            profile = None
    return {"nav_categories": categories, "cart_item_count": cart_count, "user_profile": profile}

