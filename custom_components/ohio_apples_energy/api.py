"""API for Ohio Apples to Apples Energy."""
import logging
import re
import aiohttp
from bs4 import BeautifulSoup

from .const import URL_BASE, URL_COMPARISON, CATEGORY_ELECTRIC
from .exceptions import CannotConnect, NoDataAvailable

_LOGGER = logging.getLogger(__name__)


class OhioApplesApi:
    """API to fetch data from Ohio Apples to Apples Energy."""

    def __init__(self, session: aiohttp.ClientSession):
        """Initialize the API."""
        self._session = session

    async def async_fetch_providers(self, category_url: str) -> dict:
        """Scrape the provider list."""
        try:
            async with self._session.get(category_url) as response:
                response.raise_for_status()
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')

                provider_list_div = soup.find('div', class_='provider-list')
                if not provider_list_div:
                    raise NoDataAvailable

                providers = {}
                for link in provider_list_div.find_all('a'):
                    href = link.get('href', '')
                    name = link.get_text(strip=True)
                    match = re.search(r'TerritoryId=(\d+)', href)
                    if match and name:
                        t_id = match.group(1)
                        providers[t_id] = name

                if not providers:
                    raise NoDataAvailable

                return providers
        except aiohttp.ClientError as e:
            raise CannotConnect from e

    async def async_fetch_rates(self, category: str, territory_id: str, filters: dict) -> dict:
        """Fetch rates and the Standard Offer."""
        url = f"{URL_COMPARISON}?Category={category}&TerritoryId={territory_id}&RateCode=1"

        try:
            async with self._session.get(url) as response:
                response.raise_for_status()
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')

                # --- 1. SCRAPE STANDARD OFFER ---
                page_text = soup.get_text(separator=" ", strip=True)
                standard_offer = 0.0

                if category == CATEGORY_ELECTRIC:
                    match = re.search(r"\$(\d+\.\d+)/kWh", page_text)
                    if match:
                        standard_offer = float(match.group(1))
                else:
                    match = re.search(r"SCO rate is\s*\$(\d+\.\d+)", page_text, re.IGNORECASE)
                    if match:
                        standard_offer = float(match.group(1))

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
                        rate_type_filter = filters.get("rate_type")
                        if rate_type_filter and rate_type_filter != "All":
                            rate_type_lower = rate_type.lower()
                            if rate_type_filter == "Fixed":
                                if "fixed" not in rate_type_lower or "variable" in rate_type_lower:
                                    continue
                            elif rate_type_filter == "Variable":
                                if "variable" not in rate_type_lower or "fixed" in rate_type_lower:
                                    continue
                        
                        if filters.get("term_min") is not None and term_val < filters["term_min"]: continue
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

                    except (ValueError, IndexError):
                        continue

                if not rates:
                    raise NoDataAvailable

                rates.sort(key=lambda x: x['price'])
                return {"rates": rates, "standard_offer": standard_offer}

        except aiohttp.ClientError as e:
            raise CannotConnect from e
