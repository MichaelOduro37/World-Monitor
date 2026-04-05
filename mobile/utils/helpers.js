export const EVENT_TYPES = [
  { value: 'earthquake', label: '🌋 Earthquake' },
  { value: 'flood', label: '🌊 Flood' },
  { value: 'wildfire', label: '🔥 Wildfire' },
  { value: 'hurricane', label: '🌀 Hurricane' },
  { value: 'tornado', label: '🌪️ Tornado' },
  { value: 'tsunami', label: '🌊 Tsunami' },
  { value: 'drought', label: '☀️ Drought' },
  { value: 'volcano', label: '🌋 Volcano' },
  { value: 'conflict', label: '⚔️ Conflict' },
  { value: 'epidemic', label: '🦠 Epidemic' },
  { value: 'industrial', label: '🏭 Industrial' },
  { value: 'other', label: '⚠️ Other' },
];

export const SEVERITIES = [
  { value: 'low', label: 'Low' },
  { value: 'moderate', label: 'Moderate' },
  { value: 'high', label: 'High' },
  { value: 'critical', label: 'Critical' },
];

const SEVERITY_COLORS = {
  low: '#2ecc71',
  moderate: '#f39c12',
  high: '#e67e22',
  critical: '#e74c3c',
};

export function getSeverityColor(severity) {
  return SEVERITY_COLORS[severity?.toLowerCase()] || '#8888aa';
}

export function getEventTypeLabel(type) {
  const found = EVENT_TYPES.find((t) => t.value === type);
  if (found) return found.label;
  if (!type) return 'Event';
  return type.charAt(0).toUpperCase() + type.slice(1).replace(/_/g, ' ');
}

export function formatRelativeTime(dateString) {
  if (!dateString) return 'Unknown time';
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 30) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

export function truncateText(text, maxLen = 120) {
  if (!text) return '';
  if (text.length <= maxLen) return text;
  return text.substring(0, maxLen).trimEnd() + '…';
}
