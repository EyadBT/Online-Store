from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import random
from datetime import timedelta

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
            users_count = self.create_users_and_profiles()
            
            categories_count = self.create_categories()
            
            shops_count = self.create_shops()
            
            products_count = self.create_products()
            
            goods_count = self.create_goods()
            
            transactions_count = self.create_transactions()
            
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
            self.stdout.write(
                self.style.ERROR(f'Error during data seeding: {e}')
            )
            import traceback
            traceback.print_exc()

    def clear_existing_data(self):
        """Clear existing data"""
        SalesRecord.objects.all().delete()
        OrderDetails.objects.all().delete()
        OrderMaster.objects.all().delete()
        Goods.objects.all().delete()
        Product.objects.all().delete()
        Shop.objects.all().delete()
        Category.objects.all().delete()
        Wallet.objects.all().delete()
        Profile.objects.all().delete()
        User.objects.all().delete()

    def create_users_and_profiles(self):
        """Create 500 users with profiles from different countries"""
        self.stdout.write('Creating users and profiles...')
        
        countries = [
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
                country=random.choice(countries),
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
                self.stdout.write(f"Created {users_created} users...")
        
        self.stdout.write(f"Created {users_created} users with profiles and wallets")
        return users_created

    def create_categories(self):
        """Create 200 categories"""
        self.stdout.write('Creating categories...')
        
        categories = [
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
        
        categories_created = 0
        for i in range(200):
            category_name = categories[i] if i < len(categories) else f"Category {i+1}"
            category = Category.objects.create(
                name=category_name,
                description=f"Description for {category_name}"
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
        
        product_names = {
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
        
        for i in range(1000):
            category = random.choice(categories)
            
            if category.name in product_names:
                base_name = random.choice(product_names[category.name])
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
        
        for i in range(1000):
            goods = random.choice(goods_list)
            buyer = random.choice(buyers)
            
            buyer_wallet = buyer.wallet
            if buyer_wallet.balance < goods.selling_price:
                buyer_wallet.balance += goods.selling_price * Decimal(2)
                buyer_wallet.save()
            
            order = OrderMaster.objects.create(
                user=buyer,
                shipping_address=f"{random.randint(1, 9999)} Main St, City{random.randint(1, 100)}, {random.choice(['USA', 'Canada', 'UK', 'Germany', 'France'])}",
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
                self.stdout.write(f"Created {transactions_created} transactions...")
        
        self.stdout.write(f"Created {transactions_created} transactions")
        return transactions_created
