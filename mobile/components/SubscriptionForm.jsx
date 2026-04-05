import { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Switch,
  ActivityIndicator,
} from 'react-native';
import { EVENT_TYPES, SEVERITIES } from '../utils/helpers';

const DEFAULT_FORM = {
  name: '',
  event_types: [],
  min_severity: '',
  keywords: [],
  notify_email: true,
  notify_push: true,
};

export default function SubscriptionForm({ initial, onSave, onCancel, saving }) {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [keywordInput, setKeywordInput] = useState('');

  useEffect(() => {
    if (initial) {
      setForm({
        name: initial.name || '',
        event_types: initial.event_types || [],
        min_severity: initial.min_severity || '',
        keywords: initial.keywords || [],
        notify_email: initial.notify_email !== false,
        notify_push: initial.notify_push !== false,
      });
    } else {
      setForm(DEFAULT_FORM);
      setKeywordInput('');
    }
  }, [initial]);

  function toggleType(value) {
    setForm((f) => ({
      ...f,
      event_types: f.event_types.includes(value)
        ? f.event_types.filter((t) => t !== value)
        : [...f.event_types, value],
    }));
  }

  function addKeyword() {
    const kw = keywordInput.trim();
    if (kw && !form.keywords.includes(kw)) {
      setForm((f) => ({ ...f, keywords: [...f.keywords, kw] }));
    }
    setKeywordInput('');
  }

  function removeKeyword(kw) {
    setForm((f) => ({ ...f, keywords: f.keywords.filter((k) => k !== kw) }));
  }

  function handleSave() {
    onSave(form);
  }

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      keyboardShouldPersistTaps="handled"
      showsVerticalScrollIndicator={false}
    >
      {/* Name */}
      <View style={styles.fieldGroup}>
        <Text style={styles.label}>Subscription Name *</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g. European Earthquakes"
          placeholderTextColor="#555570"
          value={form.name}
          onChangeText={(t) => setForm((f) => ({ ...f, name: t }))}
        />
      </View>

      {/* Event Types */}
      <View style={styles.fieldGroup}>
        <Text style={styles.label}>Event Types (select all that apply)</Text>
        <View style={styles.checkboxGrid}>
          {EVENT_TYPES.map((opt) => {
            const checked = form.event_types.includes(opt.value);
            return (
              <TouchableOpacity
                key={opt.value}
                style={[styles.checkboxItem, checked && styles.checkboxChecked]}
                onPress={() => toggleType(opt.value)}
                activeOpacity={0.75}
              >
                <View style={[styles.checkbox, checked && styles.checkboxActive]}>
                  {checked && <Text style={styles.checkmark}>✓</Text>}
                </View>
                <Text style={[styles.checkboxLabel, checked && styles.checkboxLabelActive]}>
                  {opt.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      {/* Minimum Severity */}
      <View style={styles.fieldGroup}>
        <Text style={styles.label}>Minimum Severity</Text>
        <View style={styles.severityGrid}>
          {[{ value: '', label: 'All' }, ...SEVERITIES].map((opt) => {
            const active = form.min_severity === opt.value;
            return (
              <TouchableOpacity
                key={opt.value || 'all'}
                style={[styles.sevChip, active && styles.sevChipActive]}
                onPress={() => setForm((f) => ({ ...f, min_severity: opt.value }))}
                activeOpacity={0.75}
              >
                <Text style={[styles.sevChipText, active && styles.sevChipTextActive]}>
                  {opt.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      {/* Keywords */}
      <View style={styles.fieldGroup}>
        <Text style={styles.label}>Keywords (optional)</Text>
        <View style={styles.keywordInputRow}>
          <TextInput
            style={[styles.input, styles.keywordInput]}
            placeholder="Add keyword…"
            placeholderTextColor="#555570"
            value={keywordInput}
            onChangeText={setKeywordInput}
            onSubmitEditing={addKeyword}
            returnKeyType="done"
          />
          <TouchableOpacity style={styles.addKeywordBtn} onPress={addKeyword}>
            <Text style={styles.addKeywordText}>Add</Text>
          </TouchableOpacity>
        </View>
        {form.keywords.length > 0 && (
          <View style={styles.keywordList}>
            {form.keywords.map((kw) => (
              <View key={kw} style={styles.keywordChip}>
                <Text style={styles.keywordText}>{kw}</Text>
                <TouchableOpacity onPress={() => removeKeyword(kw)} style={styles.keywordRemove}>
                  <Text style={styles.keywordRemoveText}>✕</Text>
                </TouchableOpacity>
              </View>
            ))}
          </View>
        )}
      </View>

      {/* Notification toggles */}
      <View style={styles.fieldGroup}>
        <Text style={styles.label}>Notifications</Text>
        <View style={styles.toggleRow}>
          <Text style={styles.toggleLabel}>📧 Email Notifications</Text>
          <Switch
            value={form.notify_email}
            onValueChange={(v) => setForm((f) => ({ ...f, notify_email: v }))}
            trackColor={{ false: '#2a2a3e', true: '#2a4a7f' }}
            thumbColor={form.notify_email ? '#4f8ef7' : '#555570'}
          />
        </View>
        <View style={styles.toggleRow}>
          <Text style={styles.toggleLabel}>🔔 Push Notifications</Text>
          <Switch
            value={form.notify_push}
            onValueChange={(v) => setForm((f) => ({ ...f, notify_push: v }))}
            trackColor={{ false: '#2a2a3e', true: '#2a4a7f' }}
            thumbColor={form.notify_push ? '#4f8ef7' : '#555570'}
          />
        </View>
      </View>

      {/* Actions */}
      <View style={styles.actions}>
        <TouchableOpacity
          style={styles.cancelBtn}
          onPress={onCancel}
          disabled={saving}
          activeOpacity={0.8}
        >
          <Text style={styles.cancelText}>Cancel</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.saveBtn, (!form.name.trim() || saving) && styles.saveBtnDisabled]}
          onPress={handleSave}
          disabled={!form.name.trim() || saving}
          activeOpacity={0.8}
        >
          {saving ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <Text style={styles.saveText}>Save</Text>
          )}
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, paddingBottom: 40 },
  fieldGroup: { marginBottom: 20 },
  label: { color: '#aaaacc', fontSize: 13, fontWeight: '600', marginBottom: 10 },
  input: {
    backgroundColor: '#0f0f1a',
    borderWidth: 1,
    borderColor: '#2a2a3e',
    borderRadius: 10,
    padding: 12,
    color: '#ffffff',
    fontSize: 14,
  },
  checkboxGrid: { gap: 6 },
  checkboxItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#2a2a3e',
    backgroundColor: '#0f0f1a',
    gap: 10,
  },
  checkboxChecked: {
    borderColor: '#4f8ef7',
    backgroundColor: '#1a2a3e',
  },
  checkbox: {
    width: 18,
    height: 18,
    borderRadius: 4,
    borderWidth: 2,
    borderColor: '#555570',
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkboxActive: { borderColor: '#4f8ef7', backgroundColor: '#4f8ef7' },
  checkmark: { color: '#fff', fontSize: 11, fontWeight: 'bold' },
  checkboxLabel: { color: '#8888aa', fontSize: 13 },
  checkboxLabelActive: { color: '#ffffff', fontWeight: '600' },
  severityGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  sevChip: {
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 20,
    backgroundColor: '#0f0f1a',
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  sevChipActive: { backgroundColor: '#2a4a7f', borderColor: '#4f8ef7' },
  sevChipText: { color: '#8888aa', fontSize: 13, fontWeight: '600' },
  sevChipTextActive: { color: '#ffffff' },
  keywordInputRow: {
    flexDirection: 'row',
    gap: 8,
    alignItems: 'center',
  },
  keywordInput: { flex: 1 },
  addKeywordBtn: {
    backgroundColor: '#4f8ef7',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 10,
  },
  addKeywordText: { color: '#fff', fontWeight: '600', fontSize: 14 },
  keywordList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 10,
  },
  keywordChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1a2a3e',
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 5,
    gap: 6,
    borderWidth: 1,
    borderColor: '#4f8ef7',
  },
  keywordText: { color: '#4f8ef7', fontSize: 12, fontWeight: '600' },
  keywordRemove: { padding: 2 },
  keywordRemoveText: { color: '#8888aa', fontSize: 12 },
  toggleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#2a2a3e',
  },
  toggleLabel: { color: '#ccccee', fontSize: 14 },
  actions: { flexDirection: 'row', gap: 12, marginTop: 8 },
  cancelBtn: {
    flex: 1,
    padding: 14,
    borderRadius: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  cancelText: { color: '#8888aa', fontSize: 15, fontWeight: '600' },
  saveBtn: {
    flex: 2,
    padding: 14,
    borderRadius: 10,
    alignItems: 'center',
    backgroundColor: '#4f8ef7',
  },
  saveBtnDisabled: { opacity: 0.5 },
  saveText: { color: '#fff', fontSize: 15, fontWeight: 'bold' },
});
