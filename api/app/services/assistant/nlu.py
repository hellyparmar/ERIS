"""Rule-based natural-language understanding for retail questions.

Extracts intent, time periods, outlets, categories, products, "top N" and forecast horizon from plain
English (with a little Hinglish). Fast, deterministic and works offline; an optional LLM can refine it.
"""
from __future__ import annotations

import calendar
import re
from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import clock
from app.models import Category, Outlet, Product
from app.services.analytics import DateRange

MONTHS = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
MONTHS.update({m.lower(): i for i, m in enumerate(calendar.month_abbr) if m})
MONTHS["sept"] = 9

INTENTS = [
    "business_overview", "sales_summary", "compare_periods", "sales_trend", "top_products", "slow_products",
    "outlet_ranking", "category_mix", "forecast", "stock_status", "reorder", "customers", "peak_hours",
    "payment_mix", "profitability", "purchase_orders", "basket_analysis", "advice", "help", "general",
]

# (intent, weight, pattern)
INTENT_PATTERNS: list[tuple[str, float, str]] = [
    ("forecast", 3, r"\b(forecast|predict|prediction|projection|project(ed)?|expect(ed)?|anticipate|outlook)\b"),
    ("forecast", 2.5, r"\b(next|coming|upcoming)\s+(\d+\s+)?(day|days|week|weeks|month|months|fortnight|quarter)\b"),
    ("forecast", 2, r"\b(tomorrow|will (we|i|it)|going to sell|future demand|demand for)\b"),
    ("reorder", 3, r"\b(reorder|re-order|restock|replenish|what should (i|we) (order|buy)|purchase suggestion|order more)\b"),
    ("stock_status", 3, r"\b(out of stock|stock ?out|low stock|running low|stock level|in stock|inventory|stock khatam|how much .* (left|have))\b"),
    ("stock_status", 1.5, r"\bstock\b"),
    ("top_products", 3, r"\b(top|best|most|highest|popular|fast)[\s-]*(\d+\s+)?(selling|seller|sellers|sold|moving|products?|items?|skus?)\b"),
    ("top_products", 1.5, r"\b(best|top)\s+\d*\s*(products?|items?)\b|\bbestsellers?\b"),
    ("slow_products", 3, r"\b(slow|least|worst|lowest|poor(ly)?|bottom|dead)[\s-]*(\d+\s+)?(selling|seller|sellers|sold|moving|performing|products?|items?|stock)\b|\bnot selling\b"),
    ("outlet_ranking", 3, r"\b(outlets?|stores?|branch(es)?|shops?|locations?)\b.*\b(best|worst|top|rank|ranking|compare|comparison|performance|performing|perform|which)\b"),
    ("outlet_ranking", 3, r"\b(best|worst|top|rank|ranking|compare|comparison|which)\b.*\b(outlets?|stores?|branch(es)?|shops?|locations?)\b"),
    ("category_mix", 3, r"\b(categor(y|ies)|department|segment mix|sales mix|product mix)\b"),
    ("customers", 3, r"\b(customers?|clients?|shoppers?|loyal(ty)?|churn|at risk|repeat|rfm|segments?)\b"),
    ("peak_hours", 3, r"\b(peak|busiest|rush|footfall|what time|which (hour|day)|busy (hours?|days?)|slowest (hour|day|time))\b"),
    ("payment_mix", 3, r"\b(payment|upi|cash|card|credit|digital payments?)\b"),
    ("profitability", 3, r"\b(margin|margins|profitab\w*|most profitable|least profitable|markup)\b"),
    ("profitability", 1, r"\bprofit\b"),
    ("purchase_orders", 3, r"\b(purchase orders?|pos?\b|pending orders?|supplier orders?|deliver(y|ies) from|overdue orders?)\b"),
    ("sales_trend", 3, r"\b(trend|trends|growth|grow|grew|growing|declin\w*|over time|month on month|month-over-month|monthly sales|weekly sales|yoy|year over year)\b"),
    ("compare_periods", 3, r"\b(compare|comparison|versus|vs\.?|compared (to|with))\b"),
    ("sales_summary", 2, r"\b(sales|sell|sold|revenue|turnover|income|earn\w*|orders?|bills?|transactions?|basket|bikri|kitna)\b"),
    ("sales_summary", 1, r"\b(how much|how many|total)\b"),
    ("business_overview", 3, r"\b(how (is|was|are) (the )?(business|we doing|things|sales going)|overview|summary|summari[sz]e|brief(ing)?|insights?|focus on|health|kpis?|dashboard|highlights?|what('s| is) happening)\b"),
    ("advice", 3.5, r"\b(how (can|do|should|could|to) (i|we)? ?(increase|improve|boost|grow|raise|reduce|cut|get more|sell more|attract|win)|ways to|tips|recommendations?|advice|advise|ideas|action items|what (can|should) (i|we) do)\b"),
    ("advice", 3, r"\b(increase|improve|boost|grow|maximi[sz]e) (my |our |the )?(sales|revenue|profits?|margins?|footfall|customers|business)\b"),
    ("basket_analysis", 4, r"\b(bought together|buy together|cross[- ]?sell|bundle|bundles|basket analysis|market basket|combo|combos|pairs? well|affinity|goes (well )?with|go (well )?with|bought with|buy with|along with|paired with)\b"),
    ("help", 4, r"^\s*(hi|hello|hey|namaste|help|what can you do|who are you)\b[\s!?.]*$"),
    ("help", 3, r"\b(what can you do|how do i use|what can i ask|capabilities)\b"),
]

CATEGORY_SYNONYMS = {
    "beverage": "Beverages", "beverages": "Beverages", "drinks": "Beverages", "drink": "Beverages", "juices": "Beverages",
    "tea": "Tea & Coffee", "coffee": "Tea & Coffee", "chai": "Tea & Coffee",
    "dairy": "Dairy & Eggs", "eggs": "Dairy & Eggs",
    "bakery": "Bakery", "breads": "Bakery", "baked": "Bakery",
    "snacks": "Snacks & Confectionery", "snack": "Snacks & Confectionery", "confectionery": "Snacks & Confectionery",
    "staples": "Staples & Grains", "grains": "Staples & Grains", "groceries": "Staples & Grains", "grocery": "Staples & Grains",
    "fruits": "Fruits & Vegetables", "fruit": "Fruits & Vegetables", "vegetables": "Fruits & Vegetables",
    "veggies": "Fruits & Vegetables", "produce": "Fruits & Vegetables", "sabzi": "Fruits & Vegetables",
    "frozen": "Frozen & Ready-to-eat", "ready to eat": "Frozen & Ready-to-eat", "ready-to-eat": "Frozen & Ready-to-eat",
    "sweets": "Sweets & Festive", "mithai": "Sweets & Festive", "festive": "Sweets & Festive",
}
PRODUCT_STOPWORDS = {
    "and", "the", "with", "pack", "pcs", "fresh", "classic", "packaged", "premium", "organic", "farm", "box", "tin",
    "bag", "bar", "cup", "jar", "loaf", "roasted", "extra", "whole", "salted", "plain", "mix", "ready", "eat",
    "tender", "toned", "malai", "robusta", "shimla", "hass", "red", "baby", "belgian", "california", "alphonso",
    "darjeeling", "assam", "refined", "virgin", "rolled", "gift", "frozen", "cold",
}


def _stem(word: str) -> str:
    """Very small plural stemmer: mangoes -> mango, eggs -> egg, peaches -> peach."""
    if len(word) > 4 and word.endswith(("oes", "ches", "shes", "xes")):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


@dataclass
class Parsed:
    text: str
    intent: str = "general"
    confidence: float = 0.0
    periods: list[tuple[DateRange, str]] = field(default_factory=list)
    outlet_ids: list[int] = field(default_factory=list)
    outlet_names: list[str] = field(default_factory=list)
    category_id: int | None = None
    category_name: str | None = None
    product_ids: list[int] = field(default_factory=list)
    product_names: list[str] = field(default_factory=list)
    top_n: int | None = None
    horizon: int | None = None
    sort: str = "revenue"
    flags: set[str] = field(default_factory=set)

    @property
    def period(self) -> tuple[DateRange, str] | None:
        return self.periods[0] if self.periods else None

    def to_context(self) -> dict:
        return {
            "intent": self.intent,
            "periods": [{"start": r.start.isoformat(), "end": r.end.isoformat(), "label": label} for r, label in self.periods],
            "outlet_ids": self.outlet_ids, "outlet_names": self.outlet_names,
            "category_id": self.category_id, "category_name": self.category_name,
            "product_ids": self.product_ids, "product_names": self.product_names,
            "top_n": self.top_n, "horizon": self.horizon, "sort": self.sort, "flags": sorted(self.flags),
        }


# ------------------------------------------------------------------------------------------ periods
def _month_range(year: int, month: int) -> DateRange:
    return DateRange(date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1]))


def _clip(r: DateRange, anchor: date) -> DateRange:
    return DateRange(r.start, min(r.end, anchor))


def parse_periods(text: str, anchor: date) -> list[tuple[DateRange, str]]:
    t = text.lower()
    found: list[tuple[int, DateRange, str]] = []

    def add(m: re.Match, r: DateRange, label: str):
        if r.start <= anchor:
            found.append((m.start(), _clip(r, anchor), label))

    for m in re.finditer(r"\b(today|aaj)\b", t):
        add(m, DateRange(anchor, anchor), "today" if anchor == clock.today() else f"{anchor:%d %b %Y} (latest data)")
    for m in re.finditer(r"\byesterday\b", t):
        d = anchor - timedelta(days=1)
        add(m, DateRange(d, d), f"yesterday ({d:%d %b})")
    for m in re.finditer(r"\b(this|current) week\b", t):
        add(m, DateRange(anchor - timedelta(days=anchor.weekday()), anchor), "this week")
    for m in re.finditer(r"\b(last|previous|past) week\b", t):
        start = anchor - timedelta(days=anchor.weekday() + 7)
        add(m, DateRange(start, start + timedelta(days=6)), "last week")
    for m in re.finditer(r"\b(this|current) month\b|\bmtd\b", t):
        add(m, DateRange(anchor.replace(day=1), anchor), f"this month ({anchor:%B})")
    for m in re.finditer(r"\b(last|previous|past) month\b", t):
        prev = anchor.replace(day=1) - timedelta(days=1)
        add(m, _month_range(prev.year, prev.month), f"last month ({prev:%B %Y})")
    for m in re.finditer(r"\b(this|current) year\b|\bytd\b", t):
        add(m, DateRange(anchor.replace(month=1, day=1), anchor), f"this year ({anchor.year})")
    for m in re.finditer(r"\b(last|previous|past) year\b", t):
        y = anchor.year - 1
        add(m, DateRange(date(y, 1, 1), date(y, 12, 31)), f"last year ({y})")
    for m in re.finditer(r"\b(this|current) quarter\b", t):
        q_start = date(anchor.year, 3 * ((anchor.month - 1) // 3) + 1, 1)
        add(m, DateRange(q_start, anchor), "this quarter")
    for m in re.finditer(r"\b(last|previous) quarter\b", t):
        q_start = date(anchor.year, 3 * ((anchor.month - 1) // 3) + 1, 1)
        prev_end = q_start - timedelta(days=1)
        prev_start = date(prev_end.year, 3 * ((prev_end.month - 1) // 3) + 1, 1)
        add(m, DateRange(prev_start, prev_end), "last quarter")
    for m in re.finditer(r"\b(?:last|past|previous|recent)\s+(\d{1,3})\s*(day|week|month|year)s?\b", t):
        n, unit = int(m.group(1)), m.group(2)
        days = n * {"day": 1, "week": 7, "month": 30, "year": 365}[unit]
        add(m, DateRange(anchor - timedelta(days=days - 1), anchor), f"last {n} {unit}{'s' if n > 1 else ''}")
    for m in re.finditer(r"\b(?:last|past)\s+(fortnight)\b", t):
        add(m, DateRange(anchor - timedelta(days=13), anchor), "last 14 days")
    month_re = "|".join(sorted(MONTHS, key=len, reverse=True))
    for m in re.finditer(rf"\b({month_re})\b(?:[\s,']+(\d{{4}}|\d{{2}}))?", t):
        word = m.group(1)
        if word in ("may", "mar") and not re.search(rf"\b(in|for|during|of|since|from|vs|and|than)\s+{word}\b|\b{word}\s+\d", t):
            continue  # "may" as a verb / "mar" ambiguity
        month = MONTHS[word]
        if m.group(2):
            year = int(m.group(2)) + (2000 if len(m.group(2)) == 2 else 0)
        else:
            year = anchor.year if month <= anchor.month else anchor.year - 1
        r = _month_range(year, month)
        add(m, r, f"{calendar.month_name[month]} {year}")
    found.sort(key=lambda x: x[0])
    out: list[tuple[DateRange, str]] = []
    for _, r, label in found:
        if not any(r.start == o.start and r.end == o.end for o, _ in out):
            out.append((r, label))
    return out


def parse_horizon(text: str) -> int | None:
    t = text.lower()
    m = re.search(r"\b(?:next|coming|upcoming)\s+(\d{1,3})\s*(day|week|month)s?\b", t)
    if m:
        return min(90, int(m.group(1)) * {"day": 1, "week": 7, "month": 30}[m.group(2)])
    if re.search(r"\b(next|coming) (fortnight|two weeks)\b", t):
        return 14
    if re.search(r"\b(next|coming|upcoming) week\b|\btomorrow\b", t):
        return 7
    if re.search(r"\b(next|coming|upcoming) month\b", t):
        return 30
    if re.search(r"\b(next|coming) quarter\b|\bnext (3|three) months\b", t):
        return 90
    return None


# ------------------------------------------------------------------------------------------ entities
class EntityIndex:
    """Lookup tables for outlets, categories and products (built per request; data is small)."""

    def __init__(self, db: Session):
        self.outlets = db.scalars(select(Outlet).order_by(Outlet.id)).all()
        self.categories = db.scalars(select(Category)).all()
        self.products = db.scalars(select(Product).where(Product.is_active.is_(True))).all()
        self.cat_by_name = {c.name.lower(): c for c in self.categories}
        self.product_tokens = {p.id: self._tokens(p.name) for p in self.products}
        token_count: dict[str, int] = {}
        for toks in self.product_tokens.values():
            for tok in toks:
                token_count[tok] = token_count.get(tok, 0) + 1
        self.token_count = token_count

    @staticmethod
    def _tokens(name: str) -> set[str]:
        words = re.findall(r"[a-z]+", name.lower())
        toks = {w for w in words if len(w) >= 3 and w not in PRODUCT_STOPWORDS}
        return {_stem(t) for t in toks}

    def match_outlets(self, text: str) -> list[Outlet]:
        t = text.lower()
        hits = []
        for o in self.outlets:
            keys = {o.name.lower(), o.code.lower()}
            first = o.name.lower().split()[0]
            if len(first) >= 4 and first not in ("west", "east", "road", "new"):
                keys.add(first)
            if any(re.search(rf"\b{re.escape(k)}\b", t) for k in keys):
                hits.append(o)
        if not hits:
            for o in self.outlets:
                city = o.city.lower()
                aliases = {city, {"bengaluru": "bangalore", "mumbai": "bombay", "pune": "poona"}.get(city, city)}
                if any(re.search(rf"\b{re.escape(a)}\b", t) for a in aliases):
                    hits.append(o)
        return hits

    def match_category(self, text: str) -> Category | None:
        t = text.lower()
        for c in self.categories:
            if c.name.lower() in t:
                return c
        for word, name in sorted(CATEGORY_SYNONYMS.items(), key=lambda kv: -len(kv[0])):
            if re.search(rf"\b{re.escape(word)}\b", t) and name.lower() in self.cat_by_name:
                return self.cat_by_name[name.lower()]
        return None

    def match_products(self, text: str) -> list[Product]:
        t = text.lower()
        for p in self.products:  # exact SKU or full name
            if re.search(rf"\b{re.escape(p.sku.lower())}\b", t) or p.name.lower() in t:
                return [p]
        words = {_stem(w) for w in re.findall(r"[a-z]+", t)}
        scored = []
        for p in self.products:
            toks = self.product_tokens[p.id]
            hit = toks & words
            if hit:
                # rarer tokens are more specific ("paneer" > "coffee")
                score = sum(1 / self.token_count[h] for h in hit) + len(hit)
                scored.append((score, p))
        if not scored:
            return []
        scored.sort(key=lambda x: -x[0])
        best = scored[0][0]
        return [p for s, p in scored if s >= best - 1e-9]


# ------------------------------------------------------------------------------------------ main
def parse(db: Session, text: str, anchor: date, index: EntityIndex | None = None) -> Parsed:
    index = index or EntityIndex(db)
    t = text.lower().strip()
    p = Parsed(text=text)

    scores: dict[str, float] = {}
    for intent, weight, pattern in INTENT_PATTERNS:
        if re.search(pattern, t):
            scores[intent] = scores.get(intent, 0) + weight

    p.periods = parse_periods(t, anchor)
    p.horizon = parse_horizon(t)
    m = re.search(r"\b(?:top|best|bottom|worst|least|first)\s+(\d{1,2})\b|\b(\d{1,2})\s+(?:best|top|worst|slowest|products|items)\b", t)
    if m:
        p.top_n = int(m.group(1) or m.group(2))

    outlets = index.match_outlets(t)
    p.outlet_ids = [o.id for o in outlets]
    p.outlet_names = [o.name for o in outlets]

    cat = index.match_category(t)
    products = index.match_products(t)
    if products:
        specific = len(products) == 1 or len(products) <= 3
        # A single generic token ("coffee") that names a category is treated as the category.
        if cat and len(products) > 1:
            products = []
        elif specific:
            p.product_ids = [x.id for x in products]
            p.product_names = [x.name for x in products]
    if cat and not p.product_ids:
        p.category_id, p.category_name = cat.id, cat.name

    if re.search(r"\b(units?|quantity|qty|volume|pieces)\b", t):
        p.sort = "units"
    elif re.search(r"\b(profit|margin)\w*\b", t):
        p.sort = "profit"
    if re.search(r"\b(out of stock|stock ?out|stock khatam|zero stock)\b", t):
        p.flags.add("out_only")
    if re.search(r"\b(low stock|running low|below reorder)\b", t):
        p.flags.add("low_only")
    if re.search(r"\b(at risk|churn\w*|lost|inactive|stopped (buying|coming))\b", t):
        p.flags.add("at_risk")
    if re.search(r"\b(segment|segments|rfm)\b", t):
        p.flags.add("segments")
    if re.search(r"\b(overdue|late)\b", t):
        p.flags.add("overdue")

    # Contextual adjustments
    if len(p.periods) >= 2 and ("compare_periods" in scores or re.search(r"\b(and|than)\b", t)):
        scores["compare_periods"] = scores.get("compare_periods", 0) + 3
    if "compare_periods" in scores and len(p.periods) < 2 and len(p.outlet_ids) >= 2:
        scores["outlet_ranking"] = scores.get("outlet_ranking", 0) + 3
    if "compare_periods" in scores and len(p.periods) == 1 and not len(p.outlet_ids) >= 2:
        scores["compare_periods"] += 1  # compare a period with the one before it
    if p.horizon and "forecast" not in scores and re.search(r"\b(sell|sales|revenue|demand|need)\b", t):
        scores["forecast"] = scores.get("forecast", 0) + 2
    if p.product_ids and not scores:
        scores["sales_summary"] = 1
    if "stock_status" in scores and "reorder" in scores:
        scores["reorder"] += 1

    if scores:
        priority = {name: i for i, name in enumerate(INTENTS)}
        best = max(scores.items(), key=lambda kv: (kv[1], -priority[kv[0]]))
        p.intent, p.confidence = best[0], min(1.0, best[1] / 4)
    elif p.periods or p.outlet_ids or p.category_id:
        p.intent, p.confidence = "sales_summary", 0.4
    else:
        p.intent, p.confidence = "general", 0.0
    return p
