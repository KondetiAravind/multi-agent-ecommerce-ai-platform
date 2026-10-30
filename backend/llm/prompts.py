"""LLM Prompts for AI Agents

Each prompt instructs the model to respond with JSON only (required when
using Groq's response_format={"type": "json_object"} mode).
"""

DEMAND_FORECAST_SYSTEM = "You are a demand forecasting expert. Always respond with valid JSON only."

DEMAND_FORECAST_PROMPT = """Analyze this e-commerce sales data and forecast demand for the top product:

- Total orders (period): {total_orders}
- Top product: {top_product_name} (SKU {top_product_sku})
- Units sold: {top_product_units}
- Current stock on hand: {top_product_stock}
- Total products tracked: {total_products}
- Low-stock items: {low_stock_count}

Respond with JSON only, in this exact shape:
{{
  "high_demand_reasoning": "<one sentence citing the units sold and how it compares to average>",
  "demand_trend_percent": <number, percent change vs baseline, can be negative>,
  "confidence": <number between 0 and 1>
}}"""

INVENTORY_SYSTEM = "You are an inventory optimization specialist. Always respond with valid JSON only."

INVENTORY_PROMPT = """Analyze inventory for this product and recommend an action:

- Product: {product_name} (SKU {product_sku})
- Current stock: {current_stock}
- Reorder point: {reorder_point}
- Reorder quantity: {reorder_quantity}
- Recent units sold: {units_sold}

Respond with JSON only, in this exact shape:
{{
  "low_inventory_reasoning": "<one sentence on stock level vs reorder point>",
  "recommended_action": "<reorder|reduce|hold>",
  "confidence": <number between 0 and 1>
}}"""

PRICING_SYSTEM = "You are a pricing strategy expert. Always respond with valid JSON only."

PRICING_PROMPT = """Analyze pricing for this product and recommend a price adjustment:

- Product: {product_name} (SKU {product_sku})
- Current price: ${current_price}
- Cost: ${cost}
- Units sold (period): {units_sold}
- Revenue (period): ${revenue}

Respond with JSON only, in this exact shape:
{{
  "market_trend_reasoning": "<one sentence on margin vs similar products>",
  "price_change_percent": <number, percent to adjust price by, can be negative>,
  "revenue_impact_reasoning": "<one sentence estimating monthly revenue impact in dollars>",
  "confidence": <number between 0 and 1>
}}"""

EXECUTIVE_SYSTEM = "You are a business strategy executive. Always respond with valid JSON only."

EXECUTIVE_PROMPT = """Synthesize these AI agent findings into one executive recommendation:

Demand: {demand_json}
Inventory: {inventory_json}
Pricing: {pricing_json}

Respond with JSON only, in this exact shape:
{{
  "executive_summary": "<one sentence, the single recommended action>",
  "confidence_score": <number between 0 and 1, overall confidence>
}}"""
