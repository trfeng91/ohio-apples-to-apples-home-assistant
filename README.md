Ohio Apples to Apples Energy Monitor

A custom integration for Home Assistant that tracks electricity and natural gas rates from the official Energy Choice Ohio (Apples to Apples) website.

This integration scrapes current offers based on your specific utility provider and allows you to compare them against your current contract and the utility's Standard Choice Offer (SCO) / Price to Compare.

✨ Features

Dual Support: Tracks both Electric and Natural Gas providers.

Smart Scraping: Automatically fetches the Standard Offer (Price to Compare) directly from the utility page header.

Granular Sensors: Creates sensors for:

🏆 Best Overall Rate: The absolute lowest price found.

🚫 Best "No Fee" Rate: The lowest price with $0 monthly fees, $0 early termination fees, and no intro rate.

📅 Term-Specific Rates: Best rates for 1, 2, 3, 6, 9, 12, 18, 24, 36, 48, and 60-month contracts.

🔢 Matching Offers: Counts how many plans match your filters.

Rich Attributes: Sensors include Supplier Name, Rate Type (Fixed/Variable), Monthly Fees, and Early Termination Fees.

Configurable Filters: Filter out variable rates, short-term contracts, or high-fee plans during setup.

📥 Installation

Option 1: HACS (Recommended)

Go to HACS > Integrations.

Click the three dots in the top right corner and select Custom repositories.

Paste the URL of this repository and select Integration.

Click Install.

Restart Home Assistant.

Option 2: Manual

Download the ohio_apples_energy folder from this repository.

Copy the folder into your Home Assistant config/custom_components/ directory.

Restart Home Assistant.

⚙️ Configuration

Go to Settings > Devices & Services.

Click + Add Integration.

Search for Ohio Apples to Apples Energy.

Step 1: Select your utility category (Electric or NaturalGas).

Step 2: Select your specific Utility Provider (e.g., AEP Ohio, Columbia Gas).

Step 3: Configure your filters (Optional):

Refresh Interval: How often to scrape (default: 12 hours).

Rate Type: Filter for "Fixed" only.

Term Min/Max: Filter contract lengths.

Note: You can add the integration twice to track both Gas and Electric simultaneously.

📊 Dashboard Card

To visualize your savings, you must set up the input helpers and then add the card configuration.

1. Create Price Helpers (Required)

For the dashboard card to calculate your savings, you must create two "Input Number" helpers where you will enter your current contract rates.

Go to Settings > Devices & Services > Helpers.

Click + Create Helper and select Number.

Create the Gas helper:

Name: My Gas Rate

Entity ID: input_number.my_gas_rate

Unit of Measurement: $/ccf

Click + Create Helper again for the Electric helper:

Name: My Electric Rate

Entity ID: input_number.my_electric_rate

Unit of Measurement: $/kWh

2. Add Card to Dashboard

Add a Markdown card to your dashboard and paste this YAML. It will automatically color-code savings in Green and losses in Red.

{% raw %}

type: markdown
content: |
  # ⚡ Energy Savings Analysis

  ---

  ## 🔥 Natural Gas
  
  | Compare | Rate / Term | Monthly Impact* |
  | :--- | :--- | :--- |
  | **My Contract** | **${{ states('input_number.my_gas_rate') }}** | — |
  | **Utility Std** | ${{ states('sensor.columbia_gas_of_ohio_naturalgas_standard_offer') }} <br> _(Variable)_ | {% set savings = (states('input_number.my_gas_rate')|float(0) - states('sensor.columbia_gas_of_ohio_naturalgas_standard_offer')|float(0)) * 100 %} {% if savings >= 0 %} <font color="green">**${{ '%.2f' | format(savings) }}**</font> {% else %} <font color="red">**${{ '%.2f' | format(savings) }}**</font> {% endif %} |
  | **Best No-Fee** | **${{ states('sensor.columbia_gas_of_ohio_naturalgas_best_rate_no_fees') }}** <br> _({{ state_attr('sensor.columbia_gas_of_ohio_naturalgas_best_rate_no_fees', 'term_length') }})_ | {% set savings = (states('input_number.my_gas_rate')|float(0) - states('sensor.columbia_gas_of_ohio_naturalgas_best_rate_no_fees')|float(0)) * 100 %} {% if savings >= 0 %} <font color="green">**${{ '%.2f' | format(savings) }}**</font> {% else %} <font color="red">**${{ '%.2f' | format(savings) }}**</font> {% endif %} |
  
  _<small> *Savings if you switch (based on 100 ccf/mo) </small>_

  ---

  ## ⚡ Electricity
  
  | Compare | Rate / Term | Monthly Impact* |
  | :--- | :--- | :--- |
  | **My Contract** | **${{ states('input_number.my_electric_rate') }}** | — |
  | **Utility Std** | ${{ states('sensor.american_electric_power_electric_standard_offer') }} <br> _(Variable)_ | {% set savings = (states('input_number.my_electric_rate')|float(0) - states('sensor.american_electric_power_electric_standard_offer')|float(0)) * 1000 %} {% if savings >= 0 %} <font color="green">**${{ '%.2f' | format(savings) }}**</font> {% else %} <font color="red">**${{ '%.2f' | format(savings) }}**</font> {% endif %} |
  | **Best No-Fee** | **${{ states('sensor.american_electric_power_electric_best_rate_no_fees') }}** <br> _({{ state_attr('sensor.american_electric_power_electric_best_rate_no_fees', 'term_length') }})_ | {% set savings = (states('input_number.my_electric_rate')|float(0) - states('sensor.american_electric_power_electric_best_rate_no_fees')|float(0)) * 1000 %} {% if savings >= 0 %} <font color="green">**${{ '%.2f' | format(savings) }}**</font> {% else %} <font color="red">**${{ '%.2f' | format(savings) }}**</font> {% endif %} |

  _<small> *Savings if you switch (based on 1000 kWh/mo) </small>_
title: Savings Calculator


{% endraw %}

> Note: Ensure your sensor entity IDs match those in the code above. They may vary slightly based on the Utility Provider you selected during setup.

🔔 Automation Example

Get a notification on your phone when a "No-Fee" plan appears that is cheaper than your current contract.

{% raw %}

alias: "💰 Energy Savings Alert"
trigger:
  - platform: state
    entity_id:
      - sensor.american_electric_power_electric_best_rate_no_fees
      - sensor.columbia_gas_of_ohio_naturalgas_best_rate_no_fees
condition:
  - condition: or
    conditions:
      - condition: template
        value_template: >
          {{ states('sensor.american_electric_power_electric_best_rate_no_fees')|float(0) < states('input_number.my_electric_rate')|float(0) }}
      - condition: template
        value_template: >
          {{ states('sensor.columbia_gas_of_ohio_naturalgas_best_rate_no_fees')|float(0) < states('input_number.my_gas_rate')|float(0) }}
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "📉 Cheaper Energy Rate Found!"
      message: "A new energy rate is available that beats your current contract!"


{% endraw %}

⚠️ Disclaimer

This integration is not affiliated with the Public Utilities Commission of Ohio (PUCO). It scrapes data from the public energychoice.ohio.gov website. While efforts are made to ensure accuracy, always verify rates on the official website before signing a contract.

📄 License

MIT License

Copyright 2025 Trent Fagrell

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.