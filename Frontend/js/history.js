document.addEventListener('DOMContentLoaded', () => {
  const tableBody = document.getElementById('history-body');
  tableBody.innerHTML = mockHistory.map(item => `
    <tr>
      <td>${item.date}</td>
      <td>${item.emp}</td>
      <td>${item.type}</td>
      <td>${item.comment || '—'}</td>
      <td>
        <button style="background:none; border:none; cursor:pointer; font-size: 16px;" title="Скачать PDF">
          ⬇
        </button>
      </td>
    </tr>
  `).join('');
});