import { create } from 'zustand';

export const useAuthStore = create((set) => {
  let initialUser = null;
  let initialToken = null;
  try {
    const storedUser = localStorage.getItem('eris-user');
    const storedToken = localStorage.getItem('eris-token');
    if (storedUser) initialUser = JSON.parse(storedUser);
    if (storedToken) initialToken = storedToken;
  } catch (e) {
    console.error('Failed to parse user from localStorage', e);
  }

  return {
    user: initialUser,
    token: initialToken,
    setUser: (user) => {
      if (user) {
        localStorage.setItem('eris-user', JSON.stringify(user));
      } else {
        localStorage.removeItem('eris-user');
      }
      set({ user });
    },
    setToken: (token) => {
      if (token) {
        localStorage.setItem('eris-token', token);
      } else {
        localStorage.removeItem('eris-token');
      }
      set({ token });
    },
    logout: () => {
      localStorage.removeItem('eris-user');
      localStorage.removeItem('eris-token');
      localStorage.removeItem('eris-auth');
      set({ user: null, token: null });
    }
  };
});
