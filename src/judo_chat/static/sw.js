// Service worker do PWA (docs/decisoes/0002-disponibilizar-como-pwa.md). Guarda só a página,
// o manifest e os ícones, para a página abrir sem conexão e mostrar "sem conexão" na pergunta.
// O config.js, as fontes e a API vão sempre à rede: um config.js guardado serviria a URL antiga
// da API depois de uma troca.
// O pages.yml troca __VERSAO__ pelo commit publicado, e cada deploy cria um cache novo.
const CACHE = "judo-chat-__VERSAO__";
const SHELL = ["./", "manifest.webmanifest", "icon-192.png", "icon-512.png", "icon-maskable-512.png", "apple-touch-icon.png"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k.startsWith("judo-chat-") && k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

// Rede primeiro: com conexão, a página vem sempre do deploy mais recente e atualiza o cache;
// sem conexão, sai do cache. Só trata GET da própria origem para os arquivos da lista acima.
// Fora deles (config.js, /api/, /docs quando a API serve a página) o navegador segue sozinho.
function shellKey(url) {
  const scope = new URL(self.registration.scope);
  if (url.origin !== scope.origin || !url.pathname.startsWith(scope.pathname)) return null;
  const path = url.pathname.slice(scope.pathname.length);
  const key = path === "" || path === "index.html" ? "./" : path;
  return SHELL.includes(key) ? new URL(key, scope).href : null;
}

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  const key = shellKey(new URL(event.request.url));
  if (!key) return;
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (response.ok) {
          const copy = response.clone();
          event.waitUntil(caches.open(CACHE).then((cache) => cache.put(key, copy)));
        }
        return response;
      })
      .catch(() => caches.match(key).then((cached) => cached || Response.error())),
  );
});
