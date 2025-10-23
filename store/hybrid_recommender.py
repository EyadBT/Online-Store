import pandas as pd
import numpy as np
from django.db.models import Avg
from store.models import Review, Product, Goods

def get_hybrid_recommendations(user_id, limit=8, factors=20, iterations=15, reg=0.1):

    reviews = Review.objects.all().values("user_id", "product_id", "rating")
    if not reviews.exists():
        return []

    reviews_df = pd.DataFrame(list(reviews))

    user_ids = reviews_df["user_id"].unique()
    product_ids = reviews_df["product_id"].unique()
    user_index = {u: i for i, u in enumerate(user_ids)}
    product_index = {p: i for i, p in enumerate(product_ids)}

    R = np.zeros((len(user_ids), len(product_ids)))
    for _, row in reviews_df.iterrows():
        R[user_index[row["user_id"]], product_index[row["product_id"]]] = row["rating"]

    np.random.seed(42)
    U = np.random.normal(scale=1. / factors, size=(len(user_ids), factors))
    V = np.random.normal(scale=1. / factors, size=(len(product_ids), factors))

    for _ in range(iterations):
        for u in range(len(user_ids)):
            idx = R[u, :] > 0
            if np.sum(idx) == 0:
                continue
            V_i = V[idx]
            R_u = R[u, idx]
            A = V_i.T @ V_i + reg * np.eye(factors)
            b = V_i.T @ R_u
            U[u] = np.linalg.solve(A, b)

        for i in range(len(product_ids)):
            idx = R[:, i] > 0
            if np.sum(idx) == 0:
                continue
            U_i = U[idx]
            R_i = R[idx, i]
            A = U_i.T @ U_i + reg * np.eye(factors)
            b = U_i.T @ R_i
            V[i] = np.linalg.solve(A, b)

    predictions = U @ V.T
    predicted_df = pd.DataFrame(predictions, index=user_ids, columns=product_ids)

    user_reviews = reviews_df[reviews_df["user_id"] == user_id]
    if user_reviews.empty:
        return []
    products = Product.objects.filter(id__in=user_reviews["product_id"].tolist())
    goods_map = {g.product_id: float(g.selling_price) for g in Goods.objects.filter(product__in=products)}
    user_reviews = user_reviews.copy()
    user_reviews.loc[:, "price"] = user_reviews["product_id"].map(goods_map)
    user_reviews = user_reviews.dropna(subset=["price"])
    if user_reviews.empty:
        return []
    pq_values = user_reviews["price"] / user_reviews["rating"]
    mu, sigma = pq_values.mean(), pq_values.std()

    candidate_products = Product.objects.exclude(id__in=user_reviews["product_id"].tolist())

    recs = []
    for product in candidate_products:
        if product.id not in predicted_df.columns or user_id not in predicted_df.index:
            continue
        pred_rating = predicted_df.loc[user_id, product.id]
        if pred_rating <= 0:
            continue

        goods = Goods.objects.filter(product=product).first()
        if not goods:
            continue
        price = float(goods.selling_price)
        pq_score = price / float(pred_rating)
        distance = abs(pq_score - mu)

        recs.append({
            "product": product,
            "price": price,
            "pred_rating": float(pred_rating),
            "pq_score": float(pq_score),
            "distance": float(distance),
        })

    recs = sorted(recs, key=lambda x: (x["distance"], -x["pred_rating"]))[:limit]
    return recs

