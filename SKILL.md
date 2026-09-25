---
name: vinted-search
description: Search Vinted marketplace listings (title, brand, condition, size, price, URL) from any country without an account. Use when you or a user wants to find, browse, or price-check items on Vinted. Works anonymously via the server-side-rendered catalog page — no login, cookies, or API key required.
---

# Vinted Search

A dependency-free Python scraper for searching Vinted. Vinted removed its old JSON
API (`/api/v1/*`, `/api/v2/*`), so search results are no longer available through a
clean programmatic endpoint. Instead, Vinted now server-side-renders search results
directly into the `/catalog?search_text=...` page. This tool scrapes that page and
recovers structured listing data.

**Anonymous** — no login, no cookies, no API token.

## When to use

- A user wants to find items on Vinted ("find me a black leather jacket in Germany").
- Price-checking: how much do similar items sell for in a given country?
- Browsing/browsing a category across countries (Vinted is regional — `.de`, `.fr`, `.uk`, etc.).
- Building an answer that cites real, current listings with prices and links.

## Usage

```bash
python3 vinted_search.py "<query>" [options]
```

### Options

| Flag            | Description                                                        |
| --------------- | ------------------------------------------------------------------ |
| `--country CODE` | Country code (default `de`). See supported list below.            |
| `--limit N`      | Max listings to print (default `20`).                             |
| `--sort price`   | Sort ascending by price (cheapest first).                         |
| `--json`         | Emit raw JSON instead of a formatted list.                        |

### Supported countries

`de fr uk it es nl pl pt be at lt cz sk hu ro hr fi dk se`

### Examples

```bash
# Basic search in Germany
python3 vinted_search.py "black leather jacket"

# Search France, sort by cheapest
python3 vinted_search.py "levis 501" --country fr --sort price

# Raw JSON for further scripted processing
python3 vinted_search.py "nike dunk" --country uk --limit 10 --json
```

### Example output

```
 59.00 € | Black leather jacket it. 44  [Vera Pelle · Sehr gut · size EU 40]
          https://www.vinted.de/items/10120323702-black-leather-jacket-it-44
 25.00 € | Beautiful Black Leather Moto Jack  [Vintage Dressing · Sehr gut · size S]
          https://www.vinted.de/items/9754470841-beautiful-black-leather-moto-jack
  4.00 € | Leather jacket  [Primark · Gut · size EU 36]
          https://www.vinted.de/items/10116383100-leather-jacket
```

## Requirements

- Python 3.8+ (standard library only — no `pip install` needed).

## How it works

1. Fetches `https://www.vinted.<country>/catalog?search_text=<query>` with a browser
   `User-Agent`.
2. The page server-renders each listing as an `<a href="/items/<id>-<slug>">` element
   whose `title` attribute contains the full listing string:
   `"Title, Marke: Brand, Zustand: Condition, Größe: Size, Price €, Original €"`.
3. `parse_items()` + `parse_attr()` extract title, brand, condition, size, price and
   id/slug from those attributes.

## Notes / caveats

- **No guarantees of stability** — this depends on Vinted's undocumented HTML markup.
  If results come back empty or malformed, the place to fix them is `parse_items()` and
  `parse_attr()` (the `title`/`alt` attribute shape is what changes).
- **Item links are hardcoded to `.de` in the returned URL.** If you search a non-German
  country, rewrite the returned URL's host to that country if you need a clickable link
  (the `/items/<id>-<slug>` path is identical across regions).
- **Respect Vinted's terms of service.** This makes lightweight anonymous reads of a
  public page. Don't hammer it — add a small delay if you're doing bulk/paginated
  queries.
- Vinted may rate-limit or Cloudflare-block scripted requests from certain IPs. The
  result is usually an empty page or a 200 with no parsed items, not an error.

## For other agents

This repo is also usable as a drop-in skill. Put it in a skills directory and read this
`SKILL.md`; invoke the script with `python3 vinted_search.py "<query>"`. If a user asks
to search Vinted, run the script rather than trying Vinted's (dead) JSON API endpoints.

## Disclaimer

Not affiliated with, or endorsed by, Vinted.
