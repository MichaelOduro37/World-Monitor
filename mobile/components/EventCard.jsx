import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { formatDistanceToNow } from 'date-fns';
import { getSeverityColor, getEventTypeLabel } from '../utils/helpers';

export default function EventCard({ event }) {
  const router = useRouter();

  const severityColor = getSeverityColor(event.severity);
  const timeAgo = event.published_at
    ? formatDistanceToNow(new Date(event.published_at), { addSuffix: true })
    : 'Unknown time';

  function handlePress() {
    // Navigate to event detail if route exists, else no-op
    router.push({ pathname: '/event/[id]', params: { id: event.id } });
  }

  return (
    <TouchableOpacity
      style={styles.card}
      onPress={handlePress}
      activeOpacity={0.85}
    >
      <View style={[styles.severityBar, { backgroundColor: severityColor }]} />
      <View style={styles.content}>
        <View style={styles.topRow}>
          <View style={[styles.typeBadge, { backgroundColor: severityColor + '22' }]}>
            <Text style={[styles.typeBadgeText, { color: severityColor }]}>
              {getEventTypeLabel(event.event_type)}
            </Text>
          </View>
          <View style={[styles.severityBadge, { backgroundColor: severityColor + '33' }]}>
            <Text style={[styles.severityText, { color: severityColor }]}>
              {event.severity
                ? event.severity.charAt(0).toUpperCase() + event.severity.slice(1)
                : 'Unknown'}
            </Text>
          </View>
        </View>

        <Text style={styles.title} numberOfLines={2}>
          {event.title}
        </Text>

        {event.summary ? (
          <Text style={styles.summary} numberOfLines={2}>
            {event.summary}
          </Text>
        ) : null}

        <View style={styles.metaRow}>
          {event.country ? (
            <View style={styles.metaItem}>
              <Text style={styles.metaEmoji}>📍</Text>
              <Text style={styles.metaText}>{event.country}</Text>
            </View>
          ) : null}
          <View style={styles.metaItem}>
            <Text style={styles.metaEmoji}>🕒</Text>
            <Text style={styles.metaText}>{timeAgo}</Text>
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    marginBottom: 12,
    flexDirection: 'row',
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#2a2a3e',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 3,
  },
  severityBar: {
    width: 5,
    borderTopLeftRadius: 12,
    borderBottomLeftRadius: 12,
  },
  content: {
    flex: 1,
    padding: 14,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
    flexWrap: 'wrap',
  },
  typeBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
  },
  typeBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  severityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
  },
  severityText: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  title: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: 'bold',
    lineHeight: 20,
    marginBottom: 6,
  },
  summary: {
    color: '#aaaacc',
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 10,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    flexWrap: 'wrap',
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  metaEmoji: { fontSize: 12 },
  metaText: { color: '#666688', fontSize: 12 },
});
