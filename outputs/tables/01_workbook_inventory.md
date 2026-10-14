# Workbook inventory
Source: `data/raw/TYLY_data_sample.xlsx`

| sheet | state | max_row | max_col | merged ranges | comments | formulas |
|---|---|---|---|---|---|---|
| Column Definitions | visible | 29 | 4 | ['A2:D2'] | 0 | 0 |
| Data | visible | 3610 | 17 | - | 0 | 0 |
| Inventory | visible | 337 | 4 | - | 0 | 0 |

Defined names: []

## Sheet `Column Definitions` — first 12 raw rows (header-offset check)
```
  1: ('TYLY_data_sample - Column Definitions', None, None, None)
  2: ('Sample extract modeled on a customer and sales (TYLY) table (dummy data). The workbook has three sheets: this Column Definitions sheet, Data (one row per transaction line, this year and last year), and Inventory (weekly stock by product family, this year and last year). On the Data sheet each line belongs to a single fiscal year: FISCAL_YR = FY26 is this year (TY) and FY25 is last year (LY). Every column is populated. Year-over-year = compare DEMAND_AMT across FISCAL_YR (for example FY26 vs FY25 within the same FISCAL_WK number); trailing week = the FY26 week sequence. All values are fabricated for evaluation purposes.', None, None, None)
  3: (None, None, None, None)
  4: ('Data sheet', None, None, None)
  5: ('Column', 'Type', 'Definition', 'Example values')
  6: ('TXN_DT', 'Date', 'Calendar date of the transaction. FY26 lines fall in the current year; FY25 lines fall one year earlier.', '2026-08-18')
  7: ('FISCAL_YR', 'Text', 'Fiscal year of the transaction. FY26 = this year (TY), FY25 = last year (LY). Compare DEMAND_AMT across this column for year-over-year.', 'FY26; FY25')
  8: ('FISCAL_WK', 'Text', 'Fiscal year + week of the transaction. Align the same week number across FY26 and FY25 for weekly YoY; use the FY26 sequence for trailing-week trends.', 'FY26 W30; FY25 W30')
  9: ('GEO_REGION', 'Text', 'Region where the sale occurred.', 'North America; Europe; Greater China; Japan')
 10: ('SALES_CHANNEL', 'Text', 'Store type. RETAIL = full-price stores; OUTLET = discount outlet stores with lower prices.', 'RETAIL; OUTLET')
 11: ('CHANNEL_DETAIL', 'Text', 'Where the purchase was made within the store type: in a physical store or online.', 'Retail Store; eComm')
 12: ('PROD_CATEGORY', 'Text', 'Product category.', '1.Womens Bag; 2.Womens Accessories; 3.Womens Footwear; 4.Womens Apparel; 5.Womens Other; 6.Mens')
```
- freeze_panes: A6; autofilter: None; hidden rows: [] (n=0); hidden cols: []

## Sheet `Data` — first 12 raw rows (header-offset check)
```
  1: ('TXN_DT', 'FISCAL_YR', 'FISCAL_WK', 'GEO_REGION', 'SALES_CHANNEL', 'CHANNEL_DETAIL', 'PROD_CATEGORY', 'STYLE_GROUP', 'STYLE_DESC', 'PROD_TYPE', 'CUST_ID', 'COHORT_STATUS', 'CUST_AGE_GROUP', 'INSIDER_FLAG', 'DEMAND_AMT', 'UNIT_QTY', 'TXN_ID')
  2: (datetime.datetime(2026, 8, 7, 0, 0), 'FY26', 'FY26 W28', 'Japan', 'RETAIL', 'eComm', '1.Womens Bag', 'Tabby', 'Tabby Messenger', 'Hero', 361610, 'Retained', 'Gen X', 'N', 418.38, 1, 'SO-26-1003149')
  3: (datetime.datetime(2026, 7, 18, 0, 0), 'FY26', 'FY26 W25', 'Europe', 'OUTLET', 'eComm', '1.Womens Bag', 'Rogue', 'Rogue 25', 'Halo', 638364, 'Reactivated', 'Gen Z', 'Y', 527.34, 2, 'SO-26-1003446')
  4: (datetime.datetime(2025, 8, 8, 0, 0), 'FY25', 'FY25 W28', 'North America', 'OUTLET', 'Retail Store', '1.Womens Bag', 'Brooklyn', 'Brooklyn Crossbody', 'Evergreen', 830217, 'Retained', 'Gen X', 'Y', 225.76, 1, 'SO-25-1000281')
  5: (datetime.datetime(2026, 8, 14, 0, 0), 'FY26', 'FY26 W29', 'North America', 'RETAIL', 'eComm', '1.Womens Bag', 'Willow', 'Willow Tote', 'Core', 499408, 'New', 'Gen Z', 'N', 365.46, 1, 'SO-26-1001748')
  6: (datetime.datetime(2026, 7, 6, 0, 0), 'FY26', 'FY26 W24', 'North America', 'RETAIL', 'Retail Store', '4.Womens Apparel', 'Trench', 'Cotton Trench Coat', 'Halo', 819603, 'Retained', 'Millennial', 'Y', 388.79, 1, 'SO-26-1001631')
  7: (datetime.datetime(2026, 7, 11, 0, 0), 'FY26', 'FY26 W24', 'Europe', 'RETAIL', 'eComm', '1.Womens Bag', 'Willow', 'Willow Tote', 'Core', 372749, 'New', 'Gen X', 'N', 316.03, 1, 'SO-26-1002010')
  8: (datetime.datetime(2025, 7, 30, 0, 0), 'FY25', 'FY25 W27', 'Japan', 'RETAIL', 'eComm', '3.Womens Footwear', 'Loafer', 'Leather Loafer', 'Evergreen', 522197, 'Retained', 'Boomer', 'N', 228.44, 1, 'SO-25-1002178')
  9: (datetime.datetime(2026, 8, 9, 0, 0), 'FY26', 'FY26 W29', 'North America', 'RETAIL', 'Retail Store', '6.Mens', 'Mens Bag', 'Metropolitan Bag', 'Core', 312413, 'New', 'Gen Z', 'N', 516.58, 2, 'SO-26-1001739')
 10: (datetime.datetime(2026, 7, 9, 0, 0), 'FY26', 'FY26 W24', 'Greater China', 'RETAIL', 'Retail Store', '5.Womens Other', 'Fragrance', 'Signature Eau de Parfum', 'Evergreen', 489135, 'Reactivated', 'Boomer', 'N', 397.22, 3, 'SO-26-1000571')
 11: (datetime.datetime(2025, 8, 18, 0, 0), 'FY25', 'FY25 W30', 'Europe', 'RETAIL', 'Retail Store', '6.Mens', 'Mens SLG', 'Slim Billfold Wallet', 'Core', 791676, 'Retained', 'Millennial', 'Y', 180.97, 1, 'SO-25-1000610')
 12: (datetime.datetime(2026, 8, 10, 0, 0), 'FY26', 'FY26 W29', 'North America', 'OUTLET', 'Retail Store', '1.Womens Bag', 'Rogue', 'Rogue 25', 'Halo', 781574, 'New', 'Gen Z', 'N', 455.89, 2, 'SO-26-1002197')
```
- freeze_panes: A2; autofilter: A1:Q3610; hidden rows: [] (n=0); hidden cols: []

## Sheet `Inventory` — first 12 raw rows (header-offset check)
```
  1: ('FISCAL_YR', 'FISCAL_WK', 'STYLE_GROUP', 'ON_HAND_UNITS')
  2: ('FY26', 'FY26 W23', 'Belt Bag', 119)
  3: ('FY26', 'FY26 W23', 'Brooklyn', 177)
  4: ('FY26', 'FY26 W23', 'Card Case', 132)
  5: ('FY26', 'FY26 W23', 'Charms', 90)
  6: ('FY26', 'FY26 W23', 'Fragrance', 81)
  7: ('FY26', 'FY26 W23', 'Jewelry', 77)
  8: ('FY26', 'FY26 W23', 'Knit Dress', 77)
  9: ('FY26', 'FY26 W23', 'Loafer', 81)
 10: ('FY26', 'FY26 W23', 'Lowline Sneaker', 104)
 11: ('FY26', 'FY26 W23', 'Mens Bag', 76)
 12: ('FY26', 'FY26 W23', 'Mens Footwear', 64)
```
- freeze_panes: A2; autofilter: A1:D337; hidden rows: [] (n=0); hidden cols: []

## Column Definitions (full dump)
```
TYLY_data_sample - Column Definitions |  |  | 
Sample extract modeled on a customer and sales (TYLY) table (dummy data). The workbook has three sheets: this Column Definitions sheet, Data (one row per transaction line, this year and last year), and Inventory (weekly stock by product family, this year and last year). On the Data sheet each line belongs to a single fiscal year: FISCAL_YR = FY26 is this year (TY) and FY25 is last year (LY). Every column is populated. Year-over-year = compare DEMAND_AMT across FISCAL_YR (for example FY26 vs FY25 within the same FISCAL_WK number); trailing week = the FY26 week sequence. All values are fabricated for evaluation purposes. |  |  | 
 |  |  | 
Data sheet |  |  | 
Column | Type | Definition | Example values
TXN_DT | Date | Calendar date of the transaction. FY26 lines fall in the current year; FY25 lines fall one year earlier. | 2026-08-18
FISCAL_YR | Text | Fiscal year of the transaction. FY26 = this year (TY), FY25 = last year (LY). Compare DEMAND_AMT across this column for year-over-year. | FY26; FY25
FISCAL_WK | Text | Fiscal year + week of the transaction. Align the same week number across FY26 and FY25 for weekly YoY; use the FY26 sequence for trailing-week trends. | FY26 W30; FY25 W30
GEO_REGION | Text | Region where the sale occurred. | North America; Europe; Greater China; Japan
SALES_CHANNEL | Text | Store type. RETAIL = full-price stores; OUTLET = discount outlet stores with lower prices. | RETAIL; OUTLET
CHANNEL_DETAIL | Text | Where the purchase was made within the store type: in a physical store or online. | Retail Store; eComm
PROD_CATEGORY | Text | Product category. | 1.Womens Bag; 2.Womens Accessories; 3.Womens Footwear; 4.Womens Apparel; 5.Womens Other; 6.Mens
STYLE_GROUP | Text | Product family, e.g. all Tabby bags. Links to the Inventory sheet. | Tabby; Willow; Brooklyn; Wallet
STYLE_DESC | Text | Product name. | Tabby Shoulder Bag 26
PROD_TYPE | Text | How the business classifies each product family. Hero = the current trend-driving products; Core = everyday best-sellers; Halo = statement pieces that build the brand image; Evergreen = timeless classics that sell steadily. | Hero; Core; Halo; Evergreen
CUST_ID | Number | Identifier for the purchasing customer. | 824193
COHORT_STATUS | Text | Customer status at the time of this purchase, based on the customer's full purchase history with the brand. New = first-ever purchase; Reactivated = returning after a long gap with no purchases; Retained = active returning customer. | New; Reactivated; Retained
CUST_AGE_GROUP | Text | Customer generation. | Gen Z; Millennial; Gen X; Boomer
INSIDER_FLAG | Text | Whether the customer is a member of the loyalty program (called Insider). | Y; N
DEMAND_AMT | Number | Sales amount in USD for the line, after discounts. | 412.50
UNIT_QTY | Number | Units sold on the line. | 1
TXN_ID | Text | Transaction identifier. Count distinct for transaction counts. | SO-26-1043827
 |  |  | 
Inventory sheet |  |  | 
Column | Type | Definition | Example values
FISCAL_YR | Text | Fiscal year. FY26 = this year (TY), FY25 = last year (LY). | FY26; FY25
FISCAL_WK | Text | Fiscal year + week. Same labels as the Data sheet. | FY26 W30; FY25 W30
STYLE_GROUP | Text | Product family. Same values as STYLE_GROUP on the Data sheet. | Tabby
ON_HAND_UNITS | Number | Units in stock at the end of the week, all stores and online combined. | 85
```