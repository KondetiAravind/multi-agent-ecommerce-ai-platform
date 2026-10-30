"""Standalone AI operation endpoints (run a single agent, not the full pipeline)"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database.models import Recommendation
from backend.routers.auth import get_current_user
from backend.services.agent_data_service import build_top_product_agent_input
from backend.workflows.langgraph_workflow import (
    DemandForecastAgent, InventoryOptimizationAgent, PricingOptimizationAgent,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["ai-ops"], dependencies=[Depends(get_current_user)])

demand_agent = DemandForecastAgent()
inventory_agent = InventoryOptimizationAgent()
pricing_agent = PricingOptimizationAgent()


def _get_agent_input(db: Session) -> dict:
    agent_input = build_top_product_agent_input(db)
    if not agent_input:
        raise HTTPException(status_code=400, detail="Insufficient sales data to run agent")
    return agent_input


@router.post("/forecast")
async def run_forecast(db: Session = Depends(get_db)):
    agent_input = _get_agent_input(db)
    return await run_in_threadpool(demand_agent.execute, agent_input)


@router.post("/optimize-inventory")
async def run_inventory_optimization(db: Session = Depends(get_db)):
    agent_input = _get_agent_input(db)
    return await run_in_threadpool(inventory_agent.execute, agent_input)


@router.post("/optimize-pricing")
async def run_pricing_optimization(db: Session = Depends(get_db)):
    agent_input = _get_agent_input(db)
    return await run_in_threadpool(pricing_agent.execute, agent_input)


@router.get("/performance")
async def ai_performance(db: Session = Depends(get_db)):
    recs = db.query(Recommendation).all()
    if not recs:
        return {"total": 0, "average_confidence": 0, "approved": 0, "rejected": 0, "pending": 0}

    return {
        "total": len(recs),
        "average_confidence": round(sum(r.confidence_score or 0 for r in recs) / len(recs), 2),
        "approved": len([r for r in recs if r.approval_status == "approved"]),
        "rejected": len([r for r in recs if r.approval_status == "rejected"]),
        "pending": len([r for r in recs if r.approval_status == "pending"]),
    }
