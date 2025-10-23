from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class Profile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    email = models.EmailField(max_length=254, null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    is_seller = models.BooleanField(default=False)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wallet of {self.user.username}"


class Remittance(models.Model):
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdraw', 'Withdraw'),
        ('purchase', 'Purchase'),
        ('refund', 'Refund'),
    ]
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="remittances")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount}"


class Shop(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shops")
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='shop_logos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class Product(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name", "category"], name="unique_product_per_category")
        ]

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class Goods(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="goods")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="goods")
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} - {self.shop.name}"

    class Meta:
        verbose_name_plural = "Goods"


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating} stars)"


class OrderMaster(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_address = models.TextField()
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"

    def calculate_total(self):
        total = sum(detail.price * detail.quantity for detail in self.details.all())
        self.total_amount = total
        self.save()
        return total


class OrderDetails(models.Model):
    order = models.ForeignKey(OrderMaster, on_delete=models.CASCADE, related_name="details")
    goods = models.ForeignKey(Goods, on_delete=models.CASCADE, related_name="orderdetails")
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order.id} - {self.goods.product.name} x{self.quantity}"

    class Meta:
        verbose_name_plural = "Order Details"


class SalesRecord(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="sales_records")
    order_detail = models.ForeignKey(OrderDetails, on_delete=models.CASCADE, related_name="sales_record")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sales_records")
    quantity_sold = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2)
    profit_margin = models.DecimalField(max_digits=12, decimal_places=2)
    sale_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.shop.name} - {self.product.name} x{self.quantity_sold} on {self.sale_date}"
    
    class Meta:
        verbose_name_plural = "Sales Records"
        ordering = ['-sale_date']


def get_shop_sales_methods():
    def get_sales_records(self, time_filter=None):
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        now = timezone.now()
        
        if time_filter == 'hour':
            start_time = now - timedelta(hours=1)
        elif time_filter == 'day':
            start_time = now - timedelta(days=1)
        elif time_filter == 'week':
            start_time = now - timedelta(weeks=1)
        elif time_filter == 'month':
            start_time = now - timedelta(days=30)
        elif time_filter == 'year':
            start_time = now - timedelta(days=365)
        else:
            start_time = None
        
        queryset = self.sales_records.all()
        if start_time:
            queryset = queryset.filter(sale_date__gte=start_time)
        
        return queryset
    
    def get_total_revenue(self, time_filter=None):
        sales_records = self.get_sales_records(time_filter)
        return sales_records.aggregate(
            total=models.Sum('total_revenue')
        )['total'] or 0
    
    def get_total_profit(self, time_filter=None):
        sales_records = self.get_sales_records(time_filter)
        return sales_records.aggregate(
            total=models.Sum('profit_margin')
        )['total'] or 0
    
    def get_sales_count(self, time_filter=None):
        return self.get_sales_records(time_filter).count()
    
    def get_top_selling_products(self, time_filter=None, limit=5):
        from django.db.models import Sum
        sales_records = self.get_sales_records(time_filter)
        return sales_records.values('product__name').annotate(
            total_quantity=Sum('quantity_sold'),
            total_revenue=Sum('total_revenue')
        ).order_by('-total_quantity')[:limit]
    
    def get_profit_margin_percentage(self, time_filter=None):
        total_revenue = self.get_total_revenue(time_filter)
        total_profit = self.get_total_profit(time_filter)
        
        if total_revenue > 0:
            return (total_profit / total_revenue) * 100
        return 0
    
    return {
        'get_sales_records': get_sales_records,
        'get_total_revenue': get_total_revenue,
        'get_total_profit': get_total_profit,
        'get_sales_count': get_sales_count,
        'get_top_selling_products': get_top_selling_products,
        'get_profit_margin_percentage': get_profit_margin_percentage,
    }


for method_name, method in get_shop_sales_methods().items():
    setattr(Shop, method_name, method)


@receiver(post_save, sender=User)
def create_user_profile_and_wallet(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance, email=getattr(instance, 'email', None))
        Wallet.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        if not instance.profile.email and getattr(instance, 'email', None):
            instance.profile.email = instance.email
            instance.profile.save()
