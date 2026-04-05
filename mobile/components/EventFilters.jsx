import { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
} from 'react-native';
import { EVENT_TYPES, SEVERITIES } from '../utils/helpers';

const ALL_OPTION = { value: '', label: 'All Types' };
const SEVERITY_OPTIONS = [
  { value: '', label: 'All' },
  ...SEVERITIES.map((s) => ({ value: s.value, label: s.label })),
];

export default function EventFilters({ filters = {}, onFiltersChange }) {
  const [expandedSeverity, setExpandedSeverity] = useState(false);

  function setType(type) {
    onFiltersChange({ ...filters, event_type: type });
  }

  function setSeverity(severity) {
    onFiltersChange({ ...filters, min_severity: severity });
    setExpandedSeverity(false);
  }

  const typeOptions = [ALL_OPTION, ...EVENT_TYPES];

  return (
    <View style={styles.wrapper}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.row}
      >
        {typeOptions.map((opt) => {
          const active = (filters.event_type || '') === opt.value;
          return (
            <TouchableOpacity
              key={opt.value || 'all'}
              style={[styles.chip, active && styles.chipActive]}
              onPress={() => setType(opt.value)}
              activeOpacity={0.75}
            >
              <Text style={[styles.chipText, active && styles.chipTextActive]}>
                {opt.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>

      <View style={styles.severityRow}>
        <Text style={styles.severityLabel}>Severity:</Text>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.severityChips}
        >
          {SEVERITY_OPTIONS.map((opt) => {
            const active = (filters.min_severity || '') === opt.value;
            return (
              <TouchableOpacity
                key={opt.value || 'all-sev'}
                style={[styles.sevChip, active && styles.sevChipActive]}
                onPress={() => setSeverity(opt.value)}
                activeOpacity={0.75}
              >
                <Text style={[styles.sevChipText, active && styles.sevChipTextActive]}>
                  {opt.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    backgroundColor: '#1a1a2e',
    borderBottomWidth: 1,
    borderBottomColor: '#2a2a3e',
    paddingVertical: 10,
  },
  row: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    gap: 8,
    alignItems: 'center',
  },
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 20,
    backgroundColor: '#0f0f1a',
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  chipActive: {
    backgroundColor: '#4f8ef7',
    borderColor: '#4f8ef7',
  },
  chipText: { color: '#8888aa', fontSize: 13, fontWeight: '600' },
  chipTextActive: { color: '#ffffff' },
  severityRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    marginTop: 8,
  },
  severityLabel: {
    color: '#8888aa',
    fontSize: 12,
    fontWeight: '600',
    marginRight: 8,
    width: 60,
  },
  severityChips: {
    flexDirection: 'row',
    gap: 6,
    alignItems: 'center',
  },
  sevChip: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    backgroundColor: '#0f0f1a',
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  sevChipActive: {
    backgroundColor: '#2a4a7f',
    borderColor: '#4f8ef7',
  },
  sevChipText: { color: '#8888aa', fontSize: 12, fontWeight: '600' },
  sevChipTextActive: { color: '#ffffff' },
});
