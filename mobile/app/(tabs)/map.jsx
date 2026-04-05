import { useEffect, useState } from 'react';
import { View, StyleSheet, ActivityIndicator, Text } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useEventStore } from '../../store/eventStore';
import EventMap from '../../components/EventMap';

export default function MapScreen() {
  const { events, loading, fetchEvents } = useEventStore();
  const [mapReady, setMapReady] = useState(false);

  useEffect(() => {
    if (events.length === 0) {
      fetchEvents();
    }
  }, []);

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      {loading && events.length === 0 && (
        <View style={styles.loaderOverlay}>
          <ActivityIndicator size="large" color="#4f8ef7" />
          <Text style={styles.loadingText}>Loading map data…</Text>
        </View>
      )}
      <EventMap
        events={events}
        onMapReady={() => setMapReady(true)}
        style={styles.map}
      />
      {!mapReady && events.length > 0 && (
        <View style={styles.loaderOverlay} pointerEvents="none">
          <ActivityIndicator size="large" color="#4f8ef7" />
          <Text style={styles.loadingText}>Rendering map…</Text>
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f0f1a' },
  map: { flex: 1 },
  loaderOverlay: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0f0f1a',
    zIndex: 10,
  },
  loadingText: { color: '#8888aa', marginTop: 12, fontSize: 14 },
});
