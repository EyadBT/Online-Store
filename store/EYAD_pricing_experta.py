
from __future__ import annotations

import os
import math
import statistics
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from experta import KnowledgeEngine, Rule, Fact, AND, OR

from django.conf import settings
from django.utils import timezone
from django.db.models import Sum, Avg, Count, Q, F

from .models import Goods, Shop, Product, Review, SalesRecord


MIN_MARGIN_DEFAULT = 0.06
MAX_INCREASE_PCT = 0.15
MAX_DECREASE_PCT = 0.25
SMALL_STEP = 0.02
MEDIUM_STEP = 0.05
LARGE_STEP = 0.10


@dataclass
class Recommendation:
    action: str
    pct: float
    reasons: List[str]
    suggested_price: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ProductFact(Fact):
    pass


class PricingExpert(KnowledgeEngine):
    def __init__(self):
        super().__init__()
        self._decisions: List[Dict[str, Any]] = []

    def _push(self, action: str, pct: float, reason: str):
        self._decisions.append({"action": action, "pct": pct, "reason": reason})

    @Rule(ProductFact(sales='low', stock='high'))
    def r01(self):
        self._push('decrease', MEDIUM_STEP, "Low sales + high stock")

    @Rule(ProductFact(sales='low', competition='cheaper'))
    def r02(self):
        self._push('decrease', SMALL_STEP, "Competitors are cheaper than you")

    @Rule(ProductFact(sales='low', trend='falling'))
    def r03(self):
        self._push('decrease', MEDIUM_STEP, "Demand trend is falling")

    @Rule(ProductFact(margin='very_high', competition='cheaper'))
    def r04(self):
        self._push('decrease', SMALL_STEP, "High margin; can move closer to market price")

    @Rule(ProductFact(season='off', stock='high'))
    def r05(self):
        self._push('decrease', MEDIUM_STEP, "Off-season + excess inventory")

    @Rule(ProductFact(age='old', sales='low'))
    def r06(self):
        self._push('decrease', MEDIUM_STEP, "Aging product with weak demand")

    @Rule(ProductFact(elasticity='elastic'))
    def r07(self):
        self._push('decrease', SMALL_STEP, "Price-sensitive demand")

    @Rule(ProductFact(sales='high', stock='low'))
    def r08(self):
        self._push('increase', MEDIUM_STEP, "High sales + low stock")

    @Rule(ProductFact(sales='very_high'))
    def r09(self):
        self._push('increase', LARGE_STEP, "Very high demand")

    @Rule(ProductFact(trend='rising', competition='pricier'))
    def r10(self):
        self._push('increase', SMALL_STEP, "Upward trend and competitors are pricier")

    @Rule(ProductFact(margin='low', sales='stable'))
    def r11(self):
        self._push('increase', SMALL_STEP, "Weak profitability with stable sales")

    @Rule(ProductFact(rating='excellent', competition='equal'))
    def r12(self):
        self._push('increase', SMALL_STEP, "Excellent reputation justifies a small increase")

    @Rule(ProductFact(elasticity='inelastic'))
    def r13(self):
        self._push('increase', SMALL_STEP, "Demand is price-inelastic")

    @Rule(ProductFact(sales='stable', competition='equal'))
    def r14(self):
        self._push('keep', 0.0, "Price aligned with the market")

    @Rule(ProductFact(margin='good', sales='medium'))
    def r15(self):
        self._push('keep', 0.0, "Acceptable profitability and sales")

    @Rule(ProductFact(trend='flat', rating='average'))
    def r16(self):
        self._push('keep', 0.0, "No clear signal to change")

    @Rule(ProductFact(rating='poor', stock='high'))
    def r17(self):
        self._push('promotion', 0.0, "Low rating; improve value and run a promotion instead of permanent cuts")

    @Rule(ProductFact(season='peak', sales='low'))
    def r18(self):
        self._push('promotion', 0.0, "Peak season but weak sales — stimulate with a promotion")

    @Rule(ProductFact(favorites='high', competition='equal', sales='low'))
    def r19(self):
        self._push('promotion', 0.0, "High interest (favorites) but low conversion — coupon/free shipping")

    @Rule(ProductFact(stock='very_high', sales='low'))
    def r20(self):
        self._push('bundle', 0.0, "Move inventory with bundles/freebies")

    @Rule(ProductFact(margin='low', competition='cheaper'))
    def r21(self):
        self._push('free_shipping', 0.0, "Price floor reached — offer free shipping instead")

    @Rule(ProductFact(competition='pricier', margin='good', trend='rising'))
    def r22(self):
        self._push('increase', SMALL_STEP, "Price advantage + rising trend")

    @Rule(ProductFact(competition='cheaper', margin='low', trend='flat'))
    def r23(self):
        self._push('decrease', SMALL_STEP, "Strong price competition with weak margins")

    @Rule(ProductFact(sales='medium', stock='medium', trend='flat', rating='good'))
    def r24(self):
        self._push('keep', 0.0, "Overall stability without strong signals")

    @Rule(ProductFact(sales='low', favorites='low', rating='poor'))
    def r25(self):
        self._push('promotion', 0.0, "Weak product appeal; improve listing/photos/description")

    @Rule(ProductFact(sales='high', favorites='high', competition='equal'))
    def r26(self):
        self._push('increase', SMALL_STEP, "Good traction; try a small increase")

    @Rule(ProductFact(age='new', sales='low', trend='rising'))
    def r27(self):
        self._push('keep', 0.0, "New product improving; hold steady")

    @Rule(ProductFact(age='new', sales='high'))
    def r28(self):
        self._push('increase', SMALL_STEP, "Successful launch; small increase")

    @Rule(ProductFact(season='off', competition='cheaper', stock='medium'))
    def r29(self):
        self._push('decrease', SMALL_STEP, "Off-season + cheaper competition")

    @Rule(ProductFact(rating='excellent', favorites='high', trend='rising'))
    def r30(self):
        self._push('increase', SMALL_STEP, "High perceived value")

    def get_recommendation(self, current_price: float, purchase_price: float, min_margin: float) -> Recommendation:
        if not self._decisions:
            return Recommendation(action='keep', pct=0.0, reasons=["No effective rules fired"])

        inc = [d for d in self._decisions if d["action"] == "increase"]
        dec = [d for d in self._decisions if d["action"] == "decrease"]
        prom = [d for d in self._decisions if d["action"] in ("promotion", "bundle", "free_shipping")]
        keep = [d for d in self._decisions if d["action"] == "keep"]

        def cap_price(new_price: float) -> float:
            floor_price = float(purchase_price) * (1.0 + min_margin)
            return max(new_price, floor_price)

        if inc and dec:
            inc_pct = sum(d["pct"] for d in inc)
            dec_pct = sum(d["pct"] for d in dec)
            if inc_pct > dec_pct:
                pct = min(inc_pct, MAX_INCREASE_PCT)
                new_price = cap_price(current_price * (1.0 + pct))
                actual_pct = (new_price / current_price) - 1.0
                return Recommendation('increase', actual_pct, [d["reason"] for d in inc], round(new_price, 2))
            else:
                pct = min(dec_pct, MAX_DECREASE_PCT)
                target = current_price * (1.0 - pct)
                new_price = cap_price(target)
                if new_price >= current_price:
                    return Recommendation('keep', 0.0, ["Decrease blocked by minimum margin floor"] + [d["reason"] for d in dec], round(current_price, 2))
                actual_pct = (new_price / current_price) - 1.0
                return Recommendation('decrease', actual_pct, [d["reason"] for d in dec], round(new_price, 2))

        if inc:
            pct = min(sum(d["pct"] for d in inc), MAX_INCREASE_PCT)
            new_price = cap_price(current_price * (1.0 + pct))
            actual_pct = (new_price / current_price) - 1.0
            return Recommendation('increase', actual_pct, [d["reason"] for d in inc], round(new_price, 2))

        if dec:
            pct = min(sum(d["pct"] for d in dec), MAX_DECREASE_PCT)
            target = current_price * (1.0 - pct)
            new_price = cap_price(target)
            if new_price >= current_price:
                return Recommendation('keep', 0.0, ["Decrease blocked by minimum margin floor"] + [d["reason"] for d in dec], round(current_price, 2))
            actual_pct = (new_price / current_price) - 1.0
            return Recommendation('decrease', actual_pct, [d["reason"] for d in dec], round(new_price, 2))

        if prom:
            order = {'bundle': 0, 'free_shipping': 1, 'promotion': 2}
            prom_sorted = sorted(prom, key=lambda d: order.get(d["action"], 3))
            reasons = [d["reason"] for d in prom_sorted]
            return Recommendation(prom_sorted[0]["action"], 0.0, reasons, None)

        return Recommendation('keep', 0.0, [d["reason"] for d in keep] if keep else ["Price stability"])


def _sales_velocity(goods: Goods, window_days: int = 30) -> float:
    since = timezone.now() - timedelta(days=window_days)
    qs = SalesRecord.objects.filter(shop=goods.shop, product=goods.product, sale_date__gte=since)
    total_qty = qs.aggregate(total=Sum('quantity_sold'))['total'] or 0
    days = max(window_days, 1)
    return float(total_qty) / float(days)


def _competitor_price_position(goods: Goods) -> str:
    others = Goods.objects.filter(product=goods.product, is_available=True).exclude(pk=goods.pk)
    prices = [float(x.selling_price) for x in others if float(x.selling_price) > 0]
    if not prices:
        return 'unknown'
    median_price = statistics.median(prices)
    my_price = float(goods.selling_price)
    if my_price > median_price * 1.03:
        return 'pricier'
    elif my_price < median_price * 0.97:
        return 'cheaper'
    else:
        return 'equal'


def _avg_rating(product: Product) -> float:
    return float(Review.objects.filter(product=product).aggregate(avg=Avg('rating'))['avg'] or 0.0)


def _favorites_count(product: Product) -> int:
    from .models import Favorite
    return int(Favorite.objects.filter(product=product).count())


def _profit_margin_level(goods: Goods) -> str:
    p = float(goods.selling_price) or 0.0001
    margin_pct = max((p - float(goods.purchase_price)) / p, 0.0)
    if margin_pct < 0.10:
        return 'low'
    if margin_pct < 0.20:
        return 'good'
    return 'very_high'


def _trend_label(goods: Goods, window_days: int = 60) -> str:
    half = max(min(window_days//2, 30), 14)
    now = timezone.now()
    r1_from = now - timedelta(days=half)
    r2_from = now - timedelta(days=half*2)

    recent = SalesRecord.objects.filter(shop=goods.shop, product=goods.product, sale_date__gte=r1_from)
    prev = SalesRecord.objects.filter(shop=goods.shop, product=goods.product, sale_date__gte=r2_from, sale_date__lt=r1_from)

    q_recent = recent.aggregate(total=Sum('quantity_sold'))['total'] or 0
    q_prev = prev.aggregate(total=Sum('quantity_sold'))['total'] or 0

    if q_prev == 0 and q_recent == 0:
        return 'flat'
    if q_prev == 0 and q_recent > 0:
        return 'rising'
    change = (q_recent - q_prev) / max(q_prev, 1)
    if change > 0.25:
        return 'rising'
    if change < -0.25:
        return 'falling'
    return 'flat'


def _stock_level_label(goods: Goods, vpd: float) -> str:
    if vpd <= 0:
        return 'very_high' if goods.stock > 0 else 'low'
    days_cover = float(goods.stock) / vpd
    if days_cover < 5:
        return 'low'
    if days_cover < 20:
        return 'medium'
    if days_cover < 60:
        return 'high'
    return 'very_high'


def _rating_label(r: float) -> str:
    if r <= 0:
        return 'unknown'
    if r < 2.5:
        return 'poor'
    if r < 3.8:
        return 'average'
    if r < 4.5:
        return 'good'
    return 'excellent'


def _favorites_label(n: int) -> str:
    if n == 0:
        return 'low'
    if n < 10:
        return 'medium'
    return 'high'


def _age_label(product: Product) -> str:
    days = (timezone.now() - product.created_at).days if product.created_at else 0
    if days < 30:
        return 'new'
    if days < 365:
        return 'mid'
    return 'old'


def _season_label(product: Product) -> str:
    m = timezone.now().month
    if m in (11, 12):
        return 'peak'
    if m in (1, 2):
        return 'off'
    return 'normal'


def _elasticity_proxy(goods: Goods, window_days: int = 60) -> str:
    pos = _competitor_price_position(goods)
    r = _avg_rating(goods.product)
    if pos == 'pricier' and r < 3.5:
        return 'elastic'
    if pos == 'cheaper' and r >= 4.0:
        return 'inelastic'
    return 'elastic' if pos == 'pricier' else 'inelastic'


def build_facts_for_goods(goods: Goods, window_days: int = 30) -> Dict[str, str]:
    vpd = _sales_velocity(goods, window_days=window_days)
    comp = _competitor_price_position(goods)
    rating_val = _avg_rating(goods.product)
    rating = _rating_label(rating_val)
    favs = _favorites_label(_favorites_count(goods.product))
    margin = _profit_margin_level(goods)
    trend = _trend_label(goods, window_days=60)
    stock = _stock_level_label(goods, vpd=vpd)
    age = _age_label(goods.product)
    season = _season_label(goods.product)
    elast = _elasticity_proxy(goods)

    sales = 'low' if vpd < 0.06 else ('medium' if vpd < 0.25 else ('high' if vpd < 0.70 else 'very_high'))

    return {
        'sales': sales,
        'stock': stock,
        'competition': comp if comp != 'unknown' else 'equal',
        'rating': rating,
        'favorites': favs,
        'margin': margin,
        'trend': trend,
        'age': age,
        'season': season,
        'elasticity': elast
    }


def recommend_for_goods(goods_id: int, window_days: int = 30, min_margin: Optional[float] = None) -> Dict[str, Any]:
    goods = Goods.objects.select_related('product', 'shop').get(pk=goods_id)
    facts = build_facts_for_goods(goods, window_days=window_days)

    engine = PricingExpert()
    engine.reset()
    engine.declare(ProductFact(**facts))
    engine.run()

    current_price = float(goods.selling_price)
    purchase_price = float(goods.purchase_price)
    min_margin = MIN_MARGIN_DEFAULT if min_margin is None else float(min_margin)
    rec = engine.get_recommendation(current_price, purchase_price, min_margin)

    if rec.suggested_price is None and rec.pct != 0.0:
        suggested = current_price * (1.0 + rec.pct)
        rec.suggested_price = round(suggested, 2)
    
    if rec.suggested_price and rec.action in ('increase', 'decrease'):
        rec.pct = (rec.suggested_price / current_price) - 1.0

    result = rec.to_dict()
    result['facts'] = facts
    result['current_price'] = current_price
    result['purchase_price'] = purchase_price
    return result


def apply_recommendation(goods_id: int, recommendation: Dict[str, Any], dry_run: bool = True) -> Dict[str, Any]:
    goods = Goods.objects.select_related('product', 'shop').get(pk=goods_id)
    action = recommendation.get('action')
    pct = float(recommendation.get('pct', 0.0) or 0.0)
    suggested = recommendation.get('suggested_price')

    if action in ('increase', 'decrease') and suggested:
        if not dry_run:
            goods.selling_price = suggested
            goods.save(update_fields=['selling_price'])
        return {
            'updated': not dry_run,
            'new_price': float(suggested),
            'action': action
        }
    return {
        'updated': False,
        'new_price': float(goods.selling_price),
        'action': action
    }


MANAGEMENT_COMMAND_SNIPPET = r"""
from django.core.management.base import BaseCommand
from store.EYAD_pricing_experta import recommend_for_goods, apply_recommendation
from store.models import Goods

class Command(BaseCommand):
    help = "Run pricing expert system for all goods in a given shop"

    def add_arguments(self, parser):
        parser.add_argument('--shop-id', type=int, required=False)
        parser.add_argument('--apply', action='store_true', help='Apply price updates (not dry-run)')
        parser.add_argument('--window', type=int, default=30)
        parser.add_argument('--min-margin', type=float, default=None)

    def handle(self, *args, **opts):
        qs = Goods.objects.all()
        if opts.get('shop_id'):
            qs = qs.filter(shop_id=opts['shop_id'])

        for g in qs:
            rec = recommend_for_goods(g.id, window_days=opts['window'], min_margin=opts['min_margin'])
            self.stdout.write(f"Goods #{g.id} {g.product.name} @ {g.shop.name}: {rec}")
            if opts['apply'] and rec['action'] in ('increase','decrease') and rec.get('suggested_price'):
                res = apply_recommendation(g.id, rec, dry_run=False)
                self.stdout.write(f"Applied: {res}")
"""
