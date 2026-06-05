export const setTheme = (theme) => {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('rdios-theme', theme);
};

export const getTheme = () =>
  localStorage.getItem('rdios-theme') || 'dark';

export const toggleTheme = () => {
  const next = getTheme() === 'dark' ? 'light' : 'dark';
  setTheme(next);
  return next;
};
