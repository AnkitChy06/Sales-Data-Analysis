# Sales Data Analysis

A comprehensive Python data analysis project that explores 18,000+ sales transactions across 6 countries, 4 product categories, and 4 sales channels (2022–2025).

---

## Dataset

| Detail | Value |
|---|---|
| **File** | `Sales_transactions_2022_2025.csv` |
| **Rows** | 18,045 transactions (18,000 after deduplication) |
| **Columns** | 36 fields |
| **Years** | 2022 · 2023 · 2024 · 2025 |
| **Countries** | United States · United Kingdom · Canada · Germany · France · Australia |
| **Products** | 28 unique products |
| **Categories** | Electronics · Furniture · Office Supplies · Appliances |
| **Sales Channels** | Online · Retail Store · B2B Portal · Phone Order |

> The dataset is included in this repository as `Sales_transactions_2022_2025.csv`.  
> A full column-level data dictionary is provided in `sales_data_dictionary.csv`.

---

## Project Description

This project performs end-to-end sales analytics on a multi-year, multi-country transaction dataset. It covers:

- **Data Quality** – missing values, duplicates, type errors, encoding fixes, formula validation
- **Sales Analysis** – by year, month, country, region, city, channel
- **Product & Category Analysis** – top products, profit margins, subcategory breakdown
- **Customer Analysis** – segments, age groups, gender, spend behaviour
- **Profit Analysis** – margins, by region, by promotion code
- **Discount & Promotion Analysis** – discount impact on margin, promo code performance
- **Payment Analysis** – method distribution and sales by payment type
- **Return Analysis** – return rate, reasons, by product / category / channel / country
- **Delivery & Shipping Analysis** – average delivery days, SLA by method and channel
- **Customer Rating Analysis** – average rating by category, segment, channel, country
- **Geographic Analysis** – top regions and cities by sales and profit
- **Inventory Analysis** – 4-quadrant stock risk classification (High/Low Demand × High/Low Stock)
- **Sales Representative Analysis** – rep performance by revenue, profit, and rating
- **20 Business Questions** – answered with actual numerical results from the dataset
- **Interactive Dashboard** – all 20 charts displayed in a single scrollable matplotlib window

---

## Technologies Used

| Library | Version | Purpose |
|---|---|---|
| Python | 3.x | Core language |
| pandas | 2.3.2 | Data loading, cleaning, aggregation |
| numpy | 2.2.6 | Numerical operations, formula checks |
| matplotlib | 3.10.5 | Charts and interactive dashboard window |
| seaborn | 0.13.2 | Statistical chart styling |

---

## Project Structure

```
PROJECT/
├── vizual.py                          # Main analysis script
├── Sales_transactions_2022_2025.csv   # Dataset
├── sales_data_dictionary.csv          # Column definitions
├── requirements.txt                   # Python dependencies
├── README.md                          # This file
├── Salesdatanalysis.docx              # Full project report
└── charts/                            # Auto-generated chart images (20 PNG files)
    ├── 01_sales_by_year.png
    ├── 02_monthly_sales_trend.png
    ├── 03_sales_by_country.png
    ├── 04_top10_products.png
    ├── 05_sales_profit_by_product.png
    ├── 06_sales_profit_by_category.png
    ├── 07_return_rate_by_category.png
    ├── 08_sales_by_age_group.png
    ├── 09_customer_segment_comparison.png
    ├── 10_sales_channel_comparison.png
    ├── 11_discount_vs_profit.png
    ├── 12_margin_by_discount_band.png
    ├── 13_payment_method_distribution.png
    ├── 14_delivery_days_vs_rating.png
    ├── 15_top_regions.png
    ├── 16_inventory_vs_sales.png
    ├── 17_correlation_heatmap.png
    ├── 18_sales_overview_dashboard.png
    ├── 19_profitability_deepdive.png
    └── 20_return_and_delivery.png
```

---

## Setup & Run Instructions

### 1. Prerequisites

- Python 3.8 or higher
- pip

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the analysis

```bash
python vizual.py
```

### 4. What happens when you run it

1. The script loads and cleans the dataset (deduplication, type fixes, encoding corrections, categorical standardisation).
2. All 22 analysis sections run sequentially, printing results to the console.
3. 20 chart PNG files are saved to the `charts/` folder.
4. A single **interactive dashboard window** opens showing all 20 charts in a 4-column × 5-row grid. You can zoom and pan each panel using the matplotlib toolbar.
5. The script exits when you close the dashboard window.

---

## Key Findings

| Question | Answer |
|---|---|
| Highest-sales product | AeroBook 14 Laptop — $1,382,382 |
| Highest-profit product | ProBook 16 Laptop — $251,757 |
| Best-performing category | Electronics — $4,922,081 |
| Highest-margin category | Appliances — 22.01% |
| Top country | United States — $3,503,886 |
| Top region (profit) | England — $269,790 |
| Best sales channel | Online — $3,112,092 |
| Top customer segment | Consumer — $3,666,739 |
| Overall profit margin | 19.98% |
| Return rate | 10.41% |
| Average customer rating | 3.99 / 5.0 |
| Most popular payment | Credit Card (6,804 transactions) |
| Best promotion | HOLIDAY20 — $635,154 sales |
| Discount ↔ margin correlation | −0.46 (higher discount = lower margin) |
| Top sales representative | Lucas Moore — $579,157 |
| Best year | 2025 — $2,298,887 |

---

## Charts Generated

| # | Chart |
|---|---|
| 01 | Total Sales by Year |
| 02 | Monthly Sales Trend |
| 03 | Sales by Country |
| 04 | Top 10 Products by Sales |
| 05 | Sales & Profit by Product |
| 06 | Sales & Profit by Category |
| 07 | Return Rate by Category |
| 08 | Sales by Customer Age Group |
| 09 | Customer Segment Comparison |
| 10 | Sales Channel Comparison (4-panel) |
| 11 | Discount % vs Profit (scatter) |
| 12 | Profit Margin by Discount Band |
| 13 | Payment Method Distribution |
| 14 | Delivery Days vs Customer Rating |
| 15 | Top 10 Regions by Sales |
| 16 | Inventory Level vs Quantity Sold |
| 17 | Correlation Heatmap |
| 18 | Sales Overview Dashboard (4-panel) |
| 19 | Profitability Deep-Dive |
| 20 | Return Rate & Delivery Summary |

---

## Data Quality Notes

- **45 duplicate** Transaction_IDs removed before analysis.
- **Product Category**, **Order Status**, **Payment Method**, and **Region** fields contained mixed-case and encoding errors — all standardised during cleaning.
- **Promotion_Code** is missing for ~54% of rows (transactions without a promotion).
- **Customer_Rating** is missing for ~19% of rows.
- The `Sales Amount = Qty × Price × (1 − Discount%)` formula matches ~99.5% of rows; the recorded `Sales_Amount` field is used for all analysis.

---

## License

This project is submitted for academic purposes. The dataset is provided as part of the course material.
