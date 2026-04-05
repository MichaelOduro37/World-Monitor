import { create } from 'zustand';
import { apiClient } from '../api/client';

const PAGE_SIZE = 20;

export const useEventStore = create((set, get) => ({
  events: [],
  loading: false,
  loadingMore: false,
  error: null,
  hasMore: true,
  page: 1,
  filters: {
    event_type: '',
    min_severity: '',
  },

  setFilters(filters) {
    set({ filters, events: [], page: 1, hasMore: true });
    get().fetchEvents();
  },

  async fetchEvents() {
    const { filters } = get();
    set({ loading: true, error: null, page: 1, events: [] });
    try {
      const params = buildParams(filters, 1, PAGE_SIZE);
      const res = await apiClient.get('/api/events/', { params });
      const data = normalizeResponse(res.data);
      set({
        events: data.results,
        hasMore: data.hasMore,
        page: 2,
        loading: false,
      });
    } catch (err) {
      set({
        error: err?.response?.data?.detail || 'Failed to load events.',
        loading: false,
      });
    }
  },

  async loadMore() {
    const { page, hasMore, loadingMore, filters, events } = get();
    if (!hasMore || loadingMore) return;
    set({ loadingMore: true });
    try {
      const params = buildParams(filters, page, PAGE_SIZE);
      const res = await apiClient.get('/api/events/', { params });
      const data = normalizeResponse(res.data);
      set({
        events: [...events, ...data.results],
        hasMore: data.hasMore,
        page: page + 1,
        loadingMore: false,
      });
    } catch {
      set({ loadingMore: false });
    }
  },
}));

function buildParams(filters, page, pageSize) {
  const params = { page, page_size: pageSize };
  if (filters.event_type) params.event_type = filters.event_type;
  if (filters.min_severity) params.min_severity = filters.min_severity;
  return params;
}

function normalizeResponse(data) {
  if (Array.isArray(data)) {
    return { results: data, hasMore: data.length >= PAGE_SIZE };
  }
  const results = data.results ?? data.data ?? [];
  const count = data.count ?? data.total ?? null;
  const hasMore = data.next != null || (count != null && results.length < count);
  return { results, hasMore };
}
