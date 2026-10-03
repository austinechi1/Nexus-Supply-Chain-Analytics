from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
from plotly.subplots import make_subplots


st.set_page_config(
    page_title="Nexus Supply Chain Analytics",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Design tokens (Nexus warm palette, refined for contrast)
# ---------------------------------------------------------------------------
BG = "#170D09"         # espresso base
PANEL = "#221410"      # card surface
PANEL_2 = "#2C1A14"    # raised surface / hover
LINE = "#3D271E"       # borders, gridlines
INK = "#FBF3EA"        # primary text
MUTED = "#B8998A"      # secondary text
BRAND = "#C96F4F"      # Nexus terracotta
PEACH = "#F2C1A5"      # Nexus peach
CLAY = "#8A5A47"       # quiet bars / secondary series

# Semantic colours, used only where they carry meaning
GOOD = "#8FBF9F"
WARN = "#E8B04B"
BAD = "#E5604F"

STATUS_COLORS = {
    "Healthy": GOOD,
    "Low Stock": WARN,
    "Out of Stock": BAD,
    "Overstock": PEACH,
}
HEAT = [[0, PEACH], [0.5, BRAND], [1, BAD]]
FONT = "Schibsted Grotesk, system-ui, sans-serif"

pio.templates["nexus"] = go.layout.Template(
    layout=dict(
        font=dict(family=FONT, color=INK, size=13),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=[BRAND, PEACH, CLAY, GOOD, WARN],
        margin=dict(l=10, r=10, t=36, b=10),
        hoverlabel=dict(bgcolor=PANEL_2, bordercolor=LINE, font=dict(color=INK, family=FONT)),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0,
                    font=dict(color=MUTED), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(showgrid=False, linecolor=LINE, tickfont=dict(color=MUTED), title=dict(font=dict(color=MUTED))),
        yaxis=dict(gridcolor=LINE, zeroline=False, linecolor="rgba(0,0,0,0)",
                   tickfont=dict(color=MUTED), title=dict(font=dict(color=MUTED))),
        coloraxis=dict(colorbar=dict(outlinewidth=0, tickfont=dict(color=MUTED), thickness=10)),
        bargap=0.35,
    )
)
pio.templates.default = "nexus"
CHART_CONFIG = {"displayModeBar": False}

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Schibsted+Grotesk:wght@400;500;600;700;800&display=swap');

    html, body, .stApp,
    .stApp *:not([data-testid="stIconMaterial"]):not(.material-symbols-rounded):not([translate="no"]) {{
        font-family: {FONT};
    }}
    .stApp {{ background: {BG}; color: {INK}; }}
    [data-testid="stHeader"] {{ background: transparent; }}
    .block-container {{ padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1440px; }}

    /* Sidebar */
    [data-testid="stSidebar"] {{ background: {PANEL}; border-right: 1px solid {LINE}; }}
    [data-testid="stSidebar"] label p {{ color: {INK}; font-weight: 600; }}
    .wordmark {{ font-size: 1.6rem; font-weight: 800; letter-spacing: -.03em; color: {INK}; line-height: 1; }}
    .wordmark span {{ display:inline-block; width:.55em; height:.55em; background:{BRAND};
                      border-radius: 2px; margin-right:.4em; transform: translateY(-.05em) rotate(45deg); }}
    .side-note {{ color: {MUTED}; font-size: .82rem; margin: .35rem 0 1.4rem; }}
    .side-heading {{ color: {INK}; font-weight: 700; font-size: .95rem; margin: 1.2rem 0 .2rem; }}

    /* Header */
    .page-title {{ font-size: clamp(2.2rem, 4vw, 3.4rem); font-weight: 800; letter-spacing: -.045em;
                   line-height: .95; color: {INK}; margin: 0; }}
    .scope {{ color: {MUTED}; font-size: .95rem; margin: .7rem 0 0; }}
    .scope b {{ color: {INK}; font-weight: 600; }}

    /* Insight strip */
    .insight {{ display:flex; gap: .9rem; align-items: flex-start; background: {PANEL};
                border: 1px solid {LINE}; border-radius: 14px; padding: 14px 18px; margin: 1.4rem 0 1.1rem;
                color: {INK}; font-size: 1rem; line-height: 1.5; }}
    .insight .dot {{ flex: 0 0 8px; height: 8px; margin-top: .55em; border-radius: 50%; background: {BRAND};
                     box-shadow: 0 0 0 4px rgba(201,111,79,.18); }}

    /* KPI cards */
    .kpi-row {{ display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 14px; margin-bottom: 14px; }}
    @media (max-width: 1000px) {{ .kpi-row {{ grid-template-columns: repeat(2, minmax(0,1fr)); }} }}
    .kpi {{ background: {PANEL}; border: 1px solid {LINE}; border-radius: 16px; padding: 18px 20px 16px; }}
    .kpi .label {{ color: {MUTED}; font-size: .88rem; font-weight: 500; }}
    .kpi .value {{ color: {INK}; font-size: 2rem; font-weight: 700; letter-spacing: -.03em;
                   font-variant-numeric: tabular-nums; margin: .25rem 0 .55rem; line-height: 1.1;
                   white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .kpi .foot {{ font-size: .82rem; color: {MUTED}; font-variant-numeric: tabular-nums; }}
    .kpi .foot .good {{ color: {GOOD}; font-weight: 600; }}
    .kpi .foot .bad {{ color: {BAD}; font-weight: 600; }}
    .kpi .foot .flat {{ color: {INK}; font-weight: 600; }}

    /* Chart panels (bordered containers) */
    [data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"] .panel-head),
    [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .panel-head) {{
        background: {PANEL}; border-color: {LINE} !important; border-radius: 16px;
    }}
    .panel-head {{ font-size: 1.05rem; font-weight: 700; color: {INK}; letter-spacing: -.01em; margin: 0; }}
    .panel-sub {{ font-size: .85rem; color: {MUTED}; margin: .15rem 0 0; }}

    /* Navigation (segmented control) */
    [data-testid="stButtonGroup"] button {{ border-radius: 999px !important; }}

    /* Inputs */
    div[data-baseweb="select"] > div {{ border-radius: 10px; background: {PANEL_2}; }}
    [data-testid="stDataFrame"] {{ border-radius: 12px; overflow: hidden; }}

    :focus-visible {{ outline: 2px solid {PEACH} !important; outline-offset: 2px; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
@st.cache_data
def load_data() -> pd.DataFrame:
    file_path = Path(__file__).parent / "data" / "nexus_supply_chain_clean.csv"
    if not file_path.exists():
        file_path = Path(__file__).parent / "nexus_supply_chain_clean.csv"
    data = pd.read_csv(file_path)
    for column in ["Order Date", "Expected Delivery", "Actual Delivery"]:
        data[column] = pd.to_datetime(data[column], errors="coerce")
    data["Month"] = data["Order Date"].dt.to_period("M").dt.to_timestamp()
    return data


def money(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"£{value / 1_000_000:,.2f}M"
    if abs(value) >= 1_000:
        return f"£{value / 1_000:,.1f}K"
    return f"£{value:,.0f}"


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------
def trend_note(curr, prev, kind: str, good_when: str, fmt) -> str:
    """Latest month vs the month before, coloured by whether the move is good."""
    if curr is None or prev is None or pd.isna(curr) or pd.isna(prev):
        return "Not enough months selected to compare"
    if kind == "pts":
        change = (curr - prev) * 100
        size = f"{abs(change):.1f} pts"
    else:
        change = 0 if prev == 0 else (curr - prev) / prev * 100
        size = f"{abs(change):.0f}%"
    if abs(change) < 0.05:
        return f"{fmt(curr)} last month, <span class='flat'>flat</span>"
    up = change > 0
    tone = "good" if (up == (good_when == "up")) else "bad"
    if good_when == "none":
        tone = "flat"
    word = "up" if up else "down"
    return f"{fmt(curr)} last month, <span class='{tone}'>{word} {size}</span>"


def kpi_row(cards: list[tuple[str, str, str]]) -> None:
    html = "".join(
        f"<div class='kpi'><div class='label'>{label}</div>"
        f"<div class='value' title='{value}'>{value}</div><div class='foot'>{foot}</div></div>"
        for label, value, foot in cards
    )
    st.markdown(f"<div class='kpi-row'>{html}</div>", unsafe_allow_html=True)


def insight(text: str) -> None:
    st.markdown(f"<div class='insight'><div class='dot'></div><div>{text}</div></div>", unsafe_allow_html=True)


def panel(title: str, subtitle: str, fig: go.Figure, height: int = 340) -> None:
    with st.container(border=True):
        st.markdown(f"<p class='panel-head'>{title}</p><p class='panel-sub'>{subtitle}</p>", unsafe_allow_html=True)
        fig.update_layout(height=height, paper_bgcolor=PANEL, plot_bgcolor=PANEL)
        fig.update_xaxes(automargin=True)
        fig.update_yaxes(automargin=True)
        st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG, theme=None)


def last_two(monthly: pd.DataFrame, col: str):
    if len(monthly) < 2:
        return None, None
    return monthly[col].iloc[-1], monthly[col].iloc[-2]


# ---------------------------------------------------------------------------
# Sidebar: filters
# ---------------------------------------------------------------------------
df = load_data()
FILTERS = {
    "Region": "f_region",
    "Category": "f_category",
    "Warehouse": "f_warehouse",
    "Supplier Name": "f_supplier",
}


def reset_filters() -> None:
    for key in list(FILTERS.values()) + ["f_year"]:
        st.session_state[key] = []


with st.sidebar:
    st.markdown("<div class='wordmark'><span></span>Nexus</div>", unsafe_allow_html=True)
    st.markdown("<p class='side-note'>Supply chain intelligence</p>", unsafe_allow_html=True)

    st.markdown("<p class='side-heading'>Filter the data</p>", unsafe_allow_html=True)
    st.caption("Leave a filter empty to include everything.")

    selections = {}
    years = sorted(df["Year"].dropna().astype(int).unique().tolist())
    if len(years) > 1:
        selections["Year"] = st.pills("Year", years, selection_mode="multi", key="f_year")
    labels = {"Supplier Name": "Supplier"}
    for column, key in FILTERS.items():
        options = sorted(df[column].dropna().unique().tolist())
        selections[column] = st.pills(labels.get(column, column), options, selection_mode="multi", key=key)

    st.button("Clear filters", on_click=reset_filters, use_container_width=True)

mask = pd.Series(True, index=df.index)
for column, chosen in selections.items():
    if chosen:
        values = chosen if column != "Year" else [int(y) for y in chosen]
        mask &= df[column].isin(values)
filtered = df[mask].copy()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
PAGES = ["Overview", "Inventory", "Suppliers", "Delivery"]
head_left, head_right = st.columns([1.4, 1], vertical_alignment="bottom")
with head_right:
    page = st.segmented_control("Section", PAGES, default="Overview", key="page",
                                label_visibility="collapsed") or "Overview"
with head_left:
    st.markdown(f"<h1 class='page-title'>{page}</h1>", unsafe_allow_html=True)

if filtered.empty:
    st.markdown(f"<p class='scope'>No orders match these filters.</p>", unsafe_allow_html=True)
    st.info("Remove a filter in the sidebar, or use Clear filters to start again.")
    st.stop()

active = [f"{labels.get(c, c).lower()}: {', '.join(map(str, v))}" for c, v in selections.items() if v]
scope_filters = f" Filtered by {'; '.join(active)}." if active else ""
start, end = filtered["Order Date"].min(), filtered["Order Date"].max()
st.markdown(
    f"<p class='scope'><b>{len(filtered):,}</b> purchase orders placed "
    f"<b>{start:%d %b}</b> to <b>{end:%d %b %Y}</b>.{scope_filters}</p>",
    unsafe_allow_html=True,
)

# Shared figures
total_inventory = filtered["Inventory Value"].sum()
stockout_rate = filtered["Stockout Flag"].mean()
on_time_rate = filtered["On Time Flag"].mean()
avg_lead_time = filtered["Lead Time Days"].mean()

monthly = (
    filtered.assign(
        Late=lambda d: (d["Delivery Status"] != "On Time").astype(int),
        Overstock=lambda d: (d["Inventory Status"] == "Overstock").astype(int),
        Positive_Delay=lambda d: d["Delay Days"].where(d["Delay Days"] > 0),
    )
    .groupby("Month", as_index=False)
    .agg(
        Inventory_Value=("Inventory Value", "sum"),
        Units_On_Hand=("Inventory On Hand", "sum"),
        Stockout_Rate=("Stockout Flag", "mean"),
        Stockouts=("Stockout Flag", "sum"),
        Overstock=("Overstock", "sum"),
        On_Time_Rate=("On Time Flag", "mean"),
        Lead_Time=("Lead Time Days", "mean"),
        Defect_Rate=("Defect Rate", "mean"),
        Units_Received=("Units Received", "sum"),
        Late=("Late", "sum"),
        Positive_Delay=("Positive_Delay", "mean"),
    )
    .sort_values("Month")
)
pct = lambda v: f"{v:.1%}"
days = lambda v: f"{v:.1f} days"
count = lambda v: f"{v:,.0f}"


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------
if page == "Overview":
    region = filtered.groupby("Region", as_index=False).agg(
        Inventory_Value=("Inventory Value", "sum"), On_Time_Rate=("On Time Flag", "mean")
    ).sort_values("Inventory_Value")
    wh = filtered.groupby("Warehouse")["On Time Flag"].mean().sort_values()
    top_region = region.iloc[-1]
    insight(
        f"{top_region['Region']} holds {top_region['Inventory_Value'] / total_inventory:.0%} of inventory value. "
        f"{wh.index[0]} has the lowest on-time rate at {wh.iloc[0]:.0%}, against {on_time_rate:.0%} overall."
    )

    kpi_row([
        ("Inventory value", money(total_inventory),
         trend_note(*last_two(monthly, "Inventory_Value"), "pct", "none", money)),
        ("Stockout rate", pct(stockout_rate),
         trend_note(*last_two(monthly, "Stockout_Rate"), "pts", "down", pct)),
        ("On-time delivery", pct(on_time_rate),
         trend_note(*last_two(monthly, "On_Time_Rate"), "pts", "up", pct)),
        ("Average lead time", days(avg_lead_time),
         trend_note(*last_two(monthly, "Lead_Time"), "pct", "down", days)),
    ])

    trend = make_subplots(specs=[[{"secondary_y": True}]])
    trend.add_trace(go.Scatter(
        x=monthly["Month"], y=monthly["Inventory_Value"], name="Inventory value", mode="lines",
        line=dict(color=BRAND, width=2.5, shape="spline", smoothing=0.6),
        fill="tozeroy", fillcolor="rgba(201,111,79,.16)",
        hovertemplate="%{x|%B}<br>£%{y:,.0f}<extra></extra>",
    ), secondary_y=False)
    trend.add_trace(go.Scatter(
        x=monthly["Month"], y=monthly["Units_On_Hand"], name="Units in stock", mode="lines",
        line=dict(color=PEACH, width=2, dash="dot", shape="spline", smoothing=0.6),
        hovertemplate="%{x|%B}<br>%{y:,.0f} units<extra></extra>",
    ), secondary_y=True)
    trend.update_yaxes(tickprefix="£", tickformat=".2s", rangemode="tozero", secondary_y=False)
    trend.update_yaxes(tickformat=",.0f", showgrid=False, rangemode="tozero", secondary_y=True)
    trend.update_xaxes(tickformat="%b", dtick="M1")

    status = filtered.groupby("Inventory Status", as_index=False)["Inventory Value"].sum()
    donut = go.Figure(go.Pie(
        labels=status["Inventory Status"], values=status["Inventory Value"], hole=.72, sort=True,
        marker=dict(colors=[STATUS_COLORS.get(s, CLAY) for s in status["Inventory Status"]],
                    line=dict(color=PANEL, width=3)),
        textinfo="none", hovertemplate="%{label}<br>£%{value:,.0f} (%{percent})<extra></extra>",
    ))
    donut.update_layout(
        showlegend=True, legend=dict(orientation="h", y=-0.08, x=0.5, xanchor="center", yanchor="top"),
        annotations=[dict(text=f"<b>{money(total_inventory)}</b><br><span style='color:{MUTED}'>total value</span>",
                          showarrow=False, font=dict(size=18, color=INK))],
    )

    left, right = st.columns([1.75, 1])
    with left:
        panel("Inventory over time", "Monthly inventory value with units in stock on the right axis", trend, 360)
    with right:
        panel("Where the value sits", "Share of inventory value by stock status", donut, 360)

    region_chart = go.Figure(go.Bar(
        x=region["Inventory_Value"], y=region["Region"], orientation="h", marker_color=BRAND,
        text=region["Inventory_Value"].map(money), textposition="outside", cliponaxis=False,
        textfont=dict(color=INK), hovertemplate="%{y}<br>£%{x:,.0f}<extra></extra>",
    ))
    region_chart.update_xaxes(visible=False)
    region_chart.update_yaxes(gridcolor="rgba(0,0,0,0)")
    region_chart.update_layout(margin=dict(r=60))

    category = filtered.groupby("Category", as_index=False).agg(
        Units_Ordered=("Units Ordered", "sum"), Units_Received=("Units Received", "sum")
    )
    category["Fill"] = category["Units_Received"] / category["Units_Ordered"]
    category["Label"] = category.apply(
        lambda r: f"{r['Category']}<br><span style='color:{MUTED}'>{r['Fill']:.0%} received</span>", axis=1
    )
    category_chart = go.Figure()
    category_chart.add_bar(x=category["Label"], y=category["Units_Ordered"], name="Ordered", marker_color=CLAY,
                           customdata=category["Category"], hovertemplate="%{customdata}<br>%{y:,.0f} ordered<extra></extra>")
    category_chart.add_bar(x=category["Label"], y=category["Units_Received"], name="Received", marker_color=PEACH,
                           customdata=category["Category"], hovertemplate="%{customdata}<br>%{y:,.0f} received<extra></extra>")
    category_chart.update_layout(barmode="group", bargroupgap=0.08)
    category_chart.update_yaxes(tickformat=",")

    a, b = st.columns(2)
    with a:
        panel("Inventory by region", "Total inventory value", region_chart, 320)
    with b:
        panel("Ordered vs received", "Units by category, with the share received", category_chart, 320)


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------
elif page == "Inventory":
    at_risk = filtered[filtered["Inventory Status"].isin(["Out of Stock", "Low Stock"])]
    risk_cat = at_risk["Category"].value_counts()
    insight(
        f"{len(at_risk):,} order lines are low or out of stock"
        + (f", most of them in {risk_cat.index[0]} ({risk_cat.iloc[0]:,})." if len(risk_cat) else ".")
        + f" Overstock accounts for {(filtered['Inventory Status'] == 'Overstock').mean():.0%} of lines."
    )

    kpi_row([
        ("Inventory value", money(total_inventory),
         trend_note(*last_two(monthly, "Inventory_Value"), "pct", "none", money)),
        ("Units on hand", count(filtered["Inventory On Hand"].sum()),
         trend_note(*last_two(monthly, "Units_On_Hand"), "pct", "none", count)),
        ("Overstock lines", count((filtered["Inventory Status"] == "Overstock").sum()),
         trend_note(*last_two(monthly, "Overstock"), "pct", "down", count)),
        ("Stockout lines", count(filtered["Stockout Flag"].sum()),
         trend_note(*last_two(monthly, "Stockouts"), "pct", "down", count)),
    ])

    products = filtered.groupby("Product Name", as_index=False).agg(
        Inventory_Value=("Inventory Value", "sum")
    ).nlargest(10, "Inventory_Value").sort_values("Inventory_Value")
    product_chart = go.Figure(go.Bar(
        x=products["Inventory_Value"], y=products["Product Name"], orientation="h", marker_color=BRAND,
        text=products["Inventory_Value"].map(money), textposition="outside", cliponaxis=False,
        textfont=dict(color=INK), hovertemplate="%{y}<br>£%{x:,.0f}<extra></extra>",
    ))
    product_chart.update_xaxes(visible=False)
    product_chart.update_yaxes(gridcolor="rgba(0,0,0,0)")
    product_chart.update_layout(margin=dict(r=60))

    warehouse = filtered.groupby("Warehouse", as_index=False).agg(
        Inventory_Value=("Inventory Value", "sum"), Stockout_Rate=("Stockout Flag", "mean")
    ).sort_values("Inventory_Value", ascending=False)
    warehouse_chart = px.bar(
        warehouse, x="Warehouse", y="Inventory_Value", color="Stockout_Rate", color_continuous_scale=HEAT,
        labels={"Stockout_Rate": "Stockout rate", "Inventory_Value": "Inventory value"},
    )
    warehouse_chart.update_traces(hovertemplate="%{x}<br>£%{y:,.0f}<br>Stockout rate %{marker.color:.1%}<extra></extra>")
    warehouse_chart.update_yaxes(tickprefix="£", tickformat=".2s", title=None)
    warehouse_chart.update_xaxes(title=None)
    warehouse_chart.update_coloraxes(colorbar=dict(tickformat=".1%", title=dict(text="Stockout", font=dict(color=MUTED))))

    a, b = st.columns(2)
    with a:
        panel("Top 10 products", "Ranked by inventory value", product_chart, 420)
    with b:
        panel("Warehouses", "Inventory value, coloured by stockout rate", warehouse_chart, 420)

    with st.container(border=True):
        st.markdown("<p class='panel-head'>Products that need restocking</p>"
                    "<p class='panel-sub'>Low or out of stock, lowest cover first</p>", unsafe_allow_html=True)
        attention = at_risk[[
            "Product Name", "Category", "Warehouse", "Supplier Name",
            "Inventory On Hand", "Reorder Point", "Inventory Status",
        ]].copy()
        attention["Cover"] = (attention["Inventory On Hand"] / attention["Reorder Point"]).clip(upper=1)
        attention = attention.sort_values(["Cover", "Inventory On Hand"])
        if attention.empty:
            st.success("Every product in this selection is above its reorder point.")
        else:
            st.dataframe(
                attention, use_container_width=True, hide_index=True, height=380,
                column_config={
                    "Product Name": "Product",
                    "Supplier Name": "Supplier",
                    "Inventory On Hand": st.column_config.NumberColumn("On hand", format="%d"),
                    "Reorder Point": st.column_config.NumberColumn("Reorder at", format="%d"),
                    "Inventory Status": "Status",
                    "Cover": st.column_config.ProgressColumn(
                        "Cover vs reorder point", min_value=0, max_value=1, format="percent"),
                },
            )


# ---------------------------------------------------------------------------
# Suppliers
# ---------------------------------------------------------------------------
elif page == "Suppliers":
    supplier_perf = filtered.groupby("Supplier Name", as_index=False).agg(
        Inventory_Value=("Inventory Value", "sum"),
        Units_Received=("Units Received", "sum"),
        On_Time_Rate=("On Time Flag", "mean"),
        Defect_Rate=("Defect Rate", "mean"),
        Avg_Lead_Time=("Lead Time Days", "mean"),
        Orders=("PO Number", "count"),
    )
    ranked_all = supplier_perf.sort_values(["On_Time_Rate", "Defect_Rate"], ascending=[False, True])
    best, worst = ranked_all.iloc[0], ranked_all.iloc[-1]
    if len(ranked_all) > 1:
        insight(
            f"{best['Supplier Name']} is the most reliable supplier at {best['On_Time_Rate']:.0%} on time. "
            f"{worst['Supplier Name']} trails at {worst['On_Time_Rate']:.0%}, with a {worst['Defect_Rate']:.1%} defect rate."
        )
    else:
        insight(f"{best['Supplier Name']} delivered {best['On_Time_Rate']:.0%} of orders on time.")

    kpi_row([
        ("Active suppliers", f"{supplier_perf.shape[0]}", f"{len(filtered):,} orders across them"),
        ("Most reliable", best["Supplier Name"], f"{best['On_Time_Rate']:.1%} on time"),
        ("Average defect rate", pct(filtered["Defect Rate"].mean()),
         trend_note(*last_two(monthly, "Defect_Rate"), "pts", "down", pct)),
        ("Units received", count(filtered["Units Received"].sum()),
         trend_note(*last_two(monthly, "Units_Received"), "pct", "none", count)),
    ])

    bubble = px.scatter(
        supplier_perf, x="Avg_Lead_Time", y="On_Time_Rate", size="Units_Received", color="Defect_Rate",
        hover_name="Supplier Name", text="Supplier Name", color_continuous_scale=HEAT, size_max=34,
        labels={"Avg_Lead_Time": "Average lead time (days)", "On_Time_Rate": "On-time rate", "Defect_Rate": "Defect rate"},
    )
    bubble.update_traces(
        textposition="top center", textfont=dict(color=MUTED, size=11),
        marker=dict(line=dict(color=PANEL, width=1.5), opacity=.9),
        hovertemplate="<b>%{hovertext}</b><br>Lead time %{x:.1f} days<br>On time %{y:.1%}"
                      "<br>Defects %{marker.color:.1%}<extra></extra>",
    )
    bubble.add_hline(y=supplier_perf["On_Time_Rate"].median(), line=dict(color=LINE, dash="dot"))
    bubble.add_vline(x=supplier_perf["Avg_Lead_Time"].median(), line=dict(color=LINE, dash="dot"))
    bubble.update_yaxes(tickformat=".0%", range=[max(0, supplier_perf["On_Time_Rate"].min() - 0.06), 1.03])
    bubble.update_coloraxes(colorbar=dict(tickformat=".1%", title=dict(text="Defects", font=dict(color=MUTED))))

    ranked = supplier_perf.sort_values("On_Time_Rate").tail(10)
    supplier_bar = go.Figure(go.Bar(
        x=ranked["On_Time_Rate"], y=ranked["Supplier Name"], orientation="h",
        marker_color=[BRAND if n == best["Supplier Name"] else CLAY for n in ranked["Supplier Name"]],
        text=ranked["On_Time_Rate"].map(lambda v: f"{v:.0%}"), textposition="outside", cliponaxis=False,
        textfont=dict(color=INK), hovertemplate="%{y}<br>%{x:.1%} on time<extra></extra>",
    ))
    supplier_bar.update_xaxes(visible=False, range=[0, 1.08])
    supplier_bar.update_yaxes(gridcolor="rgba(0,0,0,0)")

    a, b = st.columns([1.3, 1])
    with a:
        panel("Reliability matrix", "Top left is best: short lead times and high on-time rate. Bubble size is units received.",
              bubble, 440)
    with b:
        panel("On-time performance", "Share of orders delivered on or before the expected date", supplier_bar, 440)

    with st.container(border=True):
        st.markdown("<p class='panel-head'>Supplier scorecard</p>"
                    "<p class='panel-sub'>Sorted by on-time rate</p>", unsafe_allow_html=True)
        st.dataframe(
            ranked_all[["Supplier Name", "Orders", "Inventory_Value", "Units_Received",
                        "On_Time_Rate", "Defect_Rate", "Avg_Lead_Time"]],
            use_container_width=True, hide_index=True,
            column_config={
                "Supplier Name": "Supplier",
                "Inventory_Value": st.column_config.NumberColumn("Inventory value", format="£%,.0f"),
                "Units_Received": st.column_config.NumberColumn("Units received", format="%,d"),
                "On_Time_Rate": st.column_config.ProgressColumn("On-time rate", min_value=0, max_value=1, format="percent"),
                "Defect_Rate": st.column_config.NumberColumn("Defect rate", format="percent"),
                "Avg_Lead_Time": st.column_config.NumberColumn("Lead time (days)", format="%.1f"),
            },
        )


# ---------------------------------------------------------------------------
# Delivery
# ---------------------------------------------------------------------------
else:
    late_mask = filtered["Delivery Status"] != "On Time"
    delayed = late_mask.sum()
    avg_delay = filtered.loc[filtered["Delay Days"] > 0, "Delay Days"].mean()
    avg_delay = 0 if pd.isna(avg_delay) else avg_delay
    worst_month = monthly.loc[monthly["On_Time_Rate"].idxmin()] if len(monthly) else None
    insight(
        f"{delayed:,} of {len(filtered):,} orders arrived late, by {avg_delay:.1f} days on average."
        + (f" {worst_month['Month']:%B} was the weakest month at {worst_month['On_Time_Rate']:.0%} on time."
           if worst_month is not None and len(monthly) > 1 else "")
    )

    kpi_row([
        ("On-time delivery", pct(on_time_rate),
         trend_note(*last_two(monthly, "On_Time_Rate"), "pts", "up", pct)),
        ("Late orders", count(delayed), trend_note(*last_two(monthly, "Late"), "pct", "down", count)),
        ("Average lead time", days(avg_lead_time),
         trend_note(*last_two(monthly, "Lead_Time"), "pct", "down", days)),
        ("Average delay when late", days(avg_delay),
         trend_note(*last_two(monthly, "Positive_Delay"), "pct", "down", days)),
    ])

    flag = on_time_rate - 0.01  # flag only gaps of a point or more
    delivery_line = go.Figure()
    delivery_line.add_hline(y=on_time_rate, line=dict(color=MUTED, dash="dot", width=1),
                            annotation_text=f"Year average {on_time_rate:.0%}", annotation_position="bottom right",
                            annotation_font=dict(color=MUTED, size=11))
    delivery_line.add_trace(go.Scatter(
        x=monthly["Month"], y=monthly["On_Time_Rate"], mode="lines+markers", name="On-time rate",
        line=dict(color=BRAND, width=2.5),
        marker=dict(size=7, color=[BAD if v < flag else BRAND for v in monthly["On_Time_Rate"]],
                    line=dict(color=PANEL, width=2)),
        hovertemplate="%{x|%B}<br>%{y:.1%} on time<extra></extra>",
    ))
    lo = max(0, monthly["On_Time_Rate"].min() - 0.1)
    delivery_line.update_yaxes(tickformat=".0%", range=[lo, 1.0])
    delivery_line.update_xaxes(tickformat="%b", dtick="M1")
    delivery_line.update_layout(showlegend=False)

    warehouse_delivery = filtered.groupby("Warehouse", as_index=False).agg(
        On_Time_Rate=("On Time Flag", "mean")
    ).sort_values("On_Time_Rate")
    delivery_bar = go.Figure(go.Bar(
        x=warehouse_delivery["On_Time_Rate"], y=warehouse_delivery["Warehouse"], orientation="h",
        marker_color=[BAD if v < flag else PEACH for v in warehouse_delivery["On_Time_Rate"]],
        text=warehouse_delivery["On_Time_Rate"].map(lambda v: f"{v:.0%}"), textposition="outside",
        cliponaxis=False, textfont=dict(color=INK), hovertemplate="%{y}<br>%{x:.1%} on time<extra></extra>",
    ))
    delivery_bar.update_xaxes(visible=False, range=[0, 1.08])
    delivery_bar.update_yaxes(gridcolor="rgba(0,0,0,0)")

    a, b = st.columns([1.4, 1])
    with a:
        panel("On-time rate by month", "Red points are more than a point below the year average", delivery_line, 380)
    with b:
        panel("By warehouse", "Red bars are more than a point below the year average", delivery_bar, 380)

    with st.container(border=True):
        st.markdown("<p class='panel-head'>Late orders</p>"
                    "<p class='panel-sub'>Longest delays first</p>", unsafe_allow_html=True)
        delayed_orders = filtered.loc[filtered["Delay Days"] > 0, [
            "PO Number", "Product Name", "Supplier Name", "Warehouse",
            "Expected Delivery", "Actual Delivery", "Delay Days",
        ]].sort_values("Delay Days", ascending=False)
        if delayed_orders.empty:
            st.success("No late orders in this selection.")
        else:
            max_delay = int(delayed_orders["Delay Days"].max())
            st.dataframe(
                delayed_orders, use_container_width=True, hide_index=True, height=380,
                column_config={
                    "PO Number": "PO",
                    "Product Name": "Product",
                    "Supplier Name": "Supplier",
                    "Expected Delivery": st.column_config.DateColumn("Expected", format="D MMM YYYY"),
                    "Actual Delivery": st.column_config.DateColumn("Arrived", format="D MMM YYYY"),
                    "Delay Days": st.column_config.ProgressColumn(
                        "Days late", min_value=0, max_value=max_delay, format="%d"),
                },
            )
