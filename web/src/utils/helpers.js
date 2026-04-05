export function formatDateTime(iso) {
  if (!iso) return '—'
  try {
    const d = new Date(iso)
    return d.toLocaleString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return iso
  }
}

export function getSeverityColor(severity) {
  const s = parseFloat(severity) || 0
  if (s >= 0.75) return '#ef4444' // red – critical
  if (s >= 0.5) return '#f97316'  // orange – high
  if (s >= 0.25) return '#eab308' // yellow – medium
  return '#22c55e'                // green – low
}

export function getSeverityLabel(severity) {
  const s = parseFloat(severity) || 0
  if (s >= 0.75) return 'Critical'
  if (s >= 0.5) return 'High'
  if (s >= 0.25) return 'Medium'
  return 'Low'
}

export function getEventTypeIcon(type) {
  const icons = {
    earthquake: '🌍',
    storm: '🌪️',
    flood: '🌊',
    conflict: '⚔️',
    outbreak: '🦠',
    wildfire: '🔥',
    tsunami: '🌊',
    volcano: '🌋',
    news: '📰',
    other: '📡'
  }
  return icons[type] || '📡'
}

export function truncate(text, maxLen = 120) {
  if (!text) return ''
  return text.length > maxLen ? text.slice(0, maxLen) + '…' : text
}
