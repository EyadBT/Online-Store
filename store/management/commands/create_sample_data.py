from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from store.models import Category, Product, Shop, Goods, Wallet
from store.category_seed import ALL_CATEGORIES, CATEGORY_SIMILARITY_MAP

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample data for testing the store'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        categories = []
        for name in ALL_CATEGORIES:
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={'description': f'{name} category'}
            )
            categories.append(category)
            if created:
                self.stdout.write(f'Created category: {category.name}')
        
        
        seller, created = User.objects.get_or_create(
            username='seller1',
            defaults={
                'email': 'seller1@example.com',
                'first_name': 'John',
                'last_name': 'Seller',
            }
        )
        if created:
            seller.set_password('password123')
            seller.save()
            Wallet.objects.create(user=seller)
            self.stdout.write(f'Created seller: {seller.username}')
        
        shop, created = Shop.objects.get_or_create(
            name='Tech Store',
            owner=seller,
            defaults={
                'description': 'Your one-stop shop for all things technology',
            }
        )
        if created:
            self.stdout.write(f'Created shop: {shop.name}')
        
        sample_products = [
            ('Smartphone', 'Smartphones', 'Latest smartphone with advanced features'),
            ('Laptop', 'Laptops', 'High-performance laptop for work and gaming'),
            ('T-Shirt', "Men's Clothing", 'Comfortable cotton t-shirt'),
            ('Jeans', "Men's Clothing", 'Classic blue jeans'),
            ('Python Programming Book', 'Books', 'Learn Python programming from scratch'),
            ('Garden Tools Set', 'Tools & Home Improvement', 'Complete set of essential garden tools'),
            ('Basketball', 'Sports & Outdoors', 'Professional basketball for indoor/outdoor use'),
            ('Running Shoes', 'Shoes', 'Comfortable running shoes for athletes'),
        ]

        products = []
        name_to_category = {c.name: c for c in categories}
        for pname, cname, desc in sample_products:
            category = name_to_category.get(cname) or name_to_category['Other']
            product, created = Product.objects.get_or_create(
                name=pname,
                category=category,
                defaults={'description': desc}
            )
            products.append(product)
            if created:
                self.stdout.write(f'Created product: {product.name}')
        
        goods_data = [
            {'product': 'Smartphone', 'purchase_price': 400.00, 'selling_price': 499.99, 'stock': 10},
            {'product': 'Laptop', 'purchase_price': 800.00, 'selling_price': 999.99, 'stock': 5},
            {'product': 'T-Shirt', 'purchase_price': 15.00, 'selling_price': 24.99, 'stock': 50},
            {'product': 'Jeans', 'purchase_price': 30.00, 'selling_price': 49.99, 'stock': 25},
        ]
        
        prod_by_name = {p.name: p for p in products}
        for g in goods_data:
            product = prod_by_name[g['product']]
            goods, created = Goods.objects.get_or_create(
                product=product,
                shop=shop,
                defaults={
                    'purchase_price': g['purchase_price'],
                    'selling_price': g['selling_price'],
                    'stock': g['stock'],
                }
            )
            if created:
                self.stdout.write(f'Created goods: {goods.product.name} in {goods.shop.name}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )
        self.stdout.write('Sample seller credentials:')
        self.stdout.write('Username: seller1')
        self.stdout.write('Password: password123') 