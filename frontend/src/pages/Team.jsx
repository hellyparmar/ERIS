import { useState } from 'react';
import { Users, Mail, Phone, Shield, Activity, Calendar, MoreVertical, Plus, UserPlus } from 'lucide-react';
import { useToast } from '../components/ui/Toast';

const teamMembers = [
  { id: 1, name: 'Rajesh Kumar', role: 'Admin', department: 'Management', email: 'rajesh.k@rdios.com', phone: '+91 98765 43210', status: 'active', initials: 'RK', lastActive: 'Now' },
  { id: 2, name: 'Priya Sharma', role: 'Manager', department: 'Sales', email: 'priya.s@rdios.com', phone: '+91 98765 43211', status: 'active', initials: 'PS', lastActive: '5m ago' },
  { id: 3, name: 'Amit Verma', role: 'Analyst', department: 'Data', email: 'amit.v@rdios.com', phone: '+91 98765 43212', status: 'away', initials: 'AV', lastActive: '15m ago' },
  { id: 4, name: 'Sneha Patel', role: 'Admin', department: 'Finance', email: 'sneha.p@rdios.com', phone: '+91 98765 43213', status: 'active', initials: 'SP', lastActive: '1h ago' },
  { id: 5, name: 'Vikram Singh', role: 'Manager', department: 'Operations', email: 'vikram.s@rdios.com', phone: '+91 98765 43214', status: 'offline', initials: 'VS', lastActive: '3h ago' },
  { id: 6, name: 'Neha Gupta', role: 'Analyst', department: 'Inventory', email: 'neha.g@rdios.com', phone: '+91 98765 43215', status: 'away', initials: 'NG', lastActive: '30m ago' },
  { id: 7, name: 'Rohit Malhotra', role: 'Manager', department: 'Marketing', email: 'rohit.m@rdios.com', phone: '+91 98765 43216', status: 'offline', initials: 'RM', lastActive: '1d ago' },
  { id: 8, name: 'Ananya Reddy', role: 'Admin', department: 'HR', email: 'ananya.r@rdios.com', phone: '+91 98765 43217', status: 'active', initials: 'AR', lastActive: '10m ago' },
];

const statusDot = (status) => {
  const colors = { active: '#22c55e', away: '#f59e0b', offline: '#525252' };
  return { width: 8, height: 8, borderRadius: '50%', background: colors[status] || '#525252', display: 'inline-block' };
};

const roleGradient = (role) => {
  const g = {
    Admin: ['#f59e0b', '#d97706'],
    Manager: ['#22c55e', '#16a34a'],
    Analyst: ['#3b82f6', '#2563eb'],
  };
  return g[role] || ['#525252', '#404040'];
};

const Team = () => {
  const { showToast: addToast } = useToast();
  const [filter, setFilter] = useState('all');

  const filteredMembers = filter === 'all' ? teamMembers : teamMembers.filter(m => m.role.toLowerCase() === filter);

  const counts = {
    total: teamMembers.length,
    active: teamMembers.filter(m => m.status === 'active').length,
    admins: teamMembers.filter(m => m.role === 'Admin').length,
    managers: teamMembers.filter(m => m.role === 'Manager').length,
  };

  const analystsCount = teamMembers.filter(m => m.role === 'Analyst').length;

  return (
    <div className="team-page" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <p className="page-subtitle" style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>Collaborate, manage roles, and review organization access controls</p>
        </div>
        <button className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 18px', fontSize: 13, borderRadius: 8, background: 'var(--accent)', color: '#0f0f0f', fontWeight: 600, border: 'none', cursor: 'pointer' }} onClick={() => addToast("Invite User Modal Opened", "info")}>
          <UserPlus size={15} /> Invite Member
        </button>
      </div>

      {/* Stats — Bento Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '16px',
      }}>
        {/* Total Members - Span 2 on larger screens */}
        <div style={{
          gridColumn: 'span 2',
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: '12px',
          padding: '24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          position: 'relative',
          overflow: 'hidden'
        }}>
          <div style={{ position: 'absolute', top: 0, left: 0, width: '4px', height: '100%', background: 'var(--accent)' }} />
          <div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>Total Workspace Members</div>
            <div style={{ fontSize: '40px', fontWeight: 800, color: 'var(--text-primary)', marginTop: '12px', lineHeight: 1 }}>{counts.total}</div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px', textAlign: 'right' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--accent-green)' }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent-green)' }} />
              <span>{counts.active} Active Online</span>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              {teamMembers.filter(m => m.status === 'away').length} Away &bull; {teamMembers.filter(m => m.status === 'offline').length} Offline
            </div>
          </div>
        </div>

        {/* Admins Card */}
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: '12px',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          minHeight: '120px'
        }}>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>Administrators</div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginTop: '12px' }}>
            <div style={{ fontSize: '36px', fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1 }}>{counts.admins}</div>
            <span style={{ fontSize: '12px', color: 'var(--accent)', fontWeight: 500 }}>Full Control</span>
          </div>
        </div>

        {/* Managers Card */}
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: '12px',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          minHeight: '120px'
        }}>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>Managers & Analysts</div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginTop: '12px' }}>
            <div style={{ fontSize: '36px', fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1 }}>{counts.managers + analystsCount}</div>
            <span style={{ fontSize: '12px', color: 'var(--accent-blue)', fontWeight: 500 }}>{counts.managers} Mgr / {analystsCount} Anl</span>
          </div>
        </div>
      </div>

      {/* Filter pills */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border)', paddingBottom: '12px', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          {['All', 'Admin', 'Manager', 'Analyst'].map((item) => {
            const isActive = filter === item.toLowerCase();
            return (
              <button
                key={item}
                onClick={() => setFilter(item.toLowerCase())}
                style={{
                  padding: '6px 14px',
                  borderRadius: '6px',
                  fontSize: '12px',
                  fontWeight: 600,
                  background: isActive ? 'var(--accent)' : 'transparent',
                  color: isActive ? '#0f0f0f' : 'var(--text-secondary)',
                  border: isActive ? 'none' : '1px solid var(--border)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  fontFamily: 'inherit',
                }}
              >
                {item}
              </button>
            );
          })}
        </div>
        <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
          Showing {filteredMembers.length} of {teamMembers.length} team members
        </div>
      </div>

      {/* Team Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
        {filteredMembers.map((member) => {
          const [c1, c2] = roleGradient(member.role);
          return (
            <div
              key={member.id}
              style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border)',
                borderRadius: '12px',
                padding: '20px',
                transition: 'transform 0.2s, border-color 0.2s, box-shadow 0.2s',
                position: 'relative',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                gap: '16px'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.borderColor = 'rgba(245, 158, 11, 0.2)';
                e.currentTarget.style.boxShadow = 'var(--shadow-md)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.borderColor = 'var(--border)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
                <div style={{ width: 44, height: 44, borderRadius: '8px', background: `linear-gradient(135deg, ${c1}, ${c2})`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#0f0f0f', fontWeight: 700, fontSize: 14, flexShrink: 0 }}>
                  {member.initials}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{member.name}</h3>
                    <span style={statusDot(member.status)} />
                  </div>
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '2px 0 0 0' }}>{member.role} &bull; {member.department}</p>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '12px 14px', background: 'var(--bg-muted)', borderRadius: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '12px', color: 'var(--text-primary)' }}>
                  <Mail size={13} style={{ color: 'var(--accent)', flexShrink: 0 }} />
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{member.email}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '12px', color: 'var(--text-primary)' }}>
                  <Phone size={13} style={{ color: 'var(--accent-green)', flexShrink: 0 }} />
                  <span>{member.phone}</span>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-secondary)', borderTop: '1px solid var(--border)', paddingTop: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Activity size={12} />
                  <span>Active {member.lastActive}</span>
                </div>
                <button style={{ fontSize: '12px', fontWeight: 600, color: 'var(--accent)', background: 'none', border: 'none', cursor: 'pointer', padding: 0, fontFamily: 'inherit' }}>View Profile</button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Team;
