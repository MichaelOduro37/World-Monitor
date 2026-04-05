import React, { useEffect, useCallback } from 'react'
import useEventStore from '../store/eventStore'
import EventMap from '../components/EventMap'
import EventFilters from '../components/EventFilters'

const styles = {
  root: { display: 'flex', flexDirection: 'column', height: '100%' },
  mapWrap: { flex: 1, position: 'relative', overflow: 'hidden' },
  badge: {
    position: 'absolute', top: '12px', right: '12px',
    background: 'rgba(30,41,59,0.9)', border: '1px solid #334155',
    borderRadius: '6px', padding: '6px 12px', zIndex: 900,
    fontSize: '13px', color: '#94a3b8'
  },
  count: { color: '#38bdf8', fontWeight: 700 },
  loadingOverlay: {
    position: 'absolute', top: '12px', left: '50%',
    transform: 'translateX(-50%)',
    background: 'rgba(30,41,59,0.9)', borderRadius: '6px',
    padding: '6px 14px', zIndex: 900, fontSize: '13px', color: '#94a3b8'
  },
  errorBanner: {
    position: 'absolute', top: '12px', left: '50%',
    transform: 'translateX(-50%)',
    background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)',
    borderRadius: '6px', padding: '6px 14px',
    zIndex: 900, fontSize: '13px', color: '#fca5a5'
  }
}

export default function MapPage() {
  const { events, total, loading, error, filters, setFilter, fetchEvents } = useEventStore()

  useEffect(() => {
    fetchEvents()
  }, [fetchEvents])

  const handleFiltersChange = useCallback(
    (newFilters) => {
      Object.entries(newFilters).forEach(([k, v]) => setFilter(k, v))
      useEventStore.getState().fetchEvents(newFilters)
    },
    [setFilter]
  )

  return (
    <div style={styles.root}>
      <EventFilters filters={filters} onChange={handleFiltersChange} />
      <div style={styles.mapWrap}>
        <EventMap events={events} />
        {loading && <div style={styles.loadingOverlay}>Loading events…</div>}
        {error && !loading && <div style={styles.errorBanner}>⚠ {error}</div>}
        <div style={styles.badge}>
          <span style={styles.count}>{total}</span> events
        </div>
      </div>
    </div>
  )
}
