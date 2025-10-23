
from collections import defaultdict


CATEGORY_GROUPS = {
    "Electronics": [
        "Electronics", "Smartphones", "Tablets", "Laptops", "Desktops", "PC Components",
        "Monitors", "Keyboards", "Mice", "Cameras", "Photography Accessories",
        "Drones", "Wearables", "Smartwatches", "TV & Home Theater", "Audio",
        "Headphones", "Speakers", "Networking", "Routers", "Storage", "Printers",
        "Scanning", "Software", "E-Readers", "Projectors"
    ],
    "Gaming": [
        "Video Games", "Consoles", "Gaming Accessories", "PC Gaming", "VR & AR",
        "Game Controllers", "Gaming Chairs"
    ],
    "Computing": [
        "Servers", "Networking Gear", "Cables & Adapters", "UPS & Power", "3D Printing"
    ],
    "Clothing": [
        "Clothing", "Men's Clothing", "Women's Clothing", "Kids' Clothing", "Shoes",
        "Accessories", "Jewelry", "Watches", "Bags & Luggage"
    ],
    "BeautyHealth": [
        "Beauty", "Skincare", "Hair Care", "Makeup", "Fragrances", "Health",
        "Vitamins & Supplements", "Personal Care"
    ],
    "BabyToys": [
        "Baby", "Diapers", "Baby Gear", "Toys & Games", "Board Games", "Puzzles",
        "Educational Toys"
    ],
    "BooksMedia": [
        "Books", "eBooks", "Music", "Musical Instruments", "Movies"
    ],
    "HomeKitchen": [
        "Home & Kitchen", "Furniture", "Bedding", "Bath", "Kitchen Appliances",
        "Cookware", "Dining", "Storage & Organization", "Cleaning Supplies",
        "Lighting", "Home Decor"
    ],
    "GardenTools": [
        "Garden & Outdoor", "Patio & Lawn", "Grills & Outdoor Cooking",
        "Tools & Home Improvement", "Power Tools", "Hand Tools"
    ],
    "Automotive": [
        "Automotive", "Car Electronics", "Car Accessories", "Motorcycle"
    ],
    "Industrial": [
        "Industrial", "Lab Equipment", "Safety Supplies"
    ],
    "PetGrocery": [
        "Pet Supplies", "Groceries", "Snacks", "Beverages", "Gourmet"
    ],
    "SportsOutdoor": [
        "Sports & Outdoors", "Exercise & Fitness", "Camping & Hiking", "Cycling",
        "Team Sports", "Winter Sports", "Water Sports"
    ],
    "ArtsOffice": [
        "Arts & Crafts", "Craft Supplies", "Office Supplies", "Office Furniture",
        "Stationery"
    ],
    "SmartSecurity": [
        "Smart Home", "Security & Surveillance", "Energy & Utilities"
    ],
    "TravelParty": [
        "Travel", "Party Supplies"
    ],
    "Medical": [
        "Medical Supplies", "Mobility Aids"
    ],
    "CollectiblesHobbies": [
        "Collectibles", "Antiques", "Coins", "Stamps", "Memorabilia", "Hobbies"
    ],
    "PhotoPrint": [
        "Photography Accessories", "Printing & Scanning"
    ],
    "GreenEtc": [
        "Green Living", "Sustainable Products", "Secondhand", "DIY Kits", "Seasonal"
    ],
    "Other": ["Other"]
}


ALL_CATEGORIES = []
seen = set()
for group, items in CATEGORY_GROUPS.items():
    for name in items:
        if name not in seen:
            seen.add(name)
            ALL_CATEGORIES.append(name)

if "Other" not in seen:
    ALL_CATEGORIES.append("Other")


def build_similarity_map():
    mapping = defaultdict(list)

    def extend_unique(target, items):
        existing = set(target)
        for it in items:
            if it != target and it not in existing:
                target.append(it)
                existing.add(it)

    for group, items in CATEGORY_GROUPS.items():
        for cat in items:
            similars = [x for x in items if x != cat]
            mapping[cat].extend(similars[:5])  # cap to 5 per group

    cross_links = [
        ("Electronics", ["Gaming", "Computing", "SmartSecurity"]),
        ("Gaming", ["Electronics", "Computing"]),
        ("HomeKitchen", ["GardenTools", "SmartSecurity", "Cleaning Supplies", "Storage & Organization"]),
        ("SportsOutdoor", ["Travel", "Exercise & Fitness"]),
        ("BooksMedia", ["Arts & Crafts", "Educational Toys"]),
        ("BeautyHealth", ["Personal Care", "Vitamins & Supplements"]),
        ("PetGrocery", ["Groceries", "Snacks"]),
        ("ArtsOffice", ["Stationery", "Craft Supplies"]),
        ("GreenEtc", ["Sustainable Products", "Secondhand"]),
    ]

    for group_key, related in cross_links:
        base_items = CATEGORY_GROUPS.get(group_key, [])
        for cat in base_items:
            candidates = []
            for rel in related:
                if rel in CATEGORY_GROUPS:
                    candidates.extend(CATEGORY_GROUPS[rel][:2])  # take top 2 from related group
                else:
                    candidates.append(rel)
            extend_unique(mapping[cat], [c for c in candidates if c != cat])

    for cat in ALL_CATEGORIES:
        if len(mapping[cat]) == 0:
            mapping[cat] = [c for c in (CATEGORY_GROUPS.get("Other", []) or ["Other"]) if c != cat]
        if "Other" not in mapping[cat] and cat != "Other":
            mapping[cat].append("Other")
        mapping[cat] = mapping[cat][:8]

    return dict(mapping)


CATEGORY_SIMILARITY_MAP = build_similarity_map() 