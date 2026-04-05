import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import useAuthStore from '../store/authStore'

const styles = {
  root: {
    minHeight: '100vh', display: 'flex', alignItems: 'center',
    justifyContent: 'center', background: '#0f172a'
  },
  card: {
    width: '100%', maxWidth: '380px',
    background: '#1e293b', borderRadius: '12px',
    padding: '36px 32px', border: '1px solid #334155'
  },
  logo: { textAlign: 'center', fontSize: '32px', marginBottom: '6px' },
  heading: { textAlign: 'center', fontSize: '20px', fontWeight: 700, color: '#f1f5f9', marginBottom: '4px' },
  sub: { textAlign: 'center', fontSize: '13px', color: '#64748b', marginBottom: '28px' },
  fieldGroup: { marginBottom: '16px' },
  label: { display: 'block', fontSize: '13px', color: '#94a3b8', marginBottom: '6px' },
  input: {
    width: '100%', padding: '10px 14px',
    background: '#0f172a', border: '1px solid #475569',
    borderRadius: '6px', color: '#e2e8f0', fontSize: '14px',
    outline: 'none'
  },
  submitBtn: {
    width: '100%', padding: '11px',
    background: '#38bdf8', border: 'none',
    borderRadius: '6px', color: '#0f172a',
    cursor: 'pointer', fontSize: '15px', fontWeight: 700,
    marginTop: '6px'
  },
  error: {
    background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)',
    borderRadius: '6px', padding: '10px 12px',
    color: '#fca5a5', fontSize: '13px', marginBottom: '16px'
  },
  footer: { textAlign: 'center', marginTop: '20px', fontSize: '13px', color: '#64748b' },
  link: { color: '#38bdf8', textDecoration: 'none' }
}

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const login = useAuthStore((s) => s.login)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (!email || !password) { setError('Email and password are required'); return }
    setLoading(true)
    try {
      await login(email, password)
      navigate('/map')
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={styles.root}>
      <div style={styles.card}>
        <div style={styles.logo}>🌐</div>
        <div style={styles.heading}>World Monitor</div>
        <div style={styles.sub}>Sign in to your account</div>
        {error && <div style={styles.error}>{error}</div>}
        <form onSubmit={handleSubmit}>
          <div style={styles.fieldGroup}>
            <label style={styles.label}>Email</label>
            <input
              style={styles.input}
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
            />
          </div>
          <div style={styles.fieldGroup}>
            <label style={styles.label}>Password</label>
            <input
              style={styles.input}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
            />
          </div>
          <button type="submit" style={styles.submitBtn} disabled={loading}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
        <div style={styles.footer}>
          No account?{' '}
          <Link to="/register" style={styles.link}>
            Create one
          </Link>
        </div>
      </div>
    </div>
  )
}
