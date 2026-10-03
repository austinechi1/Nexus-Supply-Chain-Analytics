# Nexus Supply Chain Analytics

Interactive supply chain analytics dashboard built with Python, pandas, Plotly and Streamlit.

The dashboard covers inventory health, supplier performance, delivery reliability and operational trends across 2023–2025.

## Predictive analytics

- Six-month inventory value forecast for January–June 2026
- Holdout backtest with MAE and MAPE accuracy reporting
- Product-level stockout risk scoring
- Supplier late-delivery risk scoring
- Interactive filters for year, region, category, warehouse and supplier

The project uses synthetic operational data for portfolio demonstration. Forecasts and risk scores are decision-support estimates rather than guaranteed outcomes.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The theme lives in `.streamlit/config.toml` and the design tokens at the top of `app.py`.
