import React, { useState, useEffect } from 'react'

const EVENT_TYPES = [
  'earthquake', 'storm', 'flood', 'conflict', 'outbreak',
  'wildfire', 'tsunami', 'volcano', 'news', 'other'
]

const styles = {
  overlay: {
    position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    zIndex: 1000
  },
  panel: {
    background: '#1e293b', borderRadius: '10px', padding: '24px',
    width: '100%', maxWidth: '520px', maxHeight: '90vh',
    overflowY: 'auto', border: '1px solid #334155'
  },
  title: { fontSize: '18px', fontWeight: 700, color: '#f1f5f9', marginBottom: '20px' },
  fieldGroup: { marginBottom: '16px' },
  label: { display: 'block', fontSize: '13px', color: '#94a3b8', marginBottom: '6px', fontWeight: 500 },
  input: {
    width: '100%', padding: '8px 12px', background: '#0f172a',
    border: '1px solid #475569', borderRadius: '6px', color: '#e2e8f0', fontSize: '14px'
  },
  checkboxGrid: { display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '6px' },
  checkboxLabel: {
    display: 'flex', alignItems: 'center', gap: '8px',
    fontSize: '13px', color: '#94a3b8', cursor: 'pointer', padding: '4px'
  },
  sliderWrap: { display: 'flex', alignItems: 'center', gap: '10px' },
  slider: { flex: 1, accentColor: '#38bdf8' },
  sliderVal: { fontSize: '13px', color: '#38bdf8', width: '36px' },
  geoSection: {
    padding: '12px', background: '#0f172a', borderRadius: '6px',
    border: '1px solid #334155', marginBottom: '16px'
  },
  geoTitle: { fontSize: '12px', color: '#64748b', fontWeight: 600, marginBottom: '10px', textTransform: 'uppercase' },
  geoGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' },
  actions: { display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '20px' },
  cancelBtn: {
    padding: '8px 18px', background: 'transparent',
    border: '1px solid #475569', borderRadius: '6px',
    color: '#94a3b8', cursor: 'pointer', fontSize: '14px'
  },
  saveBtn: {
    padding: '8px 18px', background: '#38bdf8',
    border: 'none', borderRadius: '6px',
    color: '#0f172a', cursor: 'pointer', fontSize: '14px', fontWeight: 600
  },
  error: { color: '#ef4444', fontSize: '13px', marginBottom: '12px' }
}

const DEFAULT_FORM = {
  name: '',
  event_types: [],
  min_severity: 0,
  keywords: '',
  notify_email: true,
  notify_webpush: false,
  geo_lat: '',
  geo_lon: '',
  geo_radius_km: ''
}

export default function SubscriptionForm({ initial, onSave, onCancel }) {
  const [form, setForm] = useState({ ...DEFAULT_FORM, ...(initial || {}) })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (initial) {
      setForm({
        ...DEFAULT_FORM,
        ...initial,
        keywords: Array.isArray(initial.keywords)
          ? initial.keywords.join(', ')
          : initial.keywords || '',
        geo_lat: initial.geo_fence?.lat ?? '',
        geo_lon: initial.geo_fence?.lon ?? '',
        geo_radius_km: initial.geo_fence?.radius_km ?? ''
      })
    }
  }, [initial])

  const toggleType = (type) => {
    setForm((f) => ({
      ...f,
      event_types: f.event_types.includes(type)
        ? f.event_types.filter((t) => t !== type)
        : [...f.event_types, type]
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (!form.name.trim()) { setError('Name is required'); return }
    setSaving(true)
    try {
      const payload = {
        name: form.name.trim(),
        event_types: form.event_types,
        min_severity: form.min_severity,
        keywords: form.keywords
          ? form.keywords.split(',').map((k) => k.trim()).filter(Boolean)
          : [],
        notify_email: form.notify_email,
        notify_webpush: form.notify_webpush
      }
      if (form.geo_lat && form.geo_lon) {
        payload.geo_fence = {
          lat: parseFloat(form.geo_lat),
          lon: parseFloat(form.geo_lon),
          radius_km: form.geo_radius_km ? parseFloat(form.geo_radius_km) : 100
        }
      }
      await onSave(payload)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div style={styles.overlay} onClick={(e) => e.target === e.currentTarget && onCancel()}>
      <div style={styles.panel}>
        <div style={styles.title}>{initial?.id ? 'Edit Subscription' : 'New Subscription'}</div>
        {error && <div style={styles.error}>{error}</div>}
        <form onSubmit={handleSubmit}>
          <div style={styles.fieldGroup}>
            <label style={styles.label}>Name *</label>
            <input
              style={styles.input}
              type="text"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              placeholder="My subscription"
            />
          </div>

          <div style={styles.fieldGroup}>
            <label style={styles.label}>Event Types</label>
            <div style={styles.checkboxGrid}>
              {EVENT_TYPES.map((type) => (
                <label key={type} style={styles.checkboxLabel}>
                  <input
                    type="checkbox"
                    checked={form.event_types.includes(type)}
                    onChange={() => toggleType(type)}
                  />
                  {type}
                </label>
              ))}
            </div>
          </div>

          <div style={styles.fieldGroup}>
            <label style={styles.label}>Min Severity: {(form.min_severity * 100).toFixed(0)}%</label>
            <div style={styles.sliderWrap}>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                style={styles.slider}
                value={form.min_severity}
                onChange={(e) => setForm((f) => ({ ...f, min_severity: parseFloat(e.target.value) }))}
              />
              <span style={styles.sliderVal}>{(form.min_severity * 100).toFixed(0)}%</span>
            </div>
          </div>

          <div style={styles.fieldGroup}>
            <label style={styles.label}>Keywords (comma-separated)</label>
            <input
              style={styles.input}
              type="text"
              value={form.keywords}
              onChange={(e) => setForm((f) => ({ ...f, keywords: e.target.value }))}
              placeholder="flood, earthquake, …"
            />
          </div>

          <div style={styles.fieldGroup}>
            <label style={styles.label}>Notifications</label>
            <label style={{ ...styles.checkboxLabel, marginBottom: '6px' }}>
              <input
                type="checkbox"
                checked={form.notify_email}
                onChange={(e) => setForm((f) => ({ ...f, notify_email: e.target.checked }))}
              />
              Email notifications
            </label>
            <label style={styles.checkboxLabel}>
              <input
                type="checkbox"
                checked={form.notify_webpush}
                onChange={(e) => setForm((f) => ({ ...f, notify_webpush: e.target.checked }))}
              />
              Web Push notifications
            </label>
          </div>

          <div style={styles.geoSection}>
            <div style={styles.geoTitle}>Geo-fence (optional)</div>
            <div style={styles.geoGrid}>
              <div>
                <label style={styles.label}>Latitude</label>
                <input
                  style={styles.input}
                  type="number"
                  step="any"
                  value={form.geo_lat}
                  onChange={(e) => setForm((f) => ({ ...f, geo_lat: e.target.value }))}
                  placeholder="e.g. 40.7"
                />
              </div>
              <div>
                <label style={styles.label}>Longitude</label>
                <input
                  style={styles.input}
                  type="number"
                  step="any"
                  value={form.geo_lon}
                  onChange={(e) => setForm((f) => ({ ...f, geo_lon: e.target.value }))}
                  placeholder="e.g. -74.0"
                />
              </div>
              <div>
                <label style={styles.label}>Radius (km)</label>
                <input
                  style={styles.input}
                  type="number"
                  min={1}
                  value={form.geo_radius_km}
                  onChange={(e) => setForm((f) => ({ ...f, geo_radius_km: e.target.value }))}
                  placeholder="e.g. 100"
                />
              </div>
            </div>
          </div>

          <div style={styles.actions}>
            <button type="button" style={styles.cancelBtn} onClick={onCancel}>
              Cancel
            </button>
            <button type="submit" style={styles.saveBtn} disabled={saving}>
              {saving ? 'Saving…' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
