from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from store.models import Category, Product, Shop, Goods, Wallet, OrderMaster, OrderDetails, Remittance, Favorite, Review, Profile
from store.category_seed import ALL_CATEGORIES, CATEGORY_SIMILARITY_MAP
import random
from datetime import datetime, timedelta
import decimal

from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Generate comprehensive historical data from Jan 2024 to Sep 2025'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=50,
            help='Number of users to create'
        )
        parser.add_argument(
            '--shops',
            type=int,
            default=20,
            help='Number of shops to create'
        )
        parser.add_argument(
            '--products',
            type=int,
            default=100,
            help='Number of products to create'
        )
        parser.add_argument(
            '--orders',
            type=int,
            default=200,
            help='Number of orders to create'
        )

    def handle(self, *args, **options):
        self.stdout.write('Generating comprehensive historical data...')
        
        for name in ALL_CATEGORIES:
            Category.objects.get_or_create(name=name, defaults={'description': f'{name} category'})
        
        with transaction.atomic():
            categories = self.create_categories()
            
            products = self.create_products(categories, options['products'])
            
            users = self.create_users(options['users'])
            
            shops = self.create_shops(users, options['shops'])
            
            goods_list = self.create_goods(products, shops)
            
            self.create_historical_orders(users, goods_list, options['orders'])
            
            self.create_user_activity(users, products)
            
        self.stdout.write(
            self.style.SUCCESS('Successfully generated comprehensive historical data!')
        )
        self.stdout.write(f'Created: {len(users)} users, {len(shops)} shops, {len(products)} products, {options["orders"]} orders')

    def create_categories(self):
        categories_data = [
            {'name': 'Electronics', 'description': 'Electronic devices and gadgets'},
            {'name': 'Clothing', 'description': 'Fashion and apparel'},
            {'name': 'Books', 'description': 'Books and literature'},
            {'name': 'Home & Garden', 'description': 'Home improvement and gardening'},
            {'name': 'Sports', 'description': 'Sports equipment and accessories'},
            {'name': 'Beauty', 'description': 'Beauty and personal care'},
            {'name': 'Toys & Games', 'description': 'Toys and entertainment'},
            {'name': 'Automotive', 'description': 'Car parts and accessories'},
            {'name': 'Health', 'description': 'Health and wellness products'},
            {'name': 'Food & Beverages', 'description': 'Food and drink items'},
        ]
        
        categories = []
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            categories.append(category)
            if created:
                self.stdout.write(f'Created category: {category.name}')
        
        return categories

    def create_products(self, categories, num_products):
        product_templates = [
            {'name': 'Smartphone', 'category': 'Electronics', 'price_range': (200, 800)},
            {'name': 'Laptop', 'category': 'Electronics', 'price_range': (500, 1500)},
            {'name': 'Headphones', 'category': 'Electronics', 'price_range': (50, 300)},
            {'name': 'Tablet', 'category': 'Electronics', 'price_range': (300, 800)},
            {'name': 'Smartwatch', 'category': 'Electronics', 'price_range': (100, 400)},
            
            {'name': 'T-Shirt', 'category': 'Clothing', 'price_range': (15, 50)},
            {'name': 'Jeans', 'category': 'Clothing', 'price_range': (40, 120)},
            {'name': 'Dress', 'category': 'Clothing', 'price_range': (60, 200)},
            {'name': 'Shoes', 'category': 'Clothing', 'price_range': (80, 250)},
            {'name': 'Jacket', 'category': 'Clothing', 'price_range': (100, 300)},
            
            {'name': 'Programming Book', 'category': 'Books', 'price_range': (30, 80)},
            {'name': 'Novel', 'category': 'Books', 'price_range': (15, 40)},
            {'name': 'Cookbook', 'category': 'Books', 'price_range': (25, 60)},
            {'name': 'Self-Help Book', 'category': 'Books', 'price_range': (20, 50)},
            {'name': 'Textbook', 'category': 'Books', 'price_range': (50, 150)},
            
            {'name': 'Garden Tools Set', 'category': 'Home & Garden', 'price_range': (50, 150)},
            {'name': 'Kitchen Appliances', 'category': 'Home & Garden', 'price_range': (80, 300)},
            {'name': 'Furniture', 'category': 'Home & Garden', 'price_range': (200, 800)},
            {'name': 'Lighting', 'category': 'Home & Garden', 'price_range': (30, 120)},
            {'name': 'Storage Solutions', 'category': 'Home & Garden', 'price_range': (40, 200)},
            
            {'name': 'Basketball', 'category': 'Sports', 'price_range': (20, 80)},
            {'name': 'Running Shoes', 'category': 'Sports', 'price_range': (60, 200)},
            {'name': 'Yoga Mat', 'category': 'Sports', 'price_range': (25, 80)},
            {'name': 'Dumbbells Set', 'category': 'Sports', 'price_range': (50, 150)},
            {'name': 'Bicycle', 'category': 'Sports', 'price_range': (300, 1000)},
            
            {'name': 'Skincare Set', 'category': 'Beauty', 'price_range': (40, 120)},
            {'name': 'Makeup Kit', 'category': 'Beauty', 'price_range': (30, 100)},
            {'name': 'Hair Care Products', 'category': 'Beauty', 'price_range': (20, 80)},
            {'name': 'Perfume', 'category': 'Beauty', 'price_range': (50, 200)},
            {'name': 'Beauty Tools', 'category': 'Beauty', 'price_range': (15, 60)},
            
            {'name': 'Board Game', 'category': 'Toys & Games', 'price_range': (25, 80)},
            {'name': 'Puzzle', 'category': 'Toys & Games', 'price_range': (15, 50)},
            {'name': 'Action Figure', 'category': 'Toys & Games', 'price_range': (20, 60)},
            {'name': 'Educational Toy', 'category': 'Toys & Games', 'price_range': (30, 100)},
            {'name': 'Video Game', 'category': 'Toys & Games', 'price_range': (40, 80)},
            
            {'name': 'Car Accessories', 'category': 'Automotive', 'price_range': (30, 150)},
            {'name': 'Car Care Products', 'category': 'Automotive', 'price_range': (20, 80)},
            {'name': 'Car Electronics', 'category': 'Automotive', 'price_range': (100, 400)},
            {'name': 'Car Parts', 'category': 'Automotive', 'price_range': (50, 300)},
            {'name': 'Car Safety Equipment', 'category': 'Automotive', 'price_range': (40, 200)},
            
            {'name': 'Vitamins', 'category': 'Health', 'price_range': (20, 80)},
            {'name': 'Fitness Equipment', 'category': 'Health', 'price_range': (100, 500)},
            {'name': 'Medical Supplies', 'category': 'Health', 'price_range': (30, 150)},
            {'name': 'Wellness Products', 'category': 'Health', 'price_range': (25, 100)},
            {'name': 'Health Monitor', 'category': 'Health', 'price_range': (80, 300)},
            
            {'name': 'Organic Food', 'category': 'Food & Beverages', 'price_range': (10, 50)},
            {'name': 'Beverages', 'category': 'Food & Beverages', 'price_range': (5, 30)},
            {'name': 'Snacks', 'category': 'Food & Beverages', 'price_range': (8, 25)},
            {'name': 'Cooking Ingredients', 'category': 'Food & Beverages', 'price_range': (15, 60)},
            {'name': 'Gourmet Food', 'category': 'Food & Beverages', 'price_range': (20, 100)},
        ]
        
        products = []
        for i in range(num_products):
            template = random.choice(product_templates)
            category = next(cat for cat in categories if cat.name == template['category'])
            
            variations = ['Premium', 'Standard', 'Basic', 'Pro', 'Lite', 'Deluxe', 'Classic', 'Modern']
            variation = random.choice(variations)
            product_name = f"{variation} {template['name']}"
            
            product, created = Product.objects.get_or_create(
                name=product_name,
                category=category,
                defaults={
                    'description': f'High-quality {template["name"].lower()} for your needs.',
                    'created_at': timezone.make_aware(self.random_date_between('2024-01-01', '2025-09-01'))
                }
            )
            products.append(product)
            if created:
                self.stdout.write(f'Created product: {product.name}')
        
        return products

    def create_users(self, num_users):
        users = []
        first_names = ['John', 'Jane', 'Mike', 'Sarah', 'David', 'Lisa', 'Tom', 'Emma', 'Chris', 'Anna', 
                      'Alex', 'Maria', 'James', 'Sophie', 'Robert', 'Olivia', 'William', 'Ava', 'Daniel', 'Isabella']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 
                     'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas']
        
        for i in range(num_users):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            username = f"{first_name.lower()}{last_name.lower()}{i+1}"
            email = f"{username}@example.com"
            
            is_seller = random.choice([True, False, False, False])  # 25% chance of being seller
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'date_joined': timezone.make_aware(self.random_date_between('2024-01-01', '2025-09-01'))
                }
            )
            
            if created:
                user.set_password('password123')
                user.save()
                profile, _ = Profile.objects.get_or_create(user=user)
                profile.is_seller = is_seller
                profile.phone = f"+1{random.randint(1000000000, 9999999999)}"
                profile.city = random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose'])
                profile.address = f"{random.randint(100, 9999)} {random.choice(['Main St', 'Oak Ave', 'Pine Rd', 'Elm St', 'Maple Dr'])}"
                profile.save()
                
                wallet = Wallet.objects.create(user=user, balance=decimal.Decimal(str(random.uniform(0, 1000))))
                if random.random() > 0.3:  # 70% chance of having some balance
                    Remittance.objects.create(
                        wallet=wallet,
                        amount=wallet.balance,
                        transaction_type='deposit',
                        description='Initial deposit'
                    )
            
            users.append(user)
            if created:
                self.stdout.write(f'Created user: {user.username} (Seller: {is_seller})')
        
        return users

    def create_shops(self, users, num_shops):
        sellers = [user for user in users if hasattr(user, 'profile') and user.profile.is_seller]
        if len(sellers) < num_shops:
            non_sellers = [user for user in users if not (hasattr(user, 'profile') and user.profile.is_seller)]
            for i in range(min(num_shops - len(sellers), len(non_sellers))):
                profile, _ = Profile.objects.get_or_create(user=non_sellers[i])
                profile.is_seller = True
                profile.save()
                sellers.append(non_sellers[i])
        
        shop_names = [
            'Tech Haven', 'Fashion Forward', 'Book Corner', 'Home Essentials', 'Sports Zone',
            'Beauty Boutique', 'Toy World', 'Auto Parts Plus', 'Health First', 'Fresh Foods',
            'Digital Dreams', 'Style Studio', 'Literary Lounge', 'Garden Paradise', 'Fitness Factory',
            'Glamour Gallery', 'Play Palace', 'Car Care Center', 'Wellness Warehouse', 'Taste Town'
        ]
        
        shops = []
        for i in range(min(num_shops, len(sellers))):
            shop_name = shop_names[i] if i < len(shop_names) else f"Shop {i+1}"
            owner = sellers[i]
            
            shop, created = Shop.objects.get_or_create(
                name=shop_name,
                owner=owner,
                defaults={
                    'description': f'Your trusted source for quality products.',
                    'is_active': True,
                    'created_at': timezone.make_aware(self.random_date_between('2024-01-01', '2025-09-01'))
                }
            )
            shops.append(shop)
            if created:
                self.stdout.write(f'Created shop: {shop.name} (Owner: {owner.username})')
        
        return shops

    def create_goods(self, products, shops):
        goods_list = []
        
        for shop in shops:
            num_products = random.randint(3, 8)
            shop_products = random.sample(products, min(num_products, len(products)))
            
            for product in shop_products:
                base_price = decimal.Decimal(str(random.uniform(20, 500)))
                purchase_price = base_price * decimal.Decimal('0.6')  # 60% of selling price
                selling_price = base_price
                stock = random.randint(5, 100)
                
                goods, created = Goods.objects.get_or_create(
                    product=product,
                    shop=shop,
                    defaults={
                        'purchase_price': purchase_price,
                        'selling_price': selling_price,
                        'stock': stock,
                        'is_available': True,
                        'created_at': timezone.make_aware(self.random_date_between('2024-01-01', '2025-09-01'))
                    }
                )
                goods_list.append(goods)
                if created:
                    self.stdout.write(f'Created goods: {product.name} in {shop.name}')
        
        return goods_list

    def create_historical_orders(self, users, goods_list, num_orders):
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2025, 9, 1)
        
        for i in range(num_orders):
            order_date = start_date + timedelta(
                days=random.randint(0, (end_date - start_date).days)
            )
            
            user = random.choice(users)
            
            order = OrderMaster.objects.create(
                user=user,
                order_date=timezone.make_aware(order_date),
                status=random.choice(['pending', 'confirmed', 'shipped', 'delivered']),
                shipping_address=f"{random.randint(100, 9999)} {random.choice(['Main St', 'Oak Ave', 'Pine Rd', 'Elm St', 'Maple Dr'])}, {random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'])}",
                notes=random.choice(['', 'Please deliver in the morning', 'Handle with care', 'Leave at front door', '']),
                total_amount=0
            )
            
            num_items = random.randint(1, 4)
            order_items = random.sample(goods_list, min(num_items, len(goods_list)))
            total_amount = decimal.Decimal('0.00')
            
            for goods in order_items:
                if goods.stock <= 0:
                    continue
                    
                quantity = random.randint(1, min(3, goods.stock))
                price = goods.selling_price
                
                OrderDetails.objects.create(
                    order=order,
                    goods=goods,
                    quantity=quantity,
                    price=price
                )
                
                total_amount += price * decimal.Decimal(str(quantity))
                
                goods.stock -= quantity
                if goods.stock <= 0:
                    goods.is_available = False
                goods.save()
            
            order.total_amount = total_amount
            order.save()
            
            if order.status in ['confirmed', 'shipped', 'delivered']:
                wallet = user.wallet
                if wallet.balance >= total_amount:
                    wallet.balance -= total_amount
                    wallet.save()
                    
                    Remittance.objects.create(
                        wallet=wallet,
                        amount=total_amount,
                        transaction_type='purchase',
                        description=f'Payment for order #{order.id}'
                    )
            
            if i % 50 == 0:
                self.stdout.write(f'Created {i+1} orders...')

    def create_user_activity(self, users, products):
        for user in users:
            num_favorites = random.randint(0, 5)
            favorite_products = random.sample(products, min(num_favorites, len(products)))
            
            for product in favorite_products:
                Favorite.objects.get_or_create(
                    user=user,
                    product=product,
                    defaults={'created_at': timezone.make_aware(self.random_date_between('2024-01-01', '2025-09-01'))}
                )
        
        for product in products:
            num_reviews = random.randint(0, 8)
            reviewers = random.sample(users, min(num_reviews, len(users)))
            
            for user in reviewers:
                Review.objects.get_or_create(
                    user=user,
                    product=product,
                    defaults={
                        'rating': random.randint(1, 5),
                        'comment': random.choice([
                            'Great product!', 'Good quality', 'Fast delivery', 'As expected', 
                            'Could be better', 'Excellent service', 'Highly recommended', 'Good value for money'
                        ]),
                        'created_at': timezone.make_aware(self.random_date_between('2024-01-01', '2025-09-01'))
                    }
                )

    def random_date_between(self, start_date_str, end_date_str):
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        
        time_between_dates = end_date - start_date
        days_between_dates = time_between_dates.days
        random_number_of_days = random.randrange(days_between_dates)
        random_date = start_date + timedelta(days=random_number_of_days)
        
        return random_date 