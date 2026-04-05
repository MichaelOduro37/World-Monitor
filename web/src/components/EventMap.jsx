import React, { useMemo } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import { getSeverityColor, getEventTypeIcon, formatDateTime } from '../utils/helpers'

const popupStyle = {
  minWidth: '200px',
  color: '#1e293b',
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
}

const popupTitle = {
  fontWeight: 700,
  fontSize: '14px',
  marginBottom: '6px',
  lineHeight: 1.3
}

const popupMeta = { fontSize: '12px', marginBottom: '3px', color: '#475569' }
const popupLink = { fontSize: '12px', color: '#2563eb' }

export default function EventMap({ events }) {
  const validEvents = useMemo(
    () =>
      (events || []).filter(
        (e) => e.latitude != null && e.longitude != null &&
               !isNaN(parseFloat(e.latitude)) && !isNaN(parseFloat(e.longitude))
      ),
    [events]
  )

  return (
    <MapContainer
      center={[20, 0]}
      zoom={2}
      minZoom={2}
      style={{ height: '100%', width: '100%', background: '#0f172a' }}
      worldCopyJump
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        maxZoom={19}
      />
      {validEvents.map((event) => {
        const color = getSeverityColor(event.severity)
        const radius = 6 + (parseFloat(event.severity) || 0) * 14
        return (
          <CircleMarker
            key={event.id}
            center={[parseFloat(event.latitude), parseFloat(event.longitude)]}
            radius={radius}
            pathOptions={{
              fillColor: color,
              color: color,
              fillOpacity: 0.75,
              weight: 1.5
            }}
          >
            <Popup>
              <div style={popupStyle}>
                <div style={popupTitle}>
                  {getEventTypeIcon(event.type)} {event.title || 'Event'}
                </div>
                <div style={popupMeta}>
                  <strong>Type:</strong> {event.type}
                </div>
                <div style={popupMeta}>
                  <strong>Severity:</strong>{' '}
                  <span style={{ color }}>
                    {((parseFloat(event.severity) || 0) * 100).toFixed(0)}%
                  </span>
                </div>
                <div style={popupMeta}>
                  <strong>Time:</strong> {formatDateTime(event.occurred_at || event.created_at)}
                </div>
                {(event.country || event.region) && (
                  <div style={popupMeta}>
                    <strong>Location:</strong>{' '}
                    {[event.country, event.region].filter(Boolean).join(', ')}
                  </div>
                )}
                {event.summary && (
                  <div style={{ ...popupMeta, marginTop: '6px', fontStyle: 'italic' }}>
                    {event.summary.slice(0, 120)}
                    {event.summary.length > 120 ? '…' : ''}
                  </div>
                )}
                {event.source_url && (
                  <a
                    href={event.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={popupLink}
                  >
                    View source ↗
                  </a>
                )}
              </div>
            </Popup>
          </CircleMarker>
        )
      })}
    </MapContainer>
  )
}
