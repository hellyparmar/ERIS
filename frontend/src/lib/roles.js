export const ROLES = Object.freeze({
  ADMIN: 'admin',
  MANAGER: 'manager',
  VIEWER: 'viewer',
});

const ROLE_ALIASES = Object.freeze({
  admin: ROLES.ADMIN,
  super_admin: ROLES.ADMIN,
  superadmin: ROLES.ADMIN,
  administrator: ROLES.ADMIN,
  manager: ROLES.MANAGER,
  area_manager: ROLES.MANAGER,
  outlet_manager: ROLES.MANAGER,
  staff: ROLES.MANAGER,
  viewer: ROLES.VIEWER,
  analyst: ROLES.VIEWER,
  guest: ROLES.VIEWER,
});

export const normalizeRole = (role) => {
  const key = String(role || '').trim().toLowerCase().replaceAll(' ', '_');
  return ROLE_ALIASES[key] || ROLES.VIEWER;
};

export const normalizeUser = (user) => (
  user ? { ...user, role: normalizeRole(user.role) } : user
);
