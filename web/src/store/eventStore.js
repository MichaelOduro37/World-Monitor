import { create } from 'zustand'
import { getEvents } from '../api/client'

const DEFAULT_FILTERS = {
  type: '',
  severity_min: 0,
  q: '',
  bbox: '',
  start: '',
  end: ''
}

const useEventStore = create((set, get) => ({
  events: [],
  total: 0,
  page: 1,
  pageSize: 20,
  loading: false,
  error: null,
  filters: { ...DEFAULT_FILTERS },

  setFilter: (key, value) => {
    set((state) => ({ filters: { ...state.filters, [key]: value }, page: 1 }))
  },

  resetFilters: () => {
    set({ filters: { ...DEFAULT_FILTERS }, page: 1 })
  },

  fetchEvents: async (extraFilters = {}, replace = true) => {
    set({ loading: true, error: null })
    const { filters, page, pageSize } = get()
    const merged = { ...filters, ...extraFilters }
    const params = { page, size: pageSize }
    if (merged.type) params.type = merged.type
    if (merged.severity_min) params.severity_min = merged.severity_min
    if (merged.q) params.q = merged.q
    if (merged.bbox) params.bbox = merged.bbox
    if (merged.start) params.start = merged.start
    if (merged.end) params.end = merged.end
    try {
      const data = await getEvents(params)
      const incoming = data.items ?? data.events ?? data ?? []
      const total = data.total ?? incoming.length
      set((state) => ({
        events: replace ? incoming : [...state.events, ...incoming],
        total,
        loading: false
      }))
    } catch (err) {
      set({ loading: false, error: err.message ?? 'Failed to load events' })
    }
  },

  loadMore: async () => {
    set((state) => ({ page: state.page + 1 }))
    await get().fetchEvents({}, false)
  }
}))

export default useEventStore
