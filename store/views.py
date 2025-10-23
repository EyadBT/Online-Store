from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.models import User
from .models import Product, Category, Shop, Goods, OrderMaster, OrderDetails, Favorite, Review
from .forms import ShopForm, ProductForm, GoodsForm, CheckoutForm, AddGoodsToShopForm
from .category_seed import ALL_CATEGORIES
from django.utils import timezone
from django.db import models
from . import recommender
from .hybrid_recommender import get_hybrid_recommendations
from .fp_recommender import get_fp_recommendations_for_product
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .recommender import recommend_from_shared_category, recommend_from_new_category,get_cluster_stats
from store.expert_recommender import TrendingEngine, TimePeriod, Recommendation
from .fp_recommender import get_fp_recommendations_for_product
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from . import seasonal_forecast_recommender as sfr



def home_view(request):
	if Category.objects.count() == 0:
		Category.objects.bulk_create([
			Category(name=name, description=f"{name} category") for name in ALL_CATEGORIES
		])
	
	categories = Category.objects.all()[:6]
	featured_products = Product.objects.all()[:8]
	recent_products = Product.objects.all().order_by('-created_at')[:4]
	
	context = {
		'categories': categories,
		'featured_products': featured_products,
		'recent_products': recent_products,
	}
	return render(request, 'store/home.html', context)


def product_list(request):
	products = Product.objects.all()
	categories = Category.objects.all()
	
	category_id = request.GET.get('category')
	if category_id:
		products = products.filter(category_id=category_id)
	
	search_query = request.GET.get('search')
	if search_query:
		products = products.filter(
			Q(name__icontains=search_query) | 
			Q(description__icontains=search_query)
		)
	
	sort_by = request.GET.get('sort')
	if sort_by == 'name':
		products = products.order_by('name')
	elif sort_by == 'name_desc':
		products = products.order_by('-name')
	elif sort_by == 'newest':
		products = products.order_by('-created_at')
	else:
		products = products.order_by('name')
	
	context = {
		'products': products,
		'categories': categories,
		'current_category': category_id,
		'search_query': search_query,
		'sort_by': sort_by,
	}
	return render(request, 'store/product_list.html', context)

def category_products(request, pk):
    """Display products by category"""
    category = get_object_or_404(Category, pk=pk)
    products = Product.objects.filter(category=category)
    
    context = {
        'category': category,
        'products': products,
    }
    return render(request, 'store/category_products.html', context)


@login_required
def create_shop(request):
    """Create a new shop"""
    if not hasattr(request.user, 'profile') or not request.user.profile.is_seller:
        messages.error(request, 'You must be a seller to create a shop.')
        return redirect('store:home')
    
    if request.method == 'POST':
        form = ShopForm(request.POST, request.FILES)
        if form.is_valid():
            shop = form.save(commit=False)
            shop.owner = request.user
            shop.save()
            messages.success(request, 'Shop created successfully!')
            return redirect('store:shop_detail', pk=shop.pk)
    else:
        form = ShopForm()
    
    context = {'form': form}
    return render(request, 'store/shop_form.html', context)


@login_required
def shop_detail(request, pk):
    shop = get_object_or_404(Shop, pk=pk)
    goods = Goods.objects.filter(shop=shop, is_available=True)
    
    context = {
        'shop': shop,
        'goods': goods,
    }
    return render(request, 'store/shop_detail.html', context)


@login_required
def manage_shop(request, pk):
    shop = get_object_or_404(Shop, pk=pk, owner=request.user)
    goods = Goods.objects.filter(shop=shop)
    
    context = {
        'shop': shop,
        'goods': goods,
    }
    return render(request, 'store/manage_shop.html', context)


@login_required
def shop_sales_analytics(request, pk):
    shop = get_object_or_404(Shop, pk=pk, owner=request.user)
    
    time_filter = request.GET.get('time_filter', 'all')
    valid_filters = ['all', 'hour', 'day', 'week', 'month', 'year']
    if time_filter not in valid_filters:
        time_filter = 'all'
    
    sales_records = shop.get_sales_records(time_filter if time_filter != 'all' else None)
    total_revenue = shop.get_total_revenue(time_filter if time_filter != 'all' else None)
    total_profit = shop.get_total_profit(time_filter if time_filter != 'all' else None)
    profit_margin_percentage = shop.get_profit_margin_percentage(time_filter if time_filter != 'all' else None)
    sales_count = shop.get_sales_count(time_filter if time_filter != 'all' else None)
    top_products = shop.get_top_selling_products(time_filter if time_filter != 'all' else None)
    
    for product in top_products:
        if product['total_quantity'] > 0:
            product['avg_price'] = product['total_revenue'] / product['total_quantity']
        else:
            product['avg_price'] = 0
    
    recent_sales = sales_records[:20]  # Show last 20 sales
    
    context = {
        'shop': shop,
        'time_filter': time_filter,
        'sales_records': sales_records,
        'total_revenue': total_revenue,
        'total_profit': total_profit,
        'profit_margin_percentage': profit_margin_percentage,
        'sales_count': sales_count,
        'top_products': top_products,
        'recent_sales': recent_sales,
        'valid_filters': valid_filters,
    }
    return render(request, 'store/shop_sales_analytics.html', context)





@login_required
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('store:product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)
    
    context = {'form': form, 'product': product}
    return render(request, 'store/product_form.html', context)


@login_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('store:product_list')
    
    context = {'product': product}
    return render(request, 'store/product_confirm_delete.html', context)


@login_required
def add_goods(request):
    if not hasattr(request.user, 'profile') or not request.user.profile.is_seller:
        messages.error(request, 'You must be a seller to add goods.')
        return redirect('store:home')
    
    user_shops = Shop.objects.filter(owner=request.user)
    if not user_shops.exists():
        messages.error(request, 'You need to create a shop first before adding goods.')
        return redirect('store:create_shop')
    
    if request.method == 'POST':
        form = AddGoodsToShopForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            product_action = form.cleaned_data['product_action']
            
            if product_action == 'existing':
                product = form.cleaned_data['existing_product']
            else:
                product = Product.objects.create(
                    name=form.cleaned_data['product_name'],
                    description=form.cleaned_data['product_description'],
                    category=form.cleaned_data['product_category'],
                    image=form.cleaned_data.get('product_image')
                )
                messages.success(request, f'New product "{product.name}" created successfully!')
            
            goods = Goods.objects.create(
                shop=form.cleaned_data['shop'],
                product=product,
                purchase_price=form.cleaned_data['purchase_price'],
                selling_price=form.cleaned_data['selling_price'],
                stock=form.cleaned_data['stock'],
                is_available=form.cleaned_data['is_available']
            )
            
            messages.success(request, f'Goods "{product.name}" added to your shop successfully!')
            return redirect('store:manage_shop', pk=goods.shop.pk)
    else:
        form = AddGoodsToShopForm(user=request.user)
    
    context = {
        'form': form,
        'shops': user_shops,
    }
    return render(request, 'store/add_goods_to_shop.html', context)


@login_required
def edit_goods(request, pk):
    goods = get_object_or_404(Goods, pk=pk)
    
    if goods.shop.owner != request.user:
        messages.error(request, 'You can only edit goods in your own shops.')
        return redirect('store:home')
    
    if request.method == 'POST':
        form = GoodsForm(request.POST, instance=goods)
        if form.is_valid():
            form.save()
            messages.success(request, 'Goods updated successfully!')
            return redirect('store:manage_shop', pk=goods.shop.pk)
    else:
        form = GoodsForm(instance=goods)
    
    context = {'form': form, 'goods': goods}
    return render(request, 'store/goods_form.html', context)


@login_required
def delete_goods(request, pk):
    goods = get_object_or_404(Goods, pk=pk)
    
    if goods.shop.owner != request.user:
        messages.error(request, 'You can only delete goods in your own shops.')
        return redirect('store:home')
    
    if request.method == 'POST':
        shop_pk = goods.shop.pk
        goods.delete()
        messages.success(request, 'Goods deleted successfully!')
        return redirect('store:manage_shop', pk=shop_pk)
    
    context = {'goods': goods}
    return render(request, 'store/goods_confirm_delete.html', context)


from .cart import Cart

@login_required
def cart_view(request):
    cart = Cart(request)
    return render(request, 'store/cart.html', {'cart': cart})


@login_required
def add_to_cart(request, goods_id):
    goods = get_object_or_404(Goods, id=goods_id, is_available=True)
    cart = Cart(request)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity <= goods.stock:
        cart.add(goods=goods, quantity=quantity)
        messages.success(request, f'{goods.product.name} added to cart!')
    else:
        messages.error(request, f'Only {goods.stock} units available in stock.')
    
    return redirect('store:cart')


@login_required
def remove_from_cart(request, goods_id):
    goods = get_object_or_404(Goods, id=goods_id)
    cart = Cart(request)
    cart.remove(goods)
    messages.success(request, f'{goods.product.name} removed from cart!')
    return redirect('store:cart')


@login_required
def update_cart(request, goods_id):
    goods = get_object_or_404(Goods, id=goods_id)
    cart = Cart(request)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity > 0 and quantity <= goods.stock:
        cart.add(goods=goods, quantity=quantity, override_quantity=True)
        messages.success(request, f'{goods.product.name} quantity updated!')
    else:
        messages.error(request, f'Invalid quantity. Stock available: {goods.stock}')
    
    return redirect('store:cart')


@login_required
def checkout(request):
    cart = Cart(request)
    
    if len(cart) == 0:
        messages.warning(request, 'Your cart is empty.')
        return redirect('store:cart')
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = OrderMaster.objects.create(
                user=request.user,
                shipping_address=form.cleaned_data['shipping_address'],
                notes=form.cleaned_data['notes'],
                total_amount=cart.get_total_price()
            )
            
            for item in cart:
                order_detail = OrderDetails.objects.create(
                    order=order,
                    goods=item['goods'],
                    quantity=item['quantity'],
                    price=item['total_price']
                )
                
                from .models import SalesRecord
                unit_price = item['goods'].selling_price
                total_revenue = item['total_price']
                profit_margin = total_revenue - (item['goods'].purchase_price * item['quantity'])
                
                SalesRecord.objects.create(
                    shop=item['goods'].shop,
                    order_detail=order_detail,
                    product=item['goods'].product,
                    quantity_sold=item['quantity'],
                    unit_price=unit_price,
                    total_revenue=total_revenue,
                    profit_margin=profit_margin
                )
                
                shop_owner_wallet = item['goods'].shop.owner.wallet
                shop_owner_wallet.balance += total_revenue
                shop_owner_wallet.save()
                
                from .models import Remittance
                Remittance.objects.create(
                    wallet=shop_owner_wallet,
                    amount=total_revenue,
                    transaction_type='sale',
                    description=f'Sale of {item["goods"].product.name} x{item["quantity"]} (Order #{order.id})'
                )
                
                goods = item['goods']
                goods.stock -= item['quantity']
                if goods.stock == 0:
                    goods.is_available = False
                goods.save()
            
            payment_method = form.cleaned_data['payment_method']
            if payment_method == 'wallet':
                wallet = request.user.wallet
                if wallet.balance >= cart.get_total_price():
                    wallet.balance -= cart.get_total_price()
                    wallet.save()
                    
                    from .models import Remittance
                    Remittance.objects.create(
                        wallet=wallet,
                        amount=cart.get_total_price(),
                        transaction_type='purchase',
                        description=f'Payment for order #{order.id}'
                    )
                    
                    order.status = 'confirmed'
                    order.save()
                    messages.success(request, f'Order #{order.id} placed successfully! Payment processed from wallet.')
                else:
                    order.delete()
                    messages.error(request, 'Insufficient wallet balance.')
                    return redirect('store:wallet')
            else:  # Cash on Delivery
                order.status = 'pending'
                order.save()
                messages.success(request, f'Order #{order.id} placed successfully! Pay on delivery.')
            
            cart.clear()
            
            return redirect('store:order_detail', pk=order.pk)
    else:
        form = CheckoutForm()
    
    return render(request, 'store/checkout.html', {
        'cart': cart,
        'form': form
    })


@login_required
def order_list(request):
    orders = OrderMaster.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'store/order_list.html', {'orders': orders})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(OrderMaster, pk=pk, user=request.user)
    return render(request, 'store/order_detail.html', {'order': order})


@login_required
def toggle_favorite(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, product=product)
    
    if not created:
        favorite.delete()
        messages.success(request, 'Removed from favorites!')
    else:
        messages.success(request, 'Added to favorites!')
    
    return redirect('store:product_detail', pk=product_id)


@login_required
def favorites_list(request):
    favorites = Favorite.objects.filter(user=request.user)
    return render(request, 'store/favorites.html', {'favorites': favorites})


@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if rating:
            review, created = Review.objects.get_or_create(
                user=request.user, 
                product=product,
                defaults={'rating': rating, 'comment': comment}
            )
            if not created:
                review.rating = rating
                review.comment = comment
                review.save()
            
            messages.success(request, 'Review submitted successfully!')
        else:
            messages.error(request, 'Please provide a rating.')
    
    return redirect('store:product_detail', pk=product_id)


@login_required
def wallet_view(request):
    wallet = request.user.wallet
    remittances = wallet.remittances.all().order_by('-created_at')[:10]
    
    context = {
        'wallet': wallet,
        'remittances': remittances,
    }
    return render(request, 'store/wallet.html', context)


@login_required
def deposit_money(request):
    messages.info(request, 'Deposit functionality coming soon!')
    return redirect('store:wallet')


@login_required
def withdraw_money(request):
    messages.info(request, 'Withdraw functionality coming soon!')
    return redirect('store:wallet')


@login_required
def repricing_recommendation(request, pk):

    goods = get_object_or_404(Goods, pk=pk)
    
    if goods.shop.owner != request.user:
        messages.error(request, 'You can only get recommendations for your own products.')
        return redirect('store:manage_shop', pk=goods.shop.pk)
    
    try:
        from .EYAD_pricing_experta import recommend_for_goods, apply_recommendation
        
        recommendation = recommend_for_goods(goods_id=pk, window_days=30)
        
        if request.method == 'POST':
            action = request.POST.get('action')
            if action == 'apply' and recommendation.get('action') in ('increase', 'decrease'):
                result = apply_recommendation(goods_id=pk, recommendation=recommendation, dry_run=False)
                if result['updated']:
                    messages.success(request, f'Price updated successfully! New price: ${result["new_price"]:.2f}')
                else:
                    messages.warning(request, 'No price change was applied.')
                return redirect('store:manage_shop', pk=goods.shop.pk)
        
        context = {
            'goods': goods,
            'recommendation': recommendation,
        }
        return render(request, 'store/repricing_recommendation.html', context)
        
    except ImportError as e:
        messages.error(request, f'Pricing expert system not available: {e}')
        return redirect('store:manage_shop', pk=goods.shop.pk)
    except Exception as e:
        messages.error(request, f'Error getting recommendation: {e}')
        return redirect('store:manage_shop', pk=goods.shop.pk)



@login_required
def my_recommendations(request):
    user_id = request.user.id

    same = recommend_from_shared_category(user_id, top_n=1)
    new = recommend_from_new_category(user_id, top_n=1)

    cluster_info = get_cluster_stats(user_id)

    context = {
        "same_category_recommendations": same,
        "new_category_recommendations": new,
        "cluster_info": cluster_info,
    }
    return render(request, "store/recommendations.html", context)


@login_required
def trending_products(request, period="week"):
    from store.expert_recommender import get_trending_products

    recs = get_trending_products(period=period, top_n=6)
    context = {
        "period": period,
        "recommendations": recs
    }
    return render(request, "store/trending.html", context)


@login_required
def trending_recommendations(request, period="day"):
    engine = TrendingEngine()
    engine.reset()
    engine.declare(TimePeriod(period=period))
    engine.run()

    recs = []
    label = ""
    for fact in engine.facts.values():
        if isinstance(fact, Recommendation):
            recs = fact["recommendations"]
            label = fact["label"]

    context = {
        "period": label,
        "recommendations": recs
    }
    return render(request, "store/trending_recommendations.html", context)


@login_required
def hybrid_recommendations_view(request):
    user_id = request.user.id
    recs = get_hybrid_recommendations(user_id, limit=8)
    return render(request, "store/hybrid_recommendations.html", {"recommendations": recs})





@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    goods_list = Goods.objects.filter(product=product, is_available=True)
    reviews = Review.objects.filter(product=product).order_by('-created_at')
    related_products = Product.objects.filter(category=product.category).exclude(pk=pk)[:4]

    is_favorited = False
    if request.user.is_authenticated:
        is_favorited = Favorite.objects.filter(user=request.user, product=product).exists()

    fp_recs, fp_bundles = get_fp_recommendations_for_product(request.user, pk)

    context = {
        "product": product,
        "goods_list": goods_list,
        "reviews": reviews,
        "related_products": related_products,
        "is_favorited": is_favorited,
        "fp_recommendations": fp_recs,
        "fp_bundle_offers": fp_bundles,
    }
    return render(request, "store/product_detail.html", context)

@login_required
def add_bundle_to_cart(request):
    if request.method == "POST":
        product_ids = request.POST.getlist("product_ids")
        discount = float(request.POST.get("discount", 0))
        
        cart = request.session.get("cart", {})

        for pid in product_ids:
            try:
                product = Product.objects.get(pk=pid)
                goods = Goods.objects.filter(product=product, is_available=True).first()
                if not goods:
                    continue

                price = float(goods.selling_price)
                discounted_price = price * (1 - discount / 100)

                if str(goods.id) not in cart:
                    cart[str(goods.id)] = {
                        "product_id": product.id,
                        "name": product.name,
                        "quantity": 1,
                        "price": discounted_price,
                        "original_price": price,
                        "discount": discount,
                    }
                else:
                    cart[str(goods.id)]["quantity"] += 1

            except Product.DoesNotExist:
                continue

        request.session["cart"] = cart
        request.session.modified = True

        messages.success(request, " Bundle added to cart with discount applied!")
        return redirect("store:cart")

    return redirect("store:home")


@login_required
def recommendations_view(request):
    return render(request, "store/recommendations.html", {
        "recommendations": {"same_category": [], "related_category": []},
        "cluster_info": None,
        "ai_recommendations": [],
        "bundle_recommendations": [],
        "trending_products": [],
        "user_categories": []
    })

@login_required
def test_recommendation_system(request):
    return render(request, "store/recommendations.html", {})



@login_required
def seasonal_recommendations_view(request):
    user_id = request.user.id
    recs = sfr.get_recommendations_for_user(user_id, top_n=8, horizon_days=30)

    context = {
        "recommendations": recs,
        "season": sfr.get_current_season(),
        "prophet_available": sfr.PROPHET_AVAILABLE,
    }
    return render(request, "store/seasonal_recommendations.html", context)
