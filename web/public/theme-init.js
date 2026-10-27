try { const t = localStorage.getItem('eris-theme'); if (t) document.documentElement.dataset.theme = t } catch { /* private mode: the saved theme is simply not applied */ }
