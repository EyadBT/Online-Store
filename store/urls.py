from django.urls import path
from . import views, auth_views

app_name = 'store'

urlpatterns = [
    
    path("product/<int:pk>/", views.product_detail, name="product_detail"),
    path("recommendations/trending/<str:period>/", views.trending_recommendations, name="trending_recommendations"),
    path('recommendations/seasonal/', views.seasonal_recommendations_view, name='seasonal_recommendations'),
    path("recommendations/", views.my_recommendations, name="recommendations"),
    path("recommendations/hybrid/", views.hybrid_recommendations_view, name="hybrid_recommendations"),
    path("recommendations/fp/", views.get_fp_recommendations_for_product, name="fp_recommendations"),
    path("add-bundle-to-cart/", views.add_bundle_to_cart, name="add_bundle_to_cart"),
    
    path('register/', auth_views.register_view, name='register'),
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('profile/', auth_views.profile_view, name='profile'),
    path('dashboard/', auth_views.dashboard_view, name='dashboard'),
    
    path('check-username/', auth_views.check_username_availability, name='check_username'),
    path('check-email/', auth_views.check_email_availability, name='check_email'),
    
    path('', views.home_view, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('category/<int:pk>/', views.category_products, name='category_products'),
    
    path('shop/create/', views.create_shop, name='create_shop'),
    path('shop/<int:pk>/', views.shop_detail, name='shop_detail'),
    path('shop/<int:pk>/manage/', views.manage_shop, name='manage_shop'),
    path('shop/<int:pk>/sales/', views.shop_sales_analytics, name='shop_sales_analytics'),
    
    path('product/<int:pk>/edit/', views.edit_product, name='edit_product'),
    path('product/<int:pk>/delete/', views.delete_product, name='delete_product'),
    
    path('goods/add/', views.add_goods, name='add_goods'),
    path('goods/<int:pk>/edit/', views.edit_goods, name='edit_goods'),
    path('goods/<int:pk>/delete/', views.delete_goods, name='delete_goods'),
    path('goods/<int:pk>/reprice/', views.repricing_recommendation, name='repricing_recommendation'),
    
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:goods_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:goods_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:goods_id>/', views.update_cart, name='update_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_list, name='order_list'),
    path('order/<int:pk>/', views.order_detail, name='order_detail'),
    
    path('favorite/<int:product_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('favorites/', views.favorites_list, name='favorites'),
    path('review/<int:product_id>/', views.add_review, name='add_review'),
    
    
    path('wallet/', views.wallet_view, name='wallet'),
    path('wallet/deposit/', views.deposit_money, name='deposit_money'),
    path('wallet/withdraw/', views.withdraw_money, name='withdraw_money'),
    
    
    
]