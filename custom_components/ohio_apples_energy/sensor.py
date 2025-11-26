from datetime import timedelta
import logging
import async_timeout

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import *
from .api import OhioApplesApi
from .exceptions import CannotConnect, NoDataAvailable

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup sensor platform."""

    api = hass.data[DOMAIN][entry.entry_id]
    category = entry.data[CONF_CATEGORY]
    territory_id = entry.data[CONF_TERRITORY_ID]

# Get options from config entry, falling back to data (initial setup)
    refresh_hours = entry.options.get(CONF_REFRESH_INTERVAL, entry.data.get(CONF_REFRESH_INTERVAL, 12))
    
    filters = {
        "rate_type": entry.options.get(CONF_RATE_TYPE, entry.data.get(CONF_RATE_TYPE, "All")),
        "term_min": entry.options.get(CONF_TERM_MIN, entry.data.get(CONF_TERM_MIN)),
        "term_max": entry.options.get(CONF_TERM_MAX, entry.data.get(CONF_TERM_MAX)),
        "price_max": entry.options.get(CONF_PRICE_MAX, entry.data.get(CONF_PRICE_MAX)),
    }

    async def async_update_data():
        """Fetch data from API and process it."""
        try:
            async with async_timeout.timeout(30):
                data = await api.async_fetch_rates(category, territory_id, filters)
        except (CannotConnect, NoDataAvailable) as e:
            raise UpdateFailed(f"Error communicating with API: {e}") from e

        # Process rates once
        processed_data = {
            "standard_offer": data["standard_offer"],
            "rates": data["rates"],
            "best_rate": data["rates"][0] if data["rates"] else None,
            "best_rate_no_fees": next(
                (
                    rate
                    for rate in data["rates"]
                    if rate["monthly_fee"] == 0
                    and rate["early_term_fee"] == 0
                    and not rate["intro_price"]
                ),
                None,
            ),
        }
        for term in [0, 1, 2, 3, 6, 9, 12, 18, 24, 36, 48, 60]:
            processed_data[f"best_rate_{term}mo"] = next(
                (rate for rate in data["rates"] if rate["term"] == term), None
            )

        return processed_data

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"Ohio Energy {category} Scraper",
        update_method=async_update_data,
        update_interval=timedelta(hours=refresh_hours),
    )

    await coordinator.async_config_entry_first_refresh()

    entities = [
        BestRateSensor(coordinator, entry.title, category),
        RateCountSensor(coordinator, entry.title, category),
        StandardOfferSensor(coordinator, entry.title, category),
        BestRateNoFeesSensor(coordinator, entry.title, category)
    ]

    # Added 60 months to the list
    terms_to_track = [0, 1, 2, 3, 6, 9, 12, 18, 24, 36, 48, 60]

    for term in terms_to_track:
        entities.append(TermRateSensor(coordinator, entry.title, category, term))

    async_add_entities(entities)


class BaseOhioSensor(CoordinatorEntity, SensorEntity):
    """Base class for Ohio Energy sensors."""

    def __init__(self, coordinator, name, category):
        super().__init__(coordinator)
        self._name = name
        self._category = category
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self.coordinator.name)},
            "name": self._name,
            "manufacturer": "Ohio Apples to Apples",
        }

    @property
    def native_unit_of_measurement(self):
        if self._category == "Electric":
            return "$/kWh"
        return "$/ccf"

    @property
    def state_class(self):
        return "measurement"

    def _get_attributes(self, rate):
        """Helper to format attributes for a rate."""
        if not rate:
            return {}
        return {
            "supplier": rate['supplier'],
            "rate_type": rate['type'],
            "term_length": f"{rate['term']} months",
            "intro_price": "Yes" if rate['intro_price'] else "No",
            "monthly_fee": f"${rate['monthly_fee']:.2f}",
            "early_termination_fee": f"${rate['early_term_fee']:.2f}",
            "raw_price_string": rate['raw_price']
        }


class BestRateSensor(BaseOhioSensor):
    """Sensor for the best available rate overall."""

    @property
    def name(self):
        return f"{self._name} Best Rate Overall"

    @property
    def unique_id(self):
        return f"{self.coordinator.name}_best_rate"

    @property
    def native_value(self):
        rate = self.coordinator.data.get("best_rate")
        return rate["price"] if rate else None

    @property
    def extra_state_attributes(self):
        return self._get_attributes(self.coordinator.data.get("best_rate"))


class BestRateNoFeesSensor(BaseOhioSensor):
    """Sensor for best rate with NO monthly fee, NO early term fee, NO intro."""

    @property
    def name(self):
        return f"{self._name} Best Rate (No Fees)"

    @property
    def unique_id(self):
        return f"{self.coordinator.name}_best_rate_no_fees"

    @property
    def native_value(self):
        rate = self.coordinator.data.get("best_rate_no_fees")
        return rate["price"] if rate else None

    @property
    def extra_state_attributes(self):
        return self._get_attributes(self.coordinator.data.get("best_rate_no_fees"))


class TermRateSensor(BaseOhioSensor):
    """Sensor for best rate of a specific term length."""

    def __init__(self, coordinator, name, category, term):
        super().__init__(coordinator, name, category)
        self._term = term

    @property
    def name(self):
        return f"{self._name} Best Rate {self._term} Month"

    @property
    def unique_id(self):
        return f"{self.coordinator.name}_best_rate_{self._term}mo"

    @property
    def native_value(self):
        rate = self.coordinator.data.get(f"best_rate_{self._term}mo")
        return rate["price"] if rate else None

    @property
    def extra_state_attributes(self):
        return self._get_attributes(self.coordinator.data.get(f"best_rate_{self._term}mo"))


class RateCountSensor(CoordinatorEntity, SensorEntity):
    """Sensor for the number of matching offers."""

    def __init__(self, coordinator, name, category):
        super().__init__(coordinator)
        self._name = name
        self._category = category
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self.coordinator.name)},
            "name": self._name,
            "manufacturer": "Ohio Apples to Apples",
        }

    @property
    def name(self): return f"{self._name} Matching Offers"

    @property
    def unique_id(self): return f"{self.coordinator.name}_rate_count"

    @property
    def native_value(self): return len(self.coordinator.data.get("rates", []))


class StandardOfferSensor(BaseOhioSensor):
    """Sensor for the Utility Standard Choice Offer."""

    @property
    def name(self): return f"{self._name} Standard Offer"

    @property
    def unique_id(self): return f"{self.coordinator.name}_standard_offer"

    @property
    def native_value(self): return self.coordinator.data.get("standard_offer")

    @property
    def icon(self): return "mdi:bank"
