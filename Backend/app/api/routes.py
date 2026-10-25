import uuid
from urllib.parse import quote
from sqlalchemy.orm import Session
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, Response, status
from fastapi.responses import StreamingResponse

from Backend.app.db.session import get_session
from Backend.app.api.deps import get_current_user
from Backend.app.db.models import AccessStatus, User
from Backend.app.config import Settings, get_settings
from Backend.app.services.reports import ReportService
from Backend.app.db.repo import EmployeeRepo, ReportRepo
from Backend.app.services.org_structure import OrgStructureSyncService
from Backend.app.services.org_structure_client import OrgStructureClient
from Backend.app.api.mappers import employee_to_schema, report_to_details, report_to_schema
from Backend.app.api.schemas import (
    BlacklistRequest,
    EmployeeListResponse,
    OrgEmployeeSnapshot,
    ReportCreateRequest,
    ReportDetails,
    ReportRead,
    SyncResult,
)
from Backend.app.services.errors import (
    PdfRenderError,
    OrgStructureClientError,
    NotFoundError,
    ForbiddenError,
    ValidationError,
    NotImplementedError
)


router = APIRouter(prefix="/api/v1")


@router.get("/employees")
def list_employees(
    access_status: AccessStatus | None = Query(default=None),
    q: str | None = Query(default=None),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> EmployeeListResponse:
    repo = EmployeeRepo(db)
    return EmployeeListResponse(
        items=[employee_to_schema(employee) for employee in repo.list(status=access_status, q=q)],
        counts_by_status=repo.counts_by_status(),
    )


@router.post("/employees/{employee_id}/blacklist")
def blacklist_employee(
    employee_id: str = Path(),
    payload: BlacklistRequest = Body(default_factory=BlacklistRequest),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Response:
    repo = EmployeeRepo(db)
    employee = repo.get(employee_id)
    if employee is None:
        raise NotFoundError("Employee not found")

    repo.set_blacklisted(employee, current_user.id, payload.reason)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/employees/{employee_id}/restore")
def restore_employee(
    employee_id: str = Path(),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Response:
    repo = EmployeeRepo(db)
    employee = repo.get(employee_id)
    if employee is None:
        raise NotFoundError("Employee not found")

    repo.restore_from_blacklist(employee)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/org-structure/snapshot")
def apply_manual_snapshot(
    employees: list[OrgEmployeeSnapshot],
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> SyncResult:
    return OrgStructureSyncService(db).apply_snapshot(employees)


@router.post("/org-structure/sync")
def sync_from_org_structure(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> SyncResult:
    try:
        snapshot = OrgStructureClient(settings).fetch_snapshot()
    except OrgStructureClientError as ex:
        raise OrgStructureClientError(str(ex)) from ex
    return OrgStructureSyncService(db).apply_snapshot(snapshot.employees)


@router.post("/reports")
def create_report(
    payload: ReportCreateRequest = Body(),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ReportRead:
    report = ReportService(db).create_report(payload.mode, payload.comment, current_user)
    report = ReportRepo(db).get_with_items(report.id) or report
    return report_to_schema(report)


@router.get("/reports")
def list_reports(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[ReportRead]:
    return [report_to_schema(report) for report in ReportRepo(db).list()]


@router.get("/reports/{report_id}")
def get_report(
    report_id: uuid.UUID = Path(),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ReportDetails:
    report = ReportRepo(db).get_with_items(report_id)
    if report is None:
        raise NotFoundError("Report not found")
    return report_to_details(report)


@router.get("/reports/{report_id}/download",)
def download_report(
    report_id: uuid.UUID = Path(),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    report = ReportRepo(db).get_with_items(report_id)
    if report is None:
        raise NotFoundError("Report not found")
    try:
        content = ReportService(db).render_pdf(report)
    except PdfRenderError as ex:
        raise PdfRenderError(str(ex)) from ex
    safe_filename = quote(report.file_name.encode('utf-8'))

    return StreamingResponse(
        content=iter([content]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={safe_filename}"
        }
    )
