#!/bin/bash

# Skrypt do szybkiej analizy pliku ICS
# Użycie: ./analyze.sh twoj_plik.ics

if [ $# -eq 0 ]; then
    echo "Użycie: $0 plik.ics"
    echo "Przykład: $0 plan_zajec.ics"
    exit 1
fi

ICS_FILE="$1"

if [ ! -f "$ICS_FILE" ]; then
    echo "Błąd: Plik $ICS_FILE nie istnieje!"
    exit 1
fi

echo "🔍 Analizuję plik: $ICS_FILE"
echo ""

# Sprawdź czy biblioteka icalendar jest dostępna
if python3 -c "import icalendar" 2>/dev/null; then
    echo "✅ Używam wersji z biblioteką icalendar"
    python3 ics_analyzer.py "$ICS_FILE"
else
    echo "⚠️  Biblioteka icalendar nie jest dostępna, używam prostej wersji"
    python3 ics_analyzer_simple.py "$ICS_FILE"
fi