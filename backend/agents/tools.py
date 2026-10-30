"""Business Tools for AI Agents"""
from sqlalchemy.orm import Session

class BusinessTools:
    """Tools for AI agents to interact with business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_sales_metrics(self):
        """Get sales metrics"""
        from backend.database.models import Order
        orders = self.db.query(Order).all()
        return {
            "total_orders": len(orders),
            "total_sales": sum(o.total_amount for o in orders if o.total_amount)
        }
    
    def get_inventory_metrics(self):
        """Get inventory metrics"""
        from backend.database.models import Inventory
        inventory = self.db.query(Inventory).all()
        return {
            "total_items": len(inventory),
            "low_stock_items": len([i for i in inventory if i.quantity_on_hand < i.reorder_point])
        }
    
    def get_products(self):
        """Get all products"""
        from backend.database.models import Product
        products = self.db.query(Product).all()
        return [{"id": p.id, "name": p.name, "price": p.price} for p in products]

def get_business_tools(db: Session) -> BusinessTools:
    """Get business tools instance"""
    return BusinessTools(db)
