#!/bin/bash
# KI Code-Review für Rezept-Tagebuch
# Läuft täglich um 02:00 Uhr via Cron

set -e

# Farben
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Konfiguration
REPO_DIR="/home/gabor/easer_projekte/rezept-tagebuch"
LOG_DIR="/home/gabor/easer_projekte/logs"
REVIEW_DIR="/home/gabor/easer_projekte/ki-reviews"
MODEL="qwen2.5-coder:7b"
OLLAMA_URL="http://localhost:11434"

# Log-File mit Timestamp
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
LOG_FILE="$LOG_DIR/ki-review-$TIMESTAMP.log"
MAIN_LOG="$LOG_DIR/ki-review.log"

# Directories erstellen falls nicht existent
mkdir -p "$LOG_DIR" "$REVIEW_DIR"

# Log-Funktion
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")

    case $level in
        INFO)  echo -e "${GREEN}[$timestamp]${NC} $message" | tee -a "$LOG_FILE" "$MAIN_LOG" ;;
        WARN)  echo -e "${YELLOW}[$timestamp] WARNING:${NC} $message" | tee -a "$LOG_FILE" "$MAIN_LOG" ;;
        ERROR) echo -e "${RED}[$timestamp] ERROR:${NC} $message" | tee -a "$LOG_FILE" "$MAIN_LOG" ;;
    esac
}

# Prüfe Ollama-Verfügbarkeit
check_ollama() {
    log INFO "Prüfe Ollama-Verfügbarkeit..."
    if curl -s "$OLLAMA_URL/api/tags" > /dev/null 2>&1; then
        log INFO "✅ Ollama ist verfügbar"
        return 0
    else
        log ERROR "❌ Ollama ist nicht erreichbar"
        exit 1
    fi
}

# Git-Status holen
update_git() {
    log INFO "Hole Git-Status..."
    cd "$REPO_DIR"
    git fetch origin 2>&1 | tee -a "$LOG_FILE" "$MAIN_LOG"
    git pull origin main 2>&1 | tee -a "$LOG_FILE" "$MAIN_LOG" || true
}

# Geänderte Dateien finden (vom Vortag)
find_changed_files() {
    log INFO "Suche am Vortag geänderte Dateien..."
    cd "$REPO_DIR"

    # Berechne Zeitstempel für gestern 00:00 bis heute 00:00
    local yesterday_start=$(date -d "yesterday 00:00:00" +%s)
    local today_start=$(date -d "today 00:00:00" +%s)

    log INFO "Zeitraum: $(date -d @$yesterday_start '+%Y-%m-%d %H:%M:%S') bis $(date -d @$today_start '+%Y-%m-%d %H:%M:%S')"

    # Finde Dateien die am Vortag geändert wurden (via git log)
    local files=$(git log --since="yesterday 00:00:00" --until="today 00:00:00" --name-only --pretty=format: | \
        sort -u | \
        grep -E '\.(py|sh|js|html|css|md|yml|yaml|txt)$' | \
        grep -v -E 'node_modules|\.git|__pycache__|\.pyc|\.backup' | \
        while read file; do
            # Prüfe ob Datei noch existiert
            if [ -f "$REPO_DIR/$file" ]; then
                echo "$file"
            fi
        done)

    echo "$files"
}

# Review eine Datei
review_file() {
    local file=$1
    local file_content=$(cat "$REPO_DIR/$file")
    local lines=$(echo "$file_content" | wc -l)

    # Skip große Dateien
    if [ $lines -gt 500 ]; then
        log WARN "Datei zu groß ($lines Zeilen), überspringe: $file"
        return 1
    fi

    log INFO "Analysiere: $file"

    # Erstelle Prompt für Ollama
    local prompt="Du bist ein Code-Reviewer. Analysiere diese Datei und gebe eine kurze Bewertung:

Datei: $file
Zeilen: $lines

Code:
\`\`\`
$file_content
\`\`\`

Bewerte:
1. Code-Qualität (1-5)
2. Hauptprobleme (falls vorhanden)
3. Empfehlungen (kurz)

Format: Maximal 5 Sätze."

    # Sende Request an Ollama
    local response=$(curl -s -X POST "$OLLAMA_URL/api/generate" \
        -H "Content-Type: application/json" \
        -d "{\"model\": \"$MODEL\", \"prompt\": $(echo "$prompt" | jq -Rs .), \"stream\": false}" \
        | jq -r '.response' 2>/dev/null)

    if [ -n "$response" ]; then
        echo "## $file" >> "$REVIEW_DIR/review-$TIMESTAMP.md"
        echo "" >> "$REVIEW_DIR/review-$TIMESTAMP.md"
        echo "$response" >> "$REVIEW_DIR/review-$TIMESTAMP.md"
        echo "" >> "$REVIEW_DIR/review-$TIMESTAMP.md"
        echo "---" >> "$REVIEW_DIR/review-$TIMESTAMP.md"
        echo "" >> "$REVIEW_DIR/review-$TIMESTAMP.md"
        log INFO "  ✅ Review für $file abgeschlossen"
        return 0
    else
        log WARN "  ⚠️  Kein Review-Response für $file"
        return 1
    fi
}

# Main
main() {
    local start_time=$(date +%s)

    log INFO "🤖 KI Code-Review gestartet"
    log INFO "Projekt: $REPO_DIR"
    log INFO "Model: $MODEL"
    log INFO ""

    # Checks
    check_ollama
    update_git

    # Finde Dateien
    local files=$(find_changed_files)
    local file_count=$(echo "$files" | wc -l)

    log INFO "📝 Gefundene Dateien zum Review: $file_count"

    # Review-Report initialisieren
    echo "# KI Code-Review - Rezept-Tagebuch" > "$REVIEW_DIR/review-$TIMESTAMP.md"
    echo "" >> "$REVIEW_DIR/review-$TIMESTAMP.md"
    echo "**Datum:** $(date +'%Y-%m-%d %H:%M:%S')" >> "$REVIEW_DIR/review-$TIMESTAMP.md"
    echo "**Model:** $MODEL" >> "$REVIEW_DIR/review-$TIMESTAMP.md"
    echo "**Dateien:** $file_count" >> "$REVIEW_DIR/review-$TIMESTAMP.md"
    echo "" >> "$REVIEW_DIR/review-$TIMESTAMP.md"
    echo "---" >> "$REVIEW_DIR/review-$TIMESTAMP.md"
    echo "" >> "$REVIEW_DIR/review-$TIMESTAMP.md"

    # Review jede Datei
    local count=0
    local success=0
    for file in $files; do
        count=$((count + 1))
        log INFO "[$count/$file_count] Analysiere: $file"

        if review_file "$file"; then
            success=$((success + 1))
        fi
    done

    # Zusammenfassung
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local duration_min=$((duration / 60))
    local duration_sec=$((duration % 60))

    log INFO ""
    log INFO "📊 Review-Statistiken:"
    log INFO "   Analysierte Dateien: $success/$file_count"
    log INFO "   Review-Report: $REVIEW_DIR/review-$TIMESTAMP.md"
    log INFO "   Dauer: ${duration_min}m ${duration_sec}s"
    log INFO ""
    log INFO "🎉 KI Code-Review abgeschlossen!"
}

# Führe Main aus
main
