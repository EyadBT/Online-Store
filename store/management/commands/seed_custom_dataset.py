from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction, connection
from django.utils import timezone

from store.models import (
    Profile,
    Wallet,
    Category,
    Product,
    Shop,
    Goods,
    OrderMaster,
    OrderDetails,
    Review,
    SalesRecord,
)

from store.category_seed import ALL_CATEGORIES as BASE_CATEGORIES

from datetime import datetime, timedelta
from decimal import Decimal
import random


FOCUS_CATEGORIES_INPUT = [
    "coats", "jackets", "boots", "scarves", "sweaters", "light jackets",
    "sneakers", "t-shirts", "swimsuits", "sunglasses", "sandals", "shorts",
    "coats", "jackets", "boots", "sweaters",
]


class Command(BaseCommand):
    help = (
        "Seed a fresh dataset: 500 users (password rootroot123), 100 shops, "
        "200 realistic categories (including provided ones), products/goods, and "
        "5000 timezone-aware orders (>=1/day, >=2 items/order)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before seeding",
        )

    def handle(self, *args, **options):
        if options.get("clear"):
            self.stdout.write("Clearing existing data (raw SQL, FK off)...")
            self.clear_all_data()

        self.stdout.write("Building category list (target 200 unique)...")
        categories = self.build_categories(200)

        with transaction.atomic():
            self.stdout.write("Creating categories...")
            category_objs = self.create_categories(categories)

            self.stdout.write("Creating 500 users/profiles/wallets...")
            users = self.create_users(500)

            self.stdout.write("Creating 100 shops...")
            shops = self.create_shops(users, 100)

            self.stdout.write("Creating products (focus + general)...")
            products, focus_products = self.create_products(category_objs)

            self.stdout.write("Creating goods (inventory per shop)...")
            goods_by_product = self.create_goods(shops, products)

            self.stdout.write("Creating 5000 orders across 2023-09-01 to 2025-09-01...")
            orders = self.create_orders(users, goods_by_product, products, focus_products)

            self.stdout.write("Topping up purchases for focus products to >=30...")
            self.ensure_min_purchases_for_focus_products(users, goods_by_product, focus_products)

            self.stdout.write("Creating reviews for all purchased products with compatible comments...")
            self.create_reviews_for_all_purchases()

        self.stdout.write(self.style.SUCCESS("Seeding complete."))

    def clear_all_data(self):
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
                'store_review',
                'store_favorite',
                'store_remittance',
                'store_wallet',
                'store_profile',
                'auth_user_groups',
                'auth_user_user_permissions',
                'auth_user',
            ]
            for t in tables:
                try:
                    cursor.execute(f"DELETE FROM {t};")
                except Exception:
                    pass
            cursor.execute("PRAGMA foreign_keys=ON;")

    def build_categories(self, target_count: int):
        focus = []
        seen = set()
        for c in FOCUS_CATEGORIES_INPUT:
            cl = c.strip().lower()
            if cl not in seen:
                seen.add(cl)
                focus.append(cl)

        frequent_use = [
            'groceries', 'fresh produce', 'fruits', 'vegetables', 'dairy & eggs', 'baked goods',
            'meat & poultry', 'seafood', 'snacks', 'beverages', 'breakfast & cereals',
            'canned goods', 'frozen foods', 'pasta & rice', 'sauces & spices', 'condiments',
            'household supplies', 'personal care', 'baby care', 'pet supplies'
        ]

        names = []
        def add_unique(name):
            n = name.strip()
            if n and n.lower() not in {x.lower() for x in names}:
                names.append(n)

        for n in focus:
            add_unique(n)
        for n in frequent_use:
            add_unique(n)
        for n in BASE_CATEGORIES:
            add_unique(n)

        clothing_variants = [
            'men coats', 'women coats', 'rain jackets', 'winter jackets', 'down jackets', 'wool sweaters',
            'cardigans', 'pullover sweaters', 'running sneakers', 'basketball sneakers', 'casual t-shirts',
            'graphic t-shirts', 'board shorts', 'chino shorts', 'flip-flops', 'sport sandals',
            'polarized sunglasses', 'fashion sunglasses', 'bikini swimsuits', 'one-piece swimsuits', 'swim trunks',
            'winter scarves', 'silk scarves', 'leather boots', 'hiking boots', 'chelsea boots'
        ]
        for n in clothing_variants:
            if len(names) >= target_count:
                break
            add_unique(n)

        i = 1
        while len(names) < target_count:
            add_unique(f"General Category {i}")
            i += 1

        return names[:target_count]

    def create_categories(self, names):
        out = {}
        for n in names:
            obj, _ = Category.objects.get_or_create(
                name=n,
                defaults={"description": f"{n} category"}
            )
            out[n] = obj
        return out

    def create_users(self, count: int):
        from django.db.models.signals import post_save
        from store.models import create_user_profile_and_wallet, save_user_profile

        try:
            post_save.disconnect(receiver=create_user_profile_and_wallet, sender=User)
            post_save.disconnect(receiver=save_user_profile, sender=User)
        except Exception:
            pass

        male_first = [
            'James','John','Robert','Michael','William','David','Richard','Joseph','Thomas','Charles','Christopher','Daniel','Matthew','Anthony','Mark','Donald','Steven','Paul','Andrew','Joshua','Kenneth','Kevin','Brian','George','Edward','Ronald','Timothy','Jason','Jeffrey','Ryan','Jacob','Gary','Nicholas','Eric','Jonathan','Stephen','Larry','Justin','Scott','Brandon','Benjamin','Samuel','Gregory','Frank','Alexander','Patrick','Raymond','Jack','Dennis','Jerry','Tyler','Aaron'
        ]
        female_first = [
            'Mary','Patricia','Jennifer','Linda','Elizabeth','Barbara','Susan','Jessica','Sarah','Karen','Nancy','Lisa','Margaret','Betty','Sandra','Ashley','Dorothy','Kimberly','Emily','Donna','Michelle','Carol','Amanda','Melissa','Deborah','Stephanie','Rebecca','Laura','Sharon','Cynthia','Kathleen','Amy','Shirley','Angela','Helen','Anna','Brenda','Pamela','Nicole','Ruth','Katherine','Christine','Samantha','Emma','Olivia','Ava','Sophia','Isabella','Mia','Charlotte'
        ]
        last_names = [
            'Smith','Johnson','Williams','Brown','Jones','Garcia','Miller','Davis','Rodriguez','Martinez','Hernandez','Lopez','Gonzalez','Wilson','Anderson','Thomas','Taylor','Moore','Jackson','Martin','Lee','Perez','Thompson','White','Harris','Sanchez','Clark','Ramirez','Lewis','Robinson','Walker','Young','Allen','King','Wright','Scott','Torres','Nguyen','Hill','Flores','Green','Adams','Nelson','Baker','Hall','Rivera','Campbell','Mitchell','Carter','Roberts'
        ]

        country_cities = {
            'USA': ['New York','Los Angeles','Chicago','Houston','Phoenix','Seattle','Boston','San Francisco','Miami','Dallas'],
            'United Kingdom': ['London','Manchester','Birmingham','Leeds','Glasgow','Liverpool','Edinburgh'],
            'Germany': ['Berlin','Munich','Hamburg','Frankfurt','Cologne','Stuttgart'],
            'France': ['Paris','Lyon','Marseille','Toulouse','Nice','Bordeaux'],
            'Spain': ['Madrid','Barcelona','Valencia','Seville','Bilbao','Zaragoza'],
            'Italy': ['Rome','Milan','Naples','Turin','Florence','Bologna'],
            'Canada': ['Toronto','Vancouver','Montreal','Calgary','Ottawa','Edmonton'],
            'Australia': ['Sydney','Melbourne','Brisbane','Perth','Adelaide'],
            'India': ['Mumbai','Delhi','Bengaluru','Chennai','Hyderabad','Kolkata'],
            'Japan': ['Tokyo','Osaka','Nagoya','Sapporo','Fukuoka'],
            'Brazil': ['São Paulo','Rio de Janeiro','Belo Horizonte','Porto Alegre','Brasília'],
            'Mexico': ['Mexico City','Guadalajara','Monterrey','Puebla','Tijuana'],
            'Egypt': ['Cairo','Alexandria','Giza','Mansoura','Tanta'],
            'Saudi Arabia': ['Riyadh','Jeddah','Dammam','Mecca','Medina'],
            'United Arab Emirates': ['Dubai','Abu Dhabi','Sharjah','Ajman','Ras Al Khaimah'],
        }

        def make_unique_username(base, used):
            uname = base
            idx = 1
            while uname in used:
                idx += 1
                uname = f"{base}{idx}"
            used.add(uname)
            return uname

        used_usernames = set()
        users = []
        for i in range(1, count + 1):
            gender = random.choice(["male", "female"])  # only male/female as requested
            if gender == 'male':
                first = random.choice(male_first)
            else:
                first = random.choice(female_first)
            last = random.choice(last_names)
            base_username = f"{first}.{last}".lower().replace(' ', '')
            username = make_unique_username(base_username, used_usernames)
            email = f"{username}@example.com"

            user = User.objects.create_user(username=username, email=email, password="rootroot123")

            country = random.choice(list(country_cities.keys()))
            city = random.choice(country_cities[country])
            Profile.objects.create(
                user=user,
                email=email,
                phone=f"+1{random.randint(1000000000, 9999999999)}",
                country=country,
                city=city,
                address=f"{random.randint(100, 9999)} {random.choice(['Main St', 'Oak Ave', 'Pine Rd', 'Elm St', 'Maple Dr'])}",
                is_seller=False,  # set True for first 100 below
                gender=gender,
            )
            Wallet.objects.create(user=user, balance=Decimal("10000.00"))  # enough balance
            users.append(user)

        for u in users[:100]:
            p = u.profile
            p.is_seller = True
            p.save(update_fields=["is_seller"])

        try:
            post_save.connect(receiver=create_user_profile_and_wallet, sender=User)
            post_save.connect(receiver=save_user_profile, sender=User)
        except Exception:
            pass

        return users

    def create_shops(self, users, count: int):
        sellers = [u for u in users if getattr(u, 'profile', None) and u.profile.is_seller]
        shops = []
        for i in range(count):
            owner = sellers[i % len(sellers)]
            name = f"Shop {i+1}"
            shop, _ = Shop.objects.get_or_create(
                name=name,
                owner=owner,
                defaults={
                    'description': 'Quality goods at fair prices',
                    'is_active': True,
                }
            )
            shops.append(shop)
        return shops

    def create_products(self, category_objs):
        focus_names = {c.strip().lower() for c in FOCUS_CATEGORIES_INPUT}
        focus_categories = [obj for name, obj in category_objs.items() if name.lower() in focus_names]

        products = []
        focus_products = []

        name_templates = [
            "Classic {base}", "Premium {base}", "Eco {base}", "Sport {base}",
            "Urban {base}", "Comfy {base}", "Pro {base}", "Essential {base}"
        ]
        for cat in focus_categories:
            base = cat.name.rstrip('s')  # rough singularization for names
            for nm in name_templates[:4]:  # 4 per category
                pname = nm.format(base=base.title())
                product, _ = Product.objects.get_or_create(
                    name=pname,
                    category=cat,
                    defaults={
                        'description': f'{pname} in {cat.name}',
                    }
                )
                products.append(product)
                focus_products.append(product)

        other_categories = [obj for name, obj in category_objs.items() if obj not in focus_categories]
        random.shuffle(other_categories)
        extra_count = 150
        pool_words = [
            'Basic', 'Deluxe', 'Ultra', 'Eco', 'Compact', 'Max', 'Lite', 'Smart', 'Advance', 'Prime', 'Select', 'Value'
        ]
        for i in range(min(extra_count, len(other_categories))):
            cat = other_categories[i]
            for j in range(random.randint(1, 2)):
                label = random.choice(pool_words)
                pname = f"{label} {cat.name.title()} Item {j+1}"
                product, _ = Product.objects.get_or_create(
                    name=pname,
                    category=cat,
                    defaults={'description': f'{pname} in {cat.name}'}
                )
                products.append(product)

        return products, focus_products

    def create_goods(self, shops, products):
        goods_by_product = {p.id: [] for p in products}

        for shop in shops:
            shop_products = random.sample(products, k=min(len(products), random.randint(20, 40)))
            for product in shop_products:
                cname = product.category.name.lower()
                if any(k in cname for k in ["coat", "jacket", "boot", "sweater"]):
                    base = Decimal(random.randrange(5000, 20000)) / Decimal(100)  # 50.00 - 200.00
                elif any(k in cname for k in ["sneaker", "sandal", "shoe"]):
                    base = Decimal(random.randrange(3000, 15000)) / Decimal(100)
                elif any(k in cname for k in ["t-shirt", "short", "swimsuit", "sunglass", "scarf"]):
                    base = Decimal(random.randrange(1000, 8000)) / Decimal(100)
                elif any(k in cname for k in ["grocer", "food", "beverage", "snack", "dairy", "meat", "seafood"]):
                    base = Decimal(random.randrange(200, 3000)) / Decimal(100)
                else:
                    base = Decimal(random.randrange(500, 10000)) / Decimal(100)

                selling_price = base.quantize(Decimal("0.01"))
                purchase_price = (selling_price * Decimal("0.6")).quantize(Decimal("0.01"))
                stock = random.randint(200, 800)  # enough for purchases

                goods, _ = Goods.objects.get_or_create(
                    shop=shop,
                    product=product,
                    defaults={
                        'purchase_price': purchase_price,
                        'selling_price': selling_price,
                        'stock': stock,
                        'is_available': True,
                    }
                )
                goods_by_product[product.id].append(goods)

        return goods_by_product

    def date_range_days(self, start: datetime, end: datetime):
        cur = start
        while cur <= end:
            yield cur
            cur += timedelta(days=1)

    def create_orders(self, users, goods_by_product, products, focus_products):
        orders = []

        focus_ids = [p.id for p in focus_products]
        user_fav_pairs = {}
        for u in users:
            pair = random.sample(focus_ids, 2)
            user_fav_pairs[u.id] = tuple(pair)

        start_date = datetime(2023, 9, 1)
        end_date = datetime(2025, 9, 1)

        per_day_orders = []
        for day in self.date_range_days(start_date, end_date):
            order = self._create_single_order_for_day(
                random.choice(users), user_fav_pairs, goods_by_product, day
            )
            orders.append(order)
            per_day_orders.append(order)

        remaining = 5000 - len(per_day_orders)
        all_days = [d for d in self.date_range_days(start_date, end_date)]
        for _ in range(max(0, remaining)):
            day = random.choice(all_days)
            order = self._create_single_order_for_day(
                random.choice(users), user_fav_pairs, goods_by_product, day
            )
            orders.append(order)

        return orders

    def _create_single_order_for_day(self, user, user_fav_pairs, goods_by_product, day_dt: datetime):
        rand_dt = day_dt + timedelta(
            hours=random.randint(8, 21), minutes=random.randint(0, 59), seconds=random.randint(0, 59)
        )
        aware_dt = timezone.make_aware(rand_dt)

        order = OrderMaster.objects.create(
            user=user,
            order_date=aware_dt,
            status=random.choice(['confirmed', 'shipped', 'delivered']),
            shipping_address=f"{random.randint(100,9999)} {random.choice(['Main St','Oak Ave','Pine Rd','Elm St','Maple Dr'])}",
            notes=random.choice(['', 'Please leave at door', 'Call on arrival', 'Fragile items']),
            total_amount=Decimal('0.00'),
        )
        OrderMaster.objects.filter(pk=order.pk).update(order_date=aware_dt)
        order.order_date = aware_dt

        fav1, fav2 = user_fav_pairs[user.id]
        goods_choices = []
        if random.random() < 0.7:
            if goods_by_product.get(fav1):
                goods_choices.append(random.choice(goods_by_product[fav1]))
            if goods_by_product.get(fav2):
                goods_choices.append(random.choice(goods_by_product[fav2]))

        additional_items = random.randint(0, 2)
        for _ in range(additional_items):
            pid = random.choice(list(goods_by_product.keys()))
            if goods_by_product[pid]:
                goods_choices.append(random.choice(goods_by_product[pid]))

        while len(goods_choices) < 2:
            pid = random.choice(list(goods_by_product.keys()))
            if goods_by_product[pid]:
                goods_choices.append(random.choice(goods_by_product[pid]))

        total = Decimal('0.00')
        for goods in goods_choices:
            if goods.stock <= 0:
                continue
            qty = random.randint(1, 2)
            detail = OrderDetails.objects.create(
                order=order,
                goods=goods,
                quantity=qty,
                price=goods.selling_price,
            )
            total += goods.selling_price * Decimal(qty)
            goods.stock = max(0, goods.stock - qty)
            if goods.stock == 0:
                goods.is_available = False
            goods.save(update_fields=["stock", "is_available"])

            sr = SalesRecord.objects.create(
                shop=goods.shop,
                order_detail=detail,
                product=goods.product,
                quantity_sold=qty,
                unit_price=goods.selling_price,
                total_revenue=(goods.selling_price * Decimal(qty)).quantize(Decimal('0.01')),
                profit_margin=((goods.selling_price - goods.purchase_price) * Decimal(qty)).quantize(Decimal('0.01')),
            )
            SalesRecord.objects.filter(pk=sr.pk).update(sale_date=order.order_date)

        order.total_amount = total.quantize(Decimal('0.01'))
        order.save(update_fields=["total_amount"])
        return order

    def ensure_min_purchases_for_focus_products(self, users, goods_by_product, focus_products, min_per_product: int = 30):
        from django.db.models import Sum
        for p in focus_products:
            def get_count():
                return (
                    OrderDetails.objects.filter(goods__product_id=p.id)
                    .aggregate(q=Sum("quantity"))
                    .get("q") or 0
                )

            current = int(get_count())
            safety = 0
            while current < min_per_product and safety < 200:
                user = random.choice(users)
                day = datetime(2025, 8, random.randint(1, 31))
                fake_pairs = {user.id: (p.id, random.choice(list(goods_by_product.keys())))}
                self._create_single_order_for_day(user, fake_pairs, goods_by_product, day)
                current = int(get_count())
                safety += 1

    def create_reviews_for_all_purchases(self):
        purchases = OrderDetails.objects.values(
            "order__user_id", "goods__product_id", "order__order_date"
        )

        by_user = {}
        for row in purchases:
            uid = row["order__user_id"]
            pid = row["goods__product_id"]
            odt = row["order__order_date"]
            by_user.setdefault(uid, {}).setdefault(pid, []).append(odt)

        positive_comments = [
            "Excellent quality and value.",
            "Very satisfied with this purchase.",
            "Great fit and comfortable.",
            "Highly recommend!", "Would buy again.", "Exactly as described."
        ]
        neutral_comments = [
            "Decent for the price.", "Average quality.", "Meets expectations.", "Okay product."
        ]
        negative_comments = [
            "Poor quality, not recommended.",
            "Disappointed with the product.",
            "Does not match description.",
            "Would not buy again."
        ]

        for uid, prods in by_user.items():
            for pid, dates in prods.items():
                r = random.random()
                if r < 0.6:
                    rating = random.choice([4, 5])
                    comment = random.choice(positive_comments)
                elif r < 0.85:
                    rating = random.choice([3, 4])
                    comment = random.choice(neutral_comments)
                else:
                    rating = random.choice([1, 2])
                    comment = random.choice(negative_comments)

                created_at = max(dates) + timedelta(days=random.randint(0, 10))
                aware_created = timezone.make_aware(created_at) if timezone.is_naive(created_at) else created_at

                Review.objects.update_or_create(
                    user_id=uid,
                    product_id=pid,
                    defaults={
                        'rating': rating,
                        'comment': comment,
                        'created_at': aware_created,
                    }
                )
