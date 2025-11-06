# DeepL Translation Integration

## Übersicht
Die App kann TheMealDB-Rezepte automatisch von Englisch nach Deutsch übersetzen mit der DeepL API.

## Features
- ✅ Automatische Übersetzung von Titel, Anleitung und Zutaten
- ✅ Original-Titel bleibt in den Notizen erhalten
- ✅ Optional - funktioniert auch ohne API Key (dann auf Englisch)
- ✅ Free Tier: 500.000 Zeichen/Monat (≈1.000 Rezepte)

## Setup

### 1. DeepL API Key holen

**Registrierung:**
1. Gehe zu: https://www.deepl.com/en/pro#developer
2. Klick "Sign up for free" → Wähle "DeepL API Free"
3. Account erstellen (Email + Passwort)
4. Kreditkarte angeben (nur zur Verifizierung, **wird nicht belastet**)
5. API Key holen: https://www.deepl.com/en/your-account/keys

**Free Tier:**
- 500.000 Zeichen/Monat kostenlos
- Keine Kosten bei normaler Nutzung
- Email-Benachrichtigung bei 80% Verbrauch

### 2. API Key konfigurieren

**Option A: .env Datei (Empfohlen für lokale Entwicklung)**
```bash
cp .env.example .env
nano .env
# DEEPL_API_KEY=dein-key-hier-einfügen
```

**Option B: Umgebungsvariable**
```bash
export DEEPL_API_KEY='your-api-key-here'
```

**Option C: Docker/Podman Container**
```bash
# In build-dev.sh oder build-prod.sh
podman run -e DEEPL_API_KEY='your-key' ...
```

**Option D: SystemD Service**
```bash
# In rezept-daily-import.service
[Service]
Environment="DEEPL_API_KEY=your-key"
```

### 3. Testen

**Test-Script ausführen:**
```bash
./scripts/deployment/test-deepl.sh
# Gibt API Key ein wenn gefragt
```

**Erwartete Ausgabe:**
```json
{
    "translations": [
        {
            "detected_source_language": "EN",
            "text": "Pilzsuppe mit Buchweizen"
        }
    ]
}
```

### 4. Rezept importieren (mit Übersetzung)

**Manueller Test:**
```bash
export DEEPL_API_KEY='your-key'
curl -X POST http://localhost/rezept-tagebuch/api/recipes/daily-import
```

**Automatisch täglich um 6:00 Uhr:**
- SystemD Timer führt Import aus
- Liest API Key aus .env oder Environment
- Übersetzt automatisch wenn Key vorhanden

## Funktionsweise

### Ohne API Key
```
TheMealDB (EN) → App → DB
"Mushroom soup" → "Mushroom soup" (englisch)
```

### Mit API Key
```
TheMealDB (EN) → DeepL → App → DB
"Mushroom soup" → "Pilzsuppe" (deutsch)
```

### Was wird übersetzt?

1. **Titel:** `strMeal`
   - "Parkin Cake" → "Parkin-Kuchen"

2. **Anleitung:** `strInstructions`
   - "Preheat the oven..." → "Den Ofen vorheizen..."

3. **Zutaten:** `strIngredient1-20` + `strMeasure1-20`
   - "2 cups flour" → "2 Tassen Mehl"
   - "1 tsp salt" → "1 TL Salz"

### Gespeicherte Informationen

```
Titel: Pilzsuppe mit Buchweizen

Anleitung (übersetzt):
Die Pilze in kleine Stücke schneiden...

Zutaten:
- 200g Champignons
- 100g Buchweizen
- 1 Liter Gemüsebrühe

─────────────────────────
🌍 Quelle: TheMealDB
📖 Original: Mushroom soup with buckwheat
🏷️ Kategorie: Soup
🌎 Region: Russian
🤖 Übersetzt mit DeepL
```

## Fehlerbehebung

### API Key funktioniert nicht
```bash
# Test ob Key korrekt ist
./scripts/deployment/test-deepl.sh

# Prüfe Logs
podman logs seaser-rezept-tagebuch-dev | grep DeepL

# Erwartete Ausgabe:
# "Warning: No DeepL API key configured, skipping translation"
# ODER
# "DeepL translation error: ..."
```

### Übersetzung fehlgeschlagen
**Fallback:** Bei Fehler wird der englische Original-Text verwendet.

**Mögliche Ursachen:**
- API Key ungültig
- Limit erreicht (500k Zeichen/Monat)
- Netzwerk-Problem
- DeepL API down

**Logs prüfen:**
```bash
podman logs seaser-rezept-tagebuch
# Suche nach "DeepL translation error"
```

### Limit erreicht
**Email von DeepL:** "80% of your monthly quota used"

**Optionen:**
1. Warten bis nächster Monat (Reset am 1.)
2. Upgrade auf DeepL API Pro
3. Temporär ohne Übersetzung (englische Rezepte)

**Aktuelles Limit prüfen:**
- Login: https://www.deepl.com/en/your-account/usage
- Zeigt: Verbrauchte Zeichen / 500.000

## Kosten

### Free Tier (aktuell)
- 500.000 Zeichen/Monat
- 1 Rezept ≈ 500 Zeichen
- → ~1.000 Rezepte/Monat
- Bei täglichem Import: 30 Rezepte/Monat = **6% des Limits**

### DeepL API Pro (optional)
- Ab $5.49/Monat
- Pay-as-you-go: $25 per 1M Zeichen
- Unbegrenzte Zeichen

## Datenschutz

**DeepL Datenschutz-Policy:**
- Texte werden **nicht gespeichert**
- Keine Verwendung für Training
- DSGVO-konform
- Server in Deutschland/EU

**Übertragene Daten:**
- Rezept-Titel
- Anleitung
- Zutaten
- **Keine** Bilder oder persönliche Daten

## Code-Referenzen

### Backend (app.py)
- Zeile 978-1009: `translate_to_german()` Funktion
- Zeile 1045-1078: Translation im daily-import
- Zeile 1092: Translated title in DB speichern

### Konfiguration
- `.env.example`: API Key Template
- `test-deepl.sh`: Test-Script
- `rezept-daily-import.service`: SystemD mit EnvironmentFile

## Status

**Aktuell:** ✅ Implementiert, optional aktivierbar
**Deployment:** Wartet auf API Key
**Fallback:** Funktioniert ohne Key (englische Rezepte)

---

**Letzte Änderung:** 2025-11-05
**Dokumentiert von:** Claude Code
