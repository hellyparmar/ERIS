import { create } from 'zustand';

export const useAuthStore = create((set) => {
  let initialUser = null;
  let initialToken = null;
  try {
    const storedUser = localStorage.getItem('rdios-user');
    const storedToken = localStorage.getItem('rdios-token');
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
        localStorage.setItem('rdios-user', JSON.stringify(user));
      } else {
        localStorage.removeItem('rdios-user');
      }
      set({ user });
    },
    setToken: (token) => {
      if (token) {
        localStorage.setItem('rdios-token', token);
      } else {
        localStorage.removeItem('rdios-token');
      }
      set({ token });
    },
    logout: () => {
      localStorage.removeItem('rdios-user');
      localStorage.removeItem('rdios-token');
      localStorage.removeItem('rdios-auth');
      set({ user: null, token: null });
    }
  };
});
