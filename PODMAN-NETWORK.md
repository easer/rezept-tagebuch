# Podman Network - seaser Multi-App Infrastructure

**Network Name:** `seaser-network`
**Driver:** bridge
**Subnet:** 10.89.0.0/24
**Gateway:** 10.89.0.1
**DNS:** Enabled (Container-to-Container by name)

---

## 🎯 Übersicht

Das `seaser-network` ist ein Podman Bridge-Netzwerk, das alle seaser-Apps miteinander verbindet. Container können sich gegenseitig über ihre Container-Namen erreichen (DNS-Auflösung).

```
┌─────────────────────────────────────────────────────────┐
│  seaser-network (10.89.0.0/24)                         │
│  Gateway: 10.89.0.1                                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐  │
│  │ seaser-     │   │ seaser-     │   │ sauerteig-  │  │
│  │ proxy       │◄──┤ gateway     │   │ rechner     │  │
│  │ :80         │   │ :80         │   │ :80         │  │
│  └──────┬──────┘   └─────────────┘   └─────────────┘  │
│         │                                                │
│         │  (Nginx Reverse Proxy)                        │
│         │                                                │
│         ▼                                                │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Backend Apps                                     │  │
│  ├──────────────────────────────────────────────────┤  │
│  │  • seaser-inventar                               │  │
│  │  • seaser-localki                                │  │
│  │  • seaser-ki                                     │  │
│  │  • seaser-reviews                                │  │
│  │  • seaser-medialib                               │  │
│  │  • seaser-dokumentation                          │  │
│  │  • seaser-rezept-tagebuch                        │  │
│  │  • seaser-rezept-tagebuch-dev                    │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
                          ▲
                          │
                    Port Forwarding
                          │
              ┌───────────┴───────────┐
              │   Host: 192.168.2.139 │
              │   Port: 8000 → :80    │
              └───────────────────────┘
```

---

## 🏗️ Network-Architektur

### Network Details

```bash
# Network Info anzeigen
podman network inspect seaser-network
```

**Konfiguration:**
- **Name:** `seaser-network`
- **Driver:** bridge (Standard Podman Bridge)
- **Subnet:** `10.89.0.0/24` (254 verfügbare IPs)
- **Gateway:** `10.89.0.1` (DNS Resolver für Nginx)
- **Interface:** `podman1` (Linux Bridge Interface)
- **IPv6:** Deaktiviert
- **Internal:** Nein (Container haben Internet-Zugang)
- **DNS:** Aktiviert (automatische Container-Name-Auflösung)

### Warum Bridge Network?

- ✅ **Isolation:** Container sind vom Host-Netzwerk isoliert
- ✅ **DNS:** Automatische Container-Name-Auflösung
- ✅ **Sicherheit:** Container nur über definierte Ports erreichbar
- ✅ **Flexibilität:** Einfaches Hinzufügen/Entfernen von Containern

---

## 📊 Container im Network

### Aktive Container

| Container Name                | Image                           | Exposed Ports | Status       |
|-------------------------------|---------------------------------|---------------|--------------|
| `seaser-proxy`                | `seaser-proxy:latest`           | 8000, 8443, 8444 | Production |
| `seaser-gateway`              | `seaser-gateway:latest`         | -             | Production   |
| `sauerteig-rechner`           | `sauerteig-rechner:latest`      | -             | Production   |
| `seaser-inventar`             | `seaser-inventar:latest`        | -             | Production   |
| `seaser-localki`              | `localki-image:latest`          | -             | Production   |
| `seaser-ki`                   | `seaser-ki:optimized`           | -             | Production   |
| `seaser-reviews`              | `seaser-reviews:latest`         | -             | Production   |
| `seaser-medialib`             | `seaser-medialib:latest`        | -             | Production   |
| `seaser-dokumentation`        | `seaser-dokumentation:latest`   | -             | Production   |
| `seaser-rezept-tagebuch`      | `seaser-rezept-tagebuch:latest` | -             | Production   |
| `seaser-rezept-tagebuch-dev`  | `seaser-rezept-tagebuch:dev`    | -             | Development  |

**Hinweis:** Nur `seaser-proxy` hat exposed Ports (8000, 8443, 8444) am Host. Alle anderen Container sind nur intern über das seaser-network erreichbar.

### Container auflisten

```bash
# Alle Container im seaser-network
podman ps --filter "network=seaser-network" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"

# Mit IP-Adressen
podman ps --filter "network=seaser-network" --format "table {{.Names}}\t{{.Networks}}\t{{.Ports}}"
```

---

## 🔌 DNS & Service Discovery

### Container-zu-Container Kommunikation

Container im `seaser-network` können sich gegenseitig über ihre **Container-Namen** erreichen:

```bash
# Von seaser-proxy zu seaser-inventar
podman exec seaser-proxy ping seaser-inventar

# DNS-Auflösung testen
podman exec seaser-proxy nslookup seaser-inventar

# HTTP-Request testen
podman exec seaser-proxy curl http://seaser-inventar:80/
```

**DNS-Resolution:**
- Podman DNS Server: `10.89.0.1` (Gateway IP)
- Automatische Auflösung von Container-Namen
- Keine `/etc/hosts` Manipulation notwendig

### Nginx DNS-Konfiguration

Nginx im `seaser-proxy` Container nutzt dynamische DNS-Auflösung:

```nginx
resolver 10.89.0.1 valid=10s ipv6=off;
resolver_timeout 5s;

location /inventar/ {
    set $backend_inventar "seaser-inventar";
    proxy_pass http://$backend_inventar:80/;
}
```

**Vorteile:**
- Container-IPs können sich ändern (bei Neustarts)
- Nginx muss nicht neu geladen werden
- DNS-Cache von 10 Sekunden für Performance

---

## 🚀 Network Management

### Network erstellen (falls gelöscht)

```bash
# Network erstellen
podman network create \
    --driver bridge \
    --subnet 10.89.0.0/24 \
    --gateway 10.89.0.1 \
    --opt com.docker.network.bridge.name=podman1 \
    seaser-network

# Network prüfen
podman network inspect seaser-network
```

### Container zum Network hinzufügen

**Beim Container-Start:**
```bash
podman run -d \
    --name meine-neue-app \
    --network seaser-network \
    localhost/meine-app:latest
```

**Existierenden Container verbinden:**
```bash
# Container zum Network hinzufügen
podman network connect seaser-network meine-neue-app

# Container vom Network trennen
podman network disconnect seaser-network meine-neue-app
```

### Network entfernen (VORSICHT!)

```bash
# Alle Container müssen gestoppt sein!
podman network rm seaser-network
```

**Warnung:** Dies entfernt die gesamte Netzwerk-Infrastruktur!

---

## 🔐 Security & Isolation

### Network-Isolation

- **Eingehend:** Nur `seaser-proxy` (Port 8000) ist von außen erreichbar
- **Intern:** Alle Container können sich gegenseitig erreichen
- **Ausgehend:** Alle Container haben Internet-Zugang (für Updates, APIs)

### Firewall-Regeln

```bash
# Host-Firewall (nur Port 8000 öffnen)
sudo firewall-cmd --zone=public --add-port=8000/tcp --permanent
sudo firewall-cmd --reload

# Ports prüfen
sudo firewall-cmd --list-ports
```

### Network-Security Best Practices

1. **Minimal Exposed Ports:** Nur seaser-proxy exponiert Ports
2. **Internal Communication:** Apps kommunizieren nur über seaser-network
3. **No Direct Access:** Backend-Apps nicht direkt vom Internet erreichbar
4. **Rate Limiting:** Nginx bietet Rate Limiting für externe Requests

---

## 📡 Port Mapping

### Exposed Ports

Nur der `seaser-proxy` Container exponiert Ports am Host:

```bash
# Port Mapping anzeigen
podman port seaser-proxy

# Output:
# 80/tcp -> 0.0.0.0:8000
# 443/tcp -> 0.0.0.0:8443
# 8444/tcp -> 0.0.0.0:8444
```

**Mapping:**
- Container Port 80 → Host Port 8000 (HTTP)
- Container Port 443 → Host Port 8443 (HTTPS)
- Container Port 8444 → Host Port 8444 (Alt HTTPS)

### Zugriff von extern

**LAN:**
```
http://192.168.2.139:8000/
```

**Tailscale VPN:**
```
http://100.x.x.x:8000/
```

**Internet (falls Port-Forwarding aktiv):**
```
https://deine-domain.de:8443/
```

---

## 🐛 Troubleshooting

### Problem: Container kann anderen Container nicht erreichen

```bash
# 1. Beide Container im gleichen Network?
podman ps --filter "name=seaser-inventar" --format "{{.Networks}}"
podman ps --filter "name=seaser-proxy" --format "{{.Networks}}"

# 2. DNS-Auflösung funktioniert?
podman exec seaser-proxy nslookup seaser-inventar

# 3. Ping-Test
podman exec seaser-proxy ping -c 3 seaser-inventar

# 4. Port erreichbar?
podman exec seaser-proxy nc -zv seaser-inventar 80
```

### Problem: DNS-Auflösung schlägt fehl

```bash
# 1. Network DNS aktiviert?
podman network inspect seaser-network | grep dns_enabled

# 2. Gateway erreichbar?
podman exec seaser-proxy ping 10.89.0.1

# 3. Container neu starten (DNS-Cache)
podman restart seaser-proxy
```

### Problem: 502 Bad Gateway (Nginx → Backend)

**Ursache:** Backend-Container nicht erreichbar

```bash
# 1. Backend läuft?
podman ps | grep seaser-inventar

# 2. Backend im richtigen Network?
podman inspect seaser-inventar --format '{{.NetworkSettings.Networks}}'

# 3. Backend-Logs prüfen
podman logs seaser-inventar

# 4. DNS-Test von Nginx
podman exec seaser-proxy nslookup seaser-inventar
```

### Problem: Container hat keine Internet-Verbindung

```bash
# 1. Gateway erreichbar?
podman exec seaser-inventar ping 10.89.0.1

# 2. DNS funktioniert?
podman exec seaser-inventar ping 8.8.8.8

# 3. Name-Resolution?
podman exec seaser-inventar ping google.com

# 4. Firewall blockiert?
sudo firewall-cmd --list-all
```

---

## 📊 Network Monitoring

### Traffic überwachen

```bash
# Netzwerk-Interface Traffic (Host)
sudo iftop -i podman1

# Container-Netzwerk-Stats
podman stats --no-stream

# Verbindungen anzeigen
podman exec seaser-proxy ss -tunap
```

### Network Performance testen

```bash
# Latenz zwischen Containern
podman exec seaser-proxy ping -c 10 seaser-inventar

# Durchsatz testen (mit iperf3)
podman exec seaser-proxy iperf3 -c seaser-inventar
```

---

## 🔄 Network Rebuild

Falls das Network komplett neu aufgesetzt werden muss:

```bash
# 1. Alle Container stoppen
podman stop $(podman ps -q --filter "network=seaser-network")

# 2. Container vom Network trennen
for container in $(podman ps -a --filter "network=seaser-network" --format "{{.Names}}"); do
    podman network disconnect seaser-network $container
done

# 3. Network entfernen
podman network rm seaser-network

# 4. Network neu erstellen
podman network create \
    --driver bridge \
    --subnet 10.89.0.0/24 \
    --gateway 10.89.0.1 \
    seaser-network

# 5. Container neu starten (automatisch verbunden wenn mit --network erstellt)
podman start $(podman ps -aq --filter "name=seaser-")
```

---

## 📝 Best Practices

### 1. Konsistente Naming Convention

```bash
# ✅ Gut: Präfix "seaser-"
seaser-proxy
seaser-gateway
seaser-inventar

# ❌ Schlecht: Inkonsistent
proxy
my-gateway
inventar-app
```

### 2. Network für alle seaser-Apps nutzen

```bash
# Beim Container-Start immer --network seaser-network
podman run -d \
    --name seaser-neue-app \
    --network seaser-network \
    localhost/neue-app:latest
```

### 3. Keine Host-Network Mode

```bash
# ❌ Vermeiden (kein Isolation)
podman run --network host ...

# ✅ Verwenden
podman run --network seaser-network ...
```

### 4. DNS-Namen verwenden (keine IPs)

```bash
# ✅ Gut: DNS-Name
proxy_pass http://seaser-inventar:80/;

# ❌ Schlecht: IP (ändert sich bei Restart)
proxy_pass http://10.89.0.15:80/;
```

### 5. Port-Exposition minimieren

```bash
# Nur seaser-proxy exponiert Ports
podman run -d \
    --name seaser-proxy \
    --network seaser-network \
    -p 8000:80 \
    localhost/seaser-proxy:latest

# Backend-Apps OHNE -p Flag
podman run -d \
    --name seaser-inventar \
    --network seaser-network \
    localhost/seaser-inventar:latest
```

---

## 🔗 Weiterführende Dokumentation

- **NGINX-PROXY.md** - Nginx Reverse Proxy Konfiguration
- **README.md** - Haupt-Übersicht über seaser Multi-App Setup
- **[Podman Network Docs](https://docs.podman.io/en/latest/markdown/podman-network.1.html)** - Offizielle Podman Dokumentation

---

**Erstellt:** 2025-11-07
**Version:** 1.0
**Maintainer:** seaser DevOps Team
