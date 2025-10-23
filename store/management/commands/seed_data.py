from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import random
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver

from store.models import Profile, Wallet, Shop, Category, Product, Goods, OrderMaster, OrderDetails, SalesRecord, Remittance

class Command(BaseCommand):
    help = 'Seed comprehensive data: 500 users, 100 stores, 200 categories, 1000 products, 1000 transactions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            self.clear_existing_data()
        
        self.stdout.write('Starting comprehensive data seeding...')
        
        try:
            self.disconnect_signals()
            
            users_count = self.create_users_and_profiles()
            
            categories_count = self.create_categories()
            
            shops_count = self.create_shops()
            
            products_count = self.create_products()
            
            goods_count = self.create_goods()
            
            transactions_count = self.create_transactions()
            
            self.reconnect_signals()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nData seeding completed successfully!\n'
                    f'Users created: {users_count}\n'
                    f'Categories created: {categories_count}\n'
                    f'Shops created: {shops_count}\n'
                    f'Products created: {products_count}\n'
                    f'Goods entries created: {goods_count}\n'
                    f'Transactions created: {transactions_count}'
                )
            )
            
        except Exception as e:
            self.reconnect_signals()
            self.stdout.write(
                self.style.ERROR(f'Error during data seeding: {e}')
            )
            import traceback
            traceback.print_exc()

    def disconnect_signals(self):
        """Temporarily disconnect signals to prevent automatic profile/wallet creation"""
        self.stdout.write('Disconnecting signals...')
        post_save.disconnect(receiver=None, sender=User, dispatch_uid='create_user_profile_and_wallet')
        post_save.disconnect(receiver=None, sender=User, dispatch_uid='save_user_profile')

    def reconnect_signals(self):
        """Reconnect signals after seeding"""
        self.stdout.write('Reconnecting signals...')

    def clear_existing_data(self):
        """Clear existing data using raw SQL to handle constraints"""
        from django.db import connection
        
        self.stdout.write('Clearing all data using raw SQL...')
        
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA foreign_keys=OFF;")
            
            tables = [
                'store_salesrecord',
                'store_orderdetails', 
                'store_ordermaster',
                'store_goods',
                'store_product',
                'store_shop',
                'store_category',
                'store_remittance',
                'store_wallet',
                'store_profile',
                'auth_user'
            ]
            
            for table in tables:
                try:
                    cursor.execute(f"DELETE FROM {table};")
                    self.stdout.write(f"Cleared {table}")
                except Exception as e:
                    self.stdout.write(f"Error clearing {table}: {e}")
            
            cursor.execute("PRAGMA foreign_keys=ON;")
        
        self.stdout.write('All data cleared successfully!')

    def create_users_and_profiles(self):
        """Create 500 users with profiles"""
        self.stdout.write('Creating users and profiles...')
        
        users_created = 0
        for i in range(500):
            username = f"user{i+1:03d}"
            email = f"user{i+1:03d}@example.com"
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password='password123',
                first_name=f"User{i+1}",
                last_name=f"Last{i+1}"
            )
            
            profile, created = Profile.objects.get_or_create(
                user=user,
                defaults={
                    'email': email,
                    'phone': f"+1{random.randint(1000000000, 9999999999)}",
                    'country': f"Country{i % 100}",
                    'city': f"City{i % 100}",
                    'address': f"Address {i % 1000}",
                    'is_seller': random.choice([True, False]),
                    'gender': random.choice(['male', 'female'])
                }
            )
            
            wallet, created = Wallet.objects.get_or_create(
                user=user,
                defaults={'balance': Decimal(random.uniform(1000, 10000))}
            )
            
            users_created += 1
            if users_created % 50 == 0:
                self.stdout.write(f"Created {users_created} users...")
        
        self.stdout.write(f"Created {users_created} users with profiles and wallets")
        return users_created

    def create_categories(self):
        """Create 200 categories"""
        self.stdout.write('Creating categories...')
        
        categories_created = 0
        for i in range(200):
            category = Category.objects.create(
                name=f"Category {i+1}",
                description=f"Description for Category {i+1}"
            )
            categories_created += 1
        
        self.stdout.write(f"Created {categories_created} categories")
        return categories_created

    def create_shops(self):
        """Create 100 shops owned by seller users"""
        self.stdout.write('Creating shops...')
        
        seller_profiles = Profile.objects.filter(is_seller=True)
        if seller_profiles.count() < 100:
            additional_sellers_needed = 100 - seller_profiles.count()
            non_seller_profiles = Profile.objects.filter(is_seller=False)[:additional_sellers_needed]
            for profile in non_seller_profiles:
                profile.is_seller = True
                profile.save()
            seller_profiles = Profile.objects.filter(is_seller=True)
        
        shops_created = 0
        for i in range(100):
            profile = seller_profiles[i]
            shop = Shop.objects.create(
                owner=profile.user,
                name=f"Shop {i+1}",
                description=f"Description for Shop {i+1}",
                is_active=True
            )
            shops_created += 1
        
        self.stdout.write(f"Created {shops_created} shops")
        return shops_created

    def create_products(self):
        """Create 1000 products across different categories"""
        self.stdout.write('Creating products...')
        
        categories = list(Category.objects.all())
        products_created = 0
        
        for i in range(1000):
            category = random.choice(categories)
            product = Product.objects.create(
                name=f"Product {i+1}",
                description=f"Description for Product {i+1}",
                category=category
            )
            products_created += 1
            
            if products_created % 100 == 0:
                self.stdout.write(f"Created {products_created} products...")
        
        self.stdout.write(f"Created {products_created} products")
        return products_created

    def create_goods(self):
        """Create goods entries for products in shops with quantities >= 1"""
        self.stdout.write('Creating goods entries...')
        
        shops = list(Shop.objects.all())
        products = list(Product.objects.all())
        goods_created = 0
        
        for i in range(1000):
            shop = random.choice(shops)
            product = products[i % len(products)]
            
            purchase_price = Decimal(random.uniform(10, 200))
            selling_price = purchase_price * Decimal(random.uniform(1.2, 2.5))  # 20% to 150% markup
            stock = random.randint(1, 100)
            
            goods = Goods.objects.create(
                shop=shop,
                product=product,
                purchase_price=purchase_price,
                selling_price=selling_price,
                stock=stock,
                is_available=True
            )
            goods_created += 1
            
            if goods_created % 100 == 0:
                self.stdout.write(f"Created {goods_created} goods entries...")
        
        self.stdout.write(f"Created {goods_created} goods entries")
        return goods_created

    def create_transactions(self):
        """Create 1000 buy transactions with sufficient wallet balances"""
        self.stdout.write('Creating transactions...')
        
        goods_list = list(Goods.objects.filter(is_available=True, stock__gte=1))
        buyers = list(User.objects.all())
        
        transactions_created = 0
        max_transactions = min(1000, len(goods_list))
        
        for i in range(max_transactions):
            goods = random.choice(goods_list)
            buyer = random.choice(buyers)
            
            if not goods.is_available or goods.stock < 1:
                continue
            
            buyer_wallet = buyer.wallet
            if buyer_wallet.balance < goods.selling_price:
                buyer_wallet.balance += goods.selling_price * Decimal(2)
                buyer_wallet.save()
            
            order = OrderMaster.objects.create(
                user=buyer,
                shipping_address=f"Address {i+1}",
                notes=f"Order note {i+1}",
                total_amount=goods.selling_price,
                status='confirmed',
                order_date=timezone.now() - timedelta(days=random.randint(0, 365))
            )
            
            order_detail = OrderDetails.objects.create(
                order=order,
                goods=goods,
                quantity=1,
                price=goods.selling_price
            )
            
            profit_margin = goods.selling_price - goods.purchase_price
            sales_record = SalesRecord.objects.create(
                shop=goods.shop,
                order_detail=order_detail,
                product=goods.product,
                quantity_sold=1,
                unit_price=goods.selling_price,
                total_revenue=goods.selling_price,
                profit_margin=profit_margin,
                sale_date=order.order_date
            )
            
            buyer_wallet.balance -= goods.selling_price
            buyer_wallet.save()
            
            shop_owner_wallet = goods.shop.owner.wallet
            shop_owner_wallet.balance += goods.selling_price
            shop_owner_wallet.save()
            
            Remittance.objects.create(
                wallet=buyer_wallet,
                amount=goods.selling_price,
                transaction_type='purchase',
                description=f'Purchase of {goods.product.name} from {goods.shop.name}'
            )
            
            Remittance.objects.create(
                wallet=shop_owner_wallet,
                amount=goods.selling_price,
                transaction_type='sale',
                description=f'Sale of {goods.product.name} to {buyer.username}'
            )
            
            goods.stock = max(0, goods.stock - 1)
            if goods.stock == 0:
                goods.is_available = False
            goods.save()
            
            transactions_created += 1
            
            if transactions_created % 100 == 0:
                self.stdout.write(f"Created {transactions_created} transactions...")
        
        self.stdout.write(f"Created {transactions_created} transactions")
        return transactions_created
