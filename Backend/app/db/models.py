import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text


# Возвращает текущее время в UTC. Используется как значение по умолчанию для полей с датами.
def utc_now():
    return datetime.now(timezone.utc)


# Base - базовый класс для всех моделей (SQLAlchemy 2.0).
# Каждая модель, унаследованная от Base, становится таблицей в БД.
# Base.metadata хранит описание всех таблиц; по нему init_db() в session.py создаёт таблицы.
class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# ПЕРЕЧИСЛЕНИЯ (Enum). В PostgreSQL каждое создаётся как отдельный тип данных,
# поэтому в поле можно записать только одно из перечисленных значений.
# ---------------------------------------------------------------------------

# AccessStatus - статус доступа сотрудника к Харону (поле Employee.access_status).
#   actual      - доступ выдан и актуален
#   need_grant  - доступа нет, его нужно выдать (значение по умолчанию для нового сотрудника)
#   need_revoke - доступ есть, но его нужно отозвать (сотрудник уволился / пропал из оргструктуры)
#   revoked     - доступ отозван
#   blacklisted - сотрудник в чёрном списке, доступ ему не выдаётся (см. модель Blacklist)
class AccessStatus(str, enum.Enum):
    actual = "actual"
    need_grant = "need_grant"
    need_revoke = "need_revoke"
    revoked = "revoked"
    blacklisted = "blacklisted"


# ReportMode - режим формирования отчёта (поле Report.mode).
#   full         - в отчёт попадают все: и с актуальным доступом, и кому нужно выдать/отозвать
#   changes_only - только изменения: кому выдать и кому отозвать
class ReportMode(str, enum.Enum):
    full = "full"
    changes_only = "changes_only"


# ReportAction - действие по сотруднику, зафиксированное в строке отчёта (поле ReportItem.action).
#   actual - доступ без изменений, grant - выдать доступ, revoke - отозвать доступ
class ReportAction(str, enum.Enum):
    actual = "actual"
    grant = "grant"
    revoke = "revoke"


# ---------------------------------------------------------------------------
# МОДЕЛИ (таблицы)
# ---------------------------------------------------------------------------

# Department - таблица "departments", отдел компании (справочник отделов из оргструктуры).
# Поля:
#   id    - строковый идентификатор отдела из оргструктуры (например, "it"), первичный ключ
#   title - название отдела (например, "ИТ")
# Связи:
#   один отдел -> много сотрудников (Employee).
#   Внешний ключ хранится на стороне Employee: Employee.department_id -> departments.id.
#   employees - список сотрудников отдела (обратная сторона Employee.department).
class Department(Base):
    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)

    employees: Mapped[list["Employee"]] = relationship(back_populates="department")


# Employee - таблица "employees", сотрудник компании и состояние его доступа к Харону.
# Это центральная модель: именно её отдел кадров просматривает и меняет.
# Поля:
#   id            - логин сотрудника из оргструктуры (например, "i.ivanov"), первичный ключ
#   full_name     - ФИО (обязательно)
#   position, phone, email - должность, рабочий телефон, рабочая почта (необязательны)
#   is_active     - работает ли сотрудник сейчас (False - уволен / неактивен)
#   access_status - статус доступа к Харону (AccessStatus), по умолчанию need_grant
#   created / updated - когда запись создана и когда последний раз изменена
#   department_id - внешний ключ на отдел
# Связи:
#   много сотрудников -> один отдел (Department)
#       через внешний ключ department_id -> departments.id.
#       ondelete="CASCADE": при удалении отдела удаляются все его сотрудники;
#       onupdate="CASCADE": при смене id отдела department_id у сотрудников обновится сам.
#   один сотрудник -> ноль или одна запись в чёрном списке (Blacklist)
#       через внешний ключ Blacklist.employee_id -> employees.id (uselist=False: одна запись, а не список).
#       cascade="all, delete-orphan": если убрать запись из blacklist_entry, она удалится из БД.
#   один сотрудник -> ноль или один пользователь системы (User)
#       через внешний ключ User.employee_id -> employees.id (relationship с этой стороны не объявлен).
#   С ReportItem связь только логическая: ReportItem.employee_id хранит логин, но это НЕ внешний ключ.
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


# User - таблица "users", пользователь самого приложения (сотрудник отдела кадров / администратор),
# то есть тот, КТО работает с системой: формирует отчёты, вносит в чёрный список.
# Поля:
#   id          - UUID, генерируется автоматически, первичный ключ
#   full_name   - ФИО пользователя
#   email       - почта, уникальна и проиндексирована (по ней пользователь ищется при входе)
#   is_active   - активна ли учётная запись
#   employee_id - необязательная ссылка на карточку сотрудника, если пользователь сам есть в оргструктуре
# Связи:
#   пользователь -> ноль или один сотрудник (Employee)
#       через внешний ключ employee_id -> employees.id (CASCADE: удалили сотрудника - удалился пользователь).
#   один пользователь -> много отчётов (Report)
#       через внешний ключ Report.created_by -> users.id; reports - список его отчётов.
#   один пользователь -> много записей чёрного списка (Blacklist)
#       через внешний ключ Blacklist.created_by -> users.id (relationship с этой стороны не объявлен).
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


# Report - таблица "reports", сформированный отчёт (сводка), который выгружается в PDF
# и прикладывается к письму. По сути - история выгрузок.
# Поля:
#   id             - UUID, первичный ключ
#   created_at     - дата и время формирования
#   mode           - режим отчёта (ReportMode: full / changes_only)
#   comment        - комментарий сотрудника, который формировал отчёт (необязателен)
#   file_name      - имя PDF-файла
#   employee_count - сколько сотрудников попало в отчёт
#   created_by     - кто сформировал отчёт (внешний ключ на пользователя)
# Связи:
#   много отчётов -> один пользователь (User)
#       через внешний ключ created_by -> users.id (CASCADE: удалили пользователя - удалились его отчёты).
#       created_by_user - сам объект пользователя (обратная сторона User.reports).
#   один отчёт -> много строк отчёта (ReportItem)
#       через внешний ключ ReportItem.report_id -> reports.id.
#       cascade="all, delete-orphan": удаляется отчёт - удаляются его строки.
#       order_by: строки всегда отдаются отсортированными по ФИО.
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


# ReportItem - таблица "report_items", одна строка отчёта = один сотрудник и действие по нему.
# Это "снимок" данных сотрудника на момент формирования отчёта: ФИО, должность, отдел и т.д.
# копируются сюда, чтобы старый отчёт не менялся, даже если потом данные сотрудника изменятся.
# Поля:
#   id         - UUID, первичный ключ
#   report_id  - к какому отчёту относится строка (внешний ключ)
#   employee_id - логин сотрудника; специально НЕ внешний ключ, чтобы строка сохранилась,
#                 даже если сотрудника удалят из employees
#   action     - действие по сотруднику (ReportAction: actual / grant / revoke)
#   full_name, position, phone, email, department_title - копия данных сотрудника на момент отчёта
# Связи:
#   много строк -> один отчёт (Report)
#       через внешний ключ report_id -> reports.id (CASCADE: удалили отчёт - удалились строки).
#   С Employee связь только логическая, по значению employee_id.
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


# Blacklist - таблица "blacklist", чёрный список: сотрудники, которым доступ к Харону не выдаётся.
# Когда сотрудника вносят сюда, его Employee.access_status становится blacklisted;
# при восстановлении запись удаляется, а статус возвращается к need_grant / need_revoke.
# Поля:
#   id          - UUID, первичный ключ
#   employee_id - кого внесли в чёрный список (внешний ключ, unique: один сотрудник - максимум одна запись)
#   reason      - причина (необязательна)
#   created_at  - когда внесли
#   created_by  - кто внёс (внешний ключ на пользователя)
# Связи:
#   запись -> один сотрудник (Employee), связь один-к-одному
#       через внешний ключ employee_id -> employees.id (CASCADE: удалили сотрудника - удалилась запись).
#       employee - сам объект сотрудника (обратная сторона Employee.blacklist_entry).
#   много записей -> один пользователь (User)
#       через внешний ключ created_by -> users.id (relationship не объявлен, связь есть только в БД).
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
