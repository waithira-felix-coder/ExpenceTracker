self.addEventListener("install", event => {
    event.waitUntil(
        caches.open("expense-cache").then(cache => {
            return cache.addAll([
                "/",
                "/dashboard",
                "/static/manifest.json"
            ]);
        })
    );
});

self.addEventListener("fetch", event => {
    event.respondWith(
        caches.match(event.request).then(response => {
            return response || fetch(event.request);
        })
    );
});
