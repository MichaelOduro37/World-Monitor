import React from 'react'
import { getSeverityColor, getSeverityLabel, getEventTypeIcon, formatDateTime, truncate } from '../utils/helpers'

const styles = {
  card: {
    display: 'flex',
    background: '#1e293b',
    borderRadius: '8px',
    overflow: 'hidden',
    marginBottom: '10px',
    border: '1px solid #334155',
    transition: 'border-color 0.15s'
  },
  bar: { width: '4px', flexShrink: 0 },
  body: { flex: 1, padding: '12px 14px' },
  header: { display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px', flexWrap: 'wrap' },
  typeBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
    padding: '2px 8px',
    borderRadius: '4px',
    fontSize: '11px',
    fontWeight: 600,
    background: '#0f172a',
    color: '#94a3b8',
    textTransform: 'uppercase',
    letterSpacing: '0.05em'
  },
  severityBadge: {
    display: 'inline-block',
    padding: '2px 8px',
    borderRadius: '4px',
    fontSize: '11px',
    fontWeight: 600,
    color: '#fff'
  },
  title: { fontSize: '15px', fontWeight: 600, color: '#f1f5f9', marginBottom: '4px', lineHeight: 1.4 },
  summary: { fontSize: '13px', color: '#94a3b8', lineHeight: 1.5, marginBottom: '8px' },
  footer: { display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' },
  meta: { fontSize: '12px', color: '#64748b' },
  sourceLink: { fontSize: '12px', color: '#38bdf8', textDecoration: 'none', marginLeft: 'auto' }
}

export default function EventCard({ event }) {
  const color = getSeverityColor(event.severity)
  const label = getSeverityLabel(event.severity)
  const icon = getEventTypeIcon(event.type)
  const time = formatDateTime(event.occurred_at || event.created_at)
  const location = [event.country, event.region].filter(Boolean).join(', ')

  return (
    <div style={styles.card}>
      <div style={{ ...styles.bar, background: color }} />
      <div style={styles.body}>
        <div style={styles.header}>
          <span style={styles.typeBadge}>
            {icon} {event.type || 'unknown'}
          </span>
          <span style={{ ...styles.severityBadge, background: color }}>
            {label} ({((event.severity ?? 0) * 100).toFixed(0)}%)
          </span>
          {location && <span style={styles.meta}>📍 {location}</span>}
        </div>
        <div style={styles.title}>{event.title || 'Untitled Event'}</div>
        {event.summary && (
          <div style={styles.summary}>{truncate(event.summary, 160)}</div>
        )}
        <div style={styles.footer}>
          <span style={styles.meta}>🕐 {time}</span>
          {event.source_url && (
            <a
              href={event.source_url}
              target="_blank"
              rel="noopener noreferrer"
              style={styles.sourceLink}
            >
              Source ↗
            </a>
          )}
        </div>
      </div>
    </div>
  )
}
