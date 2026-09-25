#!/usr/bin/env python3
"""
Vinted search scraper (server-side-rendered catalog page).

Vinted's old JSON API endpoints (/api/v1/*, /api/v2/*) are gone. Search
results are now server-side-rendered directly into the catalog page HTML
at https://www.vinted.<country>/catalog?search_text=<query>.

Each listing is an <a href="/items/<id>-<slug>?..."> whose `title` (and the
<img alt="...">) attribute carries the full listing string:

    "TITLE, Marke: BRAND, Zustand: COND, Größe: SIZE, PRICE €, ORIGPRICE €"

We scrape the page and parse that attribute to recover title, brand,
condition, size, price, and item id/slug. Anonymous — no login/cookies.

Usage:
    python3 vinted_search.py "<query>" [options]

Options:
    --country CODE      Country code (default: de): de fr uk it es nl pl pt
                        be at lt cz sk hu ro hr fi dk se
    --limit N           Max listings to print (default: 20)
    --json              Output raw JSON instead of a formatted list
    --sort price        Sort ascending by price

Examples:
    python3 vinted_search.py "black leather jacket"
    python3 vinted_search.py "levis 501" --country fr --limit 10 --sort price
"""

import argparse
import html
import json
import re
import sys
import urllib.parse
import urllib.request

COUNTRIES = ["de", "fr", "uk", "it", "es", "nl", "pl", "pt", "be", "at",
             "lt", "cz", "sk", "hu", "ro", "hr", "fi", "dk", "se"]

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")


def fetch_catalog(query, country="de"):
    url = ("https://www.vinted." + country + "/catalog?search_text="
           + urllib.parse.quote(query))
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": country + "-" + country.upper() + "," + country + ";q=0.9",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def parse_items(raw):
    """Parse listings from the SSR'd catalog HTML."""
    items = []
    seen = set()

    # Every item URL is /items/<id>-<slug>
    id_to_slug = {}
    for sid, sslug in re.findall(r'/items/(\d+)-([a-z0-9-]+)', raw):
        id_to_slug.setdefault(sid, sslug)

    # The <a> tag has href BEFORE the title attribute:
    #   <a href="/items/<id>-<slug>?...referrer=catalog" ... title="FULL INFO...">
    id_to_attr = {}
    for iid, full in re.findall(
        r'href="/items/(\d+)-[^"]*"[^>]*title="([^"]{5,400})"', raw
    ):
        if iid in id_to_slug:
            id_to_attr.setdefault(iid, full)

    for iid, slug in id_to_slug.items():
        if iid in seen:
            continue
        seen.add(iid)
        attr = id_to_attr.get(iid, "")
        entry = parse_attr(attr) if attr else {"title": slug.replace("-", " ").title()}
        entry["id"] = iid
        entry["slug"] = slug
        entry["url"] = f"https://www.vinted.de/items/{iid}-{slug}"
        items.append(entry)

    return items


def parse_attr(attr):
    """Parse a listing attribute string like:
    'TITLE, Marke: BRAND, Zustand: COND, Größe: SIZE, PRICE €, ORIGPRICE €'
    Language-dependent labels; we detect German (and common EN/FR/ES) plus
    positional price tokens.
    """
    attr = html.unescape(attr).strip()
    parts = [p.strip() for p in attr.split(",")]

    result = {"title": parts[0] if parts else "", "brand": None,
              "condition": None, "size": None, "price": None,
              "original_price": None}

    price_values = []
    # label prefixes that map to a field
    brand_labels = ("marke:", "brand:", "marque:", "marca:")
    cond_labels = ("zustand:", "cond", "condition:", "etat:", "estado:")
    size_labels = ("größe:", "grosse:", "groesse:", "size:", "taille:",
                   "talla:", "taglia:")

    for p in parts[1:]:
        low = p.lower()
        if low.startswith(brand_labels):
            result["brand"] = p.split(":", 1)[1].strip() if ":" in p else p[6:].strip()
        elif any(low.startswith(l) for l in cond_labels):
            result["condition"] = p.split(":", 1)[1].strip() if ":" in p else p
        elif any(low.startswith(s) for s in size_labels):
            result["size"] = p.split(":", 1)[1].strip() if ":" in p else p[6:].strip()
        elif re.fullmatch(r"[\d.,\s]+(€|eur|£|gbp|zł|usd|\$)", low):
            val = re.sub(r"[^\d.,]", "", p).replace(",", ".")
            val = re.sub(r"\.(?=\d{3})", "", val)  # strip thousand sep
            try:
                price_values.append(float(val))
            except ValueError:
                pass

    if price_values:
        result["price"] = price_values[0]
        if len(price_values) > 1:
            result["original_price"] = price_values[1]

    return result


def fmt_list(items, limit):
    lines = []
    for it in items[:limit]:
        price = f"{it['price']:.2f} €" if it.get("price") else "—"
        meta = []
        if it.get("brand"):
            meta.append(it["brand"])
        if it.get("condition"):
            meta.append(it["condition"])
        if it.get("size"):
            meta.append("size " + it["size"])
        title = it.get("title", "")[:70]
        if meta:
            title += "  [" + " · ".join(meta) + "]"
        lines.append(f"{price:>10} | {title}")
        lines.append("          " + it["url"])
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Scrape Vinted search results.")
    ap.add_argument("query", help="Search terms")
    ap.add_argument("--country", default="de", choices=COUNTRIES)
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--sort", choices=["price"], default=None)
    args = ap.parse_args()

    raw = fetch_catalog(args.query, args.country)
    items = parse_items(raw)

    if args.sort == "price":
        items = sorted(items, key=lambda x: (x.get("price") is None,
                                             x.get("price") or 0))

    if args.json:
        print(json.dumps(items[:args.limit], ensure_ascii=False, indent=2))
    else:
        if not items:
            print("No listings found.", file=sys.stderr)
            sys.exit(1)
        print(fmt_list(items, args.limit))


if __name__ == "__main__":
    main()
