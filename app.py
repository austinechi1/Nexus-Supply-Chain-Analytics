from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st


st.set_page_config(
    page_title="Nexus Supply Chain Analytics",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAVY = "#1B0E0A"
TEAL = "#C96F4F"
AMBER = "#F2C1A5"
BG = "#1B0E0A"
SLATE = "#FFF7EF"
GREEN = "#E69A78"
RED = "#C96F4F"
MUTED = "#C9A692"
GRID = "#5A382E"

st.markdown(
    f"""
    <style>
    .stApp {{ background: {BG}; color: {SLATE}; }}
    [data-testid="stSidebar"] {{ background: {NAVY}; }}
    [data-testid="stSidebar"] * {{ color: white; }}
    [data-testid="stMetric"] {{
        background: #351A12; border: 1px solid #5A382E; border-radius: 18px;
        padding: 18px 20px; box-shadow: 0 5px 18px rgba(15, 23, 42, .05);
    }}
    [data-testid="stMetricLabel"] {{ color: {MUTED}; }}
    [data-testid="stMetricValue"] {{ color: {SLATE}; font-weight: 750; }}
    .block-container {{ padding-top: 2rem; padding-bottom: 2rem; max-width: 1500px; }}
    .eyebrow {{ color: {TEAL}; font-size: .78rem; font-weight: 800; letter-spacing: .12em; }}
    .subtitle {{ color: {MUTED}; margin-top: -.5rem; }}
    .insight {{
        background: #351A12; border-left: 5px solid {TEAL}; border-radius: 12px;
        padding: 14px 18px; margin: 8px 0 20px 0;
    }}
    div[data-baseweb="select"] > div {{ border-radius: 10px; }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data() -> pd.DataFrame:
    file_path = Path(__file__).parent / "data" / "nexus_supply_chain_clean.csv"
    if not file_path.exists():
        file_path = Path(__file__).parent / "nexus_supply_chain_clean.csv"
    data = pd.read_csv(file_path)
    for column in ["Order Date", "Expected Delivery", "Actual Delivery"]:
        data[column] = pd.to_datetime(data[column], errors="coerce")
        paper_bgcolor="#351A12",
    return data


def money(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"£{value / 1_000_000:,.1f}M"
    if abs(value) >= 1_000:
        return f"£{value / 1_000:,.1f}K"
    return f"£{value:,.0f}"


def base_layout(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=55, b=20),
        paper_bgcolor="white",
        plot_bgcolor="#351A12",
        font=dict(family="Arial", color=SLATE),
        title_font=dict(size=17, color=SLATE),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hoverlabel=dict(bgcolor="white"),
    )
    fig.update_xaxes(showgrid=False, linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


df = load_data()

with st.sidebar:
    st.markdown("## NEXUS")
    st.caption("SUPPLY CHAIN INTELLIGENCE")
    st.markdown("---")
    page = st.radio("Navigate", ["Overview", "Inventory", "Suppliers", "Delivery"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("### Filters")
    years = sorted(df["Year"].dropna().astype(int).unique().tolist())
    selected_years = st.multiselect("Year", years, default=years)
    regions = sorted(df["Region"].dropna().unique().tolist())
    selected_regions = st.multiselect("Region", regions, default=regions)
    categories = sorted(df["Category"].dropna().unique().tolist())
    selected_categories = st.multiselect("Category", categories, default=categories)
    suppliers = sorted(df["Supplier Name"].dropna().unique().tolist())
    selected_suppliers = st.multiselect("Supplier", suppliers, default=suppliers)
    st.markdown("---")
    st.caption("Built with Python, pandas, Plotly and Streamlit")

filtered = df[
    df["Year"].astype(int).isin(selected_years)
    & df["Region"].isin(selected_regions)
    & df["Category"].isin(selected_categories)
    & df["Supplier Name"].isin(selected_suppliers)
].copy()

if filtered.empty:
    st.warning("No records match the current filters. Select at least one option in each filter.")
    st.stop()

total_inventory = filtered["Inventory Value"].sum()
stockout_rate = filtered["Stockout Flag"].mean()
on_time_rate = filtered["On Time Flag"].mean()
avg_lead_time = filtered["Lead Time Days"].mean()

st.markdown('<div class="eyebrow">NEXUS OPERATIONS</div>', unsafe_allow_html=True)
st.title(f"{page} Analytics")
st.markdown(
    '<p class="subtitle">Monitor inventory health, supplier performance and delivery reliability.</p>',
    unsafe_allow_html=True,
)

if page == "Overview":
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Inventory Value", money(total_inventory))
    c2.metric("Stockout Rate", f"{stockout_rate:.1%}")
    c3.metric("On-Time Delivery", f"{on_time_rate:.1%}")
    c4.metric("Average Lead Time", f"{avg_lead_time:.1f} days")

    monthly = filtered.groupby("Month", as_index=False).agg(
        Inventory_Value=("Inventory Value", "sum"),
        Units_In_Stock=("Inventory On Hand", "sum"),
        
    )
    trend = make_subplots(specs=[[{"secondary_y": True}]])
    trend.add_trace(go.Scatter(x=monthly["Month"], y=monthly["Inventory_Value"], name="Inventory Value", line=dict(color=TEAL, width=3), mode="lines+markers"), secondary_y=False)
    trend.add_trace(go.Scatter(x=monthly["Month"], y=monthly["Units_In_Stock"], name="Units in Stock", line=dict(color=AMBER, width=3), mode="lines+markers"), secondary_y=True)
    trend.update_yaxes(title_text="Inventory value", tickprefix="£", tickformat=".2s", secondary_y=False)
    trend.update_yaxes(title_text="Units", tickformat=",", secondary_y=True, showgrid=False)
    trend.update_xaxes(tickformat="%b")
    trend.update_layout(title="Monthly Inventory Trend")
    base_layout(trend, 390)

    status = filtered.groupby("Inventory Status", as_index=False)["Inventory Value"].sum()
    donut = px.pie(status, values="Inventory Value", names="Inventory Status", hole=.68,
                   color_discrete_sequence=[TEAL, AMBER, RED, "#94A3B8"], title="Inventory Status Mix")
    donut.update_traces(textposition="outside", textinfo="percent+label")
    base_layout(donut, 390)

    left, right = st.columns([1.8, 1])
    left.plotly_chart(trend, use_container_width=True)
    right.plotly_chart(donut, use_container_width=True)

    region = filtered.groupby("Region", as_index=False).agg(
        Inventory_Value=("Inventory Value", "sum"),
        On_Time_Rate=("On Time Flag", "mean"),
    ).sort_values("Inventory_Value")
    region_chart = px.bar(region, x="Inventory_Value", y="Region", orientation="h", title="Inventory Value by Region", color_discrete_sequence=[TEAL])
    region_chart.update_xaxes(tickprefix="£", tickformat=".2s")
    base_layout(region_chart)

    category = filtered.groupby("Category", as_index=False).agg(
        Units_Ordered=("Units Ordered", "sum"), Units_Received=("Units Received", "sum")
    )
    category_chart = go.Figure()
    category_chart.add_bar(x=category["Category"], y=category["Units_Ordered"], name="Ordered", marker_color=NAVY)
    category_chart.add_bar(x=category["Category"], y=category["Units_Received"], name="Received", marker_color=AMBER)
    category_chart.update_layout(title="Ordered vs Received by Category", barmode="group")
    base_layout(category_chart)
    a, b = st.columns(2)
    a.plotly_chart(region_chart, use_container_width=True)
    b.plotly_chart(category_chart, use_container_width=True)

elif page == "Inventory":
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Inventory Value", money(total_inventory))
    c2.metric("Units on Hand", f"{filtered['Inventory On Hand'].sum():,.0f}")
    c3.metric("Overstock Records", f"{(filtered['Inventory Status'] == 'Overstock').sum():,}")
    c4.metric("Stockout Records", f"{filtered['Stockout Flag'].sum():,.0f}")

    products = filtered.groupby("Product Name", as_index=False).agg(
        Inventory_Value=("Inventory Value", "sum"), Units_On_Hand=("Inventory On Hand", "sum")
    ).nlargest(10, "Inventory_Value").sort_values("Inventory_Value")
    product_chart = px.bar(products, x="Inventory_Value", y="Product Name", orientation="h", title="Top 10 Products by Inventory Value", color_discrete_sequence=[TEAL])
    product_chart.update_xaxes(tickprefix="£", tickformat=".2s")
    base_layout(product_chart, 430)

    warehouse = filtered.groupby("Warehouse", as_index=False).agg(
        Inventory_Value=("Inventory Value", "sum"), Stockout_Rate=("Stockout Flag", "mean")
    ).sort_values("Inventory_Value", ascending=False)
    warehouse_chart = px.bar(warehouse, x="Warehouse", y="Inventory_Value", color="Stockout_Rate", title="Inventory by Warehouse", color_continuous_scale=[TEAL, AMBER, RED])
    warehouse_chart.update_yaxes(tickprefix="£", tickformat=".2s")
    base_layout(warehouse_chart, 430)
    a, b = st.columns(2)
    a.plotly_chart(product_chart, use_container_width=True)
    b.plotly_chart(warehouse_chart, use_container_width=True)

    st.subheader("Products Requiring Attention")
    attention = filtered.loc[filtered["Inventory Status"].isin(["Stockout", "Low Stock"]), [
        "Product Name", "Category", "Warehouse", "Supplier Name", "Inventory On Hand", "Reorder Point", "Inventory Status"
    ]].sort_values(["Inventory Status", "Inventory On Hand"])
    st.dataframe(attention, use_container_width=True, hide_index=True)

elif page == "Suppliers":
    supplier_perf = filtered.groupby("Supplier Name", as_index=False).agg(
        Inventory_Value=("Inventory Value", "sum"),
        Units_Received=("Units Received", "sum"),
        On_Time_Rate=("On Time Flag", "mean"),
        Defect_Rate=("Defect Rate", "mean"),
        Avg_Lead_Time=("Lead Time Days", "mean"),
    )
    best = supplier_perf.sort_values(["On_Time_Rate", "Defect_Rate"], ascending=[False, True]).iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Suppliers", f"{supplier_perf.shape[0]}")
    c2.metric("Best On-Time Supplier", best["Supplier Name"])
    c3.metric("Average Defect Rate", f"{filtered['Defect Rate'].mean():.1%}")
    c4.metric("Units Received", f"{filtered['Units Received'].sum():,.0f}")

    bubble = px.scatter(
        supplier_perf, x="Avg_Lead_Time", y="On_Time_Rate", size="Units_Received",
        color="Defect_Rate", hover_name="Supplier Name", color_continuous_scale=[TEAL, AMBER, RED],
        title="Supplier Reliability Matrix", labels={"Avg_Lead_Time": "Average Lead Time (days)", "On_Time_Rate": "On-Time Rate"}
    )
    bubble.update_yaxes(tickformat=".0%")
    base_layout(bubble, 430)

    ranked = supplier_perf.sort_values("On_Time_Rate").tail(10)
    supplier_bar = px.bar(ranked, x="On_Time_Rate", y="Supplier Name", orientation="h", title="Supplier On-Time Performance", color_discrete_sequence=[TEAL])
    supplier_bar.update_xaxes(tickformat=".0%", range=[0, 1])
    base_layout(supplier_bar, 430)
    a, b = st.columns([1.3, 1])
    a.plotly_chart(bubble, use_container_width=True)
    b.plotly_chart(supplier_bar, use_container_width=True)

    table = supplier_perf.copy()
    table["Inventory Value"] = table["Inventory_Value"].map(lambda x: f"£{x:,.0f}")
    table["On-Time Rate"] = table["On_Time_Rate"].map(lambda x: f"{x:.1%}")
    table["Defect Rate"] = table["Defect_Rate"].map(lambda x: f"{x:.1%}")
    table["Avg Lead Time"] = table["Avg_Lead_Time"].map(lambda x: f"{x:.1f}")
    st.dataframe(table[["Supplier Name", "Inventory Value", "Units_Received", "On-Time Rate", "Defect Rate", "Avg Lead Time"]], use_container_width=True, hide_index=True)

else:
    delayed = (filtered["Delivery Status"] != "On Time").sum()
    avg_delay = filtered.loc[filtered["Delay Days"] > 0, "Delay Days"].mean()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("On-Time Delivery", f"{on_time_rate:.1%}")
    c2.metric("Delayed Orders", f"{delayed:,}")
    c3.metric("Average Lead Time", f"{avg_lead_time:.1f} days")
    c4.metric("Average Positive Delay", f"{0 if pd.isna(avg_delay) else avg_delay:.1f} days")

    delivery_month = filtered.groupby("Month", as_index=False).agg(
        On_Time_Rate=("On Time Flag", "mean"), Average_Delay=("Delay Days", "mean")
    )
    delivery_line = px.line(delivery_month, x="Month", y="On_Time_Rate", markers=True, title="Monthly On-Time Delivery Rate", color_discrete_sequence=[TEAL])
    delivery_line.update_xaxes(tickformat="%b")
    delivery_line.update_yaxes(tickformat=".0%", range=[0, 1])
    base_layout(delivery_line, 400)

    warehouse_delivery = filtered.groupby("Warehouse", as_index=False).agg(
        On_Time_Rate=("On Time Flag", "mean"), Average_Lead_Time=("Lead Time Days", "mean")
    ).sort_values("On_Time_Rate")
    delivery_bar = px.bar(warehouse_delivery, x="On_Time_Rate", y="Warehouse", orientation="h", title="On-Time Rate by Warehouse", color_discrete_sequence=[AMBER])
    delivery_bar.update_xaxes(tickformat=".0%", range=[0, 1])
    base_layout(delivery_bar, 400)
    a, b = st.columns([1.4, 1])
    a.plotly_chart(delivery_line, use_container_width=True)
    b.plotly_chart(delivery_bar, use_container_width=True)

    delayed_orders = filtered.loc[filtered["Delay Days"] > 0, [
        "PO Number", "Product Name", "Supplier Name", "Warehouse", "Expected Delivery", "Actual Delivery", "Delay Days"
    ]].sort_values("Delay Days", ascending=False)
    st.subheader("Delayed Order Detail")
    st.dataframe(delayed_orders, use_container_width=True, hide_index=True)
