"""Constants for the Ohio Apples Energy integration."""

DOMAIN = "ohio_apples_energy"

CONF_CATEGORY = "category"
CONF_TERRITORY_ID = "territory_id"
CONF_TERRITORY_NAME = "territory_name"
CONF_RATE_TYPE = "rate_type"
CONF_TERM_MIN = "term_min"
CONF_TERM_MAX = "term_max"
CONF_PRICE_MAX = "price_max"
CONF_REFRESH_INTERVAL = "refresh_interval"

URL_BASE = "https://www.energychoice.ohio.gov"
URL_GAS_PROVIDERS = "https://www.energychoice.ohio.gov/ApplesToApplesCategory.aspx?Category=NaturalGas"
URL_ELEC_PROVIDERS = "https://www.energychoice.ohio.gov/ApplesToApplesCategory.aspx?Category=Electric"
URL_COMPARISON = "https://www.energychoice.ohio.gov/ApplesToApplesComparision.aspx"

CATEGORY_ELECTRIC = "Electric"
CATEGORY_GAS = "NaturalGas"