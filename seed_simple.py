#!/usr/bin/env python
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import random
from datetime import timedelta

from store.models import Profile, Wallet, Shop, Category, Product, Goods, OrderMaster, OrderDetails, SalesRecord, Remittance

def main():
    print("Starting data seeding...")
    
    existing_users = User.objects.count()
    existing_categories = Category.objects.count()
    existing_shops = Shop.objects.count()
    existing_products = Product.objects.count()
    existing_goods = Goods.objects.count()
    
    print(f"Existing data: {existing_users} users, {existing_categories} categories, {existing_shops} shops, {existing_products} products, {existing_goods} goods")
    
    users_needed = max(0, 500 - existing_users)
    if users_needed > 0:
        print(f"Creating {users_needed} additional users...")
        for i in range(users_needed):
            username = f"user{existing_users + i + 1:03d}"
            user = User.objects.create_user(
                username=username,
                email=f"{username}@example.com",
                password='password123'
            )
            
            Profile.objects.create(
                user=user,
                email=f"{username}@example.com",
                country=f"Country{(existing_users + i) % 100}",
                city=f"City{(existing_users + i) % 100}",
                address=f"Address {(existing_users + i) % 1000}",
                is_seller=random.choice([True, False]),
                gender=random.choice(['male', 'female'])
            )
            
            Wallet.objects.create(user=user, balance=Decimal('5000.00'))
            
            if (i + 1) % 50 == 0:
                print(f"Created {i + 1} additional users")
    else:
        print("No additional users needed")
    
    categories_needed = max(0, 200 - existing_categories)
    if categories_needed > 0:
        print(f"Creating {categories_needed} additional categories...")
        for i in range(categories_needed):
            Category.objects.create(
                name=f"Category {existing_categories + i + 1}",
                description=f"Description for category {existing_categories + i + 1}"
            )
    else:
        print("No additional categories needed")
    
    shops_needed = max(0, 100 - existing_shops)
    if shops_needed > 0:
        print(f"Creating {shops_needed} additional shops...")
        sellers = Profile.objects.filter(is_seller=True)
        if sellers.exists():
            for i in range(shops_needed):
                owner = sellers[i % sellers.count()].user
                Shop.objects.create(
                    owner=owner,
                    name=f"Shop {existing_shops + i + 1}",
                    description=f"Shop {existing_shops + i + 1} description"
                )
        else:
            print("No sellers found, creating some users as sellers first")
            users_to_make_sellers = User.objects.all()[:100]
            for user in users_to_make_sellers:
                if hasattr(user, 'profile'):
                    user.profile.is_seller = True
                    user.profile.save()
            
            sellers = Profile.objects.filter(is_seller=True)
            for i in range(shops_needed):
                owner = sellers[i % sellers.count()].user
                Shop.objects.create(
                    owner=owner,
                    name=f"Shop {existing_shops + i + 1}",
                    description=f"Shop {existing_shops + i + 1} description"
                )
    else:
        print("No additional shops needed")
    
    products_needed = max(0, 1000 - existing_products)
    if products_needed > 0:
        print(f"Creating {products_needed} additional products...")
        categories = list(Category.objects.all())
        for i in range(products_needed):
            Product.objects.create(
                name=f"Product {existing_products + i + 1}",
                description=f"Product {existing_products + i + 1} description",
                category=random.choice(categories)
            )
            
            if (i + 1) % 100 == 0:
                print(f"Created {i + 1} additional products")
    else:
        print("No additional products needed")
    
    goods_needed = max(0, 1000 - existing_goods)
    if goods_needed > 0:
        print(f"Creating {goods_needed} additional goods entries...")
        shops = list(Shop.objects.all())
        products = list(Product.objects.all())
        for i in range(goods_needed):
            Goods.objects.create(
                shop=random.choice(shops),
                product=products[i % len(products)],
                purchase_price=Decimal(random.uniform(10, 100)),
                selling_price=Decimal(random.uniform(20, 200)),
                stock=random.randint(1, 50)
            )
            
            if (i + 1) % 100 == 0:
                print(f"Created {i + 1} additional goods entries")
    else:
        print("No additional goods needed")
    
    goods_list = list(Goods.objects.filter(is_available=True, stock__gte=1))
    if goods_list:
        transactions_to_create = min(1000, len(goods_list))
        print(f"Creating {transactions_to_create} transactions...")
        
        users = list(User.objects.all())
        
        for i in range(transactions_to_create):
            goods = random.choice(goods_list)
            buyer = random.choice(users)
            
            buyer.wallet.balance += goods.selling_price
            buyer.wallet.save()
            
            order = OrderMaster.objects.create(
                user=buyer,
                shipping_address=f"Address {i+1}",
                total_amount=goods.selling_price,
                status='confirmed'
            )
            
            OrderDetails.objects.create(
                order=order,
                goods=goods,
                quantity=1,
                price=goods.selling_price
            )
            
            buyer.wallet.balance -= goods.selling_price
            buyer.wallet.save()
            
            goods.shop.owner.wallet.balance += goods.selling_price
            goods.shop.owner.wallet.save()
            
            if (i + 1) % 100 == 0:
                print(f"Created {i + 1} transactions")
    else:
        print("No goods available for transactions")
    
    print("Data seeding completed!")
    
    final_users = User.objects.count()
    final_categories = Category.objects.count()
    final_shops = Shop.objects.count()
    final_products = Product.objects.count()
    final_goods = Goods.objects.count()
    final_transactions = OrderMaster.objects.count()
    
    print(f"\nFinal counts:")
    print(f"Users: {final_users}")
    print(f"Categories: {final_categories}")
    print(f"Shops: {final_shops}")
    print(f"Products: {final_products}")
    print(f"Goods: {final_goods}")
    print(f"Transactions: {final_transactions}")

if __name__ == "__main__":
    main()
