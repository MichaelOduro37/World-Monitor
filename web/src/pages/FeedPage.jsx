import React, { useEffect, useCallback } from 'react'
import useEventStore from '../store/eventStore'
import EventCard from '../components/EventCard'
import EventFilters from '../components/EventFilters'

const styles = {
  root: { display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' },
  header: {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '10px 16px', background: '#1e293b', borderBottom: '1px solid #334155',
    fontSize: '13px', color: '#64748b', flexShrink: 0
  },
  totalBadge: { color: '#38bdf8', fontWeight: 700 },
  list: { flex: 1, overflowY: 'auto', padding: '16px' },
  loadMoreBtn: {
    display: 'block', width: '100%', padding: '11px',
    background: 'transparent', border: '1px solid #475569',
    borderRadius: '6px', color: '#94a3b8', cursor: 'pointer',
    fontSize: '14px', marginTop: '8px'
  },
  error: {
    margin: '16px', padding: '12px', borderRadius: '6px',
    background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)',
    color: '#fca5a5', fontSize: '13px'
  },
  empty: { textAlign: 'center', padding: '60px 20px', color: '#475569', fontSize: '15px' },
  spinner: { textAlign: 'center', padding: '30px', color: '#64748b', fontSize: '14px' }
}

export default function FeedPage() {
  const { events, total, loading, error, filters, setFilter, fetchEvents, loadMore } =
    useEventStore()

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

  const hasMore = events.length < total

  return (
    <div style={styles.root}>
      <EventFilters filters={filters} onChange={handleFiltersChange} />
      <div style={styles.header}>
        <span>
          Showing <span style={styles.totalBadge}>{events.length}</span> of{' '}
          <span style={styles.totalBadge}>{total}</span> events
        </span>
        {loading && <span>Loading…</span>}
      </div>
      <div style={styles.list}>
        {error && <div style={styles.error}>⚠ {error}</div>}
        {!loading && events.length === 0 && !error && (
          <div style={styles.empty}>No events found. Try adjusting filters.</div>
        )}
        {events.map((event) => (
          <EventCard key={event.id} event={event} />
        ))}
        {loading && events.length === 0 && (
          <div style={styles.spinner}>Loading events…</div>
        )}
        {hasMore && !loading && (
          <button style={styles.loadMoreBtn} onClick={loadMore}>
            Load more ({total - events.length} remaining)
          </button>
        )}
        {loading && events.length > 0 && (
          <div style={styles.spinner}>Loading more…</div>
        )}
      </div>
    </div>
  )
}
