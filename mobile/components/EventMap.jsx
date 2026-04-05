import { useRef, useMemo } from 'react';
import { StyleSheet, View } from 'react-native';
import { WebView } from 'react-native-webview';
import { getSeverityColor } from '../utils/helpers';

function buildLeafletHTML(events) {
  const markers = events
    .filter((e) => e.latitude != null && e.longitude != null)
    .map((e) => {
      const color = getSeverityColor(e.severity);
      const title = (e.title || '').replace(/\\/g, '\\\\').replace(/'/g, "\\'");
      const summary = (e.summary || '').replace(/\\/g, '\\\\').replace(/'/g, "\\'").substring(0, 120);
      const severity = e.severity || 'unknown';
      const type = (e.event_type || 'event').replace(/_/g, ' ');
      const country = e.country || '';
      return `
        L.circleMarker([${e.latitude}, ${e.longitude}], {
          radius: 8,
          fillColor: '${color}',
          color: '#ffffff',
          weight: 1.5,
          opacity: 1,
          fillOpacity: 0.85
        }).addTo(map).bindPopup(
          '<div style="font-family:sans-serif;min-width:180px;">' +
          '<b style="color:${color};font-size:12px;text-transform:uppercase;">${type}</b>' +
          '<p style="margin:4px 0;font-size:13px;font-weight:bold;">${title}</p>' +
          '<p style="margin:4px 0;font-size:11px;color:#666;">${summary}${summary.length >= 120 ? '...' : ''}</p>' +
          '<small style="color:#999;">${country} · ${severity}</small>' +
          '</div>'
        );
      `;
    })
    .join('\n');

  return `<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body, #map { width: 100%; height: 100%; background: #0f0f1a; }
    .leaflet-container { background: #1a1a2e; }
    .leaflet-popup-content-wrapper {
      background: #1a1a2e;
      color: #fff;
      border: 1px solid #2a2a3e;
      border-radius: 8px;
    }
    .leaflet-popup-tip { background: #1a1a2e; }
    .leaflet-popup-close-button { color: #8888aa !important; }
  </style>
</head>
<body>
  <div id="map"></div>
  <script>
    var map = L.map('map', {
      center: [20, 0],
      zoom: 2,
      zoomControl: true,
      attributionControl: false
    });

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19
    }).addTo(map);

    ${markers}

    window.addEventListener('message', function(e) {
      try {
        var data = JSON.parse(e.data);
        if (data.type === 'FLY_TO') {
          map.flyTo([data.lat, data.lng], data.zoom || 6);
        }
      } catch(err) {}
    });
  </script>
</body>
</html>`;
}

export default function EventMap({ events = [], onMapReady, style }) {
  const webViewRef = useRef(null);

  const html = useMemo(() => buildLeafletHTML(events), [events]);

  return (
    <View style={[styles.container, style]}>
      <WebView
        ref={webViewRef}
        source={{ html }}
        style={styles.webview}
        originWhitelist={['*']}
        javaScriptEnabled
        domStorageEnabled
        onLoad={onMapReady}
        startInLoadingState={false}
        scrollEnabled={false}
        bounces={false}
        showsHorizontalScrollIndicator={false}
        showsVerticalScrollIndicator={false}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f0f1a' },
  webview: { flex: 1, backgroundColor: '#0f0f1a' },
});
