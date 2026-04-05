import React, { useState, useCallback } from 'react'

const EVENT_TYPES = [
  { value: '', label: 'All Types' },
  { value: 'earthquake', label: '🌍 Earthquake' },
  { value: 'storm', label: '🌪️ Storm' },
  { value: 'flood', label: '🌊 Flood' },
  { value: 'conflict', label: '⚔️ Conflict' },
  { value: 'outbreak', label: '🦠 Outbreak' },
  { value: 'wildfire', label: '🔥 Wildfire' },
  { value: 'tsunami', label: '🌊 Tsunami' },
  { value: 'volcano', label: '🌋 Volcano' },
  { value: 'news', label: '📰 News' },
  { value: 'other', label: '📡 Other' }
]

const styles = {
  bar: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '10px',
    alignItems: 'center',
    padding: '10px 16px',
    background: '#1e293b',
    borderBottom: '1px solid #334155'
  },
  select: {
    padding: '6px 10px',
    background: '#0f172a',
    border: '1px solid #475569',
    borderRadius: '6px',
    color: '#e2e8f0',
    fontSize: '13px',
    cursor: 'pointer'
  },
  input: {
    padding: '6px 10px',
    background: '#0f172a',
    border: '1px solid #475569',
    borderRadius: '6px',
    color: '#e2e8f0',
    fontSize: '13px',
    width: '160px'
  },
  sliderWrap: { display: 'flex', alignItems: 'center', gap: '8px' },
  label: { fontSize: '12px', color: '#64748b', whiteSpace: 'nowrap' },
  slider: { width: '100px', accentColor: '#38bdf8' },
  severityVal: { fontSize: '12px', color: '#38bdf8', width: '30px' },
  resetBtn: {
    padding: '6px 12px',
    background: 'transparent',
    border: '1px solid #475569',
    borderRadius: '6px',
    color: '#94a3b8',
    cursor: 'pointer',
    fontSize: '12px'
  }
}

export default function EventFilters({ filters, onChange }) {
  const update = useCallback(
    (key, value) => {
      onChange({ ...filters, [key]: value })
    },
    [filters, onChange]
  )

  const reset = () =>
    onChange({ type: '', severity_min: 0, q: '', bbox: '', start: '', end: '' })

  return (
    <div style={styles.bar}>
      <select
        style={styles.select}
        value={filters.type || ''}
        onChange={(e) => update('type', e.target.value)}
      >
        {EVENT_TYPES.map((t) => (
          <option key={t.value} value={t.value}>
            {t.label}
          </option>
        ))}
      </select>

      <div style={styles.sliderWrap}>
        <span style={styles.label}>Min severity:</span>
        <input
          type="range"
          min={0}
          max={1}
          step={0.05}
          style={styles.slider}
          value={filters.severity_min ?? 0}
          onChange={(e) => update('severity_min', parseFloat(e.target.value))}
        />
        <span style={styles.severityVal}>{((filters.severity_min ?? 0) * 100).toFixed(0)}%</span>
      </div>

      <input
        style={styles.input}
        type="text"
        placeholder="Search…"
        value={filters.q || ''}
        onChange={(e) => update('q', e.target.value)}
      />

      <div style={styles.sliderWrap}>
        <span style={styles.label}>From:</span>
        <input
          type="date"
          style={{ ...styles.input, width: '140px' }}
          value={filters.start || ''}
          onChange={(e) => update('start', e.target.value)}
        />
      </div>

      <div style={styles.sliderWrap}>
        <span style={styles.label}>To:</span>
        <input
          type="date"
          style={{ ...styles.input, width: '140px' }}
          value={filters.end || ''}
          onChange={(e) => update('end', e.target.value)}
        />
      </div>

      <button style={styles.resetBtn} onClick={reset}>
        Reset
      </button>
    </div>
  )
}
