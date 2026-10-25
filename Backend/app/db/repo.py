from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import func, select, true
from sqlalchemy.orm import joinedload, selectinload

from Backend.app.db.models import (
    AccessStatus,
    Blacklist,
    Department,
    Employee,
    Report,
    ReportAction,
    ReportItem,
    ReportMode,
    User,
)


def utc_now():
    return datetime.now(timezone.utc)


class UserRepo:
    def __init__(self, db):
        self.db = db

    def get_or_create_dev_user(self, email, full_name):
        user = self.db.scalar(select(User).where(User.email == email))
        if user:
            return user

        user = User(full_name=full_name, email=email, is_active=True)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user


class EmployeeRepo:
    def __init__(self, db):
        self.db = db

    def list(self, status=None, q=None):
        query = select(Employee).options(joinedload(Employee.department)).order_by(Employee.full_name)
        if status is not None:
            query = query.where(Employee.access_status == status)
        if q:
            pattern = f"%{q.strip()}%"
            query = query.where(
                Employee.full_name.ilike(pattern)
                | Employee.id.ilike(pattern)
                | Employee.email.ilike(pattern)
            )
        return list(self.db.scalars(query).all())

    def counts_by_status(self):
        return dict(
            self.db.execute(
                select(Employee.access_status, func.count(Employee.id)).group_by(Employee.access_status)
            ).all()
        )

    def get(self, employee_id):
        return self.db.scalar(
            select(Employee)
            .options(joinedload(Employee.department), joinedload(Employee.blacklist_entry))
            .where(Employee.id == employee_id)
        )

    def upsert_department(self, department_id, title):
        department = self.db.get(Department, department_id)
        if department is None:
            department = Department(id=department_id, title=title)
            self.db.add(department)
        else:
            department.title = title
        return department

    def employees_missing_from_snapshot(self, incoming_ids):
        condition = Employee.id.notin_(incoming_ids) if incoming_ids else true()
        return list(
            self.db.scalars(
                select(Employee).where(
                    Employee.is_active.is_(True),
                    condition,
                    Employee.access_status.not_in([AccessStatus.blacklisted, AccessStatus.revoked]),
                )
            ).all()
        )

    def set_blacklisted(self, employee, user_id, reason):
        employee.access_status = AccessStatus.blacklisted
        employee.updated = utc_now()
        if employee.blacklist_entry is None:
            self.db.add(Blacklist(employee_id=employee.id, reason=reason or None, created_by=user_id))
        else:
            employee.blacklist_entry.reason = reason or employee.blacklist_entry.reason

    def restore_from_blacklist(self, employee: Employee) -> None:
        if employee.blacklist_entry is not None:
            self.db.delete(employee.blacklist_entry)

        employee.access_status = AccessStatus.need_grant if employee.is_active else AccessStatus.need_revoke
        employee.updated = utc_now()


class ReportRepo:
    def __init__(self, db):
        self.db = db

    def list(self):
        return list(
            self.db.scalars(
                select(Report)
                .options(joinedload(Report.created_by_user))
                .order_by(Report.created_at.desc())
            ).all()
        )

    def get_with_items(self, report_id):
        return self.db.scalar(
            select(Report)
            .options(selectinload(Report.items), joinedload(Report.created_by_user))
            .where(Report.id == report_id)
        )

    def employees_for_report(self, mode):
        statuses = [AccessStatus.need_grant, AccessStatus.need_revoke]
        if mode == ReportMode.full:
            statuses.append(AccessStatus.actual)

        return list(
            self.db.scalars(
                select(Employee)
                .options(joinedload(Employee.department))
                .where(Employee.access_status.in_(statuses))
                .order_by(Employee.full_name)
            ).all()
        )

    def create_with_items(self, mode, comment, file_name, user_id, employees):
        report = Report(
            mode=mode,
            comment=comment or None,
            file_name=file_name,
            employee_count=len(employees),
            created_by=user_id,
            created_at=utc_now(),
        )
        self.db.add(report)
        self.db.flush()

        status_to_action = {
            AccessStatus.actual: ReportAction.actual,
            AccessStatus.need_grant: ReportAction.grant,
            AccessStatus.need_revoke: ReportAction.revoke,
        }
        now = utc_now()
        for employee in employees:
            action = status_to_action[employee.access_status]
            self.db.add(
                ReportItem(
                    report_id=report.id,
                    employee_id=employee.id,
                    action=action,
                    full_name=employee.full_name,
                    position=employee.position,
                    phone=employee.phone,
                    email=employee.email,
                    department_title=employee.department.title if employee.department else None,
                )
            )

            if action == ReportAction.grant:
                employee.access_status = AccessStatus.actual
                employee.is_active = True
                employee.updated = now
            elif action == ReportAction.revoke:
                employee.access_status = AccessStatus.revoked
                employee.is_active = False
                employee.updated = now

        self.db.flush()
        return report
