# Authentication Setup - seaser Multi-App Gateway

**Auth-Methode:** IP-basierte Basic Auth (Nginx)
**Credential File:** `/etc/nginx/nginx.htpasswd`
**Backup-System:** Authelia/OAuth2-Proxy (in Vorbereitung)

---

## 🎯 Übersicht

Die seaser-Apps verwenden eine **IP-basierte Authentifizierung**:
- ✅ **Kein Passwort:** Lokales LAN (192.168.2.x), Tailscale VPN (100.64.x.x)
- 🔒 **Basic Auth:** Alle anderen IPs (extern)

```
┌─────────────────────────────────────────────┐
│  Client Request                              │
├─────────────────────────────────────────────┤
│  IP: 192.168.2.50 (LAN) → Kein Auth        │
│  IP: 100.64.1.10 (VPN)  → Kein Auth        │
│  IP: 8.8.8.8 (Extern)   → Basic Auth       │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│  Nginx seaser-proxy                         │
│  - geo $auth_type (IP-Check)                │
│  - auth_basic $auth_type                    │
│  - auth_basic_user_file nginx.htpasswd      │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│  Backend Apps                                │
│  (seaser-inventar, seaser-reviews, etc.)    │
└─────────────────────────────────────────────┘
```

---

## 🔐 IP-basierte Auth-Konfiguration

### Nginx geo Module

In der Nginx-Config (`/etc/nginx/conf.d/default.conf`) des `seaser-proxy` Containers:

```nginx
geo $remote_addr $auth_type {
    default "Seaser Login";      # Alle anderen: Auth erforderlich
    100.64.0.0/10 "off";         # Tailscale VPN: Kein Auth
    192.168.2.0/24 "off";        # Lokales LAN: Kein Auth
    10.89.0.0/16 "off";          # Podman Bridge: Kein Auth
    127.0.0.1/8 "off";           # Localhost: Kein Auth
}
```

**Erklärung:**
- `$auth_type = "off"` → Keine Authentifizierung
- `$auth_type = "Seaser Login"` → Basic Auth mit Realm "Seaser Login"

### Location-Block Beispiel

```nginx
location /inventar/ {
    auth_basic $auth_type;
    auth_basic_user_file /etc/nginx/nginx.htpasswd;

    # ... proxy_pass config
}
```

**Verhalten:**
- LAN/VPN: `auth_basic "off"` → Direkt durchgelassen
- Extern: `auth_basic "Seaser Login"` → Username/Passwort erforderlich

---

## 🔑 Passwort-Management

### Aktueller Benutzer

**Username:** `admin`
**Passwort-Hash:** SHA-512 (in `nginx.htpasswd`)

**Location:**
```
Host:      /home/gabor/easer_projekte/nginx.htpasswd
Container: /etc/nginx/nginx.htpasswd
```

### Passwort ändern

```bash
cd /home/gabor/easer_projekte

# 1. Neues Passwort setzen (überschreibt alte Datei)
htpasswd -c nginx.htpasswd admin

# 2. In Container kopieren
podman cp nginx.htpasswd seaser-proxy:/etc/nginx/nginx.htpasswd

# 3. Nginx reloaden
podman exec seaser-proxy nginx -s reload

# 4. Testen
curl -u admin:neues-passwort http://192.168.2.139:8000/
```

### Zusätzlichen Benutzer hinzufügen

```bash
# User hinzufügen (OHNE -c Flag!)
htpasswd nginx.htpasswd natalie

# In Container kopieren
podman cp nginx.htpasswd seaser-proxy:/etc/nginx/nginx.htpasswd

# Nginx reloaden
podman exec seaser-proxy nginx -s reload
```

**Wichtig:** `-c` Flag überschreibt die Datei! Ohne `-c` wird nur ein Benutzer hinzugefügt.

---

## 🌐 IP-Bereiche

### Erlaubte IP-Bereiche (kein Auth)

| IP-Bereich        | CIDR           | Beschreibung                  |
|-------------------|----------------|-------------------------------|
| Localhost         | 127.0.0.1/8    | Loopback-Interface            |
| Podman Bridge     | 10.89.0.0/16   | seaser-network intern         |
| Lokales LAN       | 192.168.2.0/24 | Heimnetzwerk                  |
| Tailscale VPN     | 100.64.0.0/10  | Tailscale CGNAT-Bereich       |

### IP-Bereich hinzufügen

**Beispiel: Zusätzliches VPN (10.20.0.0/24) erlauben:**

```nginx
geo $remote_addr $auth_type {
    default "Seaser Login";
    100.64.0.0/10 "off";
    192.168.2.0/24 "off";
    10.89.0.0/16 "off";
    127.0.0.1/8 "off";
    10.20.0.0/24 "off";        # Neues VPN
}
```

**Anwenden:**
```bash
# 1. Config im Container bearbeiten
podman exec -it seaser-proxy vi /etc/nginx/conf.d/default.conf

# 2. Nginx testen
podman exec seaser-proxy nginx -t

# 3. Nginx reloaden
podman exec seaser-proxy nginx -s reload
```

---

## 🧪 Auth testen

### Von erlaubtem IP (LAN)

```bash
# Kein Auth erforderlich
curl http://192.168.2.139:8000/
# → 200 OK (direkt)
```

### Von externem IP (simuliert)

```bash
# Basic Auth erforderlich
curl http://192.168.2.139:8000/
# → 401 Unauthorized

# Mit Credentials
curl -u admin:passwort http://192.168.2.139:8000/
# → 200 OK
```

### Client-IP im Log prüfen

```bash
# Nginx Access-Log ansehen
podman logs seaser-proxy 2>&1 | grep "GET /" | tail -5

# Output zeigt Client-IP:
# 192.168.2.50 - - [07/Nov/2025:12:34:56] "GET / HTTP/1.1" 200
```

---

## 🔒 Rate Limiting (Security)

Zusätzlich zur Auth gibt es Rate Limiting für kritische Endpoints:

```nginx
limit_req_zone $binary_remote_addr zone=login:10m rate=10r/m;
limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;
```

### Rate Limit Zones

| Zone    | Limit          | Anwendung                     |
|---------|----------------|-------------------------------|
| login   | 10 req/minute  | Gateway-Homepage (Login)      |
| api     | 60 req/minute  | API-Endpoints                 |

### Location mit Rate Limit

```nginx
location / {
    limit_req zone=login burst=5 nodelay;
    auth_basic $auth_type;
    auth_basic_user_file /etc/nginx/nginx.htpasswd;
    # ...
}
```

**Burst:** Erlaubt kurze Spitzen (5 zusätzliche Requests)
**Nodelay:** Keine Verzögerung bei Burst-Requests

---

## 🛡️ OAuth2-Proxy (in Vorbereitung)

### Aktueller Status

OAuth2-Proxy ist **nicht aktiv**, aber vorbereitet:

**Config:** `/home/gabor/easer_projekte/oauth2-proxy/oauth2-proxy.cfg`
**SSL Certs:**
- Tailscale: `seaser-server.taila932b0.ts.net.crt/key`
- Selfsigned: `selfsigned.crt/key`

### Zukünftige Integration

OAuth2-Proxy kann als Alternative zu Basic Auth verwendet werden:

```
Client → Nginx → OAuth2-Proxy → Backend
                  (Google OAuth)
```

**Vorteile:**
- ✅ Keine Passwörter (Google/GitHub Login)
- ✅ Session-Management
- ✅ HTTPS-Unterstützung (Tailscale Cert)

**Nachteil:**
- ❌ Externe OAuth-Abhängigkeit (Internet erforderlich)

---

## 🔐 Authelia (in Vorbereitung)

### Aktueller Status

Authelia ist **installiert aber nicht aktiv**:

**Config:** `/home/gabor/easer_projekte/authelia/configuration.yml`
**Users:** `/home/gabor/easer_projekte/authelia/users_database.yml`
**Database:** `/home/gabor/easer_projekte/authelia/db.sqlite3`

### Zukünftige Integration

Authelia bietet erweiterte Auth-Features:

```
Client → Nginx → Authelia → Backend
                  (2FA, LDAP)
```

**Features:**
- ✅ Two-Factor Authentication (TOTP)
- ✅ Single Sign-On (SSO)
- ✅ User-Management
- ✅ Access Control Lists (ACL)

---

## 🐛 Troubleshooting

### Problem: 401 Unauthorized (trotz LAN-IP)

**Ursache:** IP wird nicht als LAN erkannt

```bash
# 1. Client-IP im Nginx-Log prüfen
podman logs seaser-proxy 2>&1 | tail -5

# 2. geo-Modul testen
podman exec seaser-proxy cat /etc/nginx/conf.d/default.conf | grep -A 10 "geo.*auth_type"

# 3. IP-Bereich anpassen (falls Router-NAT)
# Beispiel: Router NAT nutzt 192.168.2.1 als Source-IP
# → In geo-Modul prüfen ob 192.168.2.1 in 192.168.2.0/24
```

### Problem: Passwort wird nicht akzeptiert

```bash
# 1. htpasswd-Datei im Container prüfen
podman exec seaser-proxy cat /etc/nginx/nginx.htpasswd

# 2. Passwort testen (lokal)
htpasswd -v nginx.htpasswd admin

# 3. Datei neu in Container kopieren
podman cp nginx.htpasswd seaser-proxy:/etc/nginx/nginx.htpasswd

# 4. Nginx reloaden
podman exec seaser-proxy nginx -s reload
```

### Problem: Tailscale VPN erfordert Auth

**Ursache:** Tailscale nutzt falsches IP-Subnet

```bash
# 1. Tailscale IP prüfen
tailscale ip -4

# Output: z.B. 100.64.1.10 (sollte in 100.64.0.0/10 sein)

# 2. Falls anderes Subnet: geo-Modul anpassen
# Beispiel: 100.100.0.0/16
geo $remote_addr $auth_type {
    default "Seaser Login";
    100.64.0.0/10 "off";
    100.100.0.0/16 "off";   # Zusätzliches Tailscale-Subnet
    # ...
}
```

### Problem: Rate Limit überschritten (429 Too Many Requests)

```bash
# 1. Rate Limit im Log prüfen
podman logs seaser-proxy 2>&1 | grep "limiting requests"

# 2. Rate Limit erhöhen (in nginx.conf)
limit_req_zone $binary_remote_addr zone=login:10m rate=20r/m;  # von 10 auf 20

# 3. Oder burst erhöhen
limit_req zone=login burst=10 nodelay;  # von 5 auf 10
```

---

## 📝 Best Practices

### 1. Starke Passwörter verwenden

```bash
# SHA-512 mit Salt (Standard bei htpasswd)
htpasswd -c nginx.htpasswd admin

# Passwort-Generator nutzen
openssl rand -base64 32
```

### 2. Regelmäßige Passwort-Rotation

```bash
# Alle 90 Tage Passwort ändern
htpasswd -c nginx.htpasswd admin
podman cp nginx.htpasswd seaser-proxy:/etc/nginx/nginx.htpasswd
podman exec seaser-proxy nginx -s reload
```

### 3. IP-Bereiche minimieren

```nginx
# ✅ Gut: Spezifisches Subnet
192.168.2.0/24 "off";

# ❌ Vermeiden: Zu breites Subnet
192.168.0.0/16 "off";  # Erlaubt 192.168.*.* (zu viele IPs)
```

### 4. Rate Limiting aktiviert lassen

```nginx
# Immer Rate Limiting für Login-Endpoints
location / {
    limit_req zone=login burst=5 nodelay;
    # ...
}
```

### 5. HTTPS für externe Zugriffe

```bash
# Für externe Zugriffe immer HTTPS verwenden
# Port 8443 (HTTPS) statt 8000 (HTTP)
https://deine-domain.de:8443/
```

---

## 🔄 Migration zu OAuth2/Authelia

Falls du von Basic Auth zu OAuth2/Authelia wechseln möchtest:

### Schritt 1: OAuth2-Proxy aktivieren

```bash
# 1. OAuth2-Proxy Container starten
podman run -d \
    --name oauth2-proxy \
    --network seaser-network \
    -v /home/gabor/easer_projekte/oauth2-proxy/oauth2-proxy.cfg:/etc/oauth2-proxy.cfg:Z \
    quay.io/oauth2-proxy/oauth2-proxy:latest \
    --config=/etc/oauth2-proxy.cfg

# 2. Nginx-Config anpassen (auth_request statt auth_basic)
location /inventar/ {
    auth_request /oauth2/auth;
    # ...
}
```

### Schritt 2: Authelia aktivieren

```bash
# 1. Authelia Container starten
podman run -d \
    --name authelia \
    --network seaser-network \
    -v /home/gabor/easer_projekte/authelia:/config:Z \
    authelia/authelia:latest

# 2. Nginx-Config anpassen
location /inventar/ {
    auth_request /authelia/api/verify;
    # ...
}
```

**Siehe:** Offizielle Authelia/OAuth2-Proxy Dokumentation für Details

---

## 🔗 Weiterführende Dokumentation

- **NGINX-PROXY.md** - Nginx Reverse Proxy Konfiguration
- **PODMAN-NETWORK.md** - Podman Network Setup
- **[Nginx Auth Request](https://docs.nginx.com/nginx/admin-guide/security-controls/configuring-subrequest-authentication/)** - Nginx Auth-Modul Doku
- **[Authelia Docs](https://www.authelia.com/docs/)** - Authelia Dokumentation
- **[OAuth2-Proxy Docs](https://oauth2-proxy.github.io/oauth2-proxy/)** - OAuth2-Proxy Dokumentation

---

**Erstellt:** 2025-11-07
**Version:** 1.0
**Maintainer:** seaser DevOps Team
