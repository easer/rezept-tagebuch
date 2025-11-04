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

## TODO Liste UX Pattern

### Swipe-to-Delete Geste

TODOs können durch Wischen nach links gelöscht werden. Dies bietet eine intuitive mobile-first UX.

**Implementierung:**
```javascript
function initSwipeToDelete(item) {
    const content = item.querySelector('.todo-content');
    let startX = 0;
    let currentX = 0;
    let isSwiping = false;
    let hasMoved = false;
    const deleteThreshold = -100;  // Pixel nach links zum Löschen
    const moveThreshold = 10;      // Minimum Bewegung für Geste

    // Touch und Mouse Events registrieren
    content.addEventListener('touchstart', handleTouchStart);
    content.addEventListener('touchmove', handleTouchMove);
    content.addEventListener('touchend', handleTouchEnd);

    // Mouse-Support für Desktop
    content.addEventListener('mousedown', handleMouseStart);
}
```

**Wichtige Parameter:**
- `deleteThreshold: -100px` - Wie weit nach links gewischt werden muss
- `moveThreshold: 10px` - Verhindert versehentliches Löschen bei einfachem Touch
- `hasMoved: boolean` - Nur löschen wenn echte Swipe-Bewegung stattfand

**Visuelle Feedback:**
- Roter Hintergrund mit "Löschen" Text erscheint beim Wischen
- Smooth transitions mit CSS `transform: translateX()`

### Prioritäten mit Pastellfarben

TODOs haben keine separaten Sektionen mehr. Stattdessen wird die Priorität durch farbige Borders visualisiert.

**Border-Farben:**
```css
.todo-item[data-priority="1"] {
    border-left: 4px solid #FFB5C0; /* Rosa Pastell - Hoch */
}

.todo-item[data-priority="2"] {
    border-left: 4px solid #FFE66D; /* Gelb Pastell - Mittel */
}

.todo-item[data-priority="3"] {
    border-left: 4px solid #AED9E0; /* Blau Pastell - Niedrig */
}
```

**Sortierung:**
- TODOs werden nach Priorität sortiert (1 → 2 → 3)
- Innerhalb gleicher Priorität nach Erstellungsdatum

**Vorteile:**
- Kompaktere Darstellung ohne Sektions-Header
- Visuelle Gruppierung durch Farbe
- Schneller Überblick über wichtige Aufgaben

### Kompakte TODO-Darstellung

Alle TODOs haben eine feste Höhe für konsistente Darstellung.

**CSS:**
```css
.todo-item {
    height: 56px;
    overflow: hidden;
    touch-action: pan-y;  /* Nur vertikales Scrollen erlauben */
}

.todo-text {
    display: -webkit-box;
    -webkit-line-clamp: 2;  /* Maximal 2 Zeilen */
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
}
```

**Vorteile:**
- Alle TODO-Items haben gleiche Höhe (56px)
- Maximale 2 Zeilen Text sichtbar
- Lange Texte werden mit "..." gekürzt
- Voller Text im Detail-View sichtbar

### TODO Detail-View

Click auf TODO öffnet Slide-Panel mit vollständigem Text und Bearbeitungsmöglichkeit.

**Features:**
- Vollständiger TODO-Text lesbar
- In-Place Bearbeitung (kein separates Edit-Formular)
- Priorität ändern
- Erledigt-Status togglen
- Löschen mit Bestätigung

**API-Endpoint:**
```python
@app.route('/api/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    """Einzelnes TODO abrufen"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM todos WHERE id = ?', (todo_id,))
    todo = c.fetchone()
    if todo:
        return jsonify(dict(todo))
    return jsonify({'error': 'TODO not found'}), 404
```

## Sticky Header & Scrolling Layout

### Architektur

Die App verwendet ein flexbox-basiertes Layout mit sticky Header und scrollbarem Content.

**Container-Struktur:**
```css
.container {
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

header {
    padding-top: 40px;  /* Abstand von oben */
    flex: 0 0 auto;     /* Nimmt nur benötigten Platz */
    z-index: 10;
}

.tabs {
    flex: 0 0 auto;
    margin-top: 25px;
}

.tab-content {
    display: flex;
    flex-direction: column;
    overflow-y: auto;   /* Nur Content scrollt */
    flex: 1;            /* Nimmt restlichen Platz */
    min-height: 0;      /* Wichtig für Flexbox-Shrinking */
}
```

**Wichtige Regeln:**
1. `overflow: hidden` auf Container verhindert doppeltes Scrollen
2. `flex: 0 0 auto` auf Header/Tabs verhindert Shrinking
3. `flex: 1` auf Content füllt restlichen Raum
4. `overflow-y: auto` nur auf Content aktiviert Scrollen
5. `min-height: 0` ermöglicht korrektes Shrinking

### Globale Suchleiste

Die Suchleiste ist sticky und bleibt beim Scrollen sichtbar.

**Position:**
```css
.global-search {
    background: rgba(40, 50, 60, 0.7);
    backdrop-filter: blur(20px);
    border-radius: 16px;
    padding: 15px 20px;
    flex: 0 0 auto;
    position: relative;
    z-index: 50;  /* Über Content, unter Modals */
}
```

**Input-Field Best Practices:**
```html
<input type="text"
       id="global-search-input"
       autocomplete="off"
       autocorrect="off"
       autocapitalize="off"
       spellcheck="false">
```

**Wichtig:**
- `autocomplete="off"` verhindert Browser-Autofill-Dropdown
- `z-index: 50` sorgt dafür, dass Input über Content liegt
- `box-sizing: border-box` für korrekte Breiten-Berechnung
- `caret-color: white` für sichtbaren Cursor

### Floating Action Button (FAB)

Ein globaler Plus-Button ersetzt die individuellen "Neu"-Buttons in jedem Tab.

**CSS:**
```css
.floating-add-btn {
    position: fixed;
    bottom: 30px;
    right: 30px;
    width: 56px;
    height: 56px;
    border-radius: 50%;
    background: linear-gradient(135deg, #FFB5C0 0%, #FFC9D6 100%);
    box-shadow: 0 4px 20px rgba(255, 181, 192, 0.5);
    z-index: 100;
    transition: transform 0.3s ease;
}

.floating-add-btn:hover {
    transform: scale(1.1) rotate(90deg);
}
```

**Context-Aware Behavior:**
```javascript
function handleFloatingAdd() {
    switch(currentTab) {
        case 'tagebuch': showAddDiaryPanel(); break;
        case 'rezepte': showAddPanel(); break;
        case 'todos': showAddTodoDialog(); break;
    }
}
```

**Vorteile:**
- Ein Button für alle Tabs
- Immer an gleicher Position (Muskelgedächtnis)
- Freier Content-Bereich (keine Button-Zeile)
- Smooth hover-Animation

## Globale Kontext-Suche

Die Suche passt sich automatisch an den aktiven Tab an.

**Implementierung:**
```javascript
function handleGlobalSearch() {
    const searchTerm = document.getElementById('global-search-input').value;

    switch(currentTab) {
        case 'tagebuch': loadDiaryEntries(searchTerm); break;
        case 'rezepte': filterRecipes(searchTerm); break;
        case 'todos': filterTodos(searchTerm); break;
    }
}
```

**TODO-Filterung:**
```javascript
function filterTodos(searchTerm) {
    if (!searchTerm.trim()) {
        renderTodos(allTodos);  // Alle anzeigen
        return;
    }
    const filtered = allTodos.filter(todo =>
        todo.text.toLowerCase().includes(searchTerm.toLowerCase())
    );
    renderTodos(filtered);
}
```

**Tab-Switch Behavior:**
- Suchfeld wird beim Tab-Wechsel geleert
- Verhindert verwirrende Suchergebnisse in falschem Tab

**Placeholder:**
- Universell: "🔍 Suchen..."
- Context-Aware Suche durch Tab-Erkennung

## Entwicklungs-Workflow

1. **Immer globales CSS nutzen** - Keine inline-styles für Layout-Properties
2. **Testen auf iPhone-Breite** - Sicherstellen, dass keine horizontale Scrollbar erscheint
3. **Konsistente Abstände** - Alle `.form-group` haben 20px Abstand
4. **Box-sizing beachten** - Immer `border-box` für Elemente mit width: 100%
5. **CRUD-Pattern befolgen** - Alle Entitäten verwenden das gleiche Pattern
6. **Pastellfarben verwenden** - Alle visuellen Elemente folgen dem Pastellfarben-Schema
7. **Kompakt halten** - Karten und Übersichten sollen kompakt und übersichtlich sein
8. **Swipe-Gesten testen** - Mindestens 10px Bewegung vor Aktion erforderlich
9. **Autocomplete deaktivieren** - Bei Suchfeldern immer `autocomplete="off"` setzen
10. **Z-Index Management** - Header: 10, Search: 50, FAB: 100, Modals: 1000
