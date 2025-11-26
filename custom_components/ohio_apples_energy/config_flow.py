import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import *
from .api import OhioApplesApi
from .exceptions import CannotConnect, NoDataAvailable


class OhioApplesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ohio Apples Energy."""

    VERSION = 1

    def __init__(self):
        self.data = {}
        self.providers = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OhioApplesOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        """Step 1: Select Category (Gas or Electric)."""
        errors = {}
        if user_input is not None:
            self.data[CONF_CATEGORY] = user_input[CONF_CATEGORY]
            return await self.async_step_provider()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_CATEGORY, default=CATEGORY_ELECTRIC): vol.In([CATEGORY_ELECTRIC, CATEGORY_GAS])
            }),
            errors=errors,
        )

    async def async_step_provider(self, user_input=None):
        """Step 2: Scrape and Select Provider."""
        errors = {}

        url = URL_ELEC_PROVIDERS if self.data[CONF_CATEGORY] == CATEGORY_ELECTRIC else URL_GAS_PROVIDERS

        try:
            if not self.providers:
                session = async_get_clientsession(self.hass)
                api = OhioApplesApi(session)
                self.providers = await api.async_fetch_providers(url)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except NoDataAvailable:
            errors["base"] = "no_data_available"

        if user_input is not None:
            self.data[CONF_TERRITORY_ID] = user_input[CONF_TERRITORY_ID]
            self.data[CONF_TERRITORY_NAME] = self.providers[user_input[CONF_TERRITORY_ID]]
            return await self.async_step_filters()

        provider_options = [
            {"label": v, "value": k}
            for k, v in sorted(self.providers.items(), key=lambda item: item[1])
        ]

        return self.async_show_form(
            step_id="provider",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TERRITORY_ID): SelectSelector(
                        SelectSelectorConfig(
                            options=provider_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_filters(self, user_input=None):
        """Step 3: Set Preferences/Filters."""
        if user_input is not None:
            # Allow for clean data entry
            self.data.update(user_input)

            # Create a readable Title
            title = f"{self.data[CONF_TERRITORY_NAME]} ({self.data[CONF_CATEGORY]})"

            # Create unique ID
            unique_id = f"{self.data[CONF_CATEGORY]}_{self.data[CONF_TERRITORY_ID]}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title=title, data=self.data)

        # We make these Optional. If the user leaves them blank, they will be None.
        return self.async_show_form(
            step_id="filters",
            data_schema=vol.Schema({
                vol.Required(CONF_REFRESH_INTERVAL, default=12): vol.All(vol.Coerce(int), vol.Range(min=1, max=168)),
                vol.Optional(CONF_RATE_TYPE, default="All"): vol.In(["All", "Fixed", "Variable"]),
                vol.Optional(CONF_TERM_MIN): cv.positive_int,
                vol.Optional(CONF_TERM_MAX): cv.positive_int,
                vol.Optional(CONF_PRICE_MAX): vol.Any(None, vol.Coerce(float)),
            })
        )


class OhioApplesOptionsFlow(config_entries.OptionsFlow):
    """Handle an options flow for Ohio Apples Energy."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_REFRESH_INTERVAL,
                    default=self.config_entry.options.get(CONF_REFRESH_INTERVAL, 12),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=168)),
                vol.Optional(
                    CONF_RATE_TYPE,
                    default=self.config_entry.options.get(CONF_RATE_TYPE, "All"),
                ): vol.In(["All", "Fixed", "Variable"]),
                vol.Optional(
                    CONF_TERM_MIN,
                    default=self.config_entry.options.get(CONF_TERM_MIN),
                ): cv.positive_int,
                vol.Optional(
                    CONF_TERM_MAX,
                    default=self.config_entry.options.get(CONF_TERM_MAX),
                ): cv.positive_int,
                vol.Optional(
                    CONF_PRICE_MAX,
                    default=self.config_entry.options.get(CONF_PRICE_MAX),
                ): vol.Any(None, vol.Coerce(float)),
            }),
        )
