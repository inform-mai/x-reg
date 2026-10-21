from Backend.app.db.models import AccessStatus, Employee, Report, ReportAction, ReportMode
from Backend.app.api.schemas import EmployeeRead, ReportDetails, ReportItemRead, ReportRead


ACCESS_STATUS_TITLES = {
    AccessStatus.actual: "Актуальная УЗ",
    AccessStatus.need_grant: "Прием",
    AccessStatus.need_revoke: "Отзыв",
    AccessStatus.revoked: "Отозвана",
    AccessStatus.blacklisted: "Исключен",
}

REPORT_MODE_TITLES = {
    ReportMode.full: "Полный",
    ReportMode.changes_only: "Только изменения",
}

REPORT_ACTION_TITLES = {
    ReportAction.actual: "Актуальная УЗ",
    ReportAction.grant: "Выдача",
    ReportAction.revoke: "Отзыв",
}


def employee_to_schema(employee: Employee) -> EmployeeRead:
    return EmployeeRead(
        id=employee.id,
        full_name=employee.full_name,
        position=employee.position,
        phone=employee.phone,
        email=employee.email,
        is_active=employee.is_active,
        access_status=employee.access_status,
        access_status_title=ACCESS_STATUS_TITLES[employee.access_status],
        department_id=employee.department_id,
        department_title=employee.department.title if employee.department else None,
    )


def report_to_schema(report: Report) -> ReportRead:
    return ReportRead(
        id=report.id,
        created_at=report.created_at,
        mode=report.mode,
        mode_title=REPORT_MODE_TITLES[report.mode],
        comment=report.comment,
        file_name=report.file_name,
        employee_count=report.employee_count,
        created_by=report.created_by,
        created_by_full_name=(
            report.created_by_user.full_name if report.created_by_user is not None else None
        ),
    )


def report_to_details(report: Report) -> ReportDetails:
    base = report_to_schema(report)
    return ReportDetails(
        **base.model_dump(),
        items=[
            ReportItemRead(
                employee_id=item.employee_id,
                action=item.action,
                action_title=REPORT_ACTION_TITLES[item.action],
                full_name=item.full_name,
                position=item.position,
                phone=item.phone,
                email=item.email,
                department_title=item.department_title,
            )
            for item in report.items
        ],
    )
