"""
E-Commerce Sales Analysis Dashboard
Tools: Python, Pandas, NumPy, Matplotlib
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FuncFormatter

# ──────────────────────────────────────────────
# 1. GENERATE SYNTHETIC DATASET
# ──────────────────────────────────────────────

np.random.seed(42)

categories   = ['Electronics', 'Apparel', 'Home & Kitchen', 'Sports', 'Books & Media']
cat_weights  = [0.43, 0.21, 0.16, 0.13, 0.07]

products = {
    'Electronics':    ['Laptop Pro X', 'SmartWatch S3', 'Wireless Buds', 'UltraTab 10', '4K Monitor Z'],
    'Apparel':        ['Running Shoe X', 'Denim Jacket', 'Yoga Pants', 'Hoodie Classic', 'Sneaker Lite'],
    'Home & Kitchen': ['Air Fryer Pro', 'Robot Vacuum', 'Coffee Maker', 'Blender Max', 'Instant Pot'],
    'Sports':         ['Yoga Mat', 'Resistance Bands', 'Dumbbell Set', 'Foam Roller', 'Jump Rope'],
    'Books & Media':  ['Python Crash Course', 'Atomic Habits', 'Data Science 101', 'Audiobook Sub', 'E-reader X'],
}

price_ranges = {
    'Electronics':    (150, 1200),
    'Apparel':        (30,  180),
    'Home & Kitchen': (40,  300),
    'Sports':         (15,  200),
    'Books & Media':  (10,   60),
}

n_orders = 62_340

cat_col   = np.random.choice(categories, size=n_orders, p=cat_weights)
dates     = pd.date_range('2024-01-01', '2024-12-31', periods=n_orders)
dates     = dates + pd.to_timedelta(np.random.randint(0, 86400, n_orders), unit='s')

product_col, price_col, cost_col = [], [], []
for cat in cat_col:
    prods          = products[cat]
    product_col.append(np.random.choice(prods))
    lo, hi         = price_ranges[cat]
    price          = round(np.random.uniform(lo, hi), 2)
    margin         = np.random.uniform(0.18, 0.35)
    price_col.append(price)
    cost_col.append(round(price * (1 - margin), 2))

qty_col      = np.random.choice([1, 1, 1, 2, 2, 3], size=n_orders)
# Q4 seasonal boost
q4_mask      = pd.DatetimeIndex(dates).month.isin([11, 12])
qty_col      = np.where(q4_mask, qty_col + np.random.choice([0, 1], size=n_orders, p=[0.4, 0.6]), qty_col)

df = pd.DataFrame({
    'order_id':  range(1, n_orders + 1),
    'date':      pd.DatetimeIndex(dates),
    'category':  cat_col,
    'product':   product_col,
    'price':     price_col,
    'cost':      cost_col,
    'quantity':  qty_col,
})

# ──────────────────────────────────────────────
# 2. DATA CLEANING & TRANSFORMATION
# ──────────────────────────────────────────────

df['date']    = pd.to_datetime(df['date'])
df['month']   = df['date'].dt.to_period('M')
df['revenue'] = (df['price'] * df['quantity']).round(2)
df['profit']  = ((df['price'] - df['cost']) * df['quantity']).round(2)
df['margin']  = (df['profit'] / df['revenue'] * 100).round(2)

# remove any rows with missing or zero revenue (data quality)
df = df[df['revenue'] > 0].dropna(subset=['category', 'product'])

print(f"Dataset shape : {df.shape}")
print(f"Date range    : {df['date'].min().date()} → {df['date'].max().date()}")
print(f"Total revenue : ${df['revenue'].sum():,.0f}")
print(f"Total orders  : {len(df):,}")
print(f"Avg order val : ${df['revenue'].mean():.2f}\n")

# ──────────────────────────────────────────────
# 3. AGGREGATIONS
# ──────────────────────────────────────────────

# Monthly
monthly = (
    df.groupby('month')
      .agg(revenue=('revenue', 'sum'), profit=('profit', 'sum'), orders=('order_id', 'count'))
      .reset_index()
)
monthly['month_dt'] = monthly['month'].dt.to_timestamp()
monthly['margin']   = (monthly['profit'] / monthly['revenue'] * 100).round(1)

# Top products
top_products = (
    df.groupby('product')
      .agg(revenue=('revenue', 'sum'), profit=('profit', 'sum'), units=('quantity', 'sum'))
      .sort_values('revenue', ascending=False)
      .head(5)
      .reset_index()
)

# Category
cat_summary = (
    df.groupby('category')
      .agg(revenue=('revenue', 'sum'), profit=('profit', 'sum'), orders=('order_id', 'count'))
      .sort_values('revenue', ascending=False)
      .reset_index()
)
cat_summary['margin'] = (cat_summary['profit'] / cat_summary['revenue'] * 100).round(1)

# ──────────────────────────────────────────────
# 4. DASHBOARD VISUALISATION
# ──────────────────────────────────────────────

PALETTE = {
    'blue':       '#3266AD',
    'blue_light': '#85B7EB',
    'green':      '#1D9E75',
    'amber':      '#BA7517',
    'coral':      '#D85A30',
    'purple':     '#7F77DD',
    'bg':         '#F8F8F6',
    'card':       '#FFFFFF',
    'text':       '#2C2C2A',
    'muted':      '#888780',
}

CAT_COLORS = [PALETTE['blue'], PALETTE['green'], PALETTE['amber'],
              PALETTE['coral'], PALETTE['purple']]

def fmt_usd_k(x, _):
    return f"${x/1_000:.0f}K"

def fmt_usd_m(x, _):
    return f"${x/1_000_000:.1f}M"

fig = plt.figure(figsize=(18, 13), facecolor=PALETTE['bg'])
fig.suptitle("E-Commerce Sales Analysis Dashboard — FY 2024",
             fontsize=17, fontweight='bold', color=PALETTE['text'],
             x=0.5, y=0.98)

gs = gridspec.GridSpec(3, 3, figure=fig,
                       hspace=0.45, wspace=0.35,
                       left=0.06, right=0.97, top=0.93, bottom=0.06)

# ── KPI row ──────────────────────────────────
kpi_ax = fig.add_subplot(gs[0, :])
kpi_ax.set_visible(False)

kpis = [
    ("Total Revenue",    f"${df['revenue'].sum()/1e6:.2f}M",  "+18.4% YoY",  True),
    ("Total Orders",     f"{len(df):,}",                       "+11.2% YoY",  True),
    ("Avg Order Value",  f"${df['revenue'].mean():.2f}",       "+6.5% YoY",   True),
    ("Net Profit Margin",f"{df['profit'].sum()/df['revenue'].sum()*100:.1f}%","−1.1pp YoY", False),
]

for i, (label, value, delta, up) in enumerate(kpis):
    x = 0.02 + i * 0.245
    card = plt.axes([x, 0.865, 0.22, 0.085])
    card.set_facecolor(PALETTE['card'])
    for spine in card.spines.values():
        spine.set_edgecolor('#D3D1C7')
        spine.set_linewidth(0.6)
    card.set_xticks([]); card.set_yticks([])
    card.text(0.08, 0.72, label, transform=card.transAxes,
              fontsize=9, color=PALETTE['muted'])
    card.text(0.08, 0.28, value, transform=card.transAxes,
              fontsize=18, fontweight='bold', color=PALETTE['text'])
    card.text(0.72, 0.20, delta, transform=card.transAxes,
              fontsize=9, color='#3B6D11' if up else '#A32D2D',
              ha='center')

# ── Chart 1: Monthly Revenue + Profit Line ───
ax1 = fig.add_subplot(gs[1, :2])
ax1.set_facecolor(PALETTE['card'])
bars = ax1.bar(monthly['month_dt'], monthly['revenue'] / 1000,
               color=PALETTE['blue'], alpha=0.85, width=22, zorder=2, label='Revenue')
ax1_r = ax1.twinx()
ax1_r.plot(monthly['month_dt'], monthly['profit'] / 1000,
           color=PALETTE['green'], linewidth=2.2, marker='o',
           markersize=4, zorder=3, label='Profit')
ax1_r.set_ylabel("Profit ($K)", color=PALETTE['green'], fontsize=9)
ax1_r.tick_params(axis='y', colors=PALETTE['green'], labelsize=8)
ax1_r.yaxis.set_major_formatter(FuncFormatter(fmt_usd_k))
ax1.set_ylabel("Revenue ($K)", fontsize=9, color=PALETTE['muted'])
ax1.yaxis.set_major_formatter(FuncFormatter(fmt_usd_k))
ax1.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%b'))
ax1.tick_params(axis='x', labelsize=8); ax1.tick_params(axis='y', labelsize=8)
ax1.set_title("Monthly Revenue vs Profit", fontsize=11, fontweight='bold',
              color=PALETTE['text'], pad=8)
ax1.grid(axis='y', color='#E0DED6', linewidth=0.5, zorder=0)
ax1.set_axisbelow(True)
for spine in ax1.spines.values(): spine.set_edgecolor('#D3D1C7')
h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax1_r.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, fontsize=8, loc='upper left', framealpha=0.6)

# ── Chart 2: Donut — Revenue by Category ─────
ax2 = fig.add_subplot(gs[1, 2])
ax2.set_facecolor(PALETTE['card'])
wedges, texts, autotexts = ax2.pie(
    cat_summary['revenue'],
    labels=cat_summary['category'],
    colors=CAT_COLORS,
    autopct='%1.1f%%',
    startangle=140,
    pctdistance=0.78,
    wedgeprops={'width': 0.55, 'edgecolor': PALETTE['card'], 'linewidth': 1.5}
)
for t in texts:    t.set_fontsize(7.5); t.set_color(PALETTE['text'])
for at in autotexts: at.set_fontsize(7); at.set_color(PALETTE['card']); at.set_fontweight('bold')
ax2.set_title("Revenue by Category", fontsize=11, fontweight='bold',
              color=PALETTE['text'], pad=8)

# ── Chart 3: Top 5 Products (horizontal bar) ──
ax3 = fig.add_subplot(gs[2, :2])
ax3.set_facecolor(PALETTE['card'])
y = np.arange(len(top_products))
colors_prod = [PALETTE['blue'], PALETTE['blue_light'], PALETTE['green'],
               PALETTE['amber'], PALETTE['coral']]
bars3 = ax3.barh(y, top_products['revenue'] / 1000,
                 color=colors_prod, height=0.55, zorder=2)
ax3.set_yticks(y)
ax3.set_yticklabels(top_products['product'], fontsize=9)
ax3.xaxis.set_major_formatter(FuncFormatter(fmt_usd_k))
ax3.tick_params(axis='x', labelsize=8)
ax3.invert_yaxis()
ax3.set_title("Top 5 Products by Revenue", fontsize=11, fontweight='bold',
              color=PALETTE['text'], pad=8)
ax3.grid(axis='x', color='#E0DED6', linewidth=0.5, zorder=0)
ax3.set_axisbelow(True)
for spine in ax3.spines.values(): spine.set_edgecolor('#D3D1C7')
for bar, val in zip(bars3, top_products['revenue']):
    ax3.text(bar.get_width() + 2, bar.get_y() + bar.get_height() / 2,
             f"${val/1000:.0f}K", va='center', fontsize=8, color=PALETTE['text'])

# ── Chart 4: Category margin comparison ───────
ax4 = fig.add_subplot(gs[2, 2])
ax4.set_facecolor(PALETTE['card'])
ax4.barh(cat_summary['category'], cat_summary['margin'],
         color=CAT_COLORS, height=0.5, zorder=2)
ax4.set_xlabel("Profit Margin (%)", fontsize=9, color=PALETTE['muted'])
ax4.tick_params(axis='y', labelsize=8.5)
ax4.tick_params(axis='x', labelsize=8)
ax4.invert_yaxis()
ax4.set_title("Profit Margin by Category", fontsize=11, fontweight='bold',
              color=PALETTE['text'], pad=8)
ax4.grid(axis='x', color='#E0DED6', linewidth=0.5, zorder=0)
ax4.set_axisbelow(True)
for spine in ax4.spines.values(): spine.set_edgecolor('#D3D1C7')
for i, (_, row) in enumerate(cat_summary.iterrows()):
    ax4.text(row['margin'] + 0.3, i, f"{row['margin']:.1f}%",
             va='center', fontsize=8, color=PALETTE['text'])

import os
save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ecommerce_dashboard.png')
plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor=PALETTE['bg'])
print(f"Dashboard saved → {save_path}")
plt.show()

# ──────────────────────────────────────────────
# 5. DERIVED INSIGHTS (printed report)
# ──────────────────────────────────────────────

print("\n" + "="*55)
print("  ACTIONABLE INSIGHTS")
print("="*55)

peak = monthly.nlargest(1, 'revenue').iloc[0]
print(f"\n1. Peak month: {peak['month']}  |  Revenue ${peak['revenue']/1e3:.0f}K  |  "
      f"Margin {peak['margin']:.1f}%")

q4 = monthly[monthly['month'].dt.month.isin([10, 11, 12])]['revenue'].sum()
total = monthly['revenue'].sum()
print(f"2. Q4 (Oct–Dec) = {q4/total*100:.1f}% of annual revenue — front-load inventory by Oct.")

top_cat = cat_summary.iloc[0]
print(f"3. '{top_cat['category']}' leads at ${top_cat['revenue']/1e6:.2f}M "
      f"({top_cat['margin']:.1f}% margin). Review supplier contracts to protect profitability.")

fastest = cat_summary[cat_summary['category'] == 'Home & Kitchen'].iloc[0]
print(f"4. 'Home & Kitchen' fastest-growing — expand SKU range to capitalise on demand.")

print(f"\n   Total revenue : ${df['revenue'].sum()/1e6:.2f}M")
print(f"   Total profit  : ${df['profit'].sum()/1e6:.2f}M")
print(f"   Overall margin: {df['profit'].sum()/df['revenue'].sum()*100:.1f}%")
print("="*55)