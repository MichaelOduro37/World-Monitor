import { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Modal,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuthStore } from '../../store/authStore';
import { apiClient } from '../../api/client';
import SubscriptionForm from '../../components/SubscriptionForm';

export default function SubscriptionsScreen() {
  const token = useAuthStore((s) => s.token);

  const [subscriptions, setSubscriptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [editTarget, setEditTarget] = useState(null);
  const [saving, setSaving] = useState(false);

  const loadSubscriptions = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get('/api/subscriptions/');
      setSubscriptions(res.data?.results ?? res.data ?? []);
    } catch (err) {
      setError('Failed to load subscriptions.');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    loadSubscriptions();
  }, [loadSubscriptions]);

  async function handleSave(formData) {
    setSaving(true);
    try {
      if (editTarget) {
        const res = await apiClient.put(`/api/subscriptions/${editTarget.id}/`, formData);
        setSubscriptions((prev) =>
          prev.map((s) => (s.id === editTarget.id ? res.data : s))
        );
      } else {
        const res = await apiClient.post('/api/subscriptions/', formData);
        setSubscriptions((prev) => [res.data, ...prev]);
      }
      setModalVisible(false);
      setEditTarget(null);
    } catch (err) {
      Alert.alert('Save Failed', err?.response?.data?.detail || 'Could not save subscription.');
    } finally {
      setSaving(false);
    }
  }

  function handleEdit(sub) {
    setEditTarget(sub);
    setModalVisible(true);
  }

  function handleAdd() {
    setEditTarget(null);
    setModalVisible(true);
  }

  async function handleDelete(sub) {
    Alert.alert(
      'Delete Subscription',
      `Delete "${sub.name}"?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await apiClient.delete(`/api/subscriptions/${sub.id}/`);
              setSubscriptions((prev) => prev.filter((s) => s.id !== sub.id));
            } catch {
              Alert.alert('Error', 'Could not delete subscription.');
            }
          },
        },
      ]
    );
  }

  function renderItem({ item }) {
    const typeList = Array.isArray(item.event_types) ? item.event_types.join(', ') : '—';
    const severityLabel = item.min_severity
      ? item.min_severity.charAt(0).toUpperCase() + item.min_severity.slice(1)
      : 'All';

    return (
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.cardName} numberOfLines={1}>{item.name}</Text>
          <View style={styles.cardActions}>
            <TouchableOpacity
              style={[styles.actionBtn, styles.editBtn]}
              onPress={() => handleEdit(item)}
            >
              <Text style={styles.actionBtnText}>Edit</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.actionBtn, styles.deleteBtn]}
              onPress={() => handleDelete(item)}
            >
              <Text style={styles.actionBtnText}>Delete</Text>
            </TouchableOpacity>
          </View>
        </View>
        <View style={styles.cardBody}>
          <Text style={styles.cardMeta}>
            <Text style={styles.metaLabel}>Types: </Text>
            <Text style={styles.metaValue}>{typeList || 'All'}</Text>
          </Text>
          <Text style={styles.cardMeta}>
            <Text style={styles.metaLabel}>Min Severity: </Text>
            <Text style={styles.metaValue}>{severityLabel}</Text>
          </Text>
          {item.keywords?.length > 0 && (
            <Text style={styles.cardMeta}>
              <Text style={styles.metaLabel}>Keywords: </Text>
              <Text style={styles.metaValue}>{item.keywords.join(', ')}</Text>
            </Text>
          )}
          <View style={styles.notifRow}>
            <Text style={styles.notifBadge(item.notify_email)}>
              {item.notify_email ? '✓ Email' : '✗ Email'}
            </Text>
            <Text style={styles.notifBadge(item.notify_push)}>
              {item.notify_push ? '✓ Push' : '✗ Push'}
            </Text>
          </View>
        </View>
      </View>
    );
  }

  function renderEmpty() {
    if (loading) return null;
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyEmoji}>🔔</Text>
        <Text style={styles.emptyTitle}>No Alerts Yet</Text>
        <Text style={styles.emptySubtitle}>
          Tap the + button to create your first alert subscription.
        </Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      {loading ? (
        <View style={styles.loaderContainer}>
          <ActivityIndicator size="large" color="#4f8ef7" />
          <Text style={styles.loadingText}>Loading subscriptions…</Text>
        </View>
      ) : error ? (
        <View style={styles.loaderContainer}>
          <Text style={styles.errorEmoji}>⚠️</Text>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryBtn} onPress={loadSubscriptions}>
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={subscriptions}
          keyExtractor={(item) => String(item.id)}
          renderItem={renderItem}
          contentContainerStyle={styles.listContent}
          ListEmptyComponent={renderEmpty}
          showsVerticalScrollIndicator={false}
        />
      )}

      <TouchableOpacity style={styles.fab} onPress={handleAdd} activeOpacity={0.85}>
        <Text style={styles.fabText}>＋</Text>
      </TouchableOpacity>

      <Modal
        visible={modalVisible}
        animationType="slide"
        transparent
        onRequestClose={() => { setModalVisible(false); setEditTarget(null); }}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalSheet}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>
                {editTarget ? 'Edit Subscription' : 'New Subscription'}
              </Text>
              <TouchableOpacity
                onPress={() => { setModalVisible(false); setEditTarget(null); }}
              >
                <Text style={styles.modalClose}>✕</Text>
              </TouchableOpacity>
            </View>
            <SubscriptionForm
              initial={editTarget}
              onSave={handleSave}
              onCancel={() => { setModalVisible(false); setEditTarget(null); }}
              saving={saving}
            />
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f0f1a' },
  listContent: { padding: 16, paddingBottom: 90 },
  loaderContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { color: '#8888aa', marginTop: 12 },
  errorEmoji: { fontSize: 40, marginBottom: 12 },
  errorText: { color: '#e74c3c', fontSize: 14, marginBottom: 16 },
  retryBtn: {
    backgroundColor: '#4f8ef7',
    paddingHorizontal: 24,
    paddingVertical: 10,
    borderRadius: 8,
  },
  retryText: { color: '#fff', fontWeight: '600' },
  card: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2a2a3e',
    overflow: 'hidden',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#2a2a3e',
  },
  cardName: { color: '#ffffff', fontSize: 16, fontWeight: 'bold', flex: 1, marginRight: 8 },
  cardActions: { flexDirection: 'row', gap: 8 },
  actionBtn: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  editBtn: { backgroundColor: '#2a4a7f' },
  deleteBtn: { backgroundColor: '#7f2a2a' },
  actionBtnText: { color: '#fff', fontSize: 12, fontWeight: '600' },
  cardBody: { padding: 14 },
  cardMeta: { color: '#aaaacc', fontSize: 13, marginBottom: 4 },
  metaLabel: { fontWeight: '600', color: '#ccccee' },
  metaValue: { color: '#aaaacc' },
  notifRow: { flexDirection: 'row', gap: 8, marginTop: 8 },
  notifBadge: (active) => ({
    fontSize: 12,
    color: active ? '#2ecc71' : '#555570',
    backgroundColor: active ? '#1a3a2a' : '#1a1a2e',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: active ? '#2ecc71' : '#2a2a3e',
    overflow: 'hidden',
  }),
  emptyContainer: {
    marginTop: 60,
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  emptyEmoji: { fontSize: 48, marginBottom: 16 },
  emptyTitle: { color: '#ffffff', fontSize: 18, fontWeight: 'bold', marginBottom: 8 },
  emptySubtitle: { color: '#8888aa', fontSize: 14, textAlign: 'center', lineHeight: 20 },
  fab: {
    position: 'absolute',
    bottom: 24,
    right: 24,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#4f8ef7',
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 8,
    shadowColor: '#4f8ef7',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 8,
  },
  fabText: { color: '#fff', fontSize: 28, lineHeight: 32, fontWeight: '300' },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'flex-end',
  },
  modalSheet: {
    backgroundColor: '#1a1a2e',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '90%',
    borderTopWidth: 1,
    borderColor: '#2a2a3e',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#2a2a3e',
  },
  modalTitle: { color: '#ffffff', fontSize: 18, fontWeight: 'bold' },
  modalClose: { color: '#8888aa', fontSize: 20, padding: 4 },
});
