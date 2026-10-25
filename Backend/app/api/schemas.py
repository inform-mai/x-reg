import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from Backend.app.db.models import AccessStatus, ReportAction, ReportMode


class EmployeeRead(BaseModel):
    id: str = Field(description="Employee login", examples=["i.ivanov"])
    full_name: str = Field(description="Employee full name", examples=["Иванов Иван Иванович"])
    position: str | None = Field(default=None, description="Employee position")
    phone: str | None = Field(default=None, description="Work phone")
    email: str | None = Field(default=None, description="Work email")
    is_active: bool = Field(description="Current activity flag")
    access_status: AccessStatus = Field(description="Local access status")
    access_status_title: str = Field(description="Readable access status")
    department_id: str = Field(description="Department id")
    department_title: str | None = Field(default=None, description="Department title")


class EmployeeListResponse(BaseModel):
    items: list[EmployeeRead] = Field(description="Employees matching filters")
    counts_by_status: dict[AccessStatus, int] = Field(description="Counters grouped by access status") # ---


class BlacklistRequest(BaseModel):
    reason: str | None = Field(
        default=None,
        description="Optional comment explaining why the employee is excluded",
        examples=["Начальство"],
    )


class OrgEmployeeSnapshot(BaseModel):
    id: str = Field(min_length=1, description="Employee login", examples=["i.ivanov"])
    full_name: str = Field(min_length=1, description="Employee full name", examples=["Иванов Иван Иванович"])
    position: str | None = Field(default=None, description="Employee position", examples=["Инженер"])
    phone: str | None = Field(default=None, description="Work phone", examples=["+7 (999) 123-45-67"])
    email: str | None = Field(default=None, description="Work email", examples=["i.ivanov@ctdl.ru"])
    is_active: bool = Field(default=True, description="Whether employee is active")
    # --- возможно выпилить
    department_id: str = Field(min_length=1, description="Department id", examples=["it"])
    department_title: str = Field(min_length=1, description="Department title", examples=["ИТ"])


class OrgSnapshotResponse(BaseModel):
    snapshot_id: str = Field(description="External snapshot identifier")
    generated_at: datetime = Field(description="Snapshot generation timestamp")
    employees: list[OrgEmployeeSnapshot] = Field(description="Employees included in the snapshot")


class SyncResult(BaseModel):
    created: int = Field(description="Number of employees created locally")
    updated: int = Field(description="Number of employees updated locally")
    marked_revoke: int = Field(description="Existing active employees missing from snapshot and marked for revoke")


class ReportCreateRequest(BaseModel):
    mode: ReportMode = Field(
        default=ReportMode.changes_only,
        description="Report mode: 'changes_only' includes grants/revokes only, 'full' also includes actual accounts",
    )
    comment: str | None = Field(default=None, description="Operator comment in export history")


class ReportItemRead(BaseModel):
    employee_id: str = Field(description="Employee login")
    action: ReportAction = Field(description="Action fixed in the report snapshot")
    action_title: str = Field(description="Readable action title")
    full_name: str = Field(description="Employee full name at report generation time")
    position: str | None = Field(default=None, description="Employee position at report generation time")
    phone: str | None = Field(default=None, description="Work phone at report generation time")
    email: str | None = Field(default=None, description="Work email at report generation time")
    department_title: str | None = Field(default=None, description="Department title at report generation time")


class ReportRead(BaseModel):
    id: uuid.UUID = Field(description="Report id")
    created_at: datetime = Field(description="Report creation timestamp")
    mode: ReportMode = Field(description="Report mode")
    mode_title: str = Field(description="Readable report mode title")
    comment: str | None = Field(default=None, description="Operator comment")
    file_name: str = Field(description="Generated .pdf-file name")
    employee_count: int = Field(description="Number of employees included in the report snapshot")
    created_by: uuid.UUID = Field(description="User id of report creator")
    created_by_full_name: str | None = Field(default=None, description="Report creator full name")


class ReportDetails(ReportRead):
    items: list[ReportItemRead] = Field(description="Rows fixed in the report snapshot")
