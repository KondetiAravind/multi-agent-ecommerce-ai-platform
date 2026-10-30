"""Builds the input dict the AI agents need, gathered from current sales/inventory data"""
from typing import Dict, Optional

from sqlalchemy.orm import Session

from backend.database.models import Inventory, Order, OrderItem, Product


def build_top_product_agent_input(db: Session) -> Optional[Dict]:
    """Return agent input data for the current best-selling product, or None if there's no sales data."""
    orders = db.query(Order).all()
    products = db.query(Product).all()
    order_items = db.query(OrderItem).all()
    inventory = db.query(Inventory).all()

    if not orders or not products:
        return None

    product_sales: Dict[int, Dict] = {}
    for item in order_items:
        entry = product_sales.setdefault(item.product_id, {"quantity": 0, "revenue": 0})
        entry["quantity"] += item.quantity
        entry["revenue"] += item.unit_price * item.quantity

    if not product_sales:
        return None

    top_pid = max(product_sales.keys(), key=lambda k: product_sales[k]["quantity"])
    top_product = db.query(Product).filter(Product.id == top_pid).first()
    top_inv = db.query(Inventory).filter(Inventory.product_id == top_pid).first()

    if not top_product or not top_inv:
        return None

    return {
        "total_orders": len(orders),
        "top_product_name": top_product.name,
        "top_product_sku": top_product.sku,
        "top_product_units": product_sales[top_pid]["quantity"],
        "top_product_stock": top_inv.quantity_on_hand,
        "total_products": len(products),
        "low_stock_count": len([i for i in inventory if i.quantity_on_hand < i.reorder_point]),
        "current_stock": top_inv.quantity_on_hand,
        "reorder_point": top_inv.reorder_point,
        "reorder_quantity": top_inv.reorder_quantity,
        "units_sold": product_sales[top_pid]["quantity"],
        "product_name": top_product.name,
        "product_sku": top_product.sku,
        "current_price": top_product.price,
        "cost": top_product.cost,
        "revenue": product_sales[top_pid]["revenue"],
    }
