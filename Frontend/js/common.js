//подгруз шапки как отдельного элемента
document.addEventListener('DOMContentLoaded', async () => {
  const placeholder = document.getElementById('header-placeholder');

  if (placeholder) {
    const response = await fetch('partials/header.html');
    const html = await response.text();
    placeholder.innerHTML = html;
  }
});