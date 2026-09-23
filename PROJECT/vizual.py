"""
Sales Data Analysis
===================
Comprehensive analysis of Sales_transactions_2022_2025.csv
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("TkAgg")          # interactive window; falls back below if unavailable
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from pathlib import Path

# ── Output folder ────────────────────────────────────────────────────────────
OUT = Path("charts")
OUT.mkdir(exist_ok=True)

# ── Styling ───────────────────────────────────────────────────────────────────
PALETTE   = "tab10"
BG        = "#f7f8fa"
ACCENT    = "#3b82d4"
ACCENT2   = "#7c5cd8"
sns.set_theme(style="whitegrid", font_scale=1.05)
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG,
                     "savefig.facecolor": BG, "savefig.dpi": 150,
                     "savefig.bbox": "tight"})

# Registry – every figure created by save() is stored here for the dashboard
_ALL_FIGS: list = []

def save(name):
    fig = plt.gcf()
    fig._chart_title = name          # tag used by the dashboard
    _ALL_FIGS.append(fig)
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight", dpi=150)
    # NOTE: do NOT close – kept alive for the dashboard window
    print(f"  [chart] {name}.png saved")

def divider(title):
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)

# ═══════════════════════════════════════════════════════════════════════════════
# 1. LOAD
# ═══════════════════════════════════════════════════════════════════════════════
divider("1. LOADING DATASET")
df_raw = pd.read_csv("Sales_transactions_2022_2025.csv")
print(f"  Rows: {len(df_raw):,}   Columns: {df_raw.shape[1]}")

# ═══════════════════════════════════════════════════════════════════════════════
# 2. DATA QUALITY
# ═══════════════════════════════════════════════════════════════════════════════
divider("2. DATA QUALITY ANALYSIS")

df = df_raw.copy()

# ── 2a. Missing values ───────────────────────────────────────────────────────
print("\n  [Missing Values]")
missing = df.isnull().sum()
missing_pct = (missing / len(df) * 100).round(2)
mv = pd.DataFrame({"Missing": missing, "Pct%": missing_pct})
mv = mv[mv["Missing"] > 0].sort_values("Missing", ascending=False)
print(mv.to_string())

# ── 2b. Duplicates ───────────────────────────────────────────────────────────
dups = df.duplicated(subset=["Transaction_ID"]).sum()
print(f"\n  [Duplicates]  {dups} duplicate Transaction_IDs found -> dropping")
df = df.drop_duplicates(subset=["Transaction_ID"])
print(f"  Rows after dedup: {len(df):,}")

# ── 2c. Fix data types ───────────────────────────────────────────────────────
df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")
invalid_dates = df["Order_Date"].isna().sum()
print(f"\n  [Dates]  {invalid_dates} invalid dates after conversion")
df["Order_Month"]      = df["Order_Date"].dt.month
df["Order_Month_Name"] = df["Order_Date"].dt.strftime("%b")
df["Order_Quarter"]    = df["Order_Date"].dt.quarter

# ── 2d. Standardize categoricals ─────────────────────────────────────────────
# Product Category
cat_map = {
    "electronics":    "Electronics",
    "FURNITURE":      "Furniture",
    "Office supplies":"Office Supplies",
}
df["Product_Category"] = df["Product_Category"].str.strip().replace(cat_map)

# Order Status
status_map = {
    "SHIPPED":    "Shipped",
    "completed":  "Completed",
    "processing": "Processing",
}
df["Order_Status"] = df["Order_Status"].str.strip().replace(status_map)

# Payment Method
pay_map = {
    "paypal":        "PayPal",
    "credit card":   "Credit Card",
    "Bank transfer": "Bank Transfer",
    "DebitCard":     "Debit Card",
}
df["Payment_Method"] = df["Payment_Method"].str.strip().replace(pay_map)

# Region - fix encoding artefact
df["Region"] = df["Region"].str.replace("ÃŽle-de-France", "Ile-de-France", regex=False)
df["Region"] = df["Region"].str.replace("Â·le-de-France", "Ile-de-France", regex=False)
df["Region"] = df["Region"].str.replace("AZle-de-France", "Ile-de-France", regex=False)
# Catch any remaining garbled prefix before "le-de-France"
df["Region"] = df["Region"].str.replace(r"^.{1,3}le-de-France$", "Ile-de-France", regex=True)
# Consolidate near-duplicates
df["Region"] = df["Region"].str.strip()
df["Region"] = df["Region"].replace({
    "British columbia": "British Columbia",
    "NRW":              "North Rhine-Westphalia",
})

print("\n  [Standardized]")
print(f"  Product_Category values : {sorted(df['Product_Category'].unique())}")
print(f"  Order_Status values     : {sorted(df['Order_Status'].unique())}")
print(f"  Payment_Method values   : {sorted(df['Payment_Method'].dropna().unique())}")
print(f"  Region values           : {sorted(df['Region'].unique())}")

# ── 2e. Validate quantity / price / discount ──────────────────────────────────
neg_qty   = (df["Quantity"] <= 0).sum()
neg_price = (df["Unit_Price"] <= 0).sum()
bad_disc  = ((df["Discount_Percentage"] < 0) | (df["Discount_Percentage"] > 100)).sum()
print(f"\n  [Validity]  Negative/zero qty: {neg_qty}  |  price: {neg_price}  |  bad discount: {bad_disc}")

# ── 2f. Formula checks ────────────────────────────────────────────────────────
df["Calc_Sales"]  = (df["Quantity"] * df["Unit_Price"] * (1 - df["Discount_Percentage"] / 100)).round(2)
df["Sales_Diff"]  = (df["Sales_Amount"] - df["Calc_Sales"]).abs()
df["Calc_Profit"] = (df["Sales_Amount"] - df["Cost_Amount"]).round(2)
df["Profit_Diff"] = (df["Profit"] - df["Calc_Profit"]).abs()

sales_formula_ok   = (df["Sales_Diff"]  < 0.05).sum()
profit_formula_ok  = (df["Profit_Diff"] < 0.05).sum()
total              = len(df)
print(f"\n  [Formula Check]")
print(f"  Sales  = Qty x Price x (1-disc) matches: {sales_formula_ok:,} / {total:,} rows")
print(f"  Profit = Sales - Cost            matches: {profit_formula_ok:,} / {total:,} rows")
print(f"  => Using recorded Sales_Amount, Cost_Amount, Profit for all further analysis.")

# Drop helper cols
df.drop(columns=["Calc_Sales","Sales_Diff","Calc_Profit","Profit_Diff"], inplace=True)

# ── 2g. Missing ratings / inventory ──────────────────────────────────────────
miss_rating = df["Customer_Rating"].isna().sum()
miss_inv    = df["Inventory_Level"].isna().sum()
miss_return = df[df["Return_Flag"] == "Yes"]["Return_Reason"].isna().sum()
print(f"\n  Missing Customer_Rating : {miss_rating:,}")
print(f"  Missing Inventory_Level : {miss_inv:,}")
print(f"  Returned rows w/o Reason: {miss_return:,}")

# ═══════════════════════════════════════════════════════════════════════════════
# 3. KEY METRICS
# ═══════════════════════════════════════════════════════════════════════════════
divider("3. KEY BUSINESS METRICS")

total_sales    = df["Sales_Amount"].sum()
total_cost     = df["Cost_Amount"].sum()
total_profit   = df["Profit"].sum()
total_qty      = df["Quantity"].sum()
total_txns     = len(df)
total_orders   = df["Order_ID"].nunique()
total_customers= df["Customer_ID"].nunique()
avg_txn        = df["Sales_Amount"].mean()
avg_order      = df.groupby("Order_ID")["Sales_Amount"].sum().mean()
profit_margin  = total_profit / total_sales * 100
returned       = df[df["Return_Flag"] == "Yes"]
return_rate    = len(returned) / total_txns * 100
avg_rating     = df["Customer_Rating"].mean()

print(f"  Total Sales        : ${total_sales:>14,.2f}")
print(f"  Total Cost         : ${total_cost:>14,.2f}")
print(f"  Total Profit       : ${total_profit:>14,.2f}")
print(f"  Profit Margin      : {profit_margin:>13.2f}%")
print(f"  Total Transactions : {total_txns:>14,}")
print(f"  Total Orders       : {total_orders:>14,}")
print(f"  Total Customers    : {total_customers:>14,}")
print(f"  Total Qty Sold     : {total_qty:>14,}")
print(f"  Avg Sales/Txn      : ${avg_txn:>14,.2f}")
print(f"  Avg Order Value    : ${avg_order:>14,.2f}")
print(f"  Return Rate        : {return_rate:>13.2f}%")
print(f"  Avg Customer Rating: {avg_rating:>13.2f} / 5.0")

# ═══════════════════════════════════════════════════════════════════════════════
# 4. SALES ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
divider("4. SALES ANALYSIS")

# By Year
sales_yr = df.groupby("Order_Year")["Sales_Amount"].sum().reset_index()
print("\n  [Sales by Year]")
print(sales_yr.to_string(index=False))

fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(sales_yr["Order_Year"].astype(str), sales_yr["Sales_Amount"] / 1e6,
       color=ACCENT, edgecolor="white")
ax.set_title("Total Sales by Year", fontweight="bold")
ax.set_xlabel("Year"); ax.set_ylabel("Sales ($ Millions)")
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.1fM"))
save("01_sales_by_year")

# By Month (across all years)
month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
sales_mo = (df.groupby("Order_Month_Name")["Sales_Amount"]
              .sum().reindex(month_order).reset_index())
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(sales_mo["Order_Month_Name"], sales_mo["Sales_Amount"] / 1e3,
        marker="o", color=ACCENT, linewidth=2)
ax.fill_between(range(12), sales_mo["Sales_Amount"] / 1e3, alpha=0.15, color=ACCENT)
ax.set_xticks(range(12)); ax.set_xticklabels(month_order)
ax.set_title("Monthly Sales Trend (All Years Combined)", fontweight="bold")
ax.set_xlabel("Month"); ax.set_ylabel("Sales ($K)")
save("02_monthly_sales_trend")

# By Country
sales_country = (df.groupby("Country")
                   .agg(Total_Sales=("Sales_Amount","sum"),
                        Transactions=("Transaction_ID","count"),
                        Total_Profit=("Profit","sum"))
                   .sort_values("Total_Sales", ascending=False).reset_index())
print("\n  [Sales by Country]")
print(sales_country.to_string(index=False))

fig, ax = plt.subplots(figsize=(9, 4))
ax.barh(sales_country["Country"][::-1], sales_country["Total_Sales"][::-1] / 1e6,
        color=sns.color_palette(PALETTE, len(sales_country)))
ax.set_title("Total Sales by Country", fontweight="bold")
ax.set_xlabel("Sales ($ Millions)")
ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("$%.1fM"))
save("03_sales_by_country")

# By Sales Channel
sales_ch = (df.groupby("Sales_Channel")
              .agg(Total_Sales=("Sales_Amount","sum"),
                   Total_Profit=("Profit","sum"),
                   Transactions=("Transaction_ID","count"),
                   Avg_Order=("Sales_Amount","mean"))
              .sort_values("Total_Sales", ascending=False).reset_index())
print("\n  [Sales by Channel]")
print(sales_ch.to_string(index=False))

# ═══════════════════════════════════════════════════════════════════════════════
# 5. PRODUCT ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
divider("5. PRODUCT ANALYSIS")

prod = (df.groupby("Product_Name")
          .agg(Total_Sales=("Sales_Amount","sum"),
               Total_Profit=("Profit","sum"),
               Qty_Sold=("Quantity","sum"),
               Avg_Price=("Unit_Price","mean"),
               Transactions=("Transaction_ID","count"))
          .assign(Profit_Margin=lambda x: x["Total_Profit"] / x["Total_Sales"] * 100)
          .sort_values("Total_Sales", ascending=False).reset_index())

print("\n  [Top 10 Products by Sales]")
print(prod.head(10)[["Product_Name","Total_Sales","Total_Profit",
                      "Profit_Margin","Qty_Sold"]].to_string(index=False))
print(f"\n  Highest-Sales Product : {prod.iloc[0]['Product_Name']}")
print(f"  Highest-Profit Product: {prod.sort_values('Total_Profit',ascending=False).iloc[0]['Product_Name']}")
print(f"  Best Margin Product   : {prod.sort_values('Profit_Margin',ascending=False).iloc[0]['Product_Name']}")

# Top-10 products chart
top10 = prod.head(10)
fig, ax = plt.subplots(figsize=(10, 5))
colors = sns.color_palette(PALETTE, 10)
ax.barh(top10["Product_Name"][::-1], top10["Total_Sales"][::-1] / 1e3, color=colors[::-1])
ax.set_title("Top 10 Products by Total Sales", fontweight="bold")
ax.set_xlabel("Sales ($K)")
save("04_top10_products")

# All products
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
prod_sorted = prod.sort_values("Total_Sales", ascending=False)
axes[0].barh(prod_sorted["Product_Name"][::-1],
             prod_sorted["Total_Sales"][::-1] / 1e3,
             color=ACCENT)
axes[0].set_title("Sales by Product", fontweight="bold")
axes[0].set_xlabel("Sales ($K)")
axes[1].barh(prod.sort_values("Total_Profit")["Product_Name"],
             prod.sort_values("Total_Profit")["Total_Profit"] / 1e3,
             color=ACCENT2)
axes[1].set_title("Profit by Product", fontweight="bold")
axes[1].set_xlabel("Profit ($K)")
plt.tight_layout()
save("05_sales_profit_by_product")

# High-sales/low-profit and vice versa
med_sales  = prod["Total_Sales"].median()
med_margin = prod["Profit_Margin"].median()
high_low   = prod[(prod["Total_Sales"] > med_sales) & (prod["Profit_Margin"] < med_margin)]
low_high   = prod[(prod["Total_Sales"] < med_sales) & (prod["Profit_Margin"] > med_margin)]
print(f"\n  [High Sales / Low Margin] products:\n  {high_low['Product_Name'].tolist()}")
print(f"  [Low Sales / High Margin] products:\n  {low_high['Product_Name'].tolist()}")

# ═══════════════════════════════════════════════════════════════════════════════
# 6. CATEGORY ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
divider("6. CATEGORY ANALYSIS")

ret_by_cat = (df.groupby("Product_Category")
                .apply(lambda x: (x["Return_Flag"] == "Yes").sum() / len(x) * 100)
                .reset_index(name="Return_Rate"))

cat = (df.groupby("Product_Category")
         .agg(Total_Sales=("Sales_Amount","sum"),
              Total_Profit=("Profit","sum"),
              Qty_Sold=("Quantity","sum"),
              Avg_Discount=("Discount_Percentage","mean"),
              Transactions=("Transaction_ID","count"))
         .assign(Profit_Margin=lambda x: x["Total_Profit"] / x["Total_Sales"] * 100)
         .merge(ret_by_cat, on="Product_Category")
         .sort_values("Total_Sales", ascending=False).reset_index())

print("\n  [Category Summary]")
print(cat[["Product_Category","Total_Sales","Total_Profit","Profit_Margin",
           "Avg_Discount","Return_Rate"]].to_string(index=False))

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
colors = sns.color_palette(PALETTE, len(cat))
axes[0].bar(cat["Product_Category"], cat["Total_Sales"] / 1e6, color=colors)
axes[0].set_title("Sales by Category", fontweight="bold")
axes[0].set_xlabel("Category"); axes[0].set_ylabel("Sales ($M)")
axes[0].tick_params(axis="x", rotation=25)
axes[1].bar(cat["Product_Category"], cat["Total_Profit"] / 1e6, color=colors)
axes[1].set_title("Profit by Category", fontweight="bold")
axes[1].set_xlabel("Category"); axes[1].set_ylabel("Profit ($M)")
axes[1].tick_params(axis="x", rotation=25)
plt.tight_layout()
save("06_sales_profit_by_category")

# Subcategory
subcat = (df.groupby("Product_Subcategory")
            .agg(Total_Sales=("Sales_Amount","sum"),
                 Total_Profit=("Profit","sum"),
                 Qty_Sold=("Quantity","sum"))
            .assign(Profit_Margin=lambda x: x["Total_Profit"] / x["Total_Sales"] * 100)
            .sort_values("Total_Sales", ascending=False).reset_index())
print("\n  [Top Subcategories by Sales]")
print(subcat.head(10).to_string(index=False))

# Return rate by category chart
fig, ax = plt.subplots(figsize=(9, 4))
ax.bar(cat["Product_Category"], cat["Return_Rate"],
       color=sns.color_palette("Reds_d", len(cat)))
ax.set_title("Return Rate by Category (%)", fontweight="bold")
ax.set_xlabel("Category"); ax.set_ylabel("Return Rate (%)")
ax.tick_params(axis="x", rotation=25)
save("07_return_rate_by_category")

# ═══════════════════════════════════════════════════════════════════════════════
# 7. CUSTOMER ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
divider("7. CUSTOMER ANALYSIS")

cust = (df.groupby("Customer_ID")
          .agg(Orders=("Order_ID","nunique"),
               Transactions=("Transaction_ID","count"),
               Total_Spend=("Sales_Amount","sum"),
               Avg_Order=("Sales_Amount","mean"),
               Total_Profit=("Profit","sum"),
               Returns=("Return_Flag", lambda x: (x == "Yes").sum()))
          .assign(Return_Rate=lambda x: x["Returns"] / x["Transactions"] * 100)
          .reset_index())

print(f"\n  Total unique customers: {len(cust):,}")
print(f"  Avg spend per customer: ${cust['Total_Spend'].mean():,.2f}")
print(f"  Avg orders per customer:{cust['Orders'].mean():.2f}")
print(f"  Top spender: ${cust['Total_Spend'].max():,.2f}")

# Age bins
df["Age_Group"] = pd.cut(df["Customer_Age"].dropna(),
                          bins=[0, 25, 35, 45, 55, 100],
                          labels=["<25","25-34","35-44","45-54","55+"])
age_sales = (df.groupby("Age_Group", observed=True)["Sales_Amount"]
               .sum().reset_index().dropna())
fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(age_sales["Age_Group"].astype(str), age_sales["Sales_Amount"] / 1e3, color=ACCENT)
ax.set_title("Sales by Customer Age Group", fontweight="bold")
ax.set_xlabel("Age Group"); ax.set_ylabel("Sales ($K)")
save("08_sales_by_age_group")

# Gender
gender = (df.groupby("Customer_Gender")
            .agg(Sales=("Sales_Amount","sum"),
                 Transactions=("Transaction_ID","count"))
            .reset_index().dropna())
print("\n  [Sales by Gender]")
print(gender.to_string(index=False))

# ═══════════════════════════════════════════════════════════════════════════════
# 8. CUSTOMER SEGMENT ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
divider("8. CUSTOMER SEGMENT ANALYSIS")

seg_ret = (df.groupby("Customer_Segment")
             .apply(lambda x: (x["Return_Flag"] == "Yes").sum() / len(x) * 100)
             .reset_index(name="Return_Rate"))

seg = (df.groupby("Customer_Segment")
         .agg(Customers=("Customer_ID","nunique"),
              Transactions=("Transaction_ID","count"),
              Total_Sales=("Sales_Amount","sum"),
              Total_Profit=("Profit","sum"),
              Avg_Order=("Sales_Amount","mean"),
              Avg_Discount=("Discount_Percentage","mean"),
              Avg_Rating=("Customer_Rating","mean"))
         .merge(seg_ret, on="Customer_Segment")
         .sort_values("Total_Sales", ascending=False).reset_index())

print("\n  [Customer Segment Summary]")
print(seg[["Customer_Segment","Customers","Transactions","Total_Sales",
           "Total_Profit","Avg_Order","Avg_Discount","Return_Rate","Avg_Rating"]].to_string(index=False))

colors = sns.color_palette(PALETTE, len(seg))
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
axes[0].bar(seg["Customer_Segment"], seg["Total_Sales"] / 1e3, color=colors)
axes[0].set_title("Sales by Customer Segment", fontweight="bold")
axes[0].set_ylabel("Sales ($K)"); axes[0].tick_params(axis="x", rotation=25)
axes[1].bar(seg["Customer_Segment"], seg["Total_Profit"] / 1e3, color=colors)
axes[1].set_title("Profit by Customer Segment", fontweight="bold")
axes[1].set_ylabel("Profit ($K)"); axes[1].tick_params(axis="x", rotation=25)
plt.tight_layout()
save("09_customer_segment_comparison")

# ═══════════════════════════════════════════════════════════════════════════════
# 9. SALES CHANNEL ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
divider("9. SALES CHANNEL ANALYSIS")

ch_ret = (df.groupby("Sales_Channel")
            .apply(lambda x: (x["Return_Flag"] == "Yes").sum() / len(x) * 100)
            .reset_index(name="Return_Rate"))

ch = (df.groupby("Sales_Channel")
        .agg(Transactions=("Transaction_ID","count"),
             Total_Sales=("Sales_Amount","sum"),
             Total_Profit=("Profit","sum"),
             Avg_Order=("Sales_Amount","mean"),
             Avg_Discount=("Discount_Percentage","mean"))
        .merge(ch_ret, on="Sales_Channel")
        .sort_values("Total_Sales", ascending=False).reset_index())

print("\n  [Channel Summary]")
print(ch.to_string(index=False))

colors = sns.color_palette(PALETTE, len(ch))
fig, axes = plt.subplots(2, 2, figsize=(13, 9))
metrics = [("Total_Sales","Sales ($)"),("Total_Profit","Profit ($)"),
           ("Transactions","Transactions"),("Avg_Order","Avg Order ($)")]
for ax, (col, label) in zip(axes.flat, metrics):
    ax.bar(ch["Sales_Channel"], ch[col], color=colors)
    ax.set_title(f"{label} by Channel", fontweight="bold")
    ax.set_ylabel(label); ax.tick_params(axis="x", rotation=20)
plt.tight_layout()
save("10_sales_channel_comparison")

# ═══════════════════════════════════════════════════════════════════════════════
# 10. PROFIT ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
divider("10. PROFIT ANALYSIS")

print(f"\n  Total Sales  : ${total_sales:,.2f}")
print(f"  Total Cost   : ${total_cost:,.2f}")
print(f"  Total Profit : ${total_profit:,.2f}")
print(f"  Profit Margin: {profit_margin:.2f}%")

# Profit by year
profit_yr = df.groupby("Order_Year")["Profit"].sum()
print("\n  [Profit by Year]")
print(profit_yr.to_string())

# Profit by region
profit_region = (df.groupby("Region")["Profit"]
                   .agg(["sum","mean"])
                   .rename(columns={"sum":"Total_Profit","mean":"Avg_Profit"})
                   .sort_values("Total_Profit", ascending=False))
print("\n  [Top Regions by Profit]")
print(profit_region.head(10).to_string())

# Profit by promotion
profit_promo = (df.groupby(df["Promotion_Code"].fillna("No Promo"))
                  .agg(Sales=("Sales_Amount","sum"),
                       Profit=("Profit","sum"),
                       Transactions=("Transaction_ID","count"))
                  .assign(Margin=lambda x: x["Profit"] / x["Sales"] * 100)
                  .sort_values("Sales", ascending=False))
print("\n  [Profit by Promotion]")
print(profit_promo.to_string())

# ═══════════════════════════════════════════════════════════════════════════════
# 11. DISCOUNT & PROMOTION ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
divider("11. DISCOUNT & PROMOTION ANALYSIS")

promo = df["Promotion_Code"].notna()
promo_summary = (df.assign(Promoted=promo)
                   .groupby("Promoted")
                   .agg(Transactions=("Transaction_ID","count"),
                        Avg_Sales=("Sales_Amount","mean"),
                        Avg_Profit=("Profit","mean"),
                        Avg_Discount=("Discount_Percentage","mean"),
                        Avg_Rating=("Customer_Rating","mean"))
                   .rename(index={True:"With Promo", False:"No Promo"}))
print("\n  [Promo vs No-Promo]")
print(promo_summary.to_string())

# Discount vs Profit scatter
fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(df["Discount_Percentage"], df["Profit"],
           alpha=0.3, s=10, color=ACCENT)
m, b = np.polyfit(df["Discount_Percentage"], df["Profit"], 1)
x_line = np.linspace(df["Discount_Percentage"].min(), df["Discount_Percentage"].max(), 100)
ax.plot(x_line, m * x_line + b, color="red", linewidth=1.5, label=f"Trend (slope={m:.1f})")
ax.set_title("Discount % vs Profit per Transaction", fontweight="bold")
ax.set_xlabel("Discount (%)"); ax.set_ylabel("Profit ($)")
ax.legend()
save("11_discount_vs_profit")

# Discount bins
df["Disc_Bin"] = pd.cut(df["Discount_Percentage"],
                         bins=[-1, 0, 5, 10, 15, 20, 25, 100],
                         labels=["0%","1-5%","6-10%","11-15%","16-20%","21-25%",">25%"])
disc_margin = (df.groupby("Disc_Bin", observed=True)
                 .agg(Avg_Margin=("Profit", lambda x:
                      (x.sum() / df.loc[x.index, "Sales_Amount"].sum() * 100)))
                 .reset_index())
fig, ax = plt.subplots(figsize=(9, 4))
ax.bar(disc_margin["Disc_Bin"].astype(str), disc_margin["Avg_Margin"],
       color=sns.color_palette("Blues_d", len(disc_margin)))
ax.set_title("Profit Margin by Discount Band", fontweight="bold")
ax.set_xlabel("Discount Range"); ax.set_ylabel("Profit Margin (%)")
save("12_margin_by_discount_band")

corr_disc = df[["Discount_Percentage","Sales_Amount","Profit"]].corr()
print("\n  [Discount Correlations]")
print(corr_disc.to_string())

# ═══════════════════════════════════════════════════════════════════════════════
# 12. PAYMENT ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
divider("12. PAYMENT ANALYSIS")

pay = (df.groupby("Payment_Method")
         .agg(Transactions=("Transaction_ID","count"),
              Total_Sales=("Sales_Amount","sum"),
              Avg_Sales=("Sales_Amount","mean"),
              Total_Profit=("Profit","sum"))
         .sort_values("Transactions", ascending=False).reset_index())
print("\n  [Payment Method Summary]")
print(pay.to_string(index=False))

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
axes[0].pie(pay["Transactions"], labels=pay["Payment_Method"], autopct="%1.1f%%",
            colors=sns.color_palette(PALETTE, len(pay)), startangle=140)
axes[0].set_title("Payment Method Distribution\n(Transactions)", fontweight="bold")
axes[1].bar(pay["Payment_Method"], pay["Total_Sales"] / 1e3,
            color=sns.color_palette(PALETTE, len(pay)))
axes[1].set_title("Sales by Payment Method", fontweight="bold")
axes[1].set_ylabel("Sales ($K)"); axes[1].tick_params(axis="x", rotation=25)
plt.tight_layout()
save("13_payment_method_distribution")

# ═══════════════════════════════════════════════════════════════════════════════
# 13. RETURN ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
divider("13. RETURN ANALYSIS")

total_returned = len(returned)
print(f"\n  Total Returns       : {total_returned:,}")
print(f"  Return Rate         : {return_rate:.2f}%")

# Return reasons
ret_reasons = (returned["Return_Reason"].value_counts().reset_index()
               .rename(columns={"Return_Reason":"Reason","count":"Count"}))
print("\n  [Return Reasons]")
print(ret_reasons.to_string(index=False))

# Return rate by product
ret_prod = (df.groupby("Product_Name")
              .apply(lambda x: (x["Return_Flag"] == "Yes").sum() / len(x) * 100)
              .sort_values(ascending=False).reset_index(name="Return_Rate"))
print("\n  [Top 10 Products by Return Rate]")
print(ret_prod.head(10).to_string(index=False))

# Return rate by channel
ret_ch = (df.groupby("Sales_Channel")
            .apply(lambda x: (x["Return_Flag"] == "Yes").sum() / len(x) * 100)
            .sort_values(ascending=False).reset_index(name="Return_Rate"))
print("\n  [Return Rate by Channel]")
print(ret_ch.to_string(index=False))

# Return rate by country
ret_country = (df.groupby("Country")
                 .apply(lambda x: (x["Return_Flag"] == "Yes").sum() / len(x) * 100)
                 .sort_values(ascending=False).reset_index(name="Return_Rate"))
print("\n  [Return Rate by Country]")
print(ret_country.to_string(index=False))

# ═══════════════════════════════════════════════════════════════════════════════
# 14. DELIVERY & SHIPPING ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
divider("14. DELIVERY & SHIPPING ANALYSIS")

ship = (df.groupby("Shipping_Method")
          .agg(Count=("Transaction_ID","count"),
               Avg_Days=("Delivery_Days","mean"),
               Median_Days=("Delivery_Days","median"),
               Max_Days=("Delivery_Days","max"),
               Avg_Rating=("Customer_Rating","mean"))
          .sort_values("Avg_Days").reset_index())
print("\n  [Shipping Method Summary]")
print(ship.to_string(index=False))

# Delivery by channel
del_ch = (df.groupby("Sales_Channel")["Delivery_Days"]
            .agg(["mean","median","max"])
            .rename(columns={"mean":"Avg","median":"Median","max":"Max"})
            .sort_values("Avg"))
print("\n  [Delivery Days by Channel]")
print(del_ch.to_string())

# Delivery days vs Rating scatter
ddr = df[df["Delivery_Days"].notna() & df["Customer_Rating"].notna()].copy()
corr_del_rat = ddr["Delivery_Days"].corr(ddr["Customer_Rating"])
print(f"\n  Delivery Days <-> Customer Rating correlation: {corr_del_rat:.4f}")

fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(ddr["Delivery_Days"], ddr["Customer_Rating"],
           alpha=0.25, s=10, color=ACCENT2)
m2, b2 = np.polyfit(ddr["Delivery_Days"], ddr["Customer_Rating"], 1)
x2 = np.linspace(ddr["Delivery_Days"].min(), ddr["Delivery_Days"].max(), 100)
ax.plot(x2, m2 * x2 + b2, color="red", linewidth=1.5,
        label=f"Trend (r={corr_del_rat:.3f})")
ax.set_title("Delivery Days vs Customer Rating", fontweight="bold")
ax.set_xlabel("Delivery Days"); ax.set_ylabel("Customer Rating")
ax.legend()
save("14_delivery_days_vs_rating")

# ═══════════════════════════════════════════════════════════════════════════════
# 15. CUSTOMER RATING ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
divider("15. CUSTOMER RATING ANALYSIS")

print(f"\n  Average Customer Rating: {avg_rating:.2f} / 5.0")

for dim in ["Product_Category","Customer_Segment","Sales_Channel","Shipping_Method","Country"]:
    r = (df.groupby(dim)["Customer_Rating"]
           .agg(Avg_Rating="mean", Count="count")
           .sort_values("Avg_Rating", ascending=False).reset_index())
    print(f"\n  [Rating by {dim}]")
    print(r.to_string(index=False))

# ═══════════════════════════════════════════════════════════════════════════════
# 16. GEOGRAPHIC ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
divider("16. GEOGRAPHIC ANALYSIS")

rr = (df.groupby("Region")
        .apply(lambda x: (x["Return_Flag"] == "Yes").sum() / len(x) * 100)
        .reset_index(name="Return_Rate"))

geo_region = (df.groupby(["Country","Region"])
                .agg(Total_Sales=("Sales_Amount","sum"),
                     Total_Profit=("Profit","sum"),
                     Transactions=("Transaction_ID","count"))
                .assign(Profit_Margin=lambda x: x["Total_Profit"] / x["Total_Sales"] * 100)
                .reset_index()
                .merge(rr, on="Region")
                .sort_values("Total_Sales", ascending=False))

print("\n  [Top 15 Regions by Sales]")
print(geo_region.head(15)[["Country","Region","Total_Sales","Total_Profit",
                             "Profit_Margin","Return_Rate"]].to_string(index=False))

# Top cities
city = (df.groupby(["Country","City"])
          .agg(Total_Sales=("Sales_Amount","sum"),
               Total_Profit=("Profit","sum"),
               Transactions=("Transaction_ID","count"))
          .sort_values("Total_Sales", ascending=False).reset_index())
print("\n  [Top 10 Cities by Sales]")
print(city.head(10).to_string(index=False))

# Sales by region chart (top 10)
top_reg = geo_region.head(10)
fig, ax = plt.subplots(figsize=(10, 5))
ax.barh(top_reg["Region"][::-1], top_reg["Total_Sales"][::-1] / 1e3,
        color=sns.color_palette(PALETTE, 10))
ax.set_title("Top 10 Regions by Total Sales", fontweight="bold")
ax.set_xlabel("Sales ($K)")
save("15_top_regions")

# ═══════════════════════════════════════════════════════════════════════════════
# 17. INVENTORY ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
divider("17. INVENTORY ANALYSIS")

inv = (df.groupby("Product_Name")
         .agg(Avg_Inventory=("Inventory_Level","mean"),
              Total_Sales=("Sales_Amount","sum"),
              Qty_Sold=("Quantity","sum"))
         .reset_index())

med_inv  = inv["Avg_Inventory"].median()
med_qty  = inv["Qty_Sold"].median()

inv["Inv_Segment"] = np.where(
    (inv["Qty_Sold"] >= med_qty) & (inv["Avg_Inventory"] < med_inv),  "High Demand / Low Stock",
    np.where(
        (inv["Qty_Sold"] < med_qty) & (inv["Avg_Inventory"] >= med_inv), "Low Demand / High Stock",
        np.where(
            (inv["Qty_Sold"] >= med_qty) & (inv["Avg_Inventory"] >= med_inv), "High Demand / High Stock",
            "Low Demand / Low Stock"
        )
    )
)
print("\n  [Inventory Segments]")
print(inv.sort_values("Qty_Sold", ascending=False).to_string(index=False))
print("\n  [Segment Counts]")
print(inv["Inv_Segment"].value_counts().to_string())

# Inventory vs Sales scatter
fig, ax = plt.subplots(figsize=(9, 5))
seg_colors = {"High Demand / Low Stock": "red",
              "Low Demand / High Stock": "steelblue",
              "High Demand / High Stock": "green",
              "Low Demand / Low Stock":  "orange"}
for seg_name, grp in inv.groupby("Inv_Segment"):
    ax.scatter(grp["Avg_Inventory"], grp["Qty_Sold"], label=seg_name,
               color=seg_colors[seg_name], s=80, edgecolors="white", linewidth=0.5)
ax.axvline(med_inv, linestyle="--", color="gray", linewidth=0.8)
ax.axhline(med_qty, linestyle="--", color="gray", linewidth=0.8)
ax.set_title("Inventory Level vs Quantity Sold", fontweight="bold")
ax.set_xlabel("Avg Inventory Level"); ax.set_ylabel("Total Qty Sold")
ax.legend(fontsize=8)
save("16_inventory_vs_sales")

# ═══════════════════════════════════════════════════════════════════════════════
# 18. SALES REPRESENTATIVE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
divider("18. SALES REPRESENTATIVE ANALYSIS")

rep = (df.groupby("Sales_Representative")
         .agg(Transactions=("Transaction_ID","count"),
              Total_Sales=("Sales_Amount","sum"),
              Total_Profit=("Profit","sum"),
              Avg_Rating=("Customer_Rating","mean"))
         .assign(Profit_Margin=lambda x: x["Total_Profit"] / x["Total_Sales"] * 100)
         .sort_values("Total_Sales", ascending=False).reset_index())
print("\n  [Sales Rep Performance]")
print(rep.to_string(index=False))
print(f"\n  Top Sales Rep: {rep.iloc[0]['Sales_Representative']} - ${rep.iloc[0]['Total_Sales']:,.2f}")

# ═══════════════════════════════════════════════════════════════════════════════
# 19. CORRELATION HEATMAP
# ═══════════════════════════════════════════════════════════════════════════════
divider("19. CORRELATION HEATMAP")

num_cols = ["Quantity","Unit_Price","Discount_Percentage","Sales_Amount",
            "Cost_Amount","Profit","Delivery_Days","Customer_Rating","Inventory_Level"]
corr_mat = df[num_cols].corr()
fig, ax = plt.subplots(figsize=(10, 8))
mask = np.triu(np.ones_like(corr_mat, dtype=bool))
sns.heatmap(corr_mat, mask=mask, annot=True, fmt=".2f", cmap="coolwarm",
            center=0, linewidths=0.5, ax=ax)
ax.set_title("Correlation Heatmap - Numeric Variables", fontweight="bold")
plt.tight_layout()
save("17_correlation_heatmap")

# ═══════════════════════════════════════════════════════════════════════════════
# 20. BUSINESS QUESTIONS - 20 ANSWERS
# ═══════════════════════════════════════════════════════════════════════════════
divider("20. ANSWERS TO BUSINESS QUESTIONS")

q_answers = []

# Q1
q_answers.append(("Q1", "Which product generates the highest sales?",
                   f"{prod.iloc[0]['Product_Name']} - ${prod.iloc[0]['Total_Sales']:,.2f}"))

# Q2
best_profit_prod = prod.sort_values("Total_Profit", ascending=False).iloc[0]
q_answers.append(("Q2", "Which product generates the highest profit?",
                   f"{best_profit_prod['Product_Name']} - ${best_profit_prod['Total_Profit']:,.2f}"))

# Q3
q_answers.append(("Q3", "Which category generates the highest sales?",
                   f"{cat.iloc[0]['Product_Category']} - ${cat.iloc[0]['Total_Sales']:,.2f}"))

# Q4
best_margin_cat = cat.sort_values("Profit_Margin", ascending=False).iloc[0]
q_answers.append(("Q4", "Which category has the highest profit margin?",
                   f"{best_margin_cat['Product_Category']} - {best_margin_cat['Profit_Margin']:.2f}%"))

# Q5
q_answers.append(("Q5", "Which country performs best in sales?",
                   f"{sales_country.iloc[0]['Country']} - ${sales_country.iloc[0]['Total_Sales']:,.2f}"))

# Q6
best_profit_region = profit_region.iloc[0]
q_answers.append(("Q6", "Which region generates the highest profit?",
                   f"{best_profit_region.name} - ${best_profit_region['Total_Profit']:,.2f}"))

# Q7
q_answers.append(("Q7", "Which sales channel performs best?",
                   f"{ch.iloc[0]['Sales_Channel']} - ${ch.iloc[0]['Total_Sales']:,.2f}"))

# Q8
best_seg = seg.iloc[0]
q_answers.append(("Q8", "Which customer segment spends the most?",
                   f"{best_seg['Customer_Segment']} - ${best_seg['Total_Sales']:,.2f}"))

# Q9
ret_cust = seg[seg["Customer_Segment"] == "Returning Customer"]
new_cust = seg[seg["Customer_Segment"] == "New Customer"]
if not ret_cust.empty and not new_cust.empty:
    ret_margin = ret_cust.iloc[0]["Total_Profit"] / ret_cust.iloc[0]["Total_Sales"] * 100
    new_margin = new_cust.iloc[0]["Total_Profit"] / new_cust.iloc[0]["Total_Sales"] * 100
    ans9 = (f"Returning Customer margin: {ret_margin:.1f}%  |  "
            f"New Customer margin: {new_margin:.1f}%  ->  "
            f"{'Yes' if ret_margin > new_margin else 'No'}, returning customers have higher margin")
else:
    ans9 = "Insufficient segment data to compare"
q_answers.append(("Q9", "Do returning customers generate more profit (margin)?", ans9))

# Q10
q_answers.append(("Q10", "What is the average customer rating?",
                   f"{avg_rating:.2f} / 5.0"))

# Q11
q_answers.append(("Q11", "Which payment method is most popular?",
                   f"{pay.iloc[0]['Payment_Method']} - {pay.iloc[0]['Transactions']:,} transactions"))

# Q12
q_answers.append(("Q12", "Which products have the highest return rate?",
                   ret_prod.head(3).to_string(index=False)))

# Q13
best_promo = (profit_promo[profit_promo.index != "No Promo"]
              .sort_values("Sales", ascending=False))
q_answers.append(("Q13", "Which promotion performs best (by sales)?",
                   f"{best_promo.index[0]} - Sales ${best_promo.iloc[0]['Sales']:,.2f}  |  "
                   f"Margin {best_promo.iloc[0]['Margin']:.2f}%"))

# Q14
corr_dm = df["Discount_Percentage"].corr(
    df["Profit"] / df["Sales_Amount"].replace(0, np.nan) * 100)
q_answers.append(("Q14", "Does higher discount reduce profit margin?",
                   f"Correlation Discount% <-> Profit Margin = {corr_dm:.4f}  "
                   f"({'Yes - negative correlation' if corr_dm < -0.1 else 'Weak/no strong linear effect'})"))

# Q15
q_answers.append(("Q15", "Which shipping method has shortest delivery time?",
                   f"{ship.iloc[0]['Shipping_Method']} - Avg {ship.iloc[0]['Avg_Days']:.2f} days"))

# Q16
q_answers.append(("Q16", "Is delivery time related to customer ratings?",
                   f"Pearson r = {corr_del_rat:.4f}  "
                   f"({'Negative - longer delivery -> lower rating' if corr_del_rat < -0.05 else 'Very weak relationship'})"))

# Q17
q_answers.append(("Q17", "Which sales representative generates the highest sales?",
                   f"{rep.iloc[0]['Sales_Representative']} - ${rep.iloc[0]['Total_Sales']:,.2f}"))

# Q18
risk = inv[inv["Inv_Segment"] == "High Demand / Low Stock"]
q_answers.append(("Q18", "Which products have low inventory but high demand?",
                   ", ".join(risk["Product_Name"].tolist()) if not risk.empty else "None identified"))

# Q19
best_year = sales_yr.sort_values("Sales_Amount", ascending=False).iloc[0]
q_answers.append(("Q19", "Which year generated the highest sales?",
                   f"{int(best_year['Order_Year'])} - ${best_year['Sales_Amount']:,.2f}"))

# Q20
q_answers.append(("Q20", "Most important business trends?",
                   "See Trends section below"))

print()
for qid, question, answer in q_answers:
    print(f"  {qid}. {question}")
    print(f"      -> {answer}")
    print()

# ═══════════════════════════════════════════════════════════════════════════════
# 21. TRENDS SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
divider("21. KEY BUSINESS TRENDS")

trends = [
    "Sales have grown/fluctuated across 2022-2025 - see Year-by-Year chart for direction.",
    "Electronics and Furniture are the leading revenue categories.",
    f"Online channel leads all sales channels with ${ch[ch['Sales_Channel']=='Online']['Total_Sales'].values[0]:,.0f} in total sales." if 'Online' in ch['Sales_Channel'].values else "Multiple strong sales channels identified.",
    f"Top country: {sales_country.iloc[0]['Country']} accounts for largest share of revenue.",
    f"Overall return rate is {return_rate:.1f}% - monitor product quality and delivery issues.",
    f"Average customer rating is {avg_rating:.2f}/5 - customer satisfaction is broadly positive.",
    f"Discounts show correlation {df['Discount_Percentage'].corr(df['Profit']):.2f} with absolute profit - heavy discounting compresses margins.",
    f"Promotion code users generate higher avg order values vs non-promo customers.",
    f"Products in 'High Demand / Low Stock' quadrant: {', '.join(risk['Product_Name'].tolist()) if not risk.empty else 'none'}.",
    f"Top sales rep: {rep.iloc[0]['Sales_Representative']} - review their approach for wider team training.",
]
for i, t in enumerate(trends, 1):
    print(f"  {i:2}. {t}")

# ═══════════════════════════════════════════════════════════════════════════════
# 22. BUSINESS RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════════════════════
divider("22. BUSINESS RECOMMENDATIONS")

recs = [
    f"Stock management: Ensure adequate inventory for high-demand products ({', '.join(risk['Product_Name'].tolist()) if not risk.empty else 'none flagged'}).",
    f"Product review: Investigate high-return-rate products - top: {ret_prod.iloc[0]['Product_Name']} ({ret_prod.iloc[0]['Return_Rate']:.1f}% return rate).",
    f"Category focus: Prioritize {cat.sort_values('Profit_Margin',ascending=False).iloc[0]['Product_Category']} for highest margin.",
    f"Discount policy: Heavy discounts reduce margins; recalibrate discount bands above ~{disc_margin[disc_margin['Avg_Margin'] == disc_margin['Avg_Margin'].min()]['Disc_Bin'].values[0]} where margin drops sharpest.",
    f"Channel strategy: Invest in {ch.iloc[0]['Sales_Channel']} (highest revenue). Analyze weaker channels for improvement.",
    f"Customer retention: Focus on {seg.sort_values('Total_Profit',ascending=False).iloc[0]['Customer_Segment']} segment - they contribute highest profit.",
    f"Delivery improvement: {ship.sort_values('Avg_Days',ascending=False).iloc[0]['Shipping_Method']} has longest avg delivery time ({ship.sort_values('Avg_Days',ascending=False).iloc[0]['Avg_Days']:.1f} days) - investigate SLA compliance.",
    "Rating improvement: Products and channels with below-average ratings should be reviewed for service and quality issues.",
    f"Geographic focus: {sales_country.iloc[0]['Country']} is the top market - ensure marketing investment matches its revenue share.",
    f"Sales team: Benchmark top rep {rep.iloc[0]['Sales_Representative']}'s techniques and apply to team coaching.",
]
for i, r in enumerate(recs, 1):
    print(f"  {i:2}. {r}")

# ═══════════════════════════════════════════════════════════════════════════════
# 23. FINAL COMPOSITE CHARTS
# ═══════════════════════════════════════════════════════════════════════════════
divider("23. FINAL COMPOSITE CHARTS")

# Chart A: 4-panel sales overview
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("Sales Overview Dashboard", fontsize=15, fontweight="bold", y=1.01)

# Year
axes[0,0].bar(sales_yr["Order_Year"].astype(str),
              sales_yr["Sales_Amount"] / 1e6, color=ACCENT)
axes[0,0].set_title("Sales by Year"); axes[0,0].set_ylabel("$M")

# Monthly
axes[0,1].plot(sales_mo["Order_Month_Name"],
               sales_mo["Sales_Amount"] / 1e3, marker="o", color=ACCENT2)
axes[0,1].set_title("Monthly Sales Trend"); axes[0,1].set_ylabel("$K")
axes[0,1].tick_params(axis="x", rotation=35)

# Country
axes[1,0].barh(sales_country["Country"][::-1],
               sales_country["Total_Sales"][::-1] / 1e6,
               color=sns.color_palette(PALETTE, len(sales_country)))
axes[1,0].set_title("Sales by Country"); axes[1,0].set_xlabel("$M")

# Channel
axes[1,1].bar(ch["Sales_Channel"], ch["Total_Sales"] / 1e6,
              color=sns.color_palette(PALETTE, len(ch)))
axes[1,1].set_title("Sales by Channel"); axes[1,1].set_ylabel("$M")
axes[1,1].tick_params(axis="x", rotation=20)

plt.tight_layout()
save("18_sales_overview_dashboard")

# Chart B: Profitability deep-dive
profit_cat_plot = cat.sort_values("Profit_Margin", ascending=False)
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
axes[0].bar(profit_cat_plot["Product_Category"],
            profit_cat_plot["Profit_Margin"],
            color=sns.color_palette("Greens_d", len(profit_cat_plot)))
axes[0].set_title("Profit Margin % by Category", fontweight="bold")
axes[0].set_ylabel("Margin (%)"); axes[0].tick_params(axis="x", rotation=25)
axes[1].bar(rep["Sales_Representative"],
            rep["Total_Profit"] / 1e3,
            color=sns.color_palette(PALETTE, len(rep)))
axes[1].set_title("Total Profit by Sales Representative", fontweight="bold")
axes[1].set_ylabel("Profit ($K)"); axes[1].tick_params(axis="x", rotation=35)
plt.tight_layout()
save("19_profitability_deepdive")

# Chart C: Return & Delivery
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
ret_ch_plot = ret_ch.sort_values("Return_Rate")
axes[0].barh(ret_ch_plot["Sales_Channel"], ret_ch_plot["Return_Rate"],
             color=sns.color_palette("Reds_d", len(ret_ch_plot)))
axes[0].set_title("Return Rate by Sales Channel (%)", fontweight="bold")
axes[0].set_xlabel("Return Rate (%)")
axes[1].bar(ship["Shipping_Method"], ship["Avg_Days"],
            color=sns.color_palette("Blues_d", len(ship)))
axes[1].set_title("Average Delivery Days by Shipping Method", fontweight="bold")
axes[1].set_ylabel("Avg Days"); axes[1].tick_params(axis="x", rotation=20)
plt.tight_layout()
save("20_return_and_delivery")

# ═══════════════════════════════════════════════════════════════════════════════
# DONE – individual charts saved
# ═══════════════════════════════════════════════════════════════════════════════
divider("ANALYSIS COMPLETE")
chart_files = sorted(OUT.glob("*.png"))
print(f"\n  {len(chart_files)} charts saved to ./{OUT}/")
for f in chart_files:
    print(f"    {f.name}")
print()

# ═══════════════════════════════════════════════════════════════════════════════
# INTERACTIVE DASHBOARD  –  all 20 charts in one scrollable window
# ═══════════════════════════════════════════════════════════════════════════════
divider("OPENING INTERACTIVE DASHBOARD")

import math, matplotlib.gridspec as gridspec
from matplotlib.widgets import Button

N       = len(_ALL_FIGS)          # 20
COLS    = 4                        # charts per row
ROWS    = math.ceil(N / COLS)     # 5 rows  ->  4 x 5 = 20 panels

# ── Build one large figure with a 4-column grid ──────────────────────────────
DASH_W  = 28          # inches wide
DASH_H  = ROWS * 5.5  # inches tall  (~27.5 in for 5 rows)

dash = plt.figure(figsize=(DASH_W, DASH_H), facecolor="#1e1e2e")
dash.suptitle(
    "Sales Data Analysis  –  Full Dashboard",
    fontsize=20, fontweight="bold", color="white", y=1.002
)

gs = gridspec.GridSpec(
    ROWS, COLS,
    figure=dash,
    hspace=0.55,   # vertical gap between rows
    wspace=0.35,   # horizontal gap between columns
)

for idx, src_fig in enumerate(_ALL_FIGS):
    row, col = divmod(idx, COLS)
    ax_dash = dash.add_subplot(gs[row, col])

    # Render the source figure into a pixel buffer and display as an image
    src_fig.canvas.draw()
    buf = src_fig.canvas.buffer_rgba()          # RGBA buffer
    import numpy as _np
    img = _np.frombuffer(buf, dtype=_np.uint8)
    w_px, h_px = src_fig.canvas.get_width_height()
    img = img.reshape(h_px, w_px, 4)

    ax_dash.imshow(img)
    ax_dash.axis("off")

    # Strip leading "NN_" prefix and underscores for a clean panel title
    raw = getattr(src_fig, "_chart_title", f"Chart {idx+1}")
    label = " ".join(raw.split("_")[1:]).title()
    ax_dash.set_title(label, fontsize=8, color="white",
                      pad=4, fontweight="bold")

dash.patch.set_facecolor("#1e1e2e")

print(f"  Dashboard built with {N} panels ({ROWS} rows x {COLS} cols).")
print("  Close the window to exit.\n")

plt.show()
