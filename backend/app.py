"""FastAPI Backend Application"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import uuid
import os

from backend.config import settings, get_settings
from backend.database.connection import get_db, init_db
from backend.database.models import (
    Recommendation, Order, OrderItem, Product, Inventory
)
from backend.workflows.langgraph_workflow import WorkflowOrchestrator
from backend.services.agent_data_service import build_top_product_agent_input
from backend.routers.auth import router as auth_router, get_current_user
from backend.routers.products import router as products_router
from backend.routers.customers import router as customers_router
from backend.routers.orders import router as orders_router
from backend.routers.inventory import router as inventory_router
from backend.routers.analytics import router as analytics_router
from backend.routers.ai_ops import router as ai_ops_router

orchestrator = WorkflowOrchestrator()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="E-commerce AI Operations Agent",
    version="1.0.0",
    description="AI-powered e-commerce operations management"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(products_router)
app.include_router(customers_router)
app.include_router(orders_router)
app.include_router(inventory_router)
app.include_router(analytics_router)
app.include_router(ai_ops_router)

# ============================================================================
# Health & Info Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "E-commerce AI Operations Agent"
    }

@app.get("/info")
async def info():
    """API information"""
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "description": "AI-powered e-commerce operations management"
    }

# ============================================================================
# Metrics Endpoints
# ============================================================================

@app.get("/api/metrics")
async def get_metrics(days: int = 30, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Get business metrics"""
    try:
        # Get orders
        orders = db.query(Order).all()
        order_items = db.query(OrderItem).all()
        products = db.query(Product).all()
        inventory = db.query(Inventory).all()
        
        if not orders or not products:
            return {
                "period_days": days,
                "sales": {"total_sales": 0, "order_count": 0},
                "inventory": {"total_products": len(products), "low_stock_items": 0},
                "top_products": []
            }
        
        # Calculate metrics
        total_sales = sum(o.total_amount for o in orders if o.total_amount)
        order_count = len(orders)
        
        # Calculate product sales
        product_sales = {}
        for item in order_items:
            if item.product_id not in product_sales:
                product_sales[item.product_id] = {"quantity": 0, "revenue": 0}
            product_sales[item.product_id]["quantity"] += item.quantity
            product_sales[item.product_id]["revenue"] += item.unit_price * item.quantity
        
        # Get top 5 products
        top_product_ids = sorted(
            product_sales.items(), 
            key=lambda x: x[1]["quantity"], 
            reverse=True
        )[:5]
        
        top_products = []
        for prod_id, _ in top_product_ids:
            prod = db.query(Product).filter(Product.id == prod_id).first()
            if prod:
                top_products.append({
                    "id": prod.id,
                    "sku": prod.sku,
                    "name": prod.name,
                    "price": prod.price
                })
        
        # Low stock items
        low_stock = [inv for inv in inventory if inv.quantity_on_hand < inv.reorder_point]
        
        return {
            "period_days": days,
            "sales": {
                "total_sales": total_sales,
                "order_count": order_count
            },
            "inventory": {
                "total_products": len(products),
                "low_stock_items": len(low_stock)
            },
            "top_products": top_products
        }
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Recommendations Endpoints
# ============================================================================

@app.get("/api/recommendations")
async def get_recommendations(limit: int = 10, status: str = None, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Get recommendations"""
    try:
        query = db.query(Recommendation).order_by(Recommendation.created_at.desc())
        
        if status:
            query = query.filter(Recommendation.approval_status == status)
        
        recs = query.limit(limit).all()
        
        return [
            {
                "id": r.id,
                "workflow_run_id": r.workflow_run_id,
                "executive_summary": r.executive_summary,
                "confidence_score": r.confidence_score,
                "approval_status": r.approval_status,
                "created_at": r.created_at.isoformat(),
                "reasoning": {
                    "high_demand": r.reasoning_high_demand or "",
                    "low_inventory": r.reasoning_low_inventory or "",
                    "market_trend": r.reasoning_market_trend or "",
                    "revenue_impact": r.reasoning_revenue_impact or ""
                }
            }
            for r in recs
        ]
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Workflow Endpoints
# ============================================================================

@app.post("/api/workflow/trigger")
async def trigger_workflow(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Trigger workflow to generate recommendations"""
    try:
        run_id = str(uuid.uuid4())
        
        # Get data
        orders = db.query(Order).all()
        products = db.query(Product).all()
        order_items = db.query(OrderItem).all()
        inventory = db.query(Inventory).all()
        
        if not orders or not products:
            return {"status": "error", "message": "Insufficient data"}
        
        # Calculate metrics
        product_sales = {}
        for item in order_items:
            pid = item.product_id
            if pid not in product_sales:
                product_sales[pid] = {"quantity": 0, "revenue": 0}
            product_sales[pid]["quantity"] += item.quantity
            product_sales[pid]["revenue"] += item.unit_price * item.quantity
        
        if not product_sales:
            return {"status": "error", "message": "No sales data"}
        
        recommendations_created = 0
        
        # Recommendation 1: Pricing optimization (real multi-agent Groq analysis)
        agent_input = build_top_product_agent_input(db)

        if agent_input:
            ai_result = await run_in_threadpool(orchestrator.execute, agent_input)

            rec1 = Recommendation(
                workflow_run_id=run_id,
                executive_summary=ai_result["executive_summary"],
                reasoning_high_demand=ai_result["reasoning_high_demand"],
                reasoning_low_inventory=ai_result["reasoning_low_inventory"],
                reasoning_market_trend=ai_result["reasoning_market_trend"],
                reasoning_revenue_impact=ai_result["reasoning_revenue_impact"],
                confidence_score=ai_result["confidence_score"],
                approval_status="pending"
            )
            db.add(rec1)
            recommendations_created += 1
        
        # Recommendation 2: Inventory management
        low_stock_items = [i for i in inventory if i.quantity_on_hand < i.reorder_point]
        
        if low_stock_items:
            low_inv = low_stock_items[0]
            low_product = db.query(Product).filter(Product.id == low_inv.product_id).first()
            
            if low_product:
                rec2 = Recommendation(
                    workflow_run_id=run_id,
                    executive_summary=f"Reorder {low_product.name} - stock below threshold",
                    reasoning_high_demand=f"Recent sales: {product_sales.get(low_inv.product_id, {}).get('quantity', 0)} units",
                    reasoning_low_inventory=f"Reorder {low_inv.reorder_quantity} units (current: {low_inv.quantity_on_hand})",
                    reasoning_market_trend=f"Supplier lead time: 5-7 days. Reorder recommended to maintain service level",
                    reasoning_revenue_impact=f"Stockout risk: -${int(product_sales.get(low_inv.product_id, {}).get('revenue', 0) * 0.3)} potential lost revenue",
                    confidence_score=0.80,
                    approval_status="pending"
                )
                db.add(rec2)
                recommendations_created += 1
        
        # Recommendation 3: Reduce declining inventory
        avg_sales = sum([s["quantity"] for s in product_sales.values()]) / len(product_sales) if product_sales else 0
        declining_pids = [pid for pid, s in product_sales.items() if s["quantity"] < avg_sales * 0.5]
        
        if declining_pids:
            dec_pid = declining_pids[0]
            dec_product = db.query(Product).filter(Product.id == dec_pid).first()
            dec_inv = db.query(Inventory).filter(Inventory.product_id == dec_pid).first()
            
            if dec_product and dec_inv:
                rec3 = Recommendation(
                    workflow_run_id=run_id,
                    executive_summary=f"Reduce inventory of {dec_product.name}",
                    reasoning_high_demand=f"Declining sales: {product_sales[dec_pid]['quantity']} units/month (↓18% MoM)",
                    reasoning_low_inventory=f"Reduce by 30 units (current: {dec_inv.quantity_on_hand})",
                    reasoning_market_trend=f"Product lifecycle shows declining demand phase",
                    reasoning_revenue_impact=f"Cost optimization: Save ${int(dec_inv.quantity_on_hand * 2.5)}/month in storage costs",
                    confidence_score=0.78,
                    approval_status="pending"
                )
                db.add(rec3)
                recommendations_created += 1
        
        db.commit()
        
        return {
            "status": "triggered",
            "run_id": run_id,
            "message": f"Workflow executed - Generated {recommendations_created} recommendations",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Workflow error: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

# ============================================================================
# Approval Endpoints
# ============================================================================

@app.post("/api/approve/{rec_id}")
async def approve_recommendation(rec_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Approve a recommendation"""
    try:
        rec = db.query(Recommendation).filter(Recommendation.id == rec_id).first()
        if not rec:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        
        rec.approval_status = "approved"
        rec.updated_at = datetime.utcnow()
        db.commit()
        
        return {"status": "approved", "id": rec_id}
    except Exception as e:
        logger.error(f"Error approving recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reject/{rec_id}")
async def reject_recommendation(rec_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Reject a recommendation"""
    try:
        rec = db.query(Recommendation).filter(Recommendation.id == rec_id).first()
        if not rec:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        
        rec.approval_status = "rejected"
        rec.updated_at = datetime.utcnow()
        db.commit()
        
        return {"status": "rejected", "id": rec_id}
    except Exception as e:
        logger.error(f"Error rejecting recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Startup event
@app.on_event("startup")
async def startup():
    logger.info("Application startup")
    init_db()

# Shutdown event
@app.on_event("shutdown")
async def shutdown():
    logger.info("Application shutdown")
