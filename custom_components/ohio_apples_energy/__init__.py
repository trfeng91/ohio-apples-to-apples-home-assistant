"""The Ohio Apples Energy integration."""
from datetime import timedelta
import logging

import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import OhioApplesApi
from .const import (
    CONF_CATEGORY,
    CONF_PRICE_MAX,
    CONF_RATE_TYPE,
    CONF_REFRESH_INTERVAL,
    CONF_TERM_MAX,
    CONF_TERM_MIN,
    CONF_TERRITORY_ID,
    DOMAIN,
)
from .exceptions import CannotConnect, NoDataAvailable

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

TERMS_TO_TRACK = [0, 1, 2, 3, 6, 9, 12, 18, 24, 36, 48, 60]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Ohio Apples Energy component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Ohio Apples Energy from a config entry."""
    # energychoice.ohio.gov only serves the leaf cert — its Sectigo intermediate
    # is never sent, so default TLS verification fails. Browsers paper over this
    # with AIA chasing; aiohttp does not. The data is a public rate listing, so
    # verify_ssl=False is an acceptable tradeoff here.
    session = async_get_clientsession(hass, verify_ssl=False)
    api = OhioApplesApi(session)

    category = entry.data[CONF_CATEGORY]
    territory_id = entry.data[CONF_TERRITORY_ID]
    refresh_hours = entry.options.get(
        CONF_REFRESH_INTERVAL, entry.data.get(CONF_REFRESH_INTERVAL, 12)
    )
    filters = {
        "rate_type": entry.options.get(
            CONF_RATE_TYPE, entry.data.get(CONF_RATE_TYPE, "All")
        ),
        "term_min": entry.options.get(CONF_TERM_MIN, entry.data.get(CONF_TERM_MIN)),
        "term_max": entry.options.get(CONF_TERM_MAX, entry.data.get(CONF_TERM_MAX)),
        "price_max": entry.options.get(CONF_PRICE_MAX, entry.data.get(CONF_PRICE_MAX)),
    }

    async def async_update_data():
        """Fetch data from API and process it."""
        try:
            async with async_timeout.timeout(60):
                data = await api.async_fetch_rates(category, territory_id, filters)
        except (CannotConnect, NoDataAvailable) as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        processed = {
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
        for term in TERMS_TO_TRACK:
            processed[f"best_rate_{term}mo"] = next(
                (rate for rate in data["rates"] if rate["term"] == term), None
            )
        return processed

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        config_entry=entry,
        name=f"Ohio Energy {category} Scraper",
        update_method=async_update_data,
        update_interval=timedelta(hours=refresh_hours),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Reload the config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
