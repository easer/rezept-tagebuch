# UX Guide - Rezept-Tagebuch App

## CSS-Regeln und Best Practices

### Form Layout

#### Abstände zwischen Formular-Feldern

Alle `.form-group` Elemente haben einen konsistenten `margin-bottom: 20px` für einheitliche vertikale Abstände.

**Wichtig:** Bei `.form-group.textarea-group` muss `!important` verwendet werden:

```css
.form-group.textarea-group {
    align-items: flex-start;
    margin-bottom: 20px !important;
}
```

**Grund:** Ohne `!important` kann eine andere CSS-Regel mit höherer Spezifität oder durch CSS-Cascade den margin-bottom überschreiben, was dazu führt, dass die Textarea direkt am nächsten Element klebt (kein vertikaler Abstand).

**Beispiel-Problem:**
- NOTIZEN Textarea klebt am BILDER Input-Feld
- Visuell sieht es aus als hätte `.form-group` keinen Abstand

**Lösung:** Das `!important` Flag erzwingt, dass diese Regel immer angewendet wird, unabhängig von anderen CSS-Regeln.

### Responsive Design (iPhone)

Alle Formular-Felder verwenden das globale `.form-group` Layout:

```css
.form-group {
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 15px;
}

.form-group input,
.form-group select {
    flex: 1;
    min-width: 0;
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
}
```

**Wichtig:**
- Keine inline-styles für `display: grid` oder custom column layouts verwenden
- Immer `box-sizing: border-box` verwenden, damit Padding in width-Berechnung einbezogen wird
- `min-width: 0` ermöglicht korrektes Shrinking in Flex-Containern

### Date Input Felder

Date-Input-Felder verwenden das gleiche CSS wie alle anderen Input-Felder. Kein spezielles CSS notwendig!

```html
<div class="form-group">
    <label>Datum</label>
    <input type="date" id="entry-date" required>
</div>
```

**Kalender-Icon verstecken:**
```css
.form-group input[type="date"]::-webkit-calendar-picker-indicator {
    display: none;
}
```

### File Input Felder

**Für Tagebuch-Formulare:** Verwende die Standard `.form-group` ohne `file-group` Klasse:

```html
<div class="form-group">
    <label>Bilder</label>
    <input type="file" id="entry-images" multiple accept="image/*">
</div>
```

**Für Rezept-Formulare:** Verwende `.form-group.file-group` (hat `margin-bottom: 0` weil danach `#file-preview` folgt)

### Button-Größen

Alle Buttons haben eine Mindesthöhe von **28px** für konsistente Touch-Targets auf mobilen Geräten.

```css
button {
    height: 28px;
    /* ... */
}
```

### Icons und Symbole

**Regel:** Keine Emojis oder Symbole verwenden, außer wenn explizit gewünscht.

**Beispiel:**
```javascript
// ❌ Falsch:
<p class="recipe-date">📅 ${formatDate(entry.date)}</p>

// ✅ Richtig:
<p class="recipe-date">${formatDate(entry.date)}</p>
```

**Grund:** Symbole können auf verschiedenen Geräten unterschiedlich dargestellt werden und sollten nur verwendet werden, wenn sie explizit Teil des Designs sind.

## Lessons Learned

### Problem: Horizontale Scrollbar auf iPhone

**Ursache:** Verwendung von `display: grid; grid-template-columns: 80px 1fr; gap: 15px;` mit inline-styles überschreibt das globale `.form-group` CSS.

**Lösung:** Immer das globale `.form-group` CSS verwenden, das mit `display: flex` arbeitet.

### Problem: Date-Input ragt über Bildschirm hinaus

**Ursache:** Spezifisches CSS für date-Input mit `width: auto; min-width: 180px` ignoriert Container-Breite.

**Lösung:** Kein spezielles CSS für date-Input - nutze das globale Input-CSS mit `width: 100%; max-width: 100%; box-sizing: border-box;`

### Problem: Textarea klebt am nächsten Element

**Ursache:** CSS-Spezifität - eine andere Regel überschreibt den `margin-bottom`.

**Lösung:** `margin-bottom: 20px !important;` auf `.form-group.textarea-group` verwenden.

## CRUD-Operationen Prinzip

Alle Entitäten (Rezepte, Tagebucheinträge, TODOs, etc.) folgen dem gleichen CRUD-Pattern:

### Create (Erstellen)

**Frontend:**
1. Button "Neuer [Entität]" öffnet Slide-Panel
2. Formular mit `.form-group` Layout
3. `async function create[Entität]()` sammelt Formulardaten
4. `POST /api/[entität]` erstellt neuen Eintrag
5. Bei Erfolg: Panel schließen und Liste neu laden

**Backend:**
```python
@app.route('/api/[entität]', methods=['POST'])
def create_[entität]():
    data = request.json
    # Insert into database
    return jsonify(new_item), 201
```

### Read (Lesen)

**List View:**
```python
@app.route('/api/[entität]', methods=['GET'])
def get_[entität]():
    # SELECT * FROM [entität] ORDER BY created_at DESC
    return jsonify(items)
```

**Detail View:**
```python
@app.route('/api/[entität]/<int:id>', methods=['GET'])
def get_[entität]_detail(id):
    # SELECT * FROM [entität] WHERE id = ?
    return jsonify(item)
```

### Update (Aktualisieren)

**Frontend:**
1. Click auf Eintrag öffnet Detail-View im Slide-Panel
2. "Bearbeiten" Button lädt Formular mit vorausgefüllten Daten
3. `async function update[Entität](id)` sendet geänderte Daten
4. `PUT /api/[entität]/<id>` aktualisiert Eintrag

**Backend:**
```python
@app.route('/api/[entität]/<int:id>', methods=['PUT'])
def update_[entität](id):
    data = request.json
    # UPDATE [entität] SET ... WHERE id = ?
    return jsonify(updated_item)
```

### Delete (Löschen)

**Frontend:**
1. "Löschen" Button in Detail-View
2. Bestätigungs-Dialog (optional)
3. `DELETE /api/[entität]/<id>` löscht Eintrag
4. Panel schließen und Liste neu laden

**Backend:**
```python
@app.route('/api/[entität]/<int:id>', methods=['DELETE'])
def delete_[entität](id):
    # DELETE FROM [entität] WHERE id = ?
    return jsonify({'success': True})
```

### CRUD Pattern-Konsistenz

**Wichtig:** Alle CRUD-Operationen folgen diesem Pattern:

1. **Namenskonvention:**
   - Frontend: `create[Entität]()`, `update[Entität]()`, `delete[Entität]()`
   - Backend: `/api/[entität]` mit HTTP-Methoden (POST, GET, PUT, DELETE)

2. **Panel-Verwaltung:**
   - Immer `openPanel()` und `closePanel()` verwenden
   - `panel-title`, `panel-content`, `panel-actions` IDs nutzen

3. **Error Handling:**
   - Immer try-catch in async functions
   - Bei Fehler: `alert()` mit Fehlermeldung
   - Bei Erfolg: Panel schließen und Liste neu laden

4. **Datenbank-Schema:**
   - Jede Tabelle hat `id`, `created_at`, `updated_at`
   - Foreign Keys mit `ON DELETE SET NULL` oder `ON DELETE CASCADE`
   - Timestamps mit `DEFAULT CURRENT_TIMESTAMP`

### Beispiel: Tagebucheinträge CRUD

**Übersicht:**
- Create: `showCreateDiaryEntry()` → `saveDiaryEntry()` → `POST /api/diary`
- Read: `showDiaryEntries()` → `GET /api/diary`
- Update: `showEditDiaryEntry(id)` → `saveDiaryEntry()` → `PUT /api/diary/<id>`
- Delete: `deleteDiaryEntry(id)` → `DELETE /api/diary/<id>`

**Gleiche Struktur für:**
- Rezepte (`/api/recipes`)
- TODOs (`/api/todos`)
- Alle zukünftigen Entitäten

## Design-System

### Farben

**Pastellfarben für Text:**
- Sacramento-Schrift verwendet Pastellfarben-Gradient für jeden Buchstaben
- Rating-Sterne: `#F4E5A0` (gelber Pastell)

**Rating-Sterne:**
- Alle Ratings (Übersicht, Detail, Edit) verwenden `#F4E5A0`
- Konsistente gelbe Pastellfarbe für alle Sterne

### Typografie

**Header:**
- Font: Sacramento (Google Fonts)
- Größe: 3.5em (Desktop), responsiv bis 1.9em (360px)
- Farben: Pastellfarben-Gradient mit drop-shadow für dickeren Effekt
- Transform: `rotate(-2deg)` für geschwungenen Effekt

**Karten-Überschriften:**
- Rezepte & Tagebuch: `font-size: 0.95em`
- Kompakt für bessere Übersicht

**Meta-Informationen:**
- Datum, Zeitdauer: `font-size: 0.8em`
- Rating: `font-size: 0.95em`

### Layout-Komponenten

**Karten (recipe-card):**
- Padding: `14px` (kompakt)
- Border-Radius: `12px`
- Hover: `translateY(-3px)` (subtil)

**Meta-Container:**
```css
.recipe-meta {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}
```
- Zeitdauer und Rating werden nebeneinander angezeigt
- Automatisches Wrapping bei kleinen Bildschirmen

### Suchfunktion

**Tagebuch:**
- Placeholder: "🔍 Eintrag suchen..."
- Backend sucht in: `dish_name`, `notes`, `recipe_title`

**Rezepte:**
- Placeholder: "🔍 Rezept suchen..."
- Backend sucht in: `title`, `notes`

**Implementierung:**
- 300ms Debounce für flüssiges Tippen
- URL-Parameter: `?search={term}`

### Dialoge

**Lösch-Bestätigung:**
- Verwende `showConfirm()` für konsistentes UX
- Gleicher Dialog für Rezepte und Tagebucheinträge
- Titel: "[Entität] löschen?"
- Nachricht: "Diese Aktion kann nicht rückgängig gemacht werden."

**TODO-Dialog:**
- Beschreibungsfeld ist `<textarea>` mit 4 Zeilen
- Unterstützt mehrzeilige Eingaben
- `resize: vertical` aktiviert

### Kompakte Darstellung

**Rezepte-Übersicht:**
- Zeigt nur: Name, Zeitdauer, Rating
- Notizen werden ausgeblendet

**Tagebuch-Übersicht:**
- Zeigt nur: Name, Datum
- Bilder und Notizen werden ausgeblendet

## Entwicklungs-Workflow

1. **Immer globales CSS nutzen** - Keine inline-styles für Layout-Properties
2. **Testen auf iPhone-Breite** - Sicherstellen, dass keine horizontale Scrollbar erscheint
3. **Konsistente Abstände** - Alle `.form-group` haben 20px Abstand
4. **Box-sizing beachten** - Immer `border-box` für Elemente mit width: 100%
5. **CRUD-Pattern befolgen** - Alle Entitäten verwenden das gleiche Pattern
6. **Pastellfarben verwenden** - Alle visuellen Elemente folgen dem Pastellfarben-Schema
7. **Kompakt halten** - Karten und Übersichten sollen kompakt und übersichtlich sein
