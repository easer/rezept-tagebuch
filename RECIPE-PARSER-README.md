# Strukturierte Rezept-Darstellung (In Entwicklung)

## Übersicht

Das System parst Rezept-Notizen und stellt sie strukturiert dar mit automatischer Erkennung von:
- **Zubereitungsschritten** (SCHRITT 1, SCHRITT 2, etc.)
- **Zutaten** (Bullet-Listen mit Mengenangaben)
- **Metadaten** (Quelle, Kategorie, Region, etc.)

## Status: 🚧 IN ENTWICKLUNG

Die Grundfunktionalität ist implementiert, aber noch nicht vollständig getestet.

### Implementiert:
- ✅ Config-Datei mit Parsing-Regeln (`recipe-format-config.json`)
- ✅ Parser-Funktion mit Regex-Erkennung
- ✅ CSS Styling für strukturierte Darstellung
- ✅ Integration in Detail-Ansicht
- ✅ Normalisierung von Line-Endings (`\r\n` → `\n`)
- ✅ Erkennung von "Zutaten:" Header-Zeile
- ✅ Debug-Logging in Browser Console

### Offen / Zu testen:
- ⚠️ Parser-Funktion auf echten Daten testen
- ⚠️ CSS-Styling im Browser verifizieren
- ⚠️ Regex-Patterns ggf. anpassen
- ⚠️ Edge-Cases behandeln (leere Sections, etc.)

## Architektur

### 1. Konfiguration (`recipe-format-config.json`)

```json
{
  "patterns": {
    "steps": {
      "regex": "^(SCHRITT \\d+|\\d+\\.|Step \\d+)",
      "section": "Zubereitung"
    },
    "ingredients": {
      "regex": "^[-•*]\\s*(\\d+|\\d+[.,]\\d+)?\\s*(g|kg|ml|...)",
      "section": "Zutaten"
    },
    "metadata": {
      "patterns": ["^🌍\\s*Quelle:", "^📖\\s*Original:", ...]
    }
  },
  "sections": {
    "order": ["Zubereitung", "Zutaten", "Metadaten"],
    "display": { ... }
  }
}
```

### 2. Parser-Funktionen (`index.html`)

#### `loadRecipeFormatConfig()`
- Lädt Config-File einmalig beim ersten Aufruf
- Cached in `recipeFormatConfig` Variable

#### `parseRecipeNotes(notes)`
- Normalisiert Line-Endings
- Splittet Text in Zeilen
- Erkennt Sections mit Regex-Patterns
- Behandelt "Zutaten:" Header speziell
- Gibt strukturiertes Objekt zurück:
  ```javascript
  {
    hasStructure: boolean,
    sections: {
      'Zubereitung': [...],
      'Zutaten': [...],
      'Metadaten': [...],
      'Sonstiges': [...]
    },
    raw: originalText
  }
  ```

#### `renderStructuredNotes(parsedNotes)`
- Rendert Sections in definierter Reihenfolge
- Verwendet Display-Config für Styling
- Fallback auf Plaintext wenn keine Struktur

### 3. CSS Styling (`index.html`)

```css
/* Section Titles */
.recipe-section-title {
  color: #FFD700;
  border-bottom: 2px solid rgba(255, 215, 0, 0.3);
}

/* Preparation Steps */
.recipe-steps li {
  margin-bottom: 24px;
  line-height: 1.8;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

/* Ingredients List */
.recipe-ingredients li {
  margin-bottom: 6px;
  line-height: 1.4;
}

/* Metadata */
.recipe-metadata {
  background: rgba(255, 255, 255, 0.05);
  border-left: 3px solid rgba(255, 215, 0, 0.5);
}
```

### 4. Integration in Detail-Ansicht

```javascript
async function renderDetailView(recipe) {
  await loadRecipeFormatConfig();
  const parsedNotes = recipe.notes ? parseRecipeNotes(recipe.notes) : null;

  // ... render with renderStructuredNotes(parsedNotes)
}
```

## Beispiel-Rezept-Format (TheMealDB)

```
SCHRITT 1

Alle Zutaten, außer den Sardinen, in eine Schüssel geben...

SCHRITT 2

Erhitzen Sie einen Grill oder eine Grillpfanne...

Zutaten:
- 8 Sardinen
- 2 Esslöffel Olivenöl
- 3 Gewürznelken Knoblauch
- 1 Esslöffel Paprika

─────────────────────────
🌍 Quelle: TheMealDB
📖 Original: Grilled Portuguese sardines
🏷️ Kategorie: Seafood
🌎 Region: Portuguese
🤖 Übersetzt mit DeepL
```

## Debugging

### Browser Console Logs aktiviert:

1. Öffne ein Rezept mit Notizen in der Detail-Ansicht
2. Öffne Browser Console (F12)
3. Schaue nach folgenden Logs:
   - `parseRecipeNotes called with: ...`
   - `recipeFormatConfig: {...}`
   - `Total lines: X`
   - `Parsed sections: {...}`

### Häufige Probleme:

1. **"Sehe keine Struktur"**
   - Config-File wird geladen? (Check Network Tab)
   - Parser wird aufgerufen? (Check Console Logs)
   - Regex matched? (Check "Parsed sections" Counts)

2. **"CSS Änderungen nicht sichtbar"**
   - Hard Refresh (Ctrl+Shift+R)
   - Container neu deployed?
   - Browser Cache löschen

3. **"Zutaten werden nicht erkannt"**
   - "Zutaten:" Header vorhanden?
   - Zeilen beginnen mit "-"?
   - Line-Endings korrekt? (sollte durch Normalisierung gefixt sein)

## Nächste Schritte

1. **Testen auf echten Daten**
   - Rezept ID 159 öffnen ("Gegrillte portugiesische Sardinen")
   - Console Logs prüfen
   - Darstellung verifizieren

2. **Parser-Verbesserungen**
   - Weitere Rezept-Formate unterstützen
   - Edge-Cases behandeln
   - Performance optimieren

3. **UI/UX Optimierungen**
   - Abstände feinjustieren
   - Farben anpassen
   - Mobile Ansicht testen

4. **Config erweitern**
   - Neue Section-Types (Tipps, Variationen)
   - Weitere Regex-Patterns
   - Mehrsprachigkeit

## Dateien

- `recipe-format-config.json` - Parser-Konfiguration
- `index.html` - Parser-Logik und CSS (Zeilen ~2700-2900)
- `app.py` - Route für Config-File (Zeile 171-173)
- `Containerfile` - Config-File in Container kopieren (Zeile 13)

## Test-Rezepte in Dev-DB

- ID 159: "Gegrillte portugiesische Sardinen" (TheMealDB Format mit Struktur)
- ID 156-158: Englische Rezepte ohne Struktur (Fallback auf Plaintext)
