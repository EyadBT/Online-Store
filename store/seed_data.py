import os
import django
from decimal import Decimal
import random
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from store.models import Profile, Wallet, Shop, Category, Product, Goods, OrderMaster, OrderDetails, SalesRecord, Remittance

COUNTRIES = [
    'Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Antigua and Barbuda', 'Argentina', 'Armenia', 'Australia', 'Austria',
    'Azerbaijan', 'Bahamas', 'Bahrain', 'Bangladesh', 'Barbados', 'Belarus', 'Belgium', 'Belize', 'Benin', 'Bhutan',
    'Bolivia', 'Bosnia and Herzegovina', 'Botswana', 'Brazil', 'Brunei', 'Bulgaria', 'Burkina Faso', 'Burundi', 'Cambodia', 'Cameroon',
    'Canada', 'Cape Verde', 'Central African Republic', 'Chad', 'Chile', 'China', 'Colombia', 'Comoros', 'Congo', 'Costa Rica',
    'Croatia', 'Cuba', 'Cyprus', 'Czech Republic', 'Democratic Republic of the Congo', 'Denmark', 'Djibouti', 'Dominica', 'Dominican Republic', 'East Timor',
    'Ecuador', 'Egypt', 'El Salvador', 'Equatorial Guinea', 'Eritrea', 'Estonia', 'Eswatini', 'Ethiopia', 'Fiji', 'Finland',
    'France', 'Gabon', 'Gambia', 'Georgia', 'Germany', 'Ghana', 'Greece', 'Grenada', 'Guatemala', 'Guinea',
    'Guinea-Bissau', 'Guyana', 'Haiti', 'Honduras', 'Hungary', 'Iceland', 'India', 'Indonesia', 'Iran', 'Iraq',
    'Ireland', 'Israel', 'Italy', 'Ivory Coast', 'Jamaica', 'Japan', 'Jordan', 'Kazakhstan', 'Kenya', 'Kiribati',
    'Kuwait', 'Kyrgyzstan', 'Laos', 'Latvia', 'Lebanon', 'Lesotho', 'Liberia', 'Libya', 'Liechtenstein', 'Lithuania',
    'Luxembourg', 'Madagascar', 'Malawi', 'Malaysia', 'Maldives', 'Mali', 'Malta', 'Marshall Islands', 'Mauritania', 'Mauritius'
]

CATEGORIES = [
    'Electronics', 'Clothing', 'Books', 'Home & Garden', 'Sports & Outdoors', 'Beauty & Health', 'Toys & Games', 'Automotive', 'Tools & Hardware', 'Jewelry',
    'Food & Beverages', 'Pet Supplies', 'Baby Products', 'Office Supplies', 'Music & Movies', 'Art & Crafts', 'Fitness & Wellness', 'Travel & Luggage', 'Garden & Outdoor', 'Kitchen & Dining',
    'Furniture', 'Lighting', 'Bath & Bedding', 'Storage & Organization', 'Party Supplies', 'School Supplies', 'Holiday Decorations', 'Wedding Supplies', 'Religious Items', 'Collectibles',
    'Antiques', 'Vintage Items', 'Handmade Crafts', 'Digital Downloads', 'Gift Cards', 'Subscription Services', 'Membership Services', 'Consulting Services', 'Educational Courses', 'Software',
    'Mobile Apps', 'Web Services', 'Cloud Storage', 'Cybersecurity', 'Data Analytics', 'Artificial Intelligence', 'Machine Learning', 'Blockchain', 'Cryptocurrency', 'NFTs',
    'Virtual Reality', 'Augmented Reality', '3D Printing', 'Robotics', 'Drones', 'Smart Home', 'Internet of Things', 'Wearable Technology', 'Biotechnology', 'Nanotechnology',
    'Renewable Energy', 'Electric Vehicles', 'Hybrid Cars', 'Solar Power', 'Wind Energy', 'Hydroelectric Power', 'Geothermal Energy', 'Biomass Energy', 'Nuclear Power', 'Fossil Fuels',
    'Organic Food', 'Gluten-Free', 'Vegan', 'Vegetarian', 'Keto', 'Paleo', 'Mediterranean', 'Asian Cuisine', 'European Cuisine', 'American Cuisine',
    'African Cuisine', 'Middle Eastern', 'Latin American', 'Caribbean', 'Indian', 'Thai', 'Japanese', 'Chinese', 'Korean', 'Vietnamese',
    'Italian', 'French', 'Spanish', 'German', 'Greek', 'Turkish', 'Russian', 'Polish', 'Czech', 'Hungarian',
    'Swedish', 'Norwegian', 'Danish', 'Finnish', 'Dutch', 'Belgian', 'Swiss', 'Austrian', 'Portuguese', 'Irish',
    'Scottish', 'Welsh', 'English', 'Canadian', 'Mexican', 'Brazilian', 'Argentine', 'Chilean', 'Peruvian', 'Colombian',
    'Venezuelan', 'Ecuadorian', 'Bolivian', 'Paraguayan', 'Uruguayan', 'Guyanese', 'Surinamese', 'French Guianese', 'Falkland Islander', 'South African',
    'Egyptian', 'Moroccan', 'Algerian', 'Tunisian', 'Libyan', 'Sudanese', 'Ethiopian', 'Kenyan', 'Tanzanian', 'Ugandan',
    'Rwandan', 'Burundian', 'Congolese', 'Cameroonian', 'Nigerian', 'Ghanaian', 'Ivorian', 'Senegalese', 'Malian', 'Burkina Faso',
    'Nigerien', 'Chadian', 'Central African', 'Gabonese', 'Equatorial Guinean', 'Sao Tomean', 'Angolan', 'Zambian', 'Zimbabwean', 'Malawian',
    'Mozambican', 'Madagascan', 'Mauritian', 'Seychellois', 'Comorian', 'Maldivian', 'Sri Lankan', 'Bangladeshi', 'Nepali', 'Bhutanese',
    'Myanmar', 'Laotian', 'Cambodian', 'Vietnamese', 'Thai', 'Malaysian', 'Singaporean', 'Indonesian', 'Philippine', 'Bruneian',
    'East Timorese', 'Papua New Guinean', 'Fijian', 'Solomon Islander', 'Vanuatuan', 'New Caledonian', 'Australian', 'New Zealander', 'Hawaiian', 'Polynesian'
]

PRODUCT_NAMES = {
    'Electronics': ['Smartphone', 'Laptop', 'Tablet', 'Smartwatch', 'Headphones', 'Speaker', 'Camera', 'TV', 'Gaming Console', 'Router'],
    'Clothing': ['T-Shirt', 'Jeans', 'Dress', 'Sweater', 'Jacket', 'Shoes', 'Hat', 'Scarf', 'Gloves', 'Socks'],
    'Books': ['Fiction Novel', 'Non-Fiction Book', 'Textbook', 'Cookbook', 'Biography', 'History Book', 'Science Book', 'Poetry Book', 'Children Book', 'Reference Book'],
    'Home & Garden': ['Plant Pot', 'Garden Tool', 'Outdoor Furniture', 'Indoor Plant', 'Garden Decoration', 'Plant Food', 'Watering Can', 'Garden Gloves', 'Plant Stand', 'Garden Light'],
    'Sports & Outdoors': ['Basketball', 'Soccer Ball', 'Tennis Racket', 'Golf Club', 'Yoga Mat', 'Dumbbells', 'Running Shoes', 'Bicycle', 'Camping Tent', 'Fishing Rod'],
    'Beauty & Health': ['Shampoo', 'Face Cream', 'Toothpaste', 'Deodorant', 'Perfume', 'Makeup Kit', 'Hair Brush', 'Mirror', 'Towel', 'Soap'],
    'Toys & Games': ['Board Game', 'Puzzle', 'Action Figure', 'Doll', 'Building Blocks', 'Art Set', 'Educational Toy', 'Remote Control Car', 'Plush Toy', 'Card Game'],
    'Automotive': ['Car Accessory', 'Tire', 'Oil Filter', 'Brake Pad', 'Car Wash Kit', 'Floor Mat', 'Seat Cover', 'Steering Wheel Cover', 'Car Charger', 'GPS Device'],
    'Tools & Hardware': ['Hammer', 'Screwdriver', 'Wrench', 'Drill', 'Saw', 'Pliers', 'Tape Measure', 'Level', 'Chisel', 'File'],
    'Jewelry': ['Necklace', 'Ring', 'Earrings', 'Bracelet', 'Watch', 'Anklet', 'Brooch', 'Cufflinks', 'Pendant', 'Chain']
}

def create_users_and_profiles():
    print("Creating users and profiles...")
    
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
        
        profile = Profile.objects.create(
            user=user,
            email=email,
            phone=f"+1{random.randint(1000000000, 9999999999)}",
            country=random.choice(COUNTRIES),
            city=f"City{random.randint(1, 100)}",
            address=f"{random.randint(1, 9999)} Main St, City{random.randint(1, 100)}",
            is_seller=random.choice([True, False]),
            gender=random.choice(['male', 'female'])
        )
        
        wallet = Wallet.objects.create(
            user=user,
            balance=Decimal(random.uniform(1000, 10000))
        )
        
        users_created += 1
        if users_created % 50 == 0:
            print(f"Created {users_created} users...")
    
    print(f"Created {users_created} users with profiles and wallets")
    return users_created

def create_categories():
    print("Creating categories...")
    
    categories_created = 0
    for i in range(200):
        category_name = CATEGORIES[i] if i < len(CATEGORIES) else f"Category {i+1}"
        category = Category.objects.create(
            name=category_name,
            description=f"Description for {category_name}"
        )
        categories_created += 1
    
    print(f"Created {categories_created} categories")
    return categories_created

def create_shops():
    print("Creating shops...")
    
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
    
    print(f"Created {shops_created} shops")
    return shops_created

def create_products():
    print("Creating products...")
    
    categories = list(Category.objects.all())
    products_created = 0
    
    for i in range(1000):
        category = random.choice(categories)
        
        if category.name in PRODUCT_NAMES:
            base_name = random.choice(PRODUCT_NAMES[category.name])
            product_name = f"{base_name} {i+1}"
        else:
            product_name = f"Product {i+1}"
        
        product = Product.objects.create(
            name=product_name,
            description=f"Description for {product_name}",
            category=category
        )
        products_created += 1
        
        if products_created % 100 == 0:
            print(f"Created {products_created} products...")
    
    print(f"Created {products_created} products")
    return products_created

def create_goods():
    print("Creating goods entries...")
    
    shops = list(Shop.objects.all())
    products = list(Product.objects.all())
    goods_created = 0
    
    for i in range(1000):
        shop = random.choice(shops)
        product = products[i % len(products)]
        
        purchase_price = Decimal(random.uniform(10, 200))
        selling_price = purchase_price * Decimal(random.uniform(1.2, 2.5))
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
            print(f"Created {goods_created} goods entries...")
    
    print(f"Created {goods_created} goods entries")
    return goods_created

def create_transactions():
    print("Creating transactions...")
    
    goods_list = list(Goods.objects.filter(is_available=True, stock__gte=1))
    buyers = list(User.objects.all())
    
    transactions_created = 0
    
    for i in range(1000):
        goods = random.choice(goods_list)
        buyer = random.choice(buyers)
        
        buyer_wallet = buyer.wallet
        if buyer_wallet.balance < goods.selling_price:
            buyer_wallet.balance += goods.selling_price * Decimal(2)
            buyer_wallet.save()
        
        order = OrderMaster.objects.create(
            user=buyer,
            shipping_address=f"{random.randint(1, 9999)} Main St, City{random.randint(1, 100)}, {random.choice(COUNTRIES)}",
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
        
        goods.stock -= 1
        if goods.stock == 0:
            goods.is_available = False
        goods.save()
        
        transactions_created += 1
        
        if transactions_created % 100 == 0:
            print(f"Created {transactions_created} transactions...")
    
    print(f"Created {transactions_created} transactions")
    return transactions_created

def main():
    print("Starting data seeding process...")
    
    try:
        users_count = create_users_and_profiles()
        
        categories_count = create_categories()
        
        shops_count = create_shops()
        
        products_count = create_products()
        
        goods_count = create_goods()
        
        transactions_count = create_transactions()
        
        print("\n" + "="*50)
        print("DATA SEEDING COMPLETED SUCCESSFULLY!")
        print("="*50)
        print(f"Users created: {users_count}")
        print(f"Categories created: {categories_count}")
        print(f"Shops created: {shops_count}")
        print(f"Products created: {products_count}")
        print(f"Goods entries created: {goods_count}")
        print(f"Transactions created: {transactions_count}")
        print("="*50)
        
    except Exception as e:
        print(f"Error during data seeding: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
