import React, { useState } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import useAuthStore from '../store/authStore'
import NotificationBadge from './NotificationBadge'

const NAV_LINKS = [
  { to: '/map', label: '🗺 Map' },
  { to: '/feed', label: '📋 Feed' },
  { to: '/dashboard', label: '📊 Dashboard' },
  { to: '/subscriptions', label: '🔔 Subscriptions' }
]

const styles = {
  root: { display: 'flex', flexDirection: 'column', height: '100vh', background: '#0f172a' },
  nav: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '0 20px',
    height: '56px',
    background: '#1e293b',
    borderBottom: '1px solid #334155',
    flexShrink: 0
  },
  logo: { fontWeight: 700, fontSize: '18px', color: '#38bdf8', marginRight: '16px', whiteSpace: 'nowrap' },
  links: { display: 'flex', gap: '4px', flex: 1 },
  link: {
    padding: '6px 14px',
    borderRadius: '6px',
    textDecoration: 'none',
    color: '#94a3b8',
    fontSize: '14px',
    fontWeight: 500,
    transition: 'all 0.15s'
  },
  activeLink: {
    padding: '6px 14px',
    borderRadius: '6px',
    textDecoration: 'none',
    color: '#38bdf8',
    fontSize: '14px',
    fontWeight: 500,
    background: 'rgba(56,189,248,0.12)'
  },
  right: { display: 'flex', alignItems: 'center', gap: '12px', marginLeft: 'auto' },
  email: { fontSize: '13px', color: '#64748b' },
  logoutBtn: {
    padding: '5px 12px',
    background: 'transparent',
    border: '1px solid #475569',
    borderRadius: '6px',
    color: '#94a3b8',
    cursor: 'pointer',
    fontSize: '13px'
  },
  content: { flex: 1, overflow: 'hidden', position: 'relative' }
}

export default function Layout() {
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div style={styles.root}>
      <nav style={styles.nav}>
        <span style={styles.logo}>🌐 World Monitor</span>
        <div style={styles.links}>
          {NAV_LINKS.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              style={({ isActive }) => (isActive ? styles.activeLink : styles.link)}
            >
              {label}
            </NavLink>
          ))}
        </div>
        <div style={styles.right}>
          <NotificationBadge />
          {user && <span style={styles.email}>{user.email || user.full_name || 'User'}</span>}
          <button style={styles.logoutBtn} onClick={handleLogout}>
            Sign out
          </button>
        </div>
      </nav>
      <div style={styles.content}>
        <Outlet />
      </div>
    </div>
  )
}
