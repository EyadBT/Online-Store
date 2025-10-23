import pandas as pd
import numpy as np
from datetime import timedelta
from collections import Counter, defaultdict
import os
import pickle
import time

from django.db.models import Sum
from django.conf import settings
from django.utils import timezone
try:
    from .category_seed import CATEGORY_SIMILARITY_MAP
except Exception:
    CATEGORY_SIMILARITY_MAP = {}

from .models import OrderDetails, OrderMaster, Product, Goods, Category

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except Exception:
    PROPHET_AVAILABLE = False

_CACHE = {}
_CACHE_TTL_SECONDS = 60 * 60

def _cache_get(key):
    entry = _CACHE.get(key)
    if not entry:
        return None
    ts, value = entry
    if (time.time() - ts) > _CACHE_TTL_SECONDS:
        del _CACHE[key]
        return None
    return value


def _cache_set(key, value):
    _CACHE[key] = (time.time(), value)


CATEGORY_SEASON_MAP = {
    "coats": ["winter"],
    "jackets": ["winter", "autumn"],
    "light jackets": ["spring", "autumn"],
    "scarves": ["winter"],
    "sweaters": ["winter", "autumn"],
    "boots": ["winter", "autumn"],
    "sneakers": ["spring", "summer", "autumn"],
    "t-shirts": ["spring", "summer"],
    "swimsuits": ["summer"],
    "sunglasses": ["summer"],
    "sandals": ["summer"],
    "shorts": ["summer"],

    "books": ["autumn", "winter"],
    "puzzles": ["autumn", "winter"],
    "stationery": ["back_to_school", "autumn"],
    "beach": ["summer"],
    "garden": ["spring", "summer"],
    "heaters": ["winter"],
    "tea": ["winter"],

    "groceries": ["spring", "summer", "autumn", "winter"],
    "fresh produce": ["spring", "summer"],
    "fruits": ["spring", "summer"],
    "vegetables": ["spring", "summer", "autumn"],
    "dairy & eggs": ["spring", "summer", "autumn", "winter"],
    "baked goods": ["autumn", "winter"],
    "meat & poultry": ["spring", "summer", "autumn", "winter"],
    "seafood": ["spring", "summer"],
    "snacks": ["spring", "summer", "autumn", "winter"],
    "beverages": ["spring", "summer"],
    "breakfast & cereals": ["spring", "summer", "autumn", "winter"],
    "canned goods": ["autumn", "winter"],
    "frozen foods": ["summer", "winter"],
    "pasta & rice": ["autumn", "winter"],
    "sauces & spices": ["spring", "summer", "autumn", "winter"],
    "condiments": ["spring", "summer", "autumn", "winter"],
    "household supplies": ["spring", "summer", "autumn", "winter"],
    "personal care": ["spring", "summer", "autumn", "winter"],
}

SEASONAL_CONFIG = {
    "pull_user_season": 16,
    "pull_season_map": 12,
    "pull_user_top": 16,
    "pull_similar_per_cat": 12,
    "max_similar_cats": 5,
    "copurchase_days": 180,
    "copurchase_limit": 60,
    "site_top_cats_limit": 10,
    "site_pull_per_cat": 12,
    "fallback_min_fill_ratio": 0.5,
    "fallback_top_limit": 20,
    "fallback_days_back": 120,
    "recency_days": 90,
    "source_bonus": {
        "copurchase": 3.0,
        "user_top_category": 2.0,
        "similar_category": 1.5,
        "rule": 1.0,
        "site_top_category": 0.5,
        "fallback": 0.0,
    },
}

def _top_categories(days_back=180, user_id=None, limit=5):
    cutoff = timezone.now() - timedelta(days=days_back)
    qs = (
        OrderDetails.objects
        .select_related("order", "goods__product__category")
        .filter(order__order_date__gte=cutoff)
    )
    if user_id is not None:
        qs = qs.filter(order__user_id=user_id)
    agg = (
        qs.values("goods__product__category__id", "goods__product__category__name")
        .annotate(total_qty=Sum("quantity"))
        .order_by("-total_qty")[:limit]
    )
    return [
        (row["goods__product__category__id"], row["goods__product__category__name"]) 
        for row in agg if row.get("goods__product__category__id")
    ]


def get_current_season(date=None):
    d = date or timezone.now()
    m = d.month
    if m in (12, 1, 2):
        return "winter"
    elif m in (3, 4, 5):
        return "spring"
    elif m in (6, 7, 8):
        return "summer"
    else:
        return "autumn"


def load_sales_dataframe(product_ids=None, days_back=365 * 2):
    cache_key = f"sales_df_{days_back}_{','.join(map(str, product_ids)) if product_ids else 'all'}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached.copy()

    cutoff = timezone.now() - timedelta(days=days_back)
    qs = (
        OrderDetails.objects
        .select_related("order", "goods__product")
        .filter(order__order_date__gte=cutoff)
        .values("order__order_date", "goods__product_id", "quantity")
    )

    rows = []
    for r in qs:
        try:
            ds = r["order__order_date"].date()
            pid = r["goods__product_id"]
            qty = r["quantity"] or 0
            rows.append({"ds": pd.to_datetime(ds), "product_id": pid, "y": qty})
        except Exception:
            continue

    if not rows:
        df_daily = pd.DataFrame(columns=["ds", "product_id", "y"])
        _cache_set(cache_key, df_daily)
        return df_daily

    df = pd.DataFrame(rows)
    df_daily = df.groupby(["ds", "product_id"], as_index=False).agg({"y": "sum"})
    _cache_set(cache_key, df_daily)
    return df_daily


def top_selling_products(limit=30, days_back=365):
    cutoff = timezone.now() - timedelta(days=days_back)
    qs = (
        OrderDetails.objects
        .select_related("order", "goods__product")
        .filter(order__order_date__gte=cutoff)
        .values("goods__product_id")
        .annotate(total_qty=Sum("quantity"))
        .order_by("-total_qty")[:limit]
    )
    return [item["goods__product_id"] for item in qs if item["goods__product_id"]]


_PROPHEST_MODEL_CACHE = {}


def _train_prophet_for_product(df_product, product_id):
    if not PROPHET_AVAILABLE:
        return None

    cached = _PROPHEST_MODEL_CACHE.get(product_id)
    if cached and (time.time() - cached[1] < 3600):
        return cached[0]

    try:
        m = Prophet(changepoint_prior_scale=0.05, yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
        if len(df_product) < 30:
            return None
        m.fit(df_product)
        _PROPHEST_MODEL_CACHE[product_id] = (m, time.time())
        return m
    except Exception:
        return None


def forecast_growth_score_for_product(product_id, horizon_days=30, recent_window=30):
    if not PROPHET_AVAILABLE:
        return None

    df_all = load_sales_dataframe(days_back=365 * 2)
    df_p = df_all[df_all["product_id"] == product_id][["ds", "y"]].sort_values("ds")
    if df_p.empty or len(df_p) < 30:
        return None

    df_p_daily = df_p.set_index("ds").resample("D").sum().fillna(0).reset_index()
    df_p_daily.columns = ["ds", "y"]

    m = _train_prophet_for_product(df_p_daily, product_id)
    if not m:
        return None

    future = m.make_future_dataframe(periods=horizon_days, freq="D")
    try:
        fcst = m.predict(future)
    except Exception:
        return None

    recent_mean = df_p_daily.tail(recent_window)["y"].mean() if recent_window <= len(df_p_daily) else df_p_daily["y"].mean()
    forecast_part = fcst.tail(horizon_days)
    if forecast_part.empty:
        return None
    forecast_mean = float(forecast_part["yhat"].mean())

    eps = 1e-6
    score = (forecast_mean - recent_mean) / (recent_mean + eps)
    return float(score)


def rules_based_recommendations_for_user(user_id, top_n=6):
    now = timezone.now()
    season = get_current_season(now)

    user_top_categories = _top_categories(days_back=180, user_id=user_id, limit=8)
    user_categories = [cid for cid, _ in user_top_categories]

    candidates = []
    for cid in user_categories:
        try:
            cat = Category.objects.get(id=cid)
        except Category.DoesNotExist:
            continue
        cat_name = (cat.name or "").lower()
        seasons = CATEGORY_SEASON_MAP.get(cat_name, [])
        if season in seasons:
            goods_qs = Goods.objects.filter(product__category=cat, is_available=True, stock__gt=0)[: SEASONAL_CONFIG.get('pull_user_season', 16) ]
            for g in goods_qs:
                candidates.append((g.product.id, g.product.name, float(g.selling_price if g.selling_price else 0.0), "rule"))

    if len(candidates) < top_n and user_top_categories:
        for cid, cname in user_top_categories:
            try:
                cat = Category.objects.get(id=cid)
            except Category.DoesNotExist:
                continue
            goods_qs = Goods.objects.filter(product__category=cat, is_available=True, stock__gt=0)[: SEASONAL_CONFIG.get('pull_user_top', 16) ]
            for g in goods_qs:
                candidates.append((g.product.id, g.product.name, float(g.selling_price if g.selling_price else 0.0), "user_top_category"))


    if len(candidates) < top_n and user_top_categories and CATEGORY_SIMILARITY_MAP:
        for cid, cname in user_top_categories:
            try:
                base_cat = Category.objects.get(id=cid)
            except Category.DoesNotExist:
                continue
            similar_names = CATEGORY_SIMILARITY_MAP.get(base_cat.name, []) or CATEGORY_SIMILARITY_MAP.get((base_cat.name or "").title(), [])
            for sim_name in similar_names[: SEASONAL_CONFIG.get('max_similar_cats', 5) ]:
                sim_cat = Category.objects.filter(name__iexact=sim_name).first()
                if not sim_cat:
                    continue
                goods_qs = Goods.objects.filter(product__category=sim_cat, is_available=True, stock__gt=0)[: SEASONAL_CONFIG.get('pull_similar_per_cat', 12) ]
                for g in goods_qs:
                    candidates.append((g.product.id, g.product.name, float(g.selling_price if g.selling_price else 0.0), "similar_category"))

    if len(candidates) < top_n:
        for cat_name, seasons in CATEGORY_SEASON_MAP.items():
            if season in seasons:
                try:
                    cat = Category.objects.filter(name__iexact=cat_name).first()
                    if not cat:
                        continue
                    goods_qs = Goods.objects.filter(product__category=cat, is_available=True, stock__gt=0)[:12]
                    for g in goods_qs:
                        candidates.append((g.product.id, g.product.name, float(g.selling_price if g.selling_price else 0.0), "rule"))
                except Exception:
                    continue


    if len(candidates) < top_n:
        cutoff = now - timedelta(days=SEASONAL_CONFIG.get("copurchase_days", 180))
        user_pids = list(
            OrderDetails.objects
            .filter(order__user_id=user_id, order__order_date__gte=cutoff)
            .values_list('goods__product_id', flat=True)
        )
        if user_pids:
            related_order_ids = list(
                OrderDetails.objects
                .filter(order__order_date__gte=cutoff, goods__product_id__in=user_pids)
                .values_list('order_id', flat=True)
                .distinct()
            )
            if related_order_ids:
                others = (
                    OrderDetails.objects
                    .filter(order_id__in=related_order_ids)
                    .exclude(goods__product_id__in=user_pids)
                    .values('goods__product_id')
                    .annotate(total=Sum('quantity'))
                    .order_by('-total')
                )
                for r in others[: SEASONAL_CONFIG.get("copurchase_limit", 60) ]:
                    pid = r['goods__product_id']
                    try:
                        prod = Product.objects.get(id=pid)
                        goods = Goods.objects.filter(product=prod, is_available=True, stock__gt=0).first()
                        if goods:
                            candidates.append((prod.id, prod.name, float(goods.selling_price), "copurchase"))
                    except Exception:
                        continue

    if len(candidates) < top_n:
        site_top_cats = _top_categories(days_back=180, user_id=None, limit=SEASONAL_CONFIG.get("site_top_cats_limit", 10))
        for cid, _ in site_top_cats:
            try:
                cat = Category.objects.get(id=cid)
            except Category.DoesNotExist:
                continue
            goods_qs = Goods.objects.filter(product__category=cat, is_available=True, stock__gt=0)[: SEASONAL_CONFIG.get("site_pull_per_cat", 12) ]
            for g in goods_qs:
                candidates.append((g.product.id, g.product.name, float(g.selling_price if g.selling_price else 0.0), "site_top_category"))

    if len(candidates) < max(2, int(top_n * SEASONAL_CONFIG.get("fallback_min_fill_ratio", 0.5))):
        top = top_selling_products(limit=20, days_back=120)
        for pid in top:
            try:
                prod = Product.objects.get(id=pid)
                goods = Goods.objects.filter(product=prod).first()
                candidates.append((prod.id, prod.name, float(goods.selling_price if goods else 0.0), "fallback"))
            except Exception:
                continue

    pids = list({pid for (pid, _, _, _) in candidates})
    recent_cutoff = now - timedelta(days=SEASONAL_CONFIG.get("recency_days", 90))
    rec_map = {
        r['goods__product_id']: float(r['total'] or 0)
        for r in (
            OrderDetails.objects
            .filter(order__order_date__gte=recent_cutoff, goods__product_id__in=pids)
            .values('goods__product_id')
            .annotate(total=Sum('quantity'))
        )
    }
    source_bonus = dict(SEASONAL_CONFIG.get("source_bonus", {}))
    best = {}
    for pid, name, price, source in candidates:
        score = rec_map.get(pid, 0.0) + source_bonus.get(source, 0.0)
        entry = best.get(pid)
        if not entry or score > entry['score']:
            best[pid] = {'product_id': pid, 'product_name': name, 'price': price, 'sources': [source], 'score': score}
        elif source not in entry['sources']:
            entry['sources'].append(source)
    ranked = sorted(best.values(), key=lambda x: x['score'], reverse=True)
    return [{k: v for k, v in d.items() if k != 'score'} for d in ranked[:top_n]]


def prophet_based_recommendations(top_n=8, horizon_days=30, top_products_to_consider=50):
    if not PROPHET_AVAILABLE:
        return []

    candidate_pids = top_selling_products(limit=top_products_to_consider, days_back=365)
    if not candidate_pids:
        return []

    scores = {}
    for pid in candidate_pids:
        try:
            score = forecast_growth_score_for_product(pid, horizon_days=horizon_days)
            if score is not None:
                scores[pid] = score
        except Exception:
            continue

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    recs = []
    for pid, score in ranked[:top_n * 2]:
        try:
            prod = Product.objects.get(id=pid)
            goods = Goods.objects.filter(product=prod).first()
            recs.append({
                "product_id": prod.id,
                "product_name": prod.name,
                "price": float(goods.selling_price) if goods and goods.selling_price else 0.0,
                "forecast_score": float(score),
                "sources": ["forecast"]
            })
        except Exception:
            continue

    return recs[:top_n]


def get_product_detail_dict(pid):
    try:
        prod = Product.objects.select_related("category").get(id=pid)
        goods = Goods.objects.filter(product=prod).first()
        image_url = None
        try:
            if getattr(prod, "image", None) and getattr(prod.image, "name", ""):
                image_url = prod.image.url
        except Exception:
            image_url = None

        return {
            "product_id": prod.id,
            "product_name": prod.name,
            "category_name": prod.category.name if prod.category else None,
            "description": prod.description,
            "image": image_url,
            "price": float(goods.selling_price) if goods and goods.selling_price else None,
        }
    except Exception:
        return None


def get_recommendations_for_user(user_id, top_n=8, horizon_days=30):
    rules = rules_based_recommendations_for_user(user_id, top_n=top_n)
    forecasts = prophet_based_recommendations(top_n=top_n, horizon_days=horizon_days)

    map_rules = {r["product_id"]: r for r in rules}
    map_fore = {f["product_id"]: f for f in forecasts}

    final = []
    used = set()

    for pid in list(map_rules.keys()):
        if pid in map_fore:
            entry = map_rules[pid]
            entry["sources"] = list(set(entry.get("sources", []) + map_fore[pid].get("sources", [])))
            details = get_product_detail_dict(pid)
            if details:
                details["sources"] = entry["sources"]
                final.append(details)
                used.add(pid)
            if len(final) >= top_n:
                return final

    for r in rules:
        pid = r["product_id"]
        if pid in used:
            continue
        details = get_product_detail_dict(pid)
        if details:
            details["sources"] = r.get("sources", ["rule"])
            final.append(details)
            used.add(pid)
        if len(final) >= top_n:
            return final

    for f in forecasts:
        pid = f["product_id"]
        if pid in used:
            continue
        details = get_product_detail_dict(pid)
        if details:
            details["sources"] = f.get("sources", ["forecast"])
            final.append(details)
            used.add(pid)
        if len(final) >= top_n:
            return final

    if len(final) < top_n:
        top = top_selling_products(limit=top_n * 2, days_back=90)
        for pid in top:
            if pid in used:
                continue
            details = get_product_detail_dict(pid)
            if details:
                details["sources"] = ["fallback"]
                final.append(details)
                used.add(pid)
            if len(final) >= top_n:
                break

    return final[:top_n]
