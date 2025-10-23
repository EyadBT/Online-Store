from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random
from datetime import timedelta

from store.models import Goods, User, OrderMaster, OrderDetails, SalesRecord, Remittance

class Command(BaseCommand):
    help = 'Add transactions to existing data'

    def handle(self, *args, **options):
        self.stdout.write('Adding transactions to existing data...')
        
        try:
            goods_list = list(Goods.objects.filter(is_available=True, stock__gte=1))
            buyers = list(User.objects.all())
            
            if not goods_list:
                self.stdout.write(self.style.ERROR('No goods available for transactions'))
                return
            
            if not buyers:
                self.stdout.write(self.style.ERROR('No users available for transactions'))
                return
            
            self.stdout.write(f'Found {len(goods_list)} goods and {len(buyers)} users')
            
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
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {transactions_created} transactions!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during transaction creation: {e}')
            )
            import traceback
            traceback.print_exc()
