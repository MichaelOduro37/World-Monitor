import React, { useEffect, useState, useCallback } from 'react'
import { getStatsSummary, getStatsHotspots } from '../api/client'
import { getSeverityColor, getEventTypeIcon } from '../utils/helpers'

const EVENT_TYPES = [
  'earthquake', 'storm', 'flood', 'conflict', 'outbreak',
  'wildfire', 'tsunami', 'volcano', 'news', 'other'
]

const styles = {
  root: { overflowY: 'auto', padding: '20px', height: '100%', boxSizing: 'border-box' },
  heading: { color: '#f1f5f9', fontSize: '20px', fontWeight: 700, marginBottom: '20px' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '16px', marginBottom: '24px' },
  card: { background: '#1e293b', borderRadius: '10px', border: '1px solid #334155', padding: '18px' },
  cardTitle: { fontSize: '12px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px' },
  bigNum: { fontSize: '36px', fontWeight: 700, color: '#38bdf8' },
  bigNumLabel: { fontSize: '13px', color: '#94a3b8', marginTop: '4px' },
  section: { marginBottom: '24px' },
  sectionTitle: { fontSize: '15px', fontWeight: 600, color: '#94a3b8', marginBottom: '14px', textTransform: 'uppercase', letterSpacing: '0.06em' },
  row: { display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' },
  label: { width: '120px', fontSize: '13px', color: '#cbd5e1', flexShrink: 0, display: 'flex', alignItems: 'center', gap: '6px' },
  barWrap: { flex: 1, height: '10px', background: '#0f172a', borderRadius: '5px', overflow: 'hidden' },
  count: { fontSize: '13px', color: '#64748b', width: '48px', textAlign: 'right', flexShrink: 0 },
  errorBox: { padding: '12px', borderRadius: '6px', background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)', color: '#fca5a5', fontSize: '13px', marginBottom: '16px' },
  hotRow: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid #1e293b', fontSize: '13px' },
  hotLabel: { color: '#cbd5e1' },
  hotCount: { color: '#38bdf8', fontWeight: 600 },
  refreshBtn: { background: 'transparent', border: '1px solid #475569', borderRadius: '6px', color: '#94a3b8', cursor: 'pointer', padding: '5px 14px', fontSize: '13px', marginLeft: '12px' },
  headerRow: { display: 'flex', alignItems: 'center', marginBottom: '20px' },
  lastUpdate: { fontSize: '12px', color: '#475569', marginLeft: '12px' },
  severityRow: { display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' },
}

const SEV_COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
  unknown: '#475569',
}

function StatCard({ title, value, sub }) {
  return (
    <div style={styles.card}>
      <div style={styles.cardTitle}>{title}</div>
      <div style={styles.bigNum}>{value ?? '—'}</div>
      {sub && <div style={styles.bigNumLabel}>{sub}</div>}
    </div>
  )
}

function TypeBar({ type, count, max }) {
  const pct = max > 0 ? (count / max) * 100 : 0
  const icon = getEventTypeIcon(type)
  return (
    <div style={styles.row}>
      <div style={styles.label}>{icon} {type}</div>
      <div style={styles.barWrap}>
        <div style={{ height: '100%', width: `${pct}%`, background: '#38bdf8', borderRadius: '5px', transition: 'width 0.4s' }} />
      </div>
      <div style={styles.count}>{count}</div>
    </div>
  )
}

function SeverityBar({ label, count, max }) {
  const pct = max > 0 ? (count / max) * 100 : 0
  const color = SEV_COLORS[label] || '#475569'
  return (
    <div style={styles.row}>
      <div style={styles.label}>
        <span style={{ display: 'inline-block', width: '10px', height: '10px', borderRadius: '50%', background: color }} />
        {label}
      </div>
      <div style={styles.barWrap}>
        <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: '5px', transition: 'width 0.4s' }} />
      </div>
      <div style={styles.count}>{count}</div>
    </div>
  )
}

export default function DashboardPage() {
  const [summary, setSummary] = useState(null)
  const [hotspots, setHotspots] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [lastUpdate, setLastUpdate] = useState(null)
  const [hotDays, setHotDays] = useState(7)

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [sum, hot] = await Promise.all([
        getStatsSummary(),
        getStatsHotspots(hotDays),
      ])
      setSummary(sum)
      setHotspots(hot)
      setLastUpdate(new Date())
    } catch (err) {
      setError(err.message || 'Failed to load statistics')
    } finally {
      setLoading(false)
    }
  }, [hotDays])

  useEffect(() => {
    loadData()
  }, [loadData])

  // Auto-refresh every 2 minutes
  useEffect(() => {
    const id = setInterval(loadData, 120_000)
    return () => clearInterval(id)
  }, [loadData])

  const byType = summary?.by_type || {}
  const byType24h = summary?.by_type_24h || {}
  const bySeverity = summary?.by_severity || {}
  const maxType = Math.max(...EVENT_TYPES.map((t) => byType[t] || 0), 1)
  const maxSev = Math.max(...Object.values(bySeverity).map(Number), 1)

  return (
    <div style={styles.root}>
      <div style={styles.headerRow}>
        <h2 style={{ ...styles.heading, marginBottom: 0 }}>📊 Dashboard</h2>
        {lastUpdate && (
          <span style={styles.lastUpdate}>
            Last updated: {lastUpdate.toLocaleTimeString()}
          </span>
        )}
        <button style={styles.refreshBtn} onClick={loadData} disabled={loading}>
          {loading ? 'Refreshing…' : '↺ Refresh'}
        </button>
      </div>

      {error && <div style={styles.errorBox}>⚠ {error}</div>}

      {/* Summary cards */}
      <div style={styles.grid}>
        <StatCard title="Total Events" value={summary?.total?.toLocaleString()} sub="all time" />
        <StatCard title="Last 24 Hours" value={summary?.last_24h?.toLocaleString()} sub="new events" />
        <StatCard title="Last 7 Days" value={summary?.last_7d?.toLocaleString()} sub="new events" />
        <StatCard title="Last 30 Days" value={summary?.last_30d?.toLocaleString()} sub="new events" />
        <StatCard
          title="Duplicates Filtered"
          value={summary?.duplicate_count?.toLocaleString()}
          sub="cross-source dedup"
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        {/* Events by type */}
        <div style={styles.section}>
          <div style={styles.sectionTitle}>Events by Type (All Time)</div>
          {EVENT_TYPES.map((t) => (
            <TypeBar key={t} type={t} count={byType[t] || 0} max={maxType} />
          ))}
        </div>

        {/* Events by type – 24h */}
        <div style={styles.section}>
          <div style={styles.sectionTitle}>Events by Type (Last 24h)</div>
          {EVENT_TYPES.map((t) => (
            <TypeBar key={t} type={t} count={byType24h[t] || 0} max={Math.max(...EVENT_TYPES.map((x) => byType24h[x] || 0), 1)} />
          ))}
        </div>
      </div>

      {/* Severity distribution */}
      <div style={styles.section}>
        <div style={styles.sectionTitle}>Severity Distribution</div>
        {['critical', 'high', 'medium', 'low', 'unknown'].map((s) => (
          <SeverityBar key={s} label={s} count={bySeverity[s] || 0} max={maxSev} />
        ))}
      </div>

      {/* Hotspots */}
      {hotspots && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
          <div style={styles.section}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '14px' }}>
              <span style={styles.sectionTitle}>Top Countries</span>
              <select
                value={hotDays}
                onChange={(e) => setHotDays(Number(e.target.value))}
                style={{ background: '#1e293b', border: '1px solid #334155', color: '#94a3b8', borderRadius: '4px', padding: '2px 6px', fontSize: '12px' }}
              >
                {[1, 7, 14, 30].map((d) => (
                  <option key={d} value={d}>Last {d}d</option>
                ))}
              </select>
            </div>
            <div style={styles.card}>
              {hotspots.top_countries.length === 0 ? (
                <div style={{ color: '#475569', fontSize: '13px' }}>No data</div>
              ) : hotspots.top_countries.map((row, i) => (
                <div key={i} style={styles.hotRow}>
                  <span style={styles.hotLabel}>🏳 {row.country}</span>
                  <span style={styles.hotCount}>{row.count}</span>
                </div>
              ))}
            </div>
          </div>
          <div style={styles.section}>
            <div style={styles.sectionTitle}>Top Regions</div>
            <div style={styles.card}>
              {hotspots.top_regions.length === 0 ? (
                <div style={{ color: '#475569', fontSize: '13px' }}>No data</div>
              ) : hotspots.top_regions.map((row, i) => (
                <div key={i} style={styles.hotRow}>
                  <span style={styles.hotLabel}>📍 {row.region}{row.country ? `, ${row.country}` : ''}</span>
                  <span style={styles.hotCount}>{row.count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
