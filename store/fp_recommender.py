import pandas as pd
from mlxtend.frequent_patterns import fpgrowth, association_rules
from store.models import OrderDetails, Product, Goods

def build_fp_model(user=None, min_support=0.01, min_threshold=0.2):
    qs = OrderDetails.objects.all().values("order__id", "goods__product_id")
    if user and user.is_authenticated:
        qs = qs.filter(order__user=user)

    df = pd.DataFrame(list(qs))
    if df.empty:
        return None, None

    df.rename(columns={"order__id": "order_id", "goods__product_id": "product_id"}, inplace=True)
    basket = df.groupby(["order_id", "product_id"])["product_id"].count().unstack().fillna(0)
    basket = basket.astype(bool)

    frequent_itemsets = fpgrowth(basket, min_support=min_support, use_colnames=True)
    if frequent_itemsets.empty:
        return None, None

    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_threshold)
    return rules, df["product_id"].unique()


def get_fp_recommendations_for_product(user, product_id, top_k=3):
    rules, all_products = build_fp_model(user)
    if rules is None:
        return [], []

    related = []
    for _, row in rules.iterrows():
        antecedents = list(row["antecedents"])
        consequents = list(row["consequents"])
        conf = row["confidence"]

        if len(antecedents) == 1 and antecedents[0] == product_id and len(consequents) == 1:
            related.append((consequents[0], conf))

    related = sorted(related, key=lambda x: x[1], reverse=True)
    top_related = related[:top_k]

    recs = []
    for pid, prob in top_related:
        try:
            product = Product.objects.get(id=pid)
            goods = Goods.objects.filter(product=product).first()
            price = float(goods.selling_price) if goods else 0.0
            recs.append({"product": product, "probability": prob, "price": price})
        except Product.DoesNotExist:
            continue

    bundle_offers = []
    if len(recs) >= 3:
        selected = recs[:3]
        total_original_price = sum(item["price"] for item in selected)
        discount_percentage = 5
        bundle_price = total_original_price * (1 - discount_percentage/100)
    
    if len(recs) >= 3:
        selected = recs[:3]
        total_original = sum(item["price"] for item in selected if item["price"])
        discount = 5
        final_price = total_original * (1 - discount / 100)

        bundle_offers.append({
            "bundle_id": f"fp_bundle_{product_id}",
            "bundle_name": "FP-Growth Smart Bundle",
            "products": selected,
            "total_original_price": total_original_price,
            "bundle_price": bundle_price,
            "total_savings": total_original_price - bundle_price,
            "discount_percentage": discount_percentage,
            "description": "Special FP-Growth bundle with 5% off for 3 products."
        })

    return recs, bundle_offers
