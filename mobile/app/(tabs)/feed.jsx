import { useEffect, useCallback, useState } from 'react';
import {
  View,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  Text,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useEventStore } from '../../store/eventStore';
import EventCard from '../../components/EventCard';
import EventFilters from '../../components/EventFilters';

export default function FeedScreen() {
  const {
    events,
    loading,
    loadingMore,
    error,
    hasMore,
    fetchEvents,
    loadMore,
    filters,
    setFilters,
  } = useEventStore();

  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchEvents();
  }, [filters]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchEvents();
    setRefreshing(false);
  }, [fetchEvents]);

  const onEndReached = useCallback(() => {
    if (!loadingMore && hasMore) {
      loadMore();
    }
  }, [loadingMore, hasMore, loadMore]);

  function renderItem({ item }) {
    return <EventCard event={item} />;
  }

  function renderFooter() {
    if (!loadingMore) return null;
    return (
      <View style={styles.footerLoader}>
        <ActivityIndicator size="small" color="#4f8ef7" />
      </View>
    );
  }

  function renderEmpty() {
    if (loading) return null;
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyEmoji}>🔭</Text>
        <Text style={styles.emptyTitle}>No Events Found</Text>
        <Text style={styles.emptySubtitle}>
          {error ? error : 'Try adjusting your filters or pull to refresh.'}
        </Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <EventFilters filters={filters} onFiltersChange={setFilters} />

      {loading && events.length === 0 ? (
        <View style={styles.loaderContainer}>
          <ActivityIndicator size="large" color="#4f8ef7" />
          <Text style={styles.loadingText}>Loading events…</Text>
        </View>
      ) : (
        <FlatList
          data={events}
          keyExtractor={(item) => String(item.id)}
          renderItem={renderItem}
          contentContainerStyle={styles.listContent}
          ListEmptyComponent={renderEmpty}
          ListFooterComponent={renderFooter}
          onEndReached={onEndReached}
          onEndReachedThreshold={0.3}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor="#4f8ef7"
              colors={['#4f8ef7']}
            />
          }
          showsVerticalScrollIndicator={false}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f0f1a' },
  listContent: { paddingHorizontal: 16, paddingBottom: 24 },
  loaderContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: { color: '#8888aa', marginTop: 12, fontSize: 14 },
  footerLoader: { paddingVertical: 20, alignItems: 'center' },
  emptyContainer: {
    flex: 1,
    marginTop: 80,
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  emptyEmoji: { fontSize: 48, marginBottom: 16 },
  emptyTitle: { color: '#ffffff', fontSize: 18, fontWeight: 'bold', marginBottom: 8 },
  emptySubtitle: { color: '#8888aa', fontSize: 14, textAlign: 'center', lineHeight: 20 },
});
