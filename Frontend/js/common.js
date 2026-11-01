document.addEventListener('DOMContentLoaded', async () => {
  //подгруз шапки как отдельного элемента
  const placeholder = document.getElementById('header-placeholder');

  //проверка наличия placeholder
  if (!placeholder) {
    console.warn('#header-placeholder не найден на странице. Шапка не будет загружена.');
    return;
  }
  //сообщение о загрузке
  placeholder.innerHTML = '<div style="text-align: center; padding: 10px; color: #888; font-size: 14px;">Загрузка шапки...</div>';
  //долгая загрузка+доп. сообщение через 2 сек.
  const slowLoadingTimer = setTimeout(() => {
    placeholder.innerHTML = '<div style="text-align: center; padding: 10px; color: #888; font-size: 14px;">Загрузка занимает больше времени, чем обычно...</div>';
  }, 2000);

  try {
    const response = await fetch('partials/header.html');
    if (!response.ok) {
      throw new Error(`Ошибка HTTP: ${response.status} ${response.statusText}`);
    }
    const html = await response.text();
    clearTimeout(slowLoadingTimer);
    placeholder.innerHTML = html;
    initProfileDropdown();
  } catch (error) {
    //обработка try+catch
    console.error('Не удалось загрузить шапку:', error);
    clearTimeout(slowLoadingTimer);
    //сообщение об ошибке загрузки шапки
    placeholder.innerHTML = `
      <div style="text-align: center; padding: 10px; color: #e74c3c; font-size: 14px; background-color: #fdf2f2; border-bottom: 1px solid #f5c6cb;">
        !Не удалось загрузить шапку. Пожалуйста, обновите страницу.
      </div>
    `;
  }
});

function initProfileDropdown() {
  const btn = document.getElementById('profile-btn');
  const dropdown = document.getElementById('profile-dropdown');
  
  if (btn && dropdown) {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      dropdown.classList.toggle('show');
    });

    document.addEventListener('click', (e) => {
      if (!btn.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.classList.remove('show');
      }
    });
  }
}