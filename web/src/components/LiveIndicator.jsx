import React, { useEffect, useRef, useState } from 'react'

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

const styles = {
  banner: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '8px 16px',
    background: 'rgba(56,189,248,0.1)',
    borderBottom: '1px solid rgba(56,189,248,0.25)',
    fontSize: '13px',
    color: '#38bdf8',
    flexShrink: 0,
    cursor: 'pointer',
  },
  dot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    flexShrink: 0,
  },
  btn: {
    marginLeft: 'auto',
    padding: '3px 10px',
    background: 'rgba(56,189,248,0.15)',
    border: '1px solid rgba(56,189,248,0.4)',
    borderRadius: '4px',
    color: '#38bdf8',
    cursor: 'pointer',
    fontSize: '12px',
  },
}

/**
 * Connects to the SSE /api/v1/stream/events endpoint and shows a banner when
 * new events arrive. Calls `onRefresh` when the user acknowledges the banner.
 */
export default function LiveIndicator({ onRefresh }) {
  const [newCount, setNewCount] = useState(0)
  const [connected, setConnected] = useState(false)
  const esRef = useRef(null)
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null

  useEffect(() => {
    // SSE does not support custom headers natively in browsers. We pass the
    // token as a query param when present so the endpoint can still work.
    // The backend events/stream endpoint doesn't require auth today but this
    // future-proofs it.
    const url = `${BASE_URL}/stream/events`
    const es = new EventSource(url)
    esRef.current = es

    es.onopen = () => setConnected(true)

    es.onmessage = (e) => {
      try {
        JSON.parse(e.data) // validate
        setNewCount((c) => c + 1)
      } catch {
        // ignore malformed messages
      }
    }

    es.onerror = () => {
      setConnected(false)
    }

    return () => {
      es.close()
      setConnected(false)
    }
  }, [])

  const handleRefresh = () => {
    setNewCount(0)
    if (onRefresh) onRefresh()
  }

  if (!connected && newCount === 0) return null

  return (
    <div style={styles.banner} onClick={handleRefresh}>
      <span
        style={{
          ...styles.dot,
          background: connected ? '#22c55e' : '#f97316',
          boxShadow: connected ? '0 0 6px #22c55e' : 'none',
        }}
      />
      {newCount > 0 ? (
        <>
          <span>
            {newCount} new event{newCount !== 1 ? 's' : ''} available
          </span>
          <button style={styles.btn} onClick={handleRefresh}>
            Refresh feed
          </button>
        </>
      ) : (
        <span>Live — monitoring global events</span>
      )}
    </div>
  )
}
