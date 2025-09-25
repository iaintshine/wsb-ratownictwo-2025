#!/usr/bin/env python3
"""
Skrypt do analizy pliku ICS z planem zajęć uniwersyteckich.
Analizuje wydarzenia w formacie: "Nazwa przedmiotu (Typ) - Prowadzący: ..., Sala: ..."
gdzie Typ to: (W) - wykład, (L) - laboratoria, (E-CW) - ćwiczenia na platformie
"""

import re
from collections import defaultdict
from datetime import datetime, timedelta
import argparse
from typing import Dict, List, Tuple, Optional

try:
    from icalendar import Calendar
except ImportError:
    print("Błąd: Biblioteka 'icalendar' nie jest zainstalowana.")
    print("Zainstaluj ją komendą: pip install icalendar")
    exit(1)


class ICSAnalyzer:
    def __init__(self):
        self.stats = {
            'wykłady': 0,
            'laboratoria': 0, 
            'e_cw': 0,
            'inne': 0,
            'total_events': 0
        }
        
        self.location_stats = {
            'teams': 0,
            'moodle': 0,
            'uczelnia': 0,
            'inne_lokalizacje': 0
        }
        
        self.subjects = defaultdict(lambda: {
            'wykłady': 0,
            'laboratoria': 0,
            'e_cw': 0,
            'prowadzący': set(),
            'sale': set()
        })
        
        self.total_duration = timedelta()

    def parse_event_title(self, title: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Parsuje tytuł wydarzenia w formacie:
        "Nazwa przedmiotu (Typ) - Prowadzący: ..., Sala: ..."
        
        Returns:
            Tuple[subject, event_type, instructor, room]
        """
        # Wzorzec do wyodrębnienia informacji z tytułu - poprawiony pattern
        pattern = r'^(.+?)\s*\(([WL]|E-CW)\)\s*-\s*Prowadzący:\s*(.+?),\s*Sala:\s*(.+)$'
        match = re.match(pattern, title.strip())
        
        if match:
            subject = match.group(1).strip()
            event_type = match.group(2).strip()
            instructor = match.group(3).strip()
            room = match.group(4).strip()
            return subject, event_type, instructor, room
        
        # Jeśli standardowy wzorzec nie pasuje, spróbuj prostszy
        simple_pattern = r'^(.+?)\s*\(([WL]|E-CW)\)'
        simple_match = re.match(simple_pattern, title.strip())
        if simple_match:
            subject = simple_match.group(1).strip()
            event_type = simple_match.group(2).strip()
            return subject, event_type, None, None
            
        return None, None, None, None

    def categorize_location(self, room: Optional[str]) -> str:
        """Kategoryzuje lokalizację na podstawie nazwy sali"""
        if not room:
            return 'inne_lokalizacje'
            
        room_lower = room.lower()
        
        if 'teams' in room_lower or 'platforma teams' in room_lower:
            return 'teams'
        elif 'moodle' in room_lower or 'platforma moodle' in room_lower:
            return 'moodle'
        elif any(keyword in room_lower for keyword in ['sala', 'budynek', 'aula', 'laboratorium']):
            return 'uczelnia'
        elif room_lower.startswith(('a', 'b', 'c')) and any(char.isdigit() for char in room_lower):
            # Prawdopodobnie sala na uczelni (np. A101, B205)
            return 'uczelnia'
        else:
            return 'inne_lokalizacje'

    def analyze_ics_file(self, file_path: str) -> None:
        """Główna funkcja analizująca plik ICS"""
        try:
            with open(file_path, 'rb') as file:
                calendar = Calendar.from_ical(file.read())
        except FileNotFoundError:
            print(f"Błąd: Nie można znaleźć pliku {file_path}")
            return
        except Exception as e:
            print(f"Błąd podczas odczytu pliku: {e}")
            return

        for component in calendar.walk():
            if component.name == "VEVENT":
                self._process_event(component)

    def _process_event(self, event) -> None:
        """Przetwarza pojedyncze wydarzenie z kalendarza"""
        title = str(event.get('summary', ''))
        start_time = event.get('dtstart')
        end_time = event.get('dtend')
        
        self.stats['total_events'] += 1
        
        # Oblicz czas trwania wydarzenia
        if start_time and end_time:
            if hasattr(start_time.dt, 'replace'):  # datetime object
                duration = end_time.dt - start_time.dt
                self.total_duration += duration
        
        # Parsuj tytuł wydarzenia
        subject, event_type, instructor, room = self.parse_event_title(title)
        
        if not subject or not event_type:
            print(f"Ostrzeżenie: Nie można sparsować tytułu: '{title}'")
            self.stats['inne'] += 1
            return
        
        # Aktualizuj statystyki główne
        if event_type == 'W':
            self.stats['wykłady'] += 1
            self.subjects[subject]['wykłady'] += 1
        elif event_type == 'L':
            self.stats['laboratoria'] += 1
            self.subjects[subject]['laboratoria'] += 1
        elif event_type == 'E-CW':
            self.stats['e_cw'] += 1
            self.subjects[subject]['e_cw'] += 1
        else:
            self.stats['inne'] += 1
        
        # Aktualizuj informacje o przedmiocie
        if instructor:
            self.subjects[subject]['prowadzący'].add(instructor)
        if room:
            self.subjects[subject]['sale'].add(room)
        
        # Kategoryzuj lokalizację
        location_category = self.categorize_location(room)
        self.location_stats[location_category] += 1

    def print_statistics(self) -> None:
        """Wyświetla zebrane statystyki"""
        print("=" * 60)
        print("ANALIZA PLANU ZAJĘĆ - STATYSTYKI")
        print("=" * 60)
        
        # Statystyki ogólne
        print("\n📊 STATYSTYKI OGÓLNE:")
        print(f"Całkowita liczba wydarzeń: {self.stats['total_events']}")
        print(f"Wykłady (W): {self.stats['wykłady']}")
        print(f"Laboratoria (L): {self.stats['laboratoria']}")
        print(f"Ćwiczenia E-CW: {self.stats['e_cw']}")
        print(f"Inne/Nieskategoryzowane: {self.stats['inne']}")
        
        # Statystyki czasu
        total_hours = self.total_duration.total_seconds() / 3600
        print(f"\nCałkowity czas zajęć: {total_hours:.1f} godzin")
        
        # Statystyki lokalizacji
        print("\n📍 STATYSTYKI LOKALIZACJI:")
        print(f"Platforma Teams: {self.location_stats['teams']} zajęć")
        print(f"Platforma Moodle: {self.location_stats['moodle']} zajęć")
        print(f"Na uczelni (laboratoria): {self.location_stats['uczelnia']} zajęć")
        print(f"Inne lokalizacje: {self.location_stats['inne_lokalizacje']} zajęć")
        
        # Statystyki per przedmiot
        print("\n📚 STATYSTYKI WEDŁUG PRZEDMIOTÓW:")
        for subject, data in sorted(self.subjects.items()):
            total_classes = data['wykłady'] + data['laboratoria'] + data['e_cw']
            print(f"\n{subject}:")
            print(f"  • Wykłady: {data['wykłady']}")
            print(f"  • Laboratoria: {data['laboratoria']}")
            print(f"  • E-CW: {data['e_cw']}")
            print(f"  • Łącznie zajęć: {total_classes}")
            
            if data['prowadzący']:
                print(f"  • Prowadzący: {', '.join(data['prowadzący'])}")
            if data['sale']:
                print(f"  • Sale: {', '.join(list(data['sale'])[:3])}{'...' if len(data['sale']) > 3 else ''}")

        # Podsumowanie wyjazdów
        print(f"\n🚗 PODSUMOWANIE WYJAZDÓW:")
        print(f"Zajęcia zdalne (Teams + Moodle): {self.location_stats['teams'] + self.location_stats['moodle']}")
        print(f"Wyjazdy na uczelnię: {self.location_stats['uczelnia']}")


def main():
    parser = argparse.ArgumentParser(description='Analizator planu zajęć z pliku ICS')
    parser.add_argument('ics_file', help='Ścieżka do pliku ICS z planem zajęć')
    parser.add_argument('-v', '--verbose', action='store_true', help='Więcej szczegółów w wynikach')
    
    args = parser.parse_args()
    
    analyzer = ICSAnalyzer()
    
    print(f"Analizuję plik: {args.ics_file}")
    analyzer.analyze_ics_file(args.ics_file)
    analyzer.print_statistics()


if __name__ == "__main__":
    main()