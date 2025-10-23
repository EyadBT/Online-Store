import datetime
from experta import *
from store.models import OrderDetails, Product
from django.utils import timezone
from django.db.models import Sum


class TimePeriod(Fact):
    period = Field(str, mandatory=True)


class Recommendation(Fact):
    pass


class TrendingEngine(KnowledgeEngine):
    def __init__(self):
        super().__init__()
        self.results = []

    @Rule(TimePeriod(period="day"))
    def daily_trending(self):
        start = timezone.now() - datetime.timedelta(days=1)
        recs = self._get_trending_products(start)
        if not recs:
            for days in (7, 30, 90):
                recs = self._get_trending_products(timezone.now() - datetime.timedelta(days=days))
                if recs:
                    break
        self.declare(Recommendation(recommendations=recs, label="Daily Trending"))

    @Rule(TimePeriod(period="week"))
    def weekly_trending(self):
        start = timezone.now() - datetime.timedelta(weeks=1)
        recs = self._get_trending_products(start)
        if not recs:
            for days in (30, 90):
                recs = self._get_trending_products(timezone.now() - datetime.timedelta(days=days))
                if recs:
                    break
        self.declare(Recommendation(recommendations=recs, label="Weekly Trending"))

    @Rule(TimePeriod(period="month"))
    def monthly_trending(self):
        start = timezone.now() - datetime.timedelta(days=30)
        recs = self._get_trending_products(start)
        if not recs:
            for days in (90, 180):
                recs = self._get_trending_products(timezone.now() - datetime.timedelta(days=days))
                if recs:
                    break
        self.declare(Recommendation(recommendations=recs, label="Monthly Trending"))

    @Rule(TimePeriod(period="season"))
    def seasonal_trending(self):
        month = timezone.now().month
        if month in [12, 1, 2]:
            season = "Winter"
        elif month in [3, 4, 5]:
            season = "Spring"
        elif month in [6, 7, 8]:
            season = "Summer"
        else:
            season = "Autumn"

        start = timezone.now() - datetime.timedelta(days=90)
        recs = self._get_trending_products(start)
        if not recs:
            for days in (180, 365):
                recs = self._get_trending_products(timezone.now() - datetime.timedelta(days=days))
                if recs:
                    break
        self.declare(Recommendation(recommendations=recs, label=f"{season} Trending"))

    def _get_trending_products(self, start_time, limit=8):
        qs = (
            OrderDetails.objects
            .filter(order__order_date__gte=start_time)
            .values("goods__product_id")
            .annotate(total_sold=Sum("quantity"))
            .order_by("-total_sold")[:limit]
        )

        products = []
        for row in qs:
            try:
                product = Product.objects.get(id=row["goods__product_id"])
                products.append({
                    "id": product.id,
                    "name": product.name,
                    "category": product.category.name if product.category else "Unknown",
                    "image": product.image.url if product.image else None,
                    "sold": row["total_sold"],
                })
            except Product.DoesNotExist:
                continue

        return products
