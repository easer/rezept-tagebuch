# Nginx Reverse Proxy - seaser Multi-App Gateway

**Container:** `seaser-proxy`
**Network:** `seaser-network`
**Ports:** 8000 (HTTP), 8443/8444 (HTTPS)
**Image:** `localhost/seaser-proxy:latest`

---

## 🎯 Übersicht

Der Nginx Reverse Proxy ist der zentrale Einstiegspunkt für alle seaser-Apps. Er routet Requests basierend auf URL-Pfaden zu den entsprechenden Backend-Containern.

```
Internet/LAN → seaser-proxy:8000 → Backend Container
              (Nginx)              (Apps im seaser-network)
```

---

## 🏗️ Architektur

### Routing-Struktur

```
http://192.168.2.139:8000/
├── /                        → seaser-gateway (Homepage)
├── /common/                 → Shared static files (CSS, JS)
├── /sauerteig/              → sauerteig-rechner
├── /inventar/               → seaser-inventar
├── /localki/                → seaser-localki
├── /dokumentation/          → seaser-dokumentation
├── /medialib/               → seaser-medialib
├── /reviews/                → seaser-reviews
├── /rezept-tagebuch/        → seaser-rezept-tagebuch (PROD)
├── /rezept-tagebuch-dev/    → seaser-rezept-tagebuch-dev (DEV)
├── /rezept-tagebuch-test/   → seaser-rezept-tagebuch-test (TEST)
└── /rezept-tagebuch-react/  → React Frontend (Experimental)
```

### Container-Mapping

| URL-Pfad                   | Backend Container          | Port | Status       |
|----------------------------|----------------------------|------|--------------|
| `/`                        | `seaser-gateway`           | 80   | Production   |
| `/sauerteig/`              | `sauerteig-rechner`        | 80   | Production   |
| `/inventar/`               | `seaser-inventar`          | 80   | Production   |
| `/localki/`                | `seaser-localki`           | 80   | Production   |
| `/dokumentation/`          | `seaser-dokumentation`     | 80   | Production   |
| `/medialib/`               | `seaser-medialib`          | 80   | Production   |
| `/reviews/`                | `seaser-reviews`           | 80   | Production   |
| `/rezept-tagebuch/`        | `seaser-rezept-tagebuch`     | 80   | Production   |
| `/rezept-tagebuch-dev/`    | `seaser-rezept-tagebuch-dev` | 80   | Development  |
| `/rezept-tagebuch-test/`   | `seaser-rezept-tagebuch-test`| 80   | Testing      |
| `/rezept-tagebuch-react/`  | React Frontend               | 80   | Experimental |

---

## 🔐 Authentifizierung

### IP-basierte Auth-Map

Nginx verwendet `geo` Module für IP-basierte Authentifizierung:

```nginx
geo $remote_addr $auth_type {
    default "Seaser Login";      # Alle anderen: Auth erforderlich
    100.64.0.0/10 "off";         # Tailscale VPN: Kein Auth
    192.168.2.0/24 "off";        # Lokales LAN: Kein Auth
    10.89.0.0/16 "off";          # Podman Bridge: Kein Auth
    127.0.0.1/8 "off";           # Localhost: Kein Auth
}
```

**Authentifizierungs-Strategie:**
- ✅ **Kein Passwort:** Lokales LAN (192.168.2.x), Tailscale VPN (100.64.x.x)
- 🔒 **Basic Auth:** Alle anderen IPs (extern)
- 📁 **Credential File:** `/etc/nginx/nginx.htpasswd`

### Rate Limiting (Security)

```nginx
limit_req_zone $binary_remote_addr zone=login:10m rate=10r/m;
limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;
```

**Zones:**
- `login`: Max 10 requests/minute (für Login-Schutz)
- `api`: Max 60 requests/minute (für API-Endpoints)

---

## 🌐 DNS Resolution

### Dynamische Container-Auflösung

Nginx verwendet dynamische DNS-Auflösung für Container-Namen:

```nginx
resolver 10.89.0.1 valid=10s ipv6=off;
resolver_timeout 5s;

# Dynamische Auflösung in Location-Blocks
set $backend_sauerteig_rechner "sauerteig-rechner";
proxy_pass http://$backend_sauerteig_rechner:80/;
```

**Wichtig:**
- Resolver IP `10.89.0.1` ist das Podman Network Gateway
- `valid=10s` cached DNS-Einträge für 10 Sekunden
- Verhindert Nginx-Neustarts bei Container-IP-Änderungen

---

## 📦 Upload & Performance

### Upload-Limits

```nginx
client_max_body_size 50M;
```

- Max Upload-Größe: **50MB** (für Bilder, Dokumente)
- Anwendbar für alle Apps (Rezepte, Inventar, MediaLib)

### Static Files Caching

```nginx
location /common/ {
    alias /usr/share/nginx/common/;
    expires 1h;
    add_header Cache-Control "public, must-revalidate";
}
```

- Gemeinsame CSS/JS Dateien werden gecached
- Cache-Dauer: 1 Stunde
- **Ohne Authentifizierung** für schnellere Ladezeiten

---

## 🔒 Security Headers

Alle Responses enthalten Security-Header:

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self' 'unsafe-inline' 'unsafe-eval'; img-src 'self' data: blob:; font-src 'self' data:;" always;
```

**Schutz gegen:**
- Clickjacking (X-Frame-Options)
- MIME-Type Sniffing (X-Content-Type-Options)
- XSS-Angriffe (X-XSS-Protection)
- CSP für Content-Security

---

## 🛠️ Nginx Container Management

### Container Info

```bash
# Container Status
podman ps | grep seaser-proxy

# Logs ansehen
podman logs --tail 50 seaser-proxy

# Live-Logs
podman logs -f seaser-proxy

# Config testen
podman exec seaser-proxy nginx -t

# Nginx reload (ohne Downtime)
podman exec seaser-proxy nginx -s reload
```

### Systemd Service

```bash
# Service Status
systemctl --user status container-seaser-proxy.service

# Neustart
systemctl --user restart container-seaser-proxy.service

# Auto-Start aktivieren
systemctl --user enable container-seaser-proxy.service
```

---

## 🔧 Nginx Config bearbeiten

### Workflow: Config-Änderung

```bash
cd /home/gabor/easer_projekte

# 1. Config im Container bearbeiten
podman exec -it seaser-proxy vi /etc/nginx/conf.d/default.conf

# 2. Config testen
podman exec seaser-proxy nginx -t

# 3. Nginx reloaden
podman exec seaser-proxy nginx -s reload

# Optional: Config aus Container exportieren
podman exec seaser-proxy cat /etc/nginx/conf.d/default.conf > nginx-backup.conf
```

### Neue Route hinzufügen

**Beispiel: Neue App `/neue-app/` hinzufügen:**

```nginx
# In /etc/nginx/conf.d/default.conf
location /neue-app/ {
    auth_basic $auth_type;
    auth_basic_user_file /etc/nginx/nginx.htpasswd;

    set $backend_neue_app "seaser-neue-app";
    proxy_pass http://$backend_neue_app:80/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

**Schritte:**
1. Config bearbeiten (siehe oben)
2. Nginx testen: `nginx -t`
3. Nginx reloaden: `nginx -s reload`
4. Gateway-HTML updaten (`seaser-main-page.html`)

---

## 🐛 Troubleshooting

### Problem: 502 Bad Gateway

**Ursache:** Backend-Container nicht erreichbar

```bash
# 1. Backend-Container läuft?
podman ps | grep seaser-inventar

# 2. DNS-Auflösung funktioniert?
podman exec seaser-proxy nslookup seaser-inventar

# 3. Netzwerk-Konnektivität testen
podman exec seaser-proxy ping seaser-inventar

# 4. Backend-Logs prüfen
podman logs seaser-inventar
```

### Problem: 401 Unauthorized (falsches Passwort)

**Ursache:** htpasswd-Datei fehlt oder falsch

```bash
# 1. htpasswd-Datei prüfen
podman exec seaser-proxy cat /etc/nginx/nginx.htpasswd

# 2. Neues Passwort setzen
htpasswd -c nginx.htpasswd username

# 3. Datei in Container kopieren
podman cp nginx.htpasswd seaser-proxy:/etc/nginx/nginx.htpasswd

# 4. Nginx reloaden
podman exec seaser-proxy nginx -s reload
```

### Problem: Config-Änderungen werden nicht übernommen

**Ursache:** Config nicht reloaded oder Syntax-Fehler

```bash
# 1. Syntax prüfen
podman exec seaser-proxy nginx -t

# 2. Bei Syntax-Fehler: Config reparieren

# 3. Nginx reloaden
podman exec seaser-proxy nginx -s reload

# 4. Falls Reload nicht hilft: Container neu starten
podman restart seaser-proxy
```

### Problem: Langsame DNS-Auflösung

**Ursache:** DNS-Cache oder Resolver-Timeout

```bash
# 1. DNS-Performance testen
time podman exec seaser-proxy nslookup seaser-inventar

# 2. Resolver-Config prüfen (in nginx.conf)
# resolver 10.89.0.1 valid=10s;

# 3. Cache-Zeit anpassen (in default.conf)
# valid=10s → valid=30s (längerer Cache)
```

---

## 📝 Best Practices

### 1. Immer Config testen vor Reload

```bash
podman exec seaser-proxy nginx -t && \
podman exec seaser-proxy nginx -s reload
```

### 2. Backup vor Änderungen

```bash
# Config exportieren
podman exec seaser-proxy cat /etc/nginx/conf.d/default.conf > \
    nginx-backup-$(date +%Y%m%d-%H%M%S).conf
```

### 3. Rate Limiting für neue Endpoints

```nginx
location /neue-app/api/ {
    limit_req zone=api burst=10 nodelay;
    # ... rest of config
}
```

### 4. Dynamische DNS für alle Backends

```nginx
# ✅ Richtig: Dynamische Auflösung
set $backend_app "seaser-app";
proxy_pass http://$backend_app:80/;

# ❌ Falsch: Statische IP (cached)
proxy_pass http://seaser-app:80/;
```

### 5. Security Headers für alle Locations

```nginx
# Global in server {} Block definieren
add_header X-Frame-Options "SAMEORIGIN" always;
```

---

## 📊 Monitoring

### Log-Analyse

```bash
# Top 10 meistbesuchte URLs
podman logs seaser-proxy 2>&1 | \
    grep -oP 'GET \K[^ ]+' | \
    sort | uniq -c | sort -rn | head -10

# 404 Errors
podman logs seaser-proxy 2>&1 | grep "404"

# 502 Bad Gateway
podman logs seaser-proxy 2>&1 | grep "502"

# Langsame Requests (>1s)
podman logs seaser-proxy 2>&1 | grep "request_time" | \
    awk '$NF > 1.0'
```

### Performance-Check

```bash
# Response-Time für Gateway
time curl -I http://192.168.2.139:8000/

# Response-Time für App
time curl -I http://192.168.2.139:8000/rezept-tagebuch/
```

---

## 🔄 Container Rebuild

Falls der Proxy-Container neu gebaut werden muss:

```bash
# 1. Dockerfile/Containerfile prüfen
ls -la /home/gabor/easer_projekte/Dockerfile*

# 2. Image bauen
podman build -t seaser-proxy:latest -f Dockerfile.proxy .

# 3. Container stoppen & entfernen
podman stop seaser-proxy
podman rm seaser-proxy

# 4. Neuen Container starten
podman run -d \
    --name seaser-proxy \
    --network seaser-network \
    -p 8000:80 \
    -p 8443:443 \
    -p 8444:8444 \
    -v /home/gabor/easer_projekte/nginx.htpasswd:/etc/nginx/nginx.htpasswd:Z \
    -v /home/gabor/easer_projekte/common:/usr/share/nginx/common:Z \
    localhost/seaser-proxy:latest

# 5. Systemd Service aktualisieren
podman generate systemd --new --name seaser-proxy > \
    ~/.config/systemd/user/container-seaser-proxy.service
systemctl --user daemon-reload
systemctl --user enable container-seaser-proxy.service
```

---

**Erstellt:** 2025-11-07
**Version:** 1.0
**Maintainer:** seaser DevOps Team
