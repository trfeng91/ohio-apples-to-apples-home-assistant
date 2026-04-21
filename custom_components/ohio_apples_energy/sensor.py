"""Sensor platform for Ohio Apples Energy."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_CATEGORY, DOMAIN

_LOGGER = logging.getLogger(__name__)

TERMS_TO_TRACK = [0, 1, 2, 3, 6, 9, 12, 18, 24, 36, 48, 60]


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    category = entry.data[CONF_CATEGORY]

    entities = [
        BestRateSensor(coordinator, entry.title, category),
        RateCountSensor(coordinator, entry.title, category),
        StandardOfferSensor(coordinator, entry.title, category),
        BestRateNoFeesSensor(coordinator, entry.title, category),
    ]

    for term in TERMS_TO_TRACK:
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
