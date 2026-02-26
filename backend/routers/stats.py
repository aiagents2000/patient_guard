"""
Router statistiche dashboard.

Endpoints:
    GET /api/v1/stats/overview    — Statistiche aggregate
    GET /api/v1/stats/department  — Statistiche per reparto
"""

from fastapi import APIRouter, Depends

from models.database import DataStore, get_datastore
from models.schemas import DepartmentStats, StatsOverview

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


@router.get("/overview", response_model=StatsOverview)
async def get_overview(
    store: DataStore = Depends(get_datastore),
):
    """Statistiche aggregate per la dashboard principale."""
    return await store.get_stats_overview()


@router.get("/department", response_model=list[DepartmentStats])
async def get_department_stats(
    store: DataStore = Depends(get_datastore),
):
    """Statistiche per reparto."""
    return await store.get_stats_department()
