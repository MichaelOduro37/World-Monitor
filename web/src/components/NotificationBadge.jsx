import React, { useState } from 'react'

const styles = {
  wrap: { position: 'relative', display: 'inline-block' },
  btn: {
    background: 'transparent',
    border: '1px solid #475569',
    borderRadius: '6px',
    color: '#94a3b8',
    cursor: 'pointer',
    fontSize: '18px',
    padding: '3px 8px',
    lineHeight: 1
  },
  badge: {
    position: 'absolute',
    top: '-4px',
    right: '-4px',
    width: '10px',
    height: '10px',
    background: '#38bdf8',
    borderRadius: '50%',
    border: '2px solid #1e293b'
  },
  tooltip: {
    position: 'absolute',
    top: '110%',
    right: 0,
    background: '#334155',
    border: '1px solid #475569',
    borderRadius: '6px',
    padding: '10px 14px',
    fontSize: '13px',
    color: '#e2e8f0',
    whiteSpace: 'nowrap',
    zIndex: 50
  },
  enableBtn: {
    marginTop: '8px',
    width: '100%',
    padding: '5px 10px',
    background: '#38bdf8',
    border: 'none',
    borderRadius: '4px',
    color: '#0f172a',
    cursor: 'pointer',
    fontSize: '12px',
    fontWeight: 600
  }
}

export default function NotificationBadge() {
  const [open, setOpen] = useState(false)
  const [status, setStatus] = useState(
    'Notification' in window ? Notification.permission : 'unsupported'
  )

  const requestPermission = async () => {
    if (!('Notification' in window)) return
    const result = await Notification.requestPermission()
    setStatus(result)
    setOpen(false)
  }

  const statusLabel = {
    granted: '🔔 Enabled',
    denied: '🔕 Blocked',
    default: '🔕 Not enabled',
    unsupported: '🔕 Unsupported'
  }[status] || '🔔'

  return (
    <div style={styles.wrap}>
      <button style={styles.btn} onClick={() => setOpen((o) => !o)} title="Notifications">
        🔔
      </button>
      {status === 'granted' && <div style={styles.badge} />}
      {open && (
        <div style={styles.tooltip}>
          <div>{statusLabel}</div>
          {status !== 'granted' && status !== 'unsupported' && (
            <button style={styles.enableBtn} onClick={requestPermission}>
              Enable push alerts
            </button>
          )}
        </div>
      )}
    </div>
  )
}
