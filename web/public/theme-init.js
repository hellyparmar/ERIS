try { const t = localStorage.getItem('eris-theme'); if (t) document.documentElement.dataset.theme = t } catch (e) {}
