from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
    Profile, Wallet, Remittance,
    Shop, Goods, Category, Product,
    Favorite, Review, OrderMaster, OrderDetails, SalesRecord
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'phone', 'country', 'city', 'is_seller', 'gender')
    list_filter = ('is_seller', 'gender', 'country')
    search_fields = ('user__username', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Remittance)
class RemittanceAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'amount', 'transaction_type', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('wallet__user__username', 'description')
    readonly_fields = ('created_at',)


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'owner__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Goods)
class GoodsAdmin(admin.ModelAdmin):
    list_display = ('product', 'shop', 'purchase_price', 'selling_price', 'stock', 'is_available')
    list_filter = ('is_available', 'shop', 'product__category')
    search_fields = ('product__name', 'shop__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'product__name')
    readonly_fields = ('created_at',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'product__name', 'comment')
    readonly_fields = ('created_at', 'updated_at')


class OrderDetailsInline(admin.TabularInline):
    model = OrderDetails
    extra = 1
    readonly_fields = ('created_at',)


@admin.register(OrderMaster)
class OrderMasterAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_amount', 'order_date')
    list_filter = ('status', 'order_date')
    search_fields = ('user__username', 'shipping_address')
    readonly_fields = ('order_date', 'total_amount')
    inlines = [OrderDetailsInline]
    
    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        if formset.model == OrderDetails:
            form.instance.calculate_total()


@admin.register(OrderDetails)
class OrderDetailsAdmin(admin.ModelAdmin):
    list_display = ('order', 'goods', 'quantity', 'price', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('order__user__username', 'goods__product__name')
    readonly_fields = ('created_at',)


@admin.register(SalesRecord)
class SalesRecordAdmin(admin.ModelAdmin):
    list_display = ('shop', 'product', 'quantity_sold', 'total_revenue', 'profit_margin', 'sale_date')
    list_filter = ('shop', 'sale_date', 'product__category')
    search_fields = ('shop__name', 'product__name', 'order_detail__order__user__username')
    readonly_fields = ('sale_date',)
    date_hierarchy = 'sale_date'
