import streamlit as st
import plotly.express as px
import pandas as pd
import sqlite3
import plotly.graph_objects as go

# ── Helper ──────────────────────────────────────────────
@st.cache_data
def query(sql: str) -> pd.DataFrame:
    with sqlite3.connect("data/processed/sales.db") as conn:
        return pd.read_sql(sql, conn)

# ── Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Sales & Operations Dashboard")
st.markdown("Analiza rentowności Superstore — wpływ rabatów na zysk.")

# ── KPI ─────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

kpi1 = query("SELECT SUM(sales) as total FROM orders")
col1.metric("💰 Total Sales", f"${kpi1['total'][0]:,.0f}")

kpi2 = query("SELECT SUM(profit) as total FROM orders")
col2.metric("📈 Total Profit", f"${kpi2['total'][0]:,.0f}")

kpi3 = query("SELECT COUNT(*) as total FROM orders")
col3.metric("🧾 Orders", f"{kpi3['total'][0]:,}")

kpi4 = query("SELECT ROUND(100.0 * SUM(profit) / SUM(sales), 2) as margin FROM orders")
col4.metric("📊 Avg Margin", f"{kpi4['margin'][0]}%")

# ── Filtry ───────────────────────────────────────────────
st.sidebar.header("🔍 Filtry")
regions = st.sidebar.multiselect(
    "Region",
    options=['East', 'West', 'South', 'Central'],
    default=['East', 'West', 'South', 'Central'],
    key="region_filter"
)

categories = st.sidebar.multiselect(
    "Category",
    options=['Furniture', 'Office Supplies', 'Technology'],
    default=['Furniture', 'Office Supplies', 'Technology'],
    key="category_filter"
)

regions_str = "', '".join(regions)
categories_str = "', '".join(categories)

# ── Discount Impact z filtrami ───────────────────────────
st.subheader("🏷️ Discount Impact Analysis")

disc_query = f"""
    SELECT 
        CASE 
            WHEN discount = 0    THEN 'No Discount'
            WHEN discount <= 0.2 THEN 'Low (1-20%)'
            WHEN discount <= 0.4 THEN 'Mid (21-40%)'
            ELSE                      'High (40%+)'
        END AS discount_bucket,
        COUNT(*) AS orders,
        ROUND(AVG(profit), 2) AS avg_profit,
        ROUND(100.0 * SUM(profit) / SUM(sales), 2) AS margin_pct
    FROM orders
    WHERE region IN ('{regions_str}')
    AND category IN ('{categories_str}')
    GROUP BY discount_bucket
    ORDER BY discount_bucket
"""
df_disc = query(disc_query)

col_a, col_b = st.columns(2)

fig_a = px.bar(
    df_disc,
    x='discount_bucket',
    y='avg_profit',
    color='avg_profit',
    title="Avg Profit per Discount",
    color_continuous_scale='RdYlGn'
)
col_a.plotly_chart(fig_a, use_container_width=True)

fig_b = px.bar(
    df_disc,
    x='discount_bucket',
    y='margin_pct',
    color='margin_pct',
    title="Profit Margin %",
    color_continuous_scale='RdYlGn'
)
col_b.plotly_chart(fig_b, use_container_width=True)

# ── Monthly Trend ────────────────────────────────────────
st.subheader("📅 Monthly Trend")

monthly_query = f"""
    SELECT 
        substr(order_date, 7, 4) || '-' || substr(order_date, 1, 2) AS month,
        SUM(sales) AS total_sales,
        SUM(profit) AS total_profit
    FROM orders
    WHERE region IN ('{regions_str}')
    AND category IN ('{categories_str}')
    GROUP BY month
    ORDER BY month
"""
monthly = query(monthly_query)

fig_trend = px.line(
    monthly,
    x='month',
    y=['total_sales', 'total_profit'],
    title='Monthly Sales vs Profit',
    markers=True,
    color_discrete_map={'total_sales': '#0077b6', 'total_profit': '#2ecc71'}
)
fig_trend.update_xaxes(tickangle=45)
st.plotly_chart(fig_trend, use_container_width=True)

# ── Category Performance ────────────────────────────────
st.subheader("🪑 Category Performance")

cat_query = f"""
    SELECT 
        category,
        ROUND(AVG(profit), 2) AS avg_profit,
        COUNT(*) AS orders
    FROM orders
    WHERE region IN ('{regions_str}')
    AND category IN ('{categories_str}')
    GROUP BY category
    ORDER BY avg_profit DESC
"""
cat_df = query(cat_query)

fig_cat = px.bar(
    cat_df,
    x='category',
    y='avg_profit',
    color='avg_profit',
    title="Avg Profit per Category",
    color_continuous_scale='RdYlGn'
)
st.plotly_chart(fig_cat, use_container_width=True)

# ── Top Customers ───────────────────────────────────────
st.subheader("👑 Top Customers by Profit")

cust_query = f"""
    SELECT 
        customer_name,
        region,
        ROUND(SUM(profit), 2) AS total_profit
    FROM orders
    WHERE region IN ('{regions_str}')
    AND category IN ('{categories_str}')
    GROUP BY customer_name, region
    ORDER BY total_profit DESC
    LIMIT 10
"""
cust_df = query(cust_query)
st.dataframe(cust_df, use_container_width=True)