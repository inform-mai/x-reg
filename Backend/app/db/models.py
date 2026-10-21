import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text


def utc_now():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class AccessStatus(str, enum.Enum):
    actual = "actual"
    need_grant = "need_grant"
    need_revoke = "need_revoke"
    revoked = "revoked"
    blacklisted = "blacklisted"


class ReportMode(str, enum.Enum):
    full = "full"
    changes_only = "changes_only"


class ReportAction(str, enum.Enum):
    actual = "actual"
    grant = "grant"
    revoke = "revoke"


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)

    employees: Mapped[list["Employee"]] = relationship(back_populates="department")


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    position: Mapped[str | None] = mapped_column(String)
    phone: Mapped[str | None] = mapped_column(String)
    email: Mapped[str | None] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    access_status: Mapped[AccessStatus] = mapped_column(
        Enum(AccessStatus, name="access_status"), nullable=False, default=AccessStatus.need_grant
    )
    created: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now())
    updated: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now(), onupdate=utc_now()
    )
    department_id: Mapped[str] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )

    department: Mapped[Department] = relationship(back_populates="employees")
    blacklist_entry: Mapped["Blacklist | None"] = relationship(
        back_populates="employee", cascade="all, delete-orphan", uselist=False
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    employee_id: Mapped[str | None] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE", onupdate="CASCADE")
    )

    reports: Mapped[list["Report"]] = relationship(back_populates="created_by_user")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now())
    mode: Mapped[ReportMode] = mapped_column(Enum(ReportMode, name="report_mode"), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    employee_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )

    created_by_user: Mapped[User] = relationship(back_populates="reports")
    items: Mapped[list["ReportItem"]] = relationship(
        back_populates="report", cascade="all, delete-orphan", order_by="ReportItem.full_name"
    )


class ReportItem(Base):
    __tablename__ = "report_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )
    employee_id: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[ReportAction] = mapped_column(Enum(ReportAction, name="report_action"), nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    position: Mapped[str | None] = mapped_column(String)
    phone: Mapped[str | None] = mapped_column(String)
    email: Mapped[str | None] = mapped_column(String)
    department_title: Mapped[str | None] = mapped_column(String)

    report: Mapped[Report] = relationship(back_populates="items")


class Blacklist(Base):
    __tablename__ = "blacklist"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[str] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        unique=True,
    )
    reason: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now())
    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )

    employee: Mapped[Employee] = relationship(back_populates="blacklist_entry")
