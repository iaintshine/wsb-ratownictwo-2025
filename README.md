# Analizator Planu Zajęć ICS

Skrypt Python do analizy pliku ICS z planem zajęć uniwersyteckich.

## Instalacja

1. Zainstaluj wymagane biblioteki:
```bash
pip install -r requirements.txt
```

## Użycie

### Wersja z biblioteką icalendar (zalecana dla większych plików):
```bash
python ics_analyzer.py plan_zajec.ics
```

### Wersja prosta (bez zewnętrznych zależności):
```bash
python3 ics_analyzer_simple.py plan_zajec.ics
```

### Opcje:
- `-v, --verbose` - więcej szczegółów w wynikach (tylko w wersji pełnej)

## Format wydarzeń

Skrypt analizuje wydarzenia w formacie:
```
"Nazwa przedmiotu (Typ) - Prowadzący: [nazwisko], Sala: [lokalizacja]"
```

Gdzie:
- **Typ zajęć:**
  - `(W)` - wykład
  - `(L)` - laboratoria
  - `(E-CW)` - ćwiczenia na platformie e-learningowej

- **Lokalizacje:**
  - `Platforma Teams` - zajęcia zdalne przez Teams
  - `Platforma Moodle` - ćwiczenia na platformie Moodle
  - Nazwy sal (np. `A101`, `Laboratorium C102`) - zajęcia na uczelni

## Przykład użycia

```bash
# Analiza przykładowego pliku - wersja z icalendar
python ics_analyzer.py plan_zajec_przyklad.ics

# Lub wersja prosta (bez instalowania bibliotek)
python3 ics_analyzer_simple.py plan_zajec_przyklad.ics
```

## Wyniki analizy

Skrypt wyświetla:
- Liczbę wykładów, laboratoriów i ćwiczeń E-CW
- Statystyki lokalizacji (Teams, Moodle, uczelnia)
- Całkowity czas zajęć
- Szczegółowe statystyki według przedmiotów
- Podsumowanie liczby wyjazdów na uczelnię

## Przykładowy wynik

```
============================================================
ANALIZA PLANU ZAJĘĆ - STATYSTYKI
============================================================

📊 STATYSTYKI OGÓLNE:
Całkowita liczba wydarzeń: 8
Wykłady (W): 3
Laboratoria (L): 3
Ćwiczenia E-CW: 2
Inne/Nieskategoryzowane: 0

Całkowity czas zajęć: 10.7 godzin

📍 STATYSTYKI LOKALIZACJI:
Platforma Teams: 2 zajęć
Platforma Moodle: 2 zajęć
Na uczelni (laboratoria): 4 zajęć
Inne lokalizacje: 0 zajęć

🚗 PODSUMOWANIE WYJAZDÓW:
Zajęcia zdalne (Teams + Moodle): 4
Wyjazdy na uczelnię: 4
```