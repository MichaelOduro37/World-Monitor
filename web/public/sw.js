// Service Worker for Web Push notifications

self.addEventListener('push', (event) => {
  let data = {}
  try {
    data = event.data ? event.data.json() : {}
  } catch {
    data = { title: 'World Monitor', body: event.data ? event.data.text() : 'New alert' }
  }

  const title = data.title || 'World Monitor Alert'
  const options = {
    body: data.body || data.summary || 'A new world event has been detected.',
    icon: '/favicon.ico',
    badge: '/favicon.ico',
    tag: data.id ? `event-${data.id}` : 'world-monitor',
    data: {
      url: data.url || '/',
      eventId: data.id
    },
    requireInteraction: data.severity >= 0.75
  }

  event.waitUntil(self.registration.showNotification(title, options))
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  const targetUrl = event.notification.data?.url || '/'

  event.waitUntil(
    clients
      .matchAll({ type: 'window', includeUncontrolled: true })
      .then((windowClients) => {
        for (const client of windowClients) {
          if (client.url === targetUrl && 'focus' in client) {
            return client.focus()
          }
        }
        if (clients.openWindow) {
          return clients.openWindow(targetUrl)
        }
      })
  )
})

self.addEventListener('install', () => self.skipWaiting())
self.addEventListener('activate', (event) => event.waitUntil(clients.claim()))
