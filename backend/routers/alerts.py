"""
Router alert.

Endpoints:
    GET   /api/v1/alerts             — Lista alert attivi
    PATCH /api/v1/alerts/{id}/read   — Segna alert come letto
    PATCH /api/v1/alerts/{id}/resolve — Segna alert come risolto
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from models.database import DataStore, get_datastore
from models.schemas import AlertResponse

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    severity: Optional[str] = Query(None, description="Filtra per severity: low, medium, high, critical"),
    is_read: Optional[bool] = Query(None, description="Filtra per stato lettura"),
    limit: int = Query(50, ge=1, le=200),
    store: DataStore = Depends(get_datastore),
):
    """Lista alert, ordinati dal più recente."""
    return await store.get_alerts(severity=severity, is_read=is_read, limit=limit)


@router.patch("/{alert_id}/read", response_model=AlertResponse)
async def mark_alert_read(
    alert_id: str,
    store: DataStore = Depends(get_datastore),
):
    """Segna un alert come letto."""
    alert = await store.mark_alert_read(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert non trovato")
    return alert


@router.patch("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: str,
    store: DataStore = Depends(get_datastore),
):
    """Segna un alert come risolto."""
    alert = await store.mark_alert_resolved(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert non trovato")
    return alert
