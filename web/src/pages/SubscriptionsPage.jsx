import React, { useEffect, useState, useCallback } from 'react'
import { getSubscriptions, createSubscription, updateSubscription, deleteSubscription } from '../api/client'
import SubscriptionForm from '../components/SubscriptionForm'
import { getEventTypeIcon } from '../utils/helpers'

const styles = {
  root: { height: '100%', overflowY: 'auto', padding: '24px' },
  topBar: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' },
  pageTitle: { fontSize: '20px', fontWeight: 700, color: '#f1f5f9' },
  addBtn: {
    padding: '8px 18px', background: '#38bdf8',
    border: 'none', borderRadius: '6px',
    color: '#0f172a', cursor: 'pointer', fontSize: '14px', fontWeight: 600
  },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' },
  card: {
    background: '#1e293b', border: '1px solid #334155',
    borderRadius: '10px', padding: '18px'
  },
  cardHeader: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' },
  cardTitle: { fontSize: '15px', fontWeight: 700, color: '#f1f5f9' },
  cardActions: { display: 'flex', gap: '6px' },
  editBtn: {
    padding: '4px 10px', background: 'transparent',
    border: '1px solid #475569', borderRadius: '4px',
    color: '#94a3b8', cursor: 'pointer', fontSize: '12px'
  },
  deleteBtn: {
    padding: '4px 10px', background: 'transparent',
    border: '1px solid rgba(239,68,68,0.4)', borderRadius: '4px',
    color: '#fca5a5', cursor: 'pointer', fontSize: '12px'
  },
  row: { display: 'flex', gap: '6px', marginBottom: '8px', flexWrap: 'wrap', alignItems: 'center' },
  rowLabel: { fontSize: '12px', color: '#64748b', width: '90px', flexShrink: 0 },
  typesWrap: { display: 'flex', gap: '4px', flexWrap: 'wrap' },
  typeBadge: {
    padding: '2px 7px', background: '#0f172a',
    borderRadius: '4px', fontSize: '11px', color: '#94a3b8'
  },
  severityBar: { height: '6px', borderRadius: '3px', background: '#38bdf8', marginBottom: '2px' },
  notifBadge: {
    padding: '2px 7px', background: '#0f172a',
    borderRadius: '4px', fontSize: '11px', color: '#38bdf8'
  },
  geoText: { fontSize: '12px', color: '#64748b' },
  error: {
    padding: '12px', borderRadius: '6px', marginBottom: '16px',
    background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)',
    color: '#fca5a5', fontSize: '13px'
  },
  empty: { textAlign: 'center', padding: '60px 20px', color: '#475569', fontSize: '15px' },
  spinner: { textAlign: 'center', padding: '60px', color: '#64748b' }
}

export default function SubscriptionsPage() {
  const [subs, setSubs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editTarget, setEditTarget] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await getSubscriptions()
      setSubs(data.items ?? data ?? [])
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load subscriptions')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleSave = async (payload) => {
    if (editTarget?.id) {
      await updateSubscription(editTarget.id, payload)
    } else {
      await createSubscription(payload)
    }
    setShowForm(false)
    setEditTarget(null)
    await load()
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this subscription?')) return
    try {
      await deleteSubscription(id)
      setSubs((s) => s.filter((x) => x.id !== id))
    } catch (err) {
      setError(err.response?.data?.detail || 'Delete failed')
    }
  }

  const openEdit = (sub) => {
    setEditTarget(sub)
    setShowForm(true)
  }

  const openNew = () => {
    setEditTarget(null)
    setShowForm(true)
  }

  return (
    <div style={styles.root}>
      <div style={styles.topBar}>
        <div style={styles.pageTitle}>🔔 Subscriptions</div>
        <button style={styles.addBtn} onClick={openNew}>+ New subscription</button>
      </div>

      {error && <div style={styles.error}>{error}</div>}

      {loading ? (
        <div style={styles.spinner}>Loading…</div>
      ) : subs.length === 0 ? (
        <div style={styles.empty}>
          No subscriptions yet. Create one to get notified about world events.
        </div>
      ) : (
        <div style={styles.grid}>
          {subs.map((sub) => (
            <div key={sub.id} style={styles.card}>
              <div style={styles.cardHeader}>
                <div style={styles.cardTitle}>{sub.name}</div>
                <div style={styles.cardActions}>
                  <button style={styles.editBtn} onClick={() => openEdit(sub)}>Edit</button>
                  <button style={styles.deleteBtn} onClick={() => handleDelete(sub.id)}>Delete</button>
                </div>
              </div>

              {sub.event_types?.length > 0 && (
                <div style={styles.row}>
                  <span style={styles.rowLabel}>Types</span>
                  <div style={styles.typesWrap}>
                    {sub.event_types.map((t) => (
                      <span key={t} style={styles.typeBadge}>
                        {getEventTypeIcon(t)} {t}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div style={styles.row}>
                <span style={styles.rowLabel}>Min severity</span>
                <div style={{ flex: 1 }}>
                  <div
                    style={{ ...styles.severityBar, width: `${((sub.min_severity ?? 0) * 100).toFixed(0)}%` }}
                  />
                  <span style={{ fontSize: '11px', color: '#64748b' }}>
                    {((sub.min_severity ?? 0) * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              {sub.keywords?.length > 0 && (
                <div style={styles.row}>
                  <span style={styles.rowLabel}>Keywords</span>
                  <span style={{ fontSize: '12px', color: '#94a3b8' }}>
                    {Array.isArray(sub.keywords) ? sub.keywords.join(', ') : sub.keywords}
                  </span>
                </div>
              )}

              <div style={styles.row}>
                <span style={styles.rowLabel}>Notify via</span>
                <div style={{ display: 'flex', gap: '4px' }}>
                  {sub.notify_email && <span style={styles.notifBadge}>📧 Email</span>}
                  {sub.notify_webpush && <span style={styles.notifBadge}>🔔 Push</span>}
                  {!sub.notify_email && !sub.notify_webpush && (
                    <span style={{ ...styles.notifBadge, color: '#64748b' }}>None</span>
                  )}
                </div>
              </div>

              {sub.geo_fence && (
                <div style={styles.row}>
                  <span style={styles.rowLabel}>Geo-fence</span>
                  <span style={styles.geoText}>
                    {sub.geo_fence.lat?.toFixed(2)}, {sub.geo_fence.lon?.toFixed(2)} —{' '}
                    {sub.geo_fence.radius_km} km
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {showForm && (
        <SubscriptionForm
          initial={editTarget}
          onSave={handleSave}
          onCancel={() => { setShowForm(false); setEditTarget(null) }}
        />
      )}
    </div>
  )
}
