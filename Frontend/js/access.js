document.addEventListener('DOMContentLoaded', async () => {
  const tableBody = document.getElementById('table-body');
  const filterBtns = document.querySelectorAll('.filter-btn');
  const searchInput = document.getElementById('search-input');

  //загрузка модалок
  try {
    const res = await fetch('partials/modals/access-modals.html');
    if (!res.ok) throw new Error('Ошибка загрузки модальных окон');
    const html = await res.text();
    document.getElementById('modals-placeholder').innerHTML = html;
    initModalsLogic();
  } catch (e) {
    console.error('Не удалось загрузить модальные окна:', e);
  }

  //фейк сотрудники пока нет апи
  let employees = [
    { id: 'i.ivanov', full_name: 'Иванов Иван', position: 'Инженер', department_title: 'ИТ', phone: '123', email: 'ivanov@mail.ru', access_status: 'actual', access_status_title: 'Актуальная УЗ' },
    { id: 'p.petrov', full_name: 'Петров Петр', position: 'Менеджер', department_title: 'Кадры', phone: '456', email: 'petrov@mail.ru', access_status: 'need_grant', access_status_title: 'Прием' },
    { id: 's.sidorov', full_name: 'Сидоров Сидор', position: 'Бухгалтер', department_title: 'Бухгалтерия', phone: '789', email: 'sidorov@mail.ru', access_status: 'need_revoke', access_status_title: 'Отзыв' },
    { id: 'k.kuznetsov', full_name: 'Кузнецов Кирилл', position: 'Охранник', department_title: 'СБ', phone: '000', email: 'kuz@mail.ru', access_status: 'blacklisted', access_status_title: 'Исключен' }
  ];
  let currentFilter = '';
  let currentSearch = '';

  //рендер таблицы
  function renderTable() {
    let filtered = employees.filter(emp => {
      const matchStatus = currentFilter === '' || emp.access_status === currentFilter;
      const searchLower = currentSearch.toLowerCase();
      const matchSearch = emp.full_name.toLowerCase().includes(searchLower) ||
                          emp.email.toLowerCase().includes(searchLower) ||
                          emp.id.toLowerCase().includes(searchLower);
      return matchStatus && matchSearch;
    });
    if (filtered.length === 0) {
      tableBody.innerHTML = '<tr><td colspan="7" style="text-align:center;">Ничего не найдено</td></tr>';
    } else {
      tableBody.innerHTML = filtered.map(emp => `
        <tr>
          <td>${emp.full_name}</td>
          <td>${emp.position || '—'}</td>
          <td>${emp.department_title || '—'}</td>
          <td>${emp.phone || '—'}</td>
          <td>${emp.email || '—'}</td>
          <td>${emp.access_status_title}</td>
          <td>
            ${renderActionButtons(emp)}
          </td>
        </tr>
      `).join('');
    }
    updateCounters();
  }

  //кнопки для каждой строки
  function renderActionButtons(emp) {
    const id = emp.id;
    if (emp.access_status === 'blacklisted') {
      return `<button class="btn-action" data-action="restore" data-id="${id}">Вернуть</button>
              <button class="btn-action" data-action="delete" data-id="${id}">Удалить</button>`;
    } else if (emp.access_status === 'actual') {
      return `<button class="btn-action" data-action="blacklist" data-id="${id}">Исключить</button>`;
    } else if (emp.access_status === 'need_grant') {
      return `<button class="btn-action" data-action="add" data-id="${id}">Добавить</button>`;
    } else {
      return `<button class="btn-action" data-action="blacklist" data-id="${id}">Исключить</button>`;
    }
  }
  function updateCounters() {
    const counts = {
      actual: employees.filter(e => e.access_status === 'actual').length,
      need_grant: employees.filter(e => e.access_status === 'need_grant').length,
      need_revoke: employees.filter(e => e.access_status === 'need_revoke').length,
      revoked: employees.filter(e => e.access_status === 'revoked').length,
      blacklisted: employees.filter(e => e.access_status === 'blacklisted').length,
      all: employees.length
    };
    filterBtns.forEach(btn => {
      const status = btn.dataset.status;
      let baseText = btn.textContent.split('(')[0].trim();
      if (status === '') {
        btn.textContent = `${baseText} (${counts.all})`;
      } else if (counts[status] !== undefined) {
        btn.textContent = `${baseText} (${counts[status]})`;
      }
    });
  }

  //обработка фильтров
  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilter = btn.dataset.status;
      renderTable();
    });
  });

  //обработка поиска
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      currentSearch = e.target.value;
      renderTable();
    });
  }
  //логика модалок
  let pendingAction = null;

  function initModalsLogic() {
    const btnAllowList = document.getElementById('btn-allow-list');
    if (btnAllowList) {
      btnAllowList.addEventListener('click', () => {
        document.getElementById('modal-allow-list').style.display = 'flex';
      });
    }

    tableBody.addEventListener('click', (e) => {
      const btn = e.target.closest('.btn-action');
      if (!btn) return;
      const id = btn.dataset.id;
      const action = btn.dataset.action;
      const emp = employees.find(e => e.id === id);
      pendingAction = { id, action };

      if (action === 'blacklist') {
        document.getElementById('modal-blacklist-name').textContent = emp.full_name;
        document.getElementById('modal-blacklist').style.display = 'flex';
      } else if (action === 'restore') {
        document.getElementById('modal-restore-name').textContent = emp.full_name;
        document.getElementById('modal-restore').style.display = 'flex';
      } else if (action === 'delete') {
        document.getElementById('modal-delete').style.display = 'flex';
      } else if (action === 'add') {
        document.getElementById('modal-add-name').textContent = emp.full_name;
        document.getElementById('modal-add').style.display = 'flex';
      }
    });

    document.querySelectorAll('.modal .btn-cancel').forEach(btn => {
      btn.addEventListener('click', () => {
        btn.closest('.modal').style.display = 'none';
        pendingAction = null;
      });
    });

    document.querySelectorAll('.modal .btn-confirm').forEach(btn => {
      btn.addEventListener('click', () => {
        if (!pendingAction) return;
        const { id, action } = pendingAction;
        if (action === 'delete') {
          employees = employees.filter(e => e.id !== id);
        } else {
          const emp = employees.find(e => e.id === id);
          if (emp) {
            if (action === 'blacklist') {
              emp.access_status = 'blacklisted';
              emp.access_status_title = 'Исключен';
            } else if (action === 'restore' || action === 'add') {
              emp.access_status = 'actual';
              emp.access_status_title = 'Актуальная УЗ';
            }
          }
        }
        btn.closest('.modal').style.display = 'none';
        pendingAction = null;
        renderTable();
      });
    });
  }

  renderTable();
});