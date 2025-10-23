import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import KMeans
from store.models import OrderDetails, Product, Goods, Category, Shop
from django.db.models import Count

def load_data():
    qs = (
        OrderDetails.objects
        .select_related("order", "goods__product")
        .values(
            "order__user_id",
            "goods__product_id",
            "goods__product__category_id",
        )
    )
    df = pd.DataFrame(list(qs))

    df.rename(columns={
        "order__user_id": "user_id",
        "goods__product_id": "product_id",
        "goods__product__category_id": "category_id",
    }, inplace=True)

    return df

df = load_data()

user_category_matrix = df.pivot_table(
    index='user_id',
    columns='category_id',
    aggfunc='size',
    fill_value=0
)

svd = TruncatedSVD(n_components=15, random_state=1)
user_embeddings = svd.fit_transform(user_category_matrix)

kmeans = KMeans(n_clusters=15, random_state=1)
clusters = kmeans.fit_predict(user_embeddings)

user_cluster_df = pd.DataFrame({
    'user_id': user_category_matrix.index,
    'cluster_id': clusters
})

def get_user_vector(user_id):
    idx = user_category_matrix.index.get_loc(user_id)
    return user_embeddings[idx], idx

def get_user_products(user_id):
    return df[df['user_id'] == user_id]['product_id']

def get_user_categories(user_id):
    return set(df[df['user_id'] == user_id]['category_id'])

def get_product_category(product_id):
    row = df[df['product_id'] == product_id]
    return row['category_id'].values[0] if not row.empty else None

def get_product_details(product_id):
    try:
        product = Product.objects.select_related("category").get(id=product_id)
        goods = product.goods.first()
        return {
            "product_id": product.id,
            "product_name": product.name,
            "category_name": product.category.name if product.category else "Unknown",
            "description": product.description,
            "image": product.image,
            "price": goods.selling_price if goods else None,
        }
    except Product.DoesNotExist:
        return None


def get_fallback_recommendations(top_n=3):
    products = (
        Goods.objects
        .filter(is_available=True, stock__gt=0)
        .annotate(order_count=Count("orderdetails"))
        .order_by("-order_count")[:top_n]
    )
    recs = []
    for goods in products:
        details = get_product_details(goods.product.id)
        if details:
            recs.append(details)
    return recs


def recommend_from_shared_category(target_user_id, top_n=4):
    try:
        cluster_id = user_cluster_df.set_index("user_id").loc[target_user_id]["cluster_id"]
    except KeyError:
        return get_fallback_recommendations(top_n)

    same_users = user_cluster_df[user_cluster_df["cluster_id"] == cluster_id]["user_id"].tolist()
    if len(same_users) <= 1:
        return get_fallback_recommendations(top_n)

    embeddings = user_embeddings[[user_category_matrix.index.get_loc(uid) for uid in same_users]]
    knn = NearestNeighbors(n_neighbors=len(same_users), metric="cosine")
    knn.fit(embeddings)

    target_index = same_users.index(target_user_id)
    distances, indices = knn.kneighbors([embeddings[target_index]])

    target_products = set(get_user_products(target_user_id))
    target_categories = get_user_categories(target_user_id)

    recs = []
    for i in indices[0][1:]:
        similar_user = same_users[i]
        sim_df = df[df["user_id"] == similar_user]
        shared = target_categories & set(sim_df["category_id"])
        if not shared:
            continue

        sim_products = sim_df[sim_df["category_id"].isin(shared)]["product_id"]
        candidates = set(sim_products) - target_products

        for pid in candidates:
            details = get_product_details(pid)
            if details:
                recs.append(details)
            if len(recs) >= top_n:
                return recs

    return recs if recs else get_fallback_recommendations(top_n)


def recommend_from_new_category(target_user_id, top_n=4):
    try:
        cluster_id = user_cluster_df.set_index("user_id").loc[target_user_id]["cluster_id"]
    except KeyError:
        return get_fallback_recommendations(top_n)

    outside_users = user_cluster_df[user_cluster_df["cluster_id"] != cluster_id]["user_id"].tolist()
    if not outside_users:
        return get_fallback_recommendations(top_n)

    outside_embeddings = user_embeddings[[user_category_matrix.index.get_loc(uid) for uid in outside_users]]
    knn = NearestNeighbors(n_neighbors=len(outside_users), metric="cosine")
    knn.fit(outside_embeddings)

    vector, index = get_user_vector(target_user_id)
    distances, indices = knn.kneighbors([vector])

    target_products = set(get_user_products(target_user_id))
    target_categories = get_user_categories(target_user_id)

    recs = []
    for i in indices[0]:
        similar_user = outside_users[i]
        sim_df = df[df["user_id"] == similar_user]

        new_categories = set(sim_df["category_id"]) - target_categories
        if not new_categories:
            continue

        sim_products = sim_df[sim_df["category_id"].isin(new_categories)]["product_id"]
        candidates = set(sim_products) - target_products

        for pid in candidates:
            details = get_product_details(pid)
            if details:
                recs.append(details)
            if len(recs) >= top_n:
                return recs

    return recs if recs else get_fallback_recommendations(top_n)


def get_cluster_stats(target_user_id=None):
    try:
        cluster_counts = (
            user_cluster_df["cluster_id"]
            .value_counts()
            .sort_index()
            .to_dict()
        )

        total_clusters = len(cluster_counts)

        user_cluster = None
        if target_user_id in user_cluster_df["user_id"].values:
            user_cluster = (
                user_cluster_df
                .set_index("user_id")
                .loc[target_user_id]["cluster_id"]
            )

        return {
            "total_clusters": total_clusters,
            "cluster_sizes": cluster_counts,
            "user_cluster": user_cluster,
        }

    except Exception as e:
        print(f" خطأ في get_cluster_stats: {e}")
        return {
            "total_clusters": 0,
            "cluster_sizes": {},
            "user_cluster": None,
        }
