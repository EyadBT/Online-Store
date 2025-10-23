from decimal import Decimal
from django.conf import settings
from .models import Goods

class Cart:
    def __init__(self, request):

        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, goods, quantity=1, override_quantity=False):
        goods_id = str(goods.id)
        if goods_id not in self.cart:
            self.cart[goods_id] = {'quantity': 0,
                                    'price': str(goods.selling_price)}
        if override_quantity:
            self.cart[goods_id]['quantity'] = quantity
        else:
            self.cart[goods_id]['quantity'] += quantity
        self.save()

    def save(self):
        self.session.modified = True

    def remove(self, goods):
        goods_id = str(goods.id)
        if goods_id in self.cart:
            del self.cart[goods_id]
            self.save()

    def __iter__(self):
        goods_ids = self.cart.keys()
        goods_list = Goods.objects.filter(id__in=goods_ids)
        cart = self.cart.copy()
        for goods in goods_list:
            cart[str(goods.id)]['goods'] = goods
        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.save() 