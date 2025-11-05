# Cursor Bug Debug Protokoll

## Problem Beschreibung
**Symptom:** Cursor blinkt nicht im Suchfeld beim Tippen/Klicken. Cursor erscheint außerhalb (oben links) beim ersten Click und kommt erst beim zweiten Click ins Feld rein.

**Beobachtung vom User:**
- Cursor blinkt außen links beim ersten Fingerdruck
- Cursor kommt erst beim zweiten Fingerdruck ins Feld
- Cursor kommt mit dem Screen mit, wenn man runter zieht
- Problem trat auf, nachdem der Header als fixed mit Titel, Tabs und Suchfeld definiert wurde

## Versuchte Lösungen

### Versuch 1: switchTab() Bug Fix
**Datum:** 2025-11-05
**Problem identifiziert:** `event.target` in `switchTab()` Funktion nicht definiert
**Änderung:**
```javascript
// VORHER
function switchTab(tabName) {
    event.target.classList.add('active'); // ❌ event nicht definiert
}

// NACHHER
function switchTab(tabName) {
    document.querySelector(`[onclick*="switchTab('${tabName}')"]`)?.classList.add('active');
}
```
**Ergebnis:** ❌ Problem bleibt bestehen

---

### Versuch 2: z-index Erhöhung
**Datum:** 2025-11-05
**Theorie:** Suchfeld liegt unter Header/Tabs
**Änderung:**
```css
/* VORHER */
.global-search {
    z-index: 50;
}

/* NACHHER */
.global-search {
    z-index: 101; /* Höher als Header (100) und Tabs (99) */
}
```
**Ergebnis:** ❌ Problem bleibt bestehen

---

### Versuch 3: Suchfeld aus <main> herausnehmen
**Datum:** 2025-11-05
**Theorie:** Suchfeld war im scrollbaren <main> Container
**Änderung HTML:**
```html
<!-- VORHER -->
<div class="container">
    <main>
        <div class="global-search">...</div>
    </main>
</div>

<!-- NACHHER -->
<div class="container">
    <main>
        <!-- Suchfeld entfernt -->
    </main>
</div>
<div class="global-search">...</div> <!-- Außerhalb von main -->
```
**Änderung CSS:**
```css
.global-search {
    position: fixed;
    top: 190px;
    /* ... */
}
```
**Ergebnis:** ⚠️ Suchfeld scrollt nicht mehr mit, aber Cursor-Problem bleibt

---

### Versuch 4: Suchfeld-Position anpassen
**Datum:** 2025-11-05
**Theorie:** Suchfeld überlappt mit Tabs
**Änderung:**
```css
/* VORHER */
.global-search {
    top: 190px;
    padding: 0;
}

/* NACHHER */
.global-search {
    top: 215px; /* Weiter runter */
    padding: 0 20px;
}

.container {
    padding-top: 285px; /* Mehr Platz */
}
```
**Ergebnis:** ✅ Position besser, aber ❌ Cursor-Problem bleibt

---

### Versuch 5: Header/Tabs/Suchfeld aus Container verschieben
**Datum:** 2025-11-05
**Theorie:** Header lässt sich hochschieben, weil er im scrollbaren Container liegt
**Änderung HTML:**
```html
<!-- VORHER -->
<div class="container">
    <header>...</header>
    <div class="tabs">...</div>
    <div class="global-search">...</div>
    <main>...</main>
</div>

<!-- NACHHER -->
<header>...</header>
<div class="tabs">...</div>
<div class="global-search">...</div>
<div class="container">
    <main>...</main>
</div>
```
**Ergebnis:** ✅ Header jetzt wirklich fixed, aber ❌ Cursor-Problem bleibt

---

### Versuch 6: onclick Handler auf Container
**Datum:** 2025-11-05
**Theorie:** Click auf Container-Div statt Input
**Änderung:**
```html
<div class="global-search" onclick="document.getElementById('global-search-input').focus()">
    <input id="global-search-input" ...>
</div>
```
**Ergebnis:** ❌ Problem bleibt, Cursor springt nach oben links

---

### Versuch 7: User-Info z-index Fix
**Datum:** 2025-11-05
**Nebenproblem:** User-Info Symbol verschwunden
**Änderung:**
```css
/* VORHER */
.user-info { z-index: 100; }
.version-badge { z-index: 1000; }
.refresh-button { z-index: 1000; }

/* NACHHER - Alle auf gleicher Ebene */
.user-info { z-index: 101; }
.version-badge { z-index: 101; }
.refresh-button { z-index: 101; }
```
**Ergebnis:** ✅ UI-Elemente wieder sichtbar, aber ❌ Cursor-Problem bleibt

---

### Versuch 8: pointer-events Strategie
**Datum:** 2025-11-05
**Theorie:** Container fängt Clicks ab
**Änderung:**
```css
.global-search {
    pointer-events: none; /* Container ignoriert Clicks */
}

.global-search input {
    pointer-events: auto; /* Nur Input ist clickbar */
    touch-action: manipulation;
}

.search-dropdown {
    pointer-events: auto; /* Dropdown auch clickbar */
}
```
**Ergebnis:** ❌ Schlimmer! Cursor springt nach oben links, Clicks gehen "durch" Container

---

### Versuch 9: Container Positionierung vereinfachen
**Datum:** 2025-11-05
**Theorie:** transform: translateX() verursacht Probleme
**Änderung:**
```css
/* VORHER */
.global-search {
    left: 50%;
    transform: translateX(-50%);
    width: calc(100% - 40px);
    padding: 0 20px;
}

/* NACHHER */
.global-search {
    left: 20px;
    right: 20px;
    padding: 0;
}
```
**Zusätzlich:**
```css
.global-search input {
    -webkit-user-select: text;
    user-select: text;
    caret-color: white !important;
}
```
**Ergebnis:** ❌ Problem bleibt, pointer-events rückgängig gemacht

---

### Versuch 10: backdrop-filter entfernen (iOS Bug)
**Datum:** 2025-11-05
**Wichtiger Hinweis vom User:** "Cursor kommt beim Runterziehen mit"
**Theorie:** `backdrop-filter: blur()` blockiert Input-Interaktion (bekannter iOS/Safari Bug)

**Änderung Header:**
```css
/* VORHER */
header {
    background: linear-gradient(to bottom, rgba(20, 30, 40, 0.95) 0%, rgba(20, 30, 40, 0.85) 80%, transparent 100%);
    backdrop-filter: blur(20px);
    z-index: 100;
}

/* NACHHER */
header {
    background: linear-gradient(to bottom, rgba(20, 30, 40, 0.98) 0%, rgba(20, 30, 40, 0.95) 80%, rgba(20, 30, 40, 0.9) 100%);
    /* backdrop-filter entfernt - verursacht iOS Input-Focus Bug */
    z-index: 100;
    pointer-events: none; /* Header selbst nicht clickbar */
}

header h1 {
    pointer-events: auto; /* Nur Text clickbar */
}
```

**Änderung Tabs:**
```css
/* VORHER */
.tabs {
    background: rgba(40, 50, 60, 0.5);
    backdrop-filter: blur(10px);
    z-index: 99;
}

/* NACHHER */
.tabs {
    background: rgba(40, 50, 60, 0.95);
    /* backdrop-filter entfernt - verursacht iOS Input-Focus Bug */
    z-index: 99;
}
```

**Ergebnis:** ❌ Problem bleibt leider bestehen

---

## Aktuelle Konfiguration (nach allen Versuchen)

### HTML-Struktur:
```html
<header>...</header>                    <!-- Außerhalb container, position: fixed -->
<div class="tabs">...</div>            <!-- Außerhalb container, position: fixed -->
<div class="global-search">            <!-- Außerhalb container, position: fixed -->
    <input id="global-search-input">
    <div class="search-dropdown"></div>
</div>
<div class="container">
    <main>...</main>                    <!-- Scrollbarer Content -->
</div>
```

### CSS z-index Hierarchie:
```
101: user-info, version-badge, refresh-button
100: header (position: fixed, pointer-events: none)
99:  tabs (position: fixed)
98:  global-search (position: fixed)
```

### Suchfeld CSS:
```css
.global-search {
    position: fixed;
    top: 215px;
    left: 20px;
    right: 20px;
    max-width: 1160px;
    margin: 0 auto;
    z-index: 98;
    padding: 0;
}

.global-search input {
    width: 100%;
    background: rgba(50, 60, 70, 0.7) !important;
    color: white !important;
    padding: 12px 16px;
    border: 2px solid rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    font-size: 17px;
    caret-color: white !important;
    touch-action: manipulation;
    -webkit-user-select: text;
    user-select: text;
}
```

## Noch nicht getestete Ansätze

### Möglichkeit 1: Input komplett ohne Container-Div
Direktes Input-Element ohne umschließendes Div

### Möglichkeit 2: ontouchstart Event hinzufügen
```javascript
document.getElementById('global-search-input').addEventListener('touchstart', function(e) {
    this.focus();
    e.preventDefault();
});
```

### Möglichkeit 3: Input größer machen
Mehr Padding für größere Touch-Area

### Möglichkeit 4: Viewport-Meta-Tag anpassen
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
```

### Möglichkeit 5: CSS appearance zurücksetzen
```css
.global-search input {
    -webkit-appearance: none;
    appearance: none;
}
```

### Möglichkeit 6: Andere Input-Felder prüfen
Checken ob andere Input-Felder im Projekt das gleiche Problem haben

### Möglichkeit 7: iOS-spezifisches CSS
```css
@supports (-webkit-touch-callout: none) {
    /* iOS-only styles */
    .global-search input {
        /* special handling */
    }
}
```

### Möglichkeit 8: Will-change Property
```css
.global-search {
    will-change: transform;
}
```

### Möglichkeit 9: Input als eigene fixed Komponente
Ohne jegliches umschließendes Div, direkt als fixed Element

### Möglichkeit 10: JavaScript Focus-Handler
```javascript
// Focus bei jedem Click erzwingen
document.addEventListener('click', function(e) {
    if (e.target.closest('.global-search')) {
        document.getElementById('global-search-input').focus();
    }
});
```

## Browser/Device Info
- **Problem tritt auf:** iOS Safari (Mobile)
- **Seit wann:** Nach Implementation von fixed header mit Titel, Tabs und Suchfeld
- **Verhalten:** Cursor außerhalb beim ersten Click, funktioniert beim zweiten Click
- **Besonderheit:** Cursor kommt mit wenn Screen runtergezogen wird

## Referenzen
- iOS/Safari backdrop-filter Input Bug: Bekanntes Problem auf iOS
- position: fixed Input-Focus Probleme auf Mobile
- pointer-events und Touch-Events Interaktion

---

**Status:** 🔴 Problem noch nicht gelöst
**Letzte Änderung:** 2025-11-05
**Nächste Schritte:** Siehe "Noch nicht getestete Ansätze"
