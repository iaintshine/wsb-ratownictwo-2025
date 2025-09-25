#!/usr/bin/env python3
"""
Prosty skrypt do analizy pliku ICS - wersja uproszczona bez zewnętrznych zależności.
Używa tylko wbudowanych bibliotek Pythona.
"""

import re
from collections import defaultdict
from datetime import datetime
import argparse
from typing import Dict, List, Tuple, Optional


class SimpleICSAnalyzer:
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
        
        # Lista wszystkich zajęć na uczelni z datami i godzinami
        self.uczelnia_schedule = []
        
        # Statystyki czasowe
        self.time_stats = {
            'total_minutes': 0,
            'wykłady_minutes': 0,
            'laboratoria_minutes': 0,
            'e_cw_minutes': 0,
            'uczelnia_minutes': 0,
            'zdalne_minutes': 0
        }

    def parse_event_title(self, title: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Parsuje tytuł wydarzenia - obsługuje różne formaty"""
        title = title.strip()
        
        # Format 1: Standard - "Nazwa (Typ) - Prowadzący: ..., Sala: ..."
        pattern1 = r'^(.+?)\s*\(([WL]|E-CW)\)\s*-\s*Prowadzący:\s*(.+?),\s*Sala:\s*(.+)$'
        match1 = re.match(pattern1, title)
        if match1:
            subject = match1.group(1).strip()
            event_type = match1.group(2).strip()
            instructor = match1.group(3).strip()
            room = match1.group(4).strip()
            return subject, event_type, instructor, room
        
        # Format 2: Alternatywny - "Nazwa (E-W) - Prowadzący: ..., Sala: ..." (E-W zamiast W)
        pattern2 = r'^(.+?)\s*\(E-W\)\s*-\s*Prowadzący:\s*(.+?),\s*Sala:\s*(.+)$'
        match2 = re.match(pattern2, title)
        if match2:
            subject = match2.group(1).strip()
            event_type = "W"  # E-W traktujemy jako wykład
            instructor = match2.group(2).strip()
            room = match2.group(3).strip()
            return subject, event_type, instructor, room
            
        # Format 3: E-ĆW (z polskim znakiem)
        pattern3 = r'^(.+?)\s*\(E-ĆW\)\s*-\s*Prowadzący:\s*(.+?),\s*Sala:\s*(.+)$'
        match3 = re.match(pattern3, title)
        if match3:
            subject = match3.group(1).strip()
            event_type = "E-CW"  # Normalizujemy do E-CW
            instructor = match3.group(2).strip()
            room = match3.group(3).strip()
            return subject, event_type, instructor, room
            
        # Format 4: ĆW (ćwiczenia bez prefiksu E- - traktujemy jak laboratoria)
        pattern4 = r'^(.+?)\s*\(ĆW\)\s*-\s*Prowadzący:\s*(.+?),\s*Sala:\s*(.+)$'
        match4 = re.match(pattern4, title)
        if match4:
            subject = match4.group(1).strip()
            event_type = "L"  # ĆW bez prefiksu E- to laboratoria/ćwiczenia stacjonarne
            instructor = match4.group(2).strip()
            room = match4.group(3).strip()
            return subject, event_type, instructor, room
        
        # Prosty fallback - tylko nazwa i typ w nawiasie
        simple_patterns = [
            r'^(.+?)\s*\(([WL]|E-CW)\)',
            r'^(.+?)\s*\(E-W\)',  # E-W jako wykład
            r'^(.+?)\s*\(E-ĆW\)', # E-ĆW jako ćwiczenia
            r'^(.+?)\s*\(ĆW\)'    # ĆW jako ćwiczenia
        ]
        
        for i, pattern in enumerate(simple_patterns):
            match = re.match(pattern, title)
            if match:
                subject = match.group(1).strip()
                if i == 0:  # Standard format
                    event_type = match.group(2).strip()
                elif i == 1:  # E-W
                    event_type = "W"
                elif i == 2:  # E-ĆW (ćwiczenia zdalne)
                    event_type = "E-CW"
                elif i == 3:  # ĆW (ćwiczenia stacjonarne - jak laboratoria)
                    event_type = "L"
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
        elif room_lower.startswith(('a', 'b', 'c', 'd', 'e', 'f')) and any(char.isdigit() for char in room_lower):
            return 'uczelnia'
        else:
            return 'inne_lokalizacje'

    def analyze_ics_file(self, file_path: str) -> None:
        """Główna funkcja analizująca plik ICS - używa tylko wbudowanych bibliotek"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
        except UnicodeDecodeError:
            # Spróbuj inne kodowanie
            with open(file_path, 'r', encoding='latin-1') as file:
                content = file.read()
        except FileNotFoundError:
            print(f"Błąd: Nie można znaleźć pliku {file_path}")
            return
        except Exception as e:
            print(f"Błąd podczas odczytu pliku: {e}")
            return

        # Proste parsowanie ICS - szukamy bloków VEVENT
        events = self._extract_events(content)
        
        for event in events:
            self._process_simple_event(event)

    def _extract_events(self, content: str) -> List[Dict[str, str]]:
        """Wyodrębnia wydarzenia z zawartości ICS"""
        events = []
        lines = content.split('\n')
        
        current_event = {}
        in_event = False
        
        for line in lines:
            line = line.strip()
            
            if line == 'BEGIN:VEVENT':
                in_event = True
                current_event = {}
            elif line == 'END:VEVENT':
                if current_event:
                    events.append(current_event)
                in_event = False
            elif in_event and ':' in line:
                key, value = line.split(':', 1)
                current_event[key] = value
        
        return events

    def _parse_datetime(self, datetime_str: str) -> tuple:
        """Parsuje datę i czas z formatu ICS"""
        if not datetime_str:
            return None, None, None
            
        # Format: 20251116T080000
        try:
            year = int(datetime_str[:4])
            month = int(datetime_str[4:6])
            day = int(datetime_str[6:8])
            hour = int(datetime_str[9:11])
            minute = int(datetime_str[11:13])
            
            # Polskie nazwy dni tygodnia
            weekdays = ['Poniedziałek', 'Wtorek', 'Środa', 'Czwartek', 'Piątek', 'Sobota', 'Niedziela']
            months = ['stycznia', 'lutego', 'marca', 'kwietnia', 'maja', 'czerwca',
                     'lipca', 'sierpnia', 'września', 'października', 'listopada', 'grudnia']
            
            from datetime import datetime as dt
            date_obj = dt(year, month, day, hour, minute)
            weekday = weekdays[date_obj.weekday()]
            
            date_str = f"{day} {months[month-1]} {year} ({weekday})"
            time_str = f"{hour:02d}:{minute:02d}"
            
            return date_str, time_str, date_obj
        except (ValueError, IndexError):
            return None, None, None

    def _print_uczelnia_schedule(self):
        """Wypisuje szczegółowy harmonogram zajęć na uczelni"""
        if not self.uczelnia_schedule:
            return
            
        print(f"\n📅 SZCZEGÓŁOWY HARMONOGRAM ZAJĘĆ NA UCZELNI:")
        print("=" * 80)
        
        # Sortuj według daty i grupuj według dni
        sorted_schedule = sorted(self.uczelnia_schedule, 
                               key=lambda x: self._parse_datetime(x['start_time'])[2] or datetime(1900, 1, 1))
        
        # Grupuj zajęcia według dnia
        from collections import defaultdict
        days_schedule = defaultdict(list)
        
        for event in sorted_schedule:
            date_str, _, date_obj = self._parse_datetime(event['start_time'])
            if date_obj:
                day_key = date_obj.strftime('%Y-%m-%d')
                days_schedule[day_key].append((date_str, event))
        
        day_counter = 0
        for day_key in sorted(days_schedule.keys()):
            day_counter += 1
            events_for_day = days_schedule[day_key]
            date_str = events_for_day[0][0]  # Pobierz sformatowaną datę
            
            print(f"\n🗓️  DZIEŃ {day_counter}: {date_str}")
            print("-" * 60)
            
            for i, (_, event) in enumerate(events_for_day, 1):
                _, start_time, _ = self._parse_datetime(event['start_time'])
                _, end_time, _ = self._parse_datetime(event['end_time'])
                
                type_name = {
                    'L': 'Laboratoria/Ćwiczenia stacjonarne',
                    'E-CW': 'Ćwiczenia zdalne',
                    'E-ĆW': 'Ćwiczenia zdalne',
                    'W': 'Wykład'
                }.get(event['type'], event['type'])
                
                print(f"  {i}. 🕐 {start_time} - {end_time if end_time else '?'}")
                print(f"     📚 {event['subject']} ({type_name})")
                print(f"     🏫 {event['room']}")
                if event['instructor']:
                    print(f"     👨‍🏫 {event['instructor']}")
                print()
        
        print(f"💡 PODSUMOWANIE: {day_counter} dni z zajęciami na uczelni ({len(sorted_schedule)} zajęć łącznie)")

    def _minutes_to_hours_str(self, minutes: int) -> str:
        """Konwertuje minuty na czytelny format godzin i minut"""
        hours = minutes // 60
        remaining_minutes = minutes % 60
        if remaining_minutes == 0:
            return f"{hours}h"
        else:
            return f"{hours}h {remaining_minutes}min"

    def _print_time_summary(self):
        """Wypisuje szczegółowe podsumowanie czasowe"""
        print(f"\n⏱️  SZCZEGÓŁOWE PODSUMOWANIE CZASOWE SEMESTRU:")
        print("=" * 80)
        
        # Całkowity czas
        total_hours = self.time_stats['total_minutes'] / 60
        print(f"\n📊 CAŁKOWITY CZAS ZAJĘĆ: {self._minutes_to_hours_str(self.time_stats['total_minutes'])}")
        print(f"    (To odpowiada {total_hours:.1f} godzinom akademickim)")
        
        # Podział według typu zajęć
        print(f"\n📚 PODZIAŁ WEDŁUG TYPU ZAJĘĆ:")
        print(f"  • Wykłady: {self._minutes_to_hours_str(self.time_stats['wykłady_minutes'])} ({self.stats['wykłady']} zajęć)")
        print(f"  • Laboratoria/Ćwiczenia stacjonarne: {self._minutes_to_hours_str(self.time_stats['laboratoria_minutes'])} ({self.stats['laboratoria']} zajęć)")
        print(f"  • Ćwiczenia zdalne (E-CW): {self._minutes_to_hours_str(self.time_stats['e_cw_minutes'])} ({self.stats['e_cw']} zajęć)")
        
        # Podział według lokalizacji
        print(f"\n📍 PODZIAŁ WEDŁUG LOKALIZACJI:")
        print(f"  • Zajęcia na uczelni: {self._minutes_to_hours_str(self.time_stats['uczelnia_minutes'])} ({self.location_stats['uczelnia']} zajęć)")
        print(f"  • Zajęcia zdalne: {self._minutes_to_hours_str(self.time_stats['zdalne_minutes'])} ({self.location_stats['teams'] + self.location_stats['moodle']} zajęć)")
        
        # Średni czas zajęć
        if self.stats['total_events'] > 0:
            avg_minutes = self.time_stats['total_minutes'] / self.stats['total_events']
            print(f"\n📈 ŚREDNI CZAS JEDNYCH ZAJĘĆ: {self._minutes_to_hours_str(int(avg_minutes))}")
        
        # Obciążenie tygodniowe (zakładając 15 tygodni semestru)
        weeks_in_semester = 15
        weekly_minutes = self.time_stats['total_minutes'] / weeks_in_semester
        weekly_uczelnia = self.time_stats['uczelnia_minutes'] / weeks_in_semester
        weekly_zdalne = self.time_stats['zdalne_minutes'] / weeks_in_semester
        
        print(f"\n📅 ŚREDNIE OBCIĄŻENIE TYGODNIOWE (przy 15 tygodniach semestru):")
        print(f"  • Łącznie: {self._minutes_to_hours_str(int(weekly_minutes))} tygodniowo")
        print(f"  • Na uczelni: {self._minutes_to_hours_str(int(weekly_uczelnia))} tygodniowo")  
        print(f"  • Zdalnie: {self._minutes_to_hours_str(int(weekly_zdalne))} tygodniowo")
        
        # Procenty
        if self.time_stats['total_minutes'] > 0:
            uczelnia_percent = (self.time_stats['uczelnia_minutes'] / self.time_stats['total_minutes']) * 100
            zdalne_percent = (self.time_stats['zdalne_minutes'] / self.time_stats['total_minutes']) * 100
            
            print(f"\n📊 PROCENTOWY PODZIAŁ CZASU:")
            print(f"  • Zajęcia na uczelni: {uczelnia_percent:.1f}% czasu")
            print(f"  • Zajęcia zdalne: {zdalne_percent:.1f}% czasu")
        
        # Praktyczne wskazówki
        uczelnia_days_per_month = (len(set(self._parse_datetime(event['start_time'])[2].strftime('%Y-%m-%d') 
                                          for event in self.uczelnia_schedule if self._parse_datetime(event['start_time'])[2])) / 4)
        
        print(f"\n💡 PRAKTYCZNE INFORMACJE:")
        print(f"  • Średnio {uczelnia_days_per_month:.1f} dni wyjazdu na uczelnię miesięcznie")
        print(f"  • Łączny czas podróży w semestrze (przy założeniu 1h w każdą stronę): {len(set(self._parse_datetime(event['start_time'])[2].strftime('%Y-%m-%d') for event in self.uczelnia_schedule if self._parse_datetime(event['start_time'])[2])) * 2}h")
        print(f"  • Oszczędność czasu dzięki zajęciom zdalnym: {self._minutes_to_hours_str(self.time_stats['zdalne_minutes'])}")

    def _calculate_duration_minutes(self, start_time: str, end_time: str) -> int:
        """Oblicza czas trwania w minutach"""
        if not start_time or not end_time:
            return 0
            
        try:
            # Format: 20251116T080000
            start_hour = int(start_time[9:11])
            start_minute = int(start_time[11:13])
            end_hour = int(end_time[9:11])
            end_minute = int(end_time[11:13])
            
            start_total_minutes = start_hour * 60 + start_minute
            end_total_minutes = end_hour * 60 + end_minute
            
            return end_total_minutes - start_total_minutes
        except (ValueError, IndexError):
            return 0

    def _process_simple_event(self, event: Dict[str, str]) -> None:
        """Przetwarza wydarzenie wyodrębnione z ICS"""
        title = event.get('SUMMARY', '')
        start_time = event.get('DTSTART;TZID=Europe/Warsaw', event.get('DTSTART', ''))
        end_time = event.get('DTEND;TZID=Europe/Warsaw', event.get('DTEND', ''))
        
        self.stats['total_events'] += 1
        
        # Oblicz czas trwania
        duration_minutes = self._calculate_duration_minutes(start_time, end_time)
        self.time_stats['total_minutes'] += duration_minutes
        
        # Parsuj tytuł wydarzenia
        subject, event_type, instructor, room = self.parse_event_title(title)
        
        if not subject or not event_type:
            print(f"Ostrzeżenie: Nie można sparsować tytułu: '{title}'")
            self.stats['inne'] += 1
            return
        
        # Aktualizuj statystyki główne i czasowe
        if event_type == 'W':
            self.stats['wykłady'] += 1
            self.subjects[subject]['wykłady'] += 1
            self.time_stats['wykłady_minutes'] += duration_minutes
        elif event_type == 'L':
            self.stats['laboratoria'] += 1
            self.subjects[subject]['laboratoria'] += 1
            self.time_stats['laboratoria_minutes'] += duration_minutes
        elif event_type in ['E-CW', 'E-ĆW']:
            self.stats['e_cw'] += 1
            self.subjects[subject]['e_cw'] += 1
            self.time_stats['e_cw_minutes'] += duration_minutes
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
        
        # Aktualizuj statystyki czasowe według lokalizacji
        if location_category == 'uczelnia':
            self.time_stats['uczelnia_minutes'] += duration_minutes
        else:
            self.time_stats['zdalne_minutes'] += duration_minutes
        
        # Jeśli zajęcia są na uczelni, dodaj do harmonogramu
        if location_category == 'uczelnia' and start_time and room:
            self.uczelnia_schedule.append({
                'subject': subject,
                'type': event_type,
                'instructor': instructor,
                'room': room,
                'start_time': start_time,
                'end_time': end_time,
                'title': title
            })

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
                print(f"  • Prowadzący: {', '.join(list(data['prowadzący'])[:2])}{'...' if len(data['prowadzący']) > 2 else ''}")
            if data['sale']:
                print(f"  • Sale: {', '.join(list(data['sale'])[:2])}{'...' if len(data['sale']) > 2 else ''}")

        # Podsumowanie wyjazdów
        print(f"\n🚗 PODSUMOWANIE WYJAZDÓW:")
        print(f"Zajęcia zdalne (Teams + Moodle): {self.location_stats['teams'] + self.location_stats['moodle']}")
        print(f"Wyjazdy na uczelnię: {self.location_stats['uczelnia']}")
        
        if self.location_stats['uczelnia'] > 0:
            print(f"💡 Musisz jechać na uczelnię {self.location_stats['uczelnia']} razy w semestrze!")
            
            # Szczegółowy harmonogram wyjazdów na uczelnię
            self._print_uczelnia_schedule()
            
        # Szczegółowe podsumowanie czasowe
        self._print_time_summary()


def main():
    parser = argparse.ArgumentParser(description='Analizator planu zajęć z pliku ICS (wersja bez zewnętrznych zależności)')
    parser.add_argument('ics_file', help='Ścieżka do pliku ICS z planem zajęć')
    
    args = parser.parse_args()
    
    analyzer = SimpleICSAnalyzer()
    
    print(f"Analizuję plik: {args.ics_file}")
    analyzer.analyze_ics_file(args.ics_file)
    analyzer.print_statistics()


if __name__ == "__main__":
    main()