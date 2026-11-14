// 생활 장부 서비스 워커: 앱 화면 파일만 저장해서 빠르게 열고, 항상 최신 버전을 먼저 받아옴 (네트워크 우선).
// 장부 데이터(Supabase)는 저장하지 않음.
const CACHE = "ledger-v1";
const SHELL = ["./", "index.html", "supabase.min.js", "manifest.webmanifest", "icon-192.png", "icon-512.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", e => {
  const u = new URL(e.request.url);
  if (e.request.method !== "GET" || u.origin !== location.origin) return;  // Supabase 등 외부 요청은 건드리지 않음
  e.respondWith(fetch(e.request).then(r => { if (r.ok) { const cp = r.clone(); caches.open(CACHE).then(c => c.put(e.request, cp)); } return r; })
    .catch(() => caches.match(e.request, { ignoreSearch: true }).then(r => r || caches.match("index.html"))));
});
