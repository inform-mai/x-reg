document.addEventListener('DOMContentLoaded', () => {
  const nameEl = document.getElementById('user-name');
  const emailEl = document.getElementById('user-email');

  async function loadUserProfile() {
    try {
      const mockUserFromBackend = {
        full_name: 'Данные придут с бэкенда',
        email: 'из get_settings()'
      };
      if (nameEl) nameEl.textContent = mockUserFromBackend.full_name;
      if (emailEl) emailEl.textContent = mockUserFromBackend.email;
    } catch (error) {
      console.error('Ошибка при загрузке профиля:', error);
      if (nameEl) nameEl.textContent = 'Ошибка загрузки';
      if (emailEl) emailEl.textContent = 'Ошибка загрузки';
    }
  }

  loadUserProfile();

  const form = document.getElementById('change-password-form');
  const currentPassInput = document.getElementById('current-password');
  const newPassInput = document.getElementById('new-password');
  const errorCurrent = document.getElementById('error-current');
  const errorNew = document.getElementById('error-new');

  function showError(element, message) {
    if (message) {
      element.textContent = message;
      element.style.display = 'block';
    } else {
      element.textContent = '';
      element.style.display = 'none';
    }
  }

  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();

      let isValid = true;
      const currentVal = currentPassInput.value.trim();
      const newVal = newPassInput.value.trim();

      //валидация
      if (currentVal === '') {
        showError(errorCurrent, 'Введите текущий пароль');
        isValid = false;
      } else {
        showError(errorCurrent, null);
      }

      if (newVal.length < 6) {
        showError(errorNew, 'Пароль должен быть не менее 6 символов');
        isValid = false;
      } else if (newVal === currentVal) {
        showError(errorNew, 'Новый пароль совпадает с текущим');
        isValid = false;
      } else {
        showError(errorNew, null);
      }

      if (isValid) {
        try {
          alert('Пароль успешно изменен!');
          form.reset();
        } catch (error) {
          console.error('Ошибка при смене пароля:', error);
          alert('Произошла ошибка при смене пароля. Попробуйте позже.');
        }
      }
    });
  }
});