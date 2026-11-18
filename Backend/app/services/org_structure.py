import logging

from Backend.app.api.schemas import OrgEmployeeSnapshot, SyncResult
from Backend.app.db.models import AccessStatus, Employee
from Backend.app.db.repo import EmployeeRepo, utc_now


logger = logging.getLogger(__name__)

# Поля сотрудника, которые приходят из оргструктуры и переносятся в таблицу employees как есть.
SNAPSHOT_FIELDS = ("full_name", "position", "phone", "email", "is_active", "department_id")


# OrgStructureSyncService - загружает в БД "снимок" оргструктуры: полный список сотрудников,
# который пришёл в ручку POST /org-structure/snapshot (вручную) или /org-structure/sync (от парсера).
#
# Что делает apply_snapshot:
#   1. Отделы: каждый department_id / department_title из снимка создаётся или обновляется в departments.
#   2. Новые сотрудники (логина ещё нет в employees) создаются:
#        работает (is_active=True)  -> статус need_grant (нужно выдать доступ);
#        не работает                -> статус revoked (доступа нет и выдавать не нужно).
#   3. Существующие сотрудники обновляются (ФИО, должность, контакты, отдел, активность),
#      а статус доступа пересчитывается, если сотрудник уволился или вернулся (см. _next_status).
#      Если сотрудник пришёл с is_active=False и у него был доступ, статус станет need_revoke,
#      и он посчитается в updated, а не в marked_revoke: по описанию SyncResult marked_revoke -
#      это только те, кто пропал из снимка.
#   4. Сотрудники, которых НЕТ в снимке, считаются ушедшими из компании: is_active=False,
#      и если у них был доступ (actual) - статус need_revoke (нужно отозвать).
#   Сотрудники из чёрного списка (blacklisted) остаются в чёрном списке, их статус не трогаем.
#
# Возвращает SyncResult: сколько сотрудников создано, обновлено и помечено на отзыв доступа.
class OrgStructureSyncService:
    def __init__(self, db):
        self.db = db
        self.repo = EmployeeRepo(db)

    def apply_snapshot(self, employees: list[OrgEmployeeSnapshot]) -> SyncResult:
        # Пустой снимок почти наверняка ошибка источника данных: без этой проверки
        # все сотрудники разом были бы помечены как уволенные. Поэтому ничего не меняем.
        if not employees:
            logger.warning("Empty org snapshot received, nothing changed")
            return SyncResult(created=0, updated=0, marked_revoke=0)

        # Если один логин пришёл несколько раз, берём последнюю запись.
        snapshot = {item.id: item for item in employees}

        created = updated = marked_revoke = 0
        now = utc_now()

        # 1. Отделы. Сначала собираем уникальные: у многих сотрудников один отдел, а upsert_department
        # не видит отдел, только что добавленный в сессию (db.get ищет только уже сохранённые),
        # и без этого попытался бы создать один и тот же отдел несколько раз.
        departments = {item.department_id: item.department_title for item in snapshot.values()}
        for department_id, title in departments.items():
            self.repo.upsert_department(department_id, title)
        # flush отправляет отделы в БД до сотрудников, иначе не сработает внешний ключ department_id
        self.db.flush()

        # 2-3. Сотрудники из снимка
        for item in snapshot.values():
            employee = self.db.get(Employee, item.id)

            if employee is None:
                self.db.add(
                    Employee(
                        id=item.id,
                        full_name=item.full_name,
                        position=item.position,
                        phone=item.phone,
                        email=item.email,
                        is_active=item.is_active,
                        department_id=item.department_id,
                        access_status=AccessStatus.need_grant if item.is_active else AccessStatus.revoked,
                        created=now,
                        updated=now,
                    )
                )
                created += 1
                continue

            changed = False
            for field in SNAPSHOT_FIELDS:
                new_value = getattr(item, field)
                if getattr(employee, field) != new_value:
                    setattr(employee, field, new_value)
                    changed = True

            new_status = self._next_status(employee.access_status, item.is_active)
            if new_status != employee.access_status:
                employee.access_status = new_status
                changed = True

            if changed:
                employee.updated = now
                updated += 1

        # 4. Сотрудники, которых нет в снимке (repo уже исключает blacklisted и revoked)
        for employee in self.repo.employees_missing_from_snapshot(list(snapshot)):
            employee.is_active = False
            employee.updated = now
            if employee.access_status == AccessStatus.actual:
                employee.access_status = AccessStatus.need_revoke
                marked_revoke += 1
            elif employee.access_status == AccessStatus.need_grant:
                # доступ так и не выдали - отзывать нечего
                employee.access_status = AccessStatus.revoked

        self.db.commit()

        logger.info(
            "Org snapshot applied: %s employees, created=%s, updated=%s, marked_revoke=%s",
            len(snapshot), created, updated, marked_revoke,
        )
        return SyncResult(created=created, updated=updated, marked_revoke=marked_revoke)

    @staticmethod
    def _next_status(current: AccessStatus, is_active: bool) -> AccessStatus:
        # Как меняется статус доступа существующего сотрудника по данным снимка.
        if current == AccessStatus.blacklisted:
            return current
        if is_active:
            # вернулся на работу:
            #   доступ уже отозван -> нужно выдать заново;
            #   доступ ещё не успели отозвать -> он по-прежнему есть, отзывать не нужно.
            if current == AccessStatus.revoked:
                return AccessStatus.need_grant
            if current == AccessStatus.need_revoke:
                return AccessStatus.actual
            return current
        # уволился / стал неактивным
        if current == AccessStatus.actual:
            return AccessStatus.need_revoke
        if current == AccessStatus.need_grant:
            return AccessStatus.revoked
        return current
