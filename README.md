# **Ohio Apples to Apples Energy Monitor**

A custom integration for **Home Assistant** that tracks electricity and natural gas rates from the official [Energy Choice Ohio (Apples to Apples)](https://www.energychoice.ohio.gov) website.

This integration scrapes current offers based on your specific utility provider and allows you to compare them against your current contract and the utility's **Standard Choice Offer (SCO)** / Price to Compare.

## **✨ Features**

* **Dual Support:** Tracks both **Electric** and **Natural Gas** providers.  
* **Smart Scraping:** Automatically fetches the **Standard Offer (Price to Compare)** directly from the utility page header.  
* **Granular Sensors:** Creates sensors for:  
  * 🏆 **Best Overall Rate:** The absolute lowest price found.  
  * 🚫 **Best "No Fee" Rate:** The lowest price with $0 monthly fees, $0 early termination fees, and no intro rate.  
  * 📅 **Term-Specific Rates:** Best rates for **1, 2, 3, 6, 9, 12, 18, 24, 36, 48, and 60-month** contracts.  
  * 🔢 **Matching Offers:** Counts how many plans match your filters.  
* **Rich Attributes:** Sensors include Supplier Name, Rate Type (Fixed/Variable), Monthly Fees, and Early Termination Fees.  
* **Configurable Filters:** Filter out variable rates, short-term contracts, or high-fee plans during setup.

## **📥 Installation**

### **Option 1: HACS (Recommended)**

1. Go to **HACS** \> **Integrations**.  
2. Click the three dots in the top right corner and select **Custom repositories**.  
3. Paste the URL of this repository and select **Integration**.  
4. Click **Install**.  
5. Restart Home Assistant.

### **Option 2: Manual**

1. Download the ohio\_apples\_energy folder from this repository.  
2. Copy the folder into your Home Assistant config/custom\_components/ directory.  
3. Restart Home Assistant.

## **⚙️ Configuration**

1. Go to **Settings** \> **Devices & Services**.  
2. Click **\+ Add Integration**.  
3. Search for **Ohio Apples to Apples Energy**.  
4. **Step 1:** Select your utility category (**Electric** or **NaturalGas**).  
5. **Step 2:** Select your specific Utility Provider (e.g., *AEP Ohio*, *Columbia Gas*).  
6. **Step 3:** Configure your filters (Optional):  
   * *Refresh Interval:* How often to scrape (default: 12 hours).  
   * *Rate Type:* Filter for "Fixed" only.  
   * *Term Min/Max:* Filter contract lengths.

**Note:** You can add the integration twice to track both Gas and Electric simultaneously.

## **📊 Dashboard Card**

To visualize your savings like a pro, follow these two steps to set up the custom Savings Calculator card.

### **Step 1: Create Price Helpers (Required)**

For the card to calculate savings, it needs to know your *current* contract price. You will create two "Input Number" helpers for this.

1. Go to **Settings** \> **Devices & Services** \> **Helpers**.  
2. Click **\+ Create Helper** and select **Number**.  
3. **Create the Gas Helper:**  
   * **Name:** My Gas Rate  
   * **Entity ID:** input\_number.my\_gas\_rate  
   * **Unit of Measurement:** $/ccf  
   * **Mode:** Box  
4. **Create the Electric Helper:**  
   * **Name:** My Electric Rate  
   * **Entity ID:** input\_number.my\_electric\_rate  
   * **Unit of Measurement:** $/kWh  
   * **Mode:** Box

### **Step 2: Add the Card**

1. Open the card configuration file: **energy\_savings\_card.txt**  
2. Copy all the code inside that file.  
3. In Home Assistant, go to your Dashboard and click the **Pencil Icon** (Edit Dashboard).  
4. Click **\+ Add Card**.  
5. Scroll down to the bottom and select **Manual**.  
6. Delete the default code and **paste the code you copied**.  
7. Click **Save**.

*\> **Note:** If the card shows errors, check that your sensor entity IDs match those in the code. They may vary slightly based on the Utility Provider you selected during setup.*

## **🔔 Automation Example**

Receive a notification on your phone whenever a "No-Fee" plan appears that is cheaper than your current contract.

1. Open the automation configuration file: **energy\_savings\_alert.txt**  
2. Copy all the code inside that file.  
3. In Home Assistant, go to **Settings** \> **Automations & Scenes**.  
4. Click **\+ Create Automation** \> **Create new automation**.  
5. Click the **three dots** in the top right corner and select **Edit in YAML**.  
6. Delete the existing code and **paste the code you copied**.  
7. Click **Save**.

## **⚠️ Disclaimer**

This integration is not affiliated with the Public Utilities Commission of Ohio (PUCO). It scrapes data from the public energychoice.ohio.gov website. While efforts are made to ensure accuracy, always verify rates on the official website of the energy provider before signing a contract.

## **📄 License**

MIT License

Copyright 2025 Trent Fagrell

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.