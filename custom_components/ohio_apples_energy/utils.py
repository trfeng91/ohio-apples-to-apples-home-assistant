import logging
import re
import aiohttp
from bs4 import BeautifulSoup
from .const import URL_BASE, URL_COMPARISON

_LOGGER = logging.getLogger(__name__)


async def fetch_providers(session, category_url):
    """Scrape the provider list."""
    try:
        async with session.get(category_url) as response:
            text = await response.text()
            soup = BeautifulSoup(text, 'html.parser')

            provider_list_div = soup.find('div', class_='provider-list')
            if not provider_list_div:
                return {}

            providers = {}
            for link in provider_list_div.find_all('a'):
                href = link.get('href', '')
                name = link.get_text(strip=True)
                match = re.search(r'TerritoryId=(\d+)', href)
                if match and name:
                    t_id = match.group(1)
                    providers[t_id] = name

            return providers
    except Exception as e:
        _LOGGER.error(f"Error fetching providers: {e}")
        return {}


async def fetch_rates(session, category, territory_id, filters):
    """Fetch rates and the Standard Offer."""
    url = f"{URL_COMPARISON}?Category={category}&TerritoryId={territory_id}&RateCode=1"

    result = {
        "rates": [],
        "standard_offer": 0.0
    }

    try:
        async with session.get(url) as response:
            text = await response.text()
            soup = BeautifulSoup(text, 'html.parser')

            # --- 1. SCRAPE STANDARD OFFER ---
            page_text = soup.get_text(separator=" ", strip=True)

            if category == "Electric":
                match = re.search(r"\$(\d+\.\d+)/kWh", page_text)
                if match:
                    result["standard_offer"] = float(match.group(1))
            else:
                match = re.search(r"SCO rate is\s*\$(\d+\.\d+)", page_text, re.IGNORECASE)
                if match:
                    result["standard_offer"] = float(match.group(1))

            # --- 2. SCRAPE RATES TABLE ---
            rates = []
            rows = soup.find_all("tr")

            for row in rows:
                cols = row.find_all('td')

                if len(cols) < 8:
                    continue

                supplier_span = cols[1].find('span', class_='retail-title')
                if not supplier_span:
                    continue

                try:
                    # -- Supplier (1)
                    supplier_text = supplier_span.contents[0] if supplier_span.contents else "Unknown"
                    supplier_name = str(supplier_text).strip()

                    # -- Price (2)
                    price_text = cols[2].get_text(strip=True)
                    clean_price = re.sub(r'[^\d.]', '', price_text)
                    if not clean_price: continue
                    price_val = float(clean_price)

                    if price_val == 0.0: continue  # Skip flat fee/unlimited plans

                    # -- Rate Type (3)
                    rate_type = cols[3].get_text(strip=True)

                    # -- Intro Price (5)
                    intro_text = cols[5].get_text(strip=True)
                    is_intro = "yes" in intro_text.lower()

                    # -- Term Length (6)
                    term_text = cols[6].get_text(strip=True)
                    term_val = 0
                    term_match = re.search(r'(\d+)', term_text)
                    if term_match:
                        term_val = int(term_match.group(1))

                    # -- Early Term Fee (7)
                    etf_text = cols[7].get_text(strip=True)
                    etf_val = 0.0
                    # Look for digits. If "$0" or "None", stays 0.0
                    etf_match = re.search(r'(\d+\.?\d*)', etf_text)
                    if etf_match:
                        etf_val = float(etf_match.group(1))

                    # -- Monthly Fee (8)
                    fee_text = cols[8].get_text(strip=True)
                    fee_val = 0.0
                    fee_match = re.search(r'(\d+\.?\d*)', fee_text)
                    if fee_match:
                        fee_val = float(fee_match.group(1))

                    # --- FILTERS ---
                    if filters.get('rate_type') and filters['rate_type'] != 'All':
                        if filters['rate_type'].lower() not in rate_type.lower():
                            continue

                    if filters.get('term_min') is not None and term_val < filters['term_min']: continue
                    if filters.get('term_max') is not None and term_val > filters['term_max']: continue
                    if filters.get('price_max') is not None and filters['price_max'] > 0.0:
                        if price_val > filters['price_max']: continue

                    rates.append({
                        "supplier": supplier_name,
                        "price": price_val,
                        "type": rate_type,
                        "term": term_val,
                        "monthly_fee": fee_val,
                        "early_term_fee": etf_val,
                        "intro_price": is_intro,
                        "raw_price": price_text
                    })

                except Exception:
                    continue

            rates.sort(key=lambda x: x['price'])
            result["rates"] = rates
            return result

    except Exception as e:
        _LOGGER.error(f"Error fetching rates: {e}")
        return result