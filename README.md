# Vinted Search

A tiny, **dependency-free** Python scraper for searching Vinted across any supported country —
no login, no cookies, no API key. Returns structured results (title, brand, condition, size,
price, and item URL) from Vinted's server-side-rendered catalog page.

> **Why this exists:** Vinted's public JSON API (`/api/v1/*`, `/api/v2/*`) has been removed.
> Search results are now server-side-rendered into the `/catalog?search_text=...` page. This
> tool extracts them back into clean data.

## Quick start

```bash
python3 vinted_search.py "black leather jacket" --country de
```

Output:

```
 59.00 € | Black leather jacket it. 44  [Vera Pelle · Sehr gut · size EU 40]
          https://www.vinted.de/items/10120323702-black-leather-jacket-it-44
 25.00 € | Beautiful Black Leather Moto Jack  [Vintage Dressing · Sehr gut · size S]
          https://www.vinted.de/items/9754470841-beautiful-black-leather-moto-jack
```

## Installation

No dependencies beyond Python 3.8+ (standard library only). Either clone and run directly, or
drop it into an agent "skills" directory and read `SKILL.md`.

```bash
git clone https://github.com/paulotruta/vinted-search.git
cd vinted-search
python3 vinted_search.py "your query here"
```

## Usage

```
python3 vinted_search.py "<query>" [options]
```

| Flag             | Description                                              |
| ---------------- | -------------------------------------------------------- |
| `--country CODE` | Country code (default `de`)                              |
| `--limit N`      | Max listings to print (default `20`)                     |
| `--sort price`   | Sort ascending by price                                  |
| `--json`         | Emit raw JSON instead of a formatted list                |
| `-h, --help`     | Show help                                                |

### Supported countries

`de fr uk it es nl pl pt be at lt cz sk hu ro hr fi dk se`

### Examples

```bash
# Search France, cheapest first
python3 vinted_search.py "levis 501" --country fr --sort price

# Get 10 raw JSON results from the UK for further processing
python3 vinted_search.py "nike dunk" --country uk --limit 10 --json
```

## How it works

1. Fetches `https://www.vinted.<country>/catalog?search_text=<query>` with a browser User-Agent.
2. Vinted server-renders each listing as an `<a href="/items/<id>-<slug>">` whose `title`
   attribute carries the full listing string:
   `"Title, Marke: Brand, Zustand: Condition, Größe: Size, Price €, Original €"`.
3. `parse_items()` + `parse_attr()` recover title, brand, condition, size, price and id/slug.

## For other agents (skill usage)

This repo doubles as an agent skill. Read `SKILL.md` for the drop-in instructions.

## Caveats

- Depends on Vinted's **undocumented, changing HTML**. If results come back empty/malformed,
  the place to fix them is `parse_items()` / `parse_attr()`.
- Item URLs follow the searched country (e.g. `--country fr` → `www.vinted.fr/...`);
  the `/items/<id>-<slug>` path is identical across regions.
- Respect Vinted's ToS and rate limits — this is a lightweight anonymous read, so keep it gentle.

## Disclaimer

Not affiliated with, or endorsed by, Vinted.
