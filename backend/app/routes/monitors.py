from fastapi import APIRouter, Depends, Query, Response

from ..dependencies import get_analytics_service, get_monitor_service, get_monitoring_service
from ..schemas import IncidentOut, MonitorInput, MonitorOut, MonitorStats, ResultOut
from ..services.analytics import AnalyticsService
from ..services.monitoring import MonitoringService
from ..services.monitors import MonitorService

router = APIRouter(prefix="/api", tags=["Monitors"])


@router.get("/approved-endpoints", response_model=dict[str, str], deprecated=True)
@router.get("/example-endpoints", response_model=dict[str, str])
def example_endpoints(service: MonitorService = Depends(get_monitor_service)):
    return service.example_endpoints()


@router.get("/monitors", response_model=list[MonitorOut])
def list_monitors(service: MonitorService = Depends(get_monitor_service)):
    return service.list()


@router.post("/monitors", response_model=MonitorOut, status_code=201)
async def create_monitor(data: MonitorInput, service: MonitorService = Depends(get_monitor_service)):
    return await service.create(data)


@router.get("/monitors/{monitor_id}", response_model=MonitorOut)
def get_monitor(monitor_id: int, service: MonitorService = Depends(get_monitor_service)):
    return service.get(monitor_id)


@router.put("/monitors/{monitor_id}", response_model=MonitorOut)
async def update_monitor(monitor_id: int, data: MonitorInput, service: MonitorService = Depends(get_monitor_service)):
    return service.update(monitor_id, data)


@router.delete("/monitors/{monitor_id}", status_code=204)
async def delete_monitor(monitor_id: int, service: MonitorService = Depends(get_monitor_service)):
    service.delete(monitor_id)
    return Response(status_code=204)


@router.get("/monitors/{monitor_id}/results", response_model=list[ResultOut])
def results(monitor_id: int, hours: int = Query(24, ge=1, le=720),
            limit: int = Query(500, ge=1, le=2000), offset: int = Query(0, ge=0),
            service: MonitorService = Depends(get_monitor_service)):
    return service.results(monitor_id, hours, limit, offset)


@router.get("/monitors/{monitor_id}/analytics", response_model=MonitorStats)
def analytics(monitor_id: int, hours: int = Query(24, ge=1, le=720),
              service: AnalyticsService = Depends(get_analytics_service)):
    return service.monitor(monitor_id, hours)


@router.get("/monitors/{monitor_id}/incidents", response_model=list[IncidentOut])
def incidents(monitor_id: int, limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0),
              service: MonitorService = Depends(get_monitor_service)):
    return service.incidents(monitor_id, limit, offset)


@router.post("/monitors/{monitor_id}/check", response_model=ResultOut)
async def manual_check(monitor_id: int, service: MonitoringService = Depends(get_monitoring_service)):
    return await service.check(monitor_id)
