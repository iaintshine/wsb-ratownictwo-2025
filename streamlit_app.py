import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import io
from datetime import datetime
from ics_analyzer_simple import SimpleICSAnalyzer

# Konfiguracja Plotly
pio.templates.default = "plotly"

# Konfiguracja strony
st.set_page_config(
    page_title="Analizator Planu Zajęć WSB",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS do stylizacji
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        font-size: 2.5rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        margin: 0.5rem 0;
    }
    .stAlert {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Nagłówek aplikacji
st.markdown('<h1 class="main-header">📚 Plan Zajęć WSB - Ratownictwo Medyczne 2025 - Statystyki</h1>',
            unsafe_allow_html=True)
st.markdown("### Szczegółowa analiza Twojego planu zajęć")


# Automatyczne ładowanie pliku PlanZajec.ics
try:
    # Utwórz analizator i analizuj plik
    analyzer = SimpleICSAnalyzer()
    analyzer.analyze_ics_file('PlanZajec.ics')

    # Wyświetl wyniki
    if analyzer.stats['total_events'] > 0:
        st.success(
            f"✅ Pomyślnie przeanalizowano {analyzer.stats['total_events']} wydarzeń!")

        # Główne metryki
        st.markdown("## 📊 Główne Statystyki")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                label="Całkowity czas",
                value=f"{analyzer.time_stats['total_minutes']//60}h {analyzer.time_stats['total_minutes'] % 60}min",
                delta="w semestrze"
            )

        with col2:
            st.metric(
                label="Wykłady",
                value=analyzer.stats['wykłady'],
                delta=f"{analyzer.time_stats['wykłady_minutes']//60}h"
            )

        with col3:
            st.metric(
                label="Laboratoria/Ćwiczenia",
                value=analyzer.stats['laboratoria'],
                delta=f"{analyzer.time_stats['laboratoria_minutes']//60}h"
            )

        with col4:
            st.metric(
                label="Zajęcia zdalne",
                value=analyzer.location_stats['teams'] +
                analyzer.location_stats['moodle'],
                delta=f"{analyzer.time_stats['zdalne_minutes']//60}h"
            )

        with col5:
            st.metric(
                label="Wyjazdy na uczelnię",
                value=len(set(analyzer._parse_datetime(event['start_time'])[2].strftime('%Y-%m-%d')
                              for event in analyzer.uczelnia_schedule
                              if analyzer._parse_datetime(event['start_time'])[2])),
                delta="dni w semestrze"
            )

        # Wykresy w dwóch kolumnach
        st.markdown("## 📈 Wizualizacje")

        col_left, col_right = st.columns(2)

        with col_left:
            # Wykres kołowy - podział zajęć według typu
            fig_pie = px.pie(
                values=[analyzer.stats['wykłady'],
                        analyzer.stats['laboratoria'], analyzer.stats['e_cw']],
                names=['Wykłady', 'Laboratoria/Ćwiczenia', 'E-learning'],
                title="Podział zajęć według typu",
                color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c']
            )
            st.plotly_chart(fig_pie, width="stretch")

        with col_right:
            # Wykres słupkowy - czas według lokalizacji
            locations = ['Na uczelni', 'Zdalne']
            times = [analyzer.time_stats['uczelnia_minutes'] /
                     60, analyzer.time_stats['zdalne_minutes']/60]

            fig_bar = px.bar(
                x=locations,
                y=times,
                title="Czas zajęć według lokalizacji",
                labels={'y': 'Godziny', 'x': 'Lokalizacja'},
                color=locations,
                color_discrete_sequence=['#ff7f0e', '#1f77b4']
            )
            st.plotly_chart(fig_bar, width="stretch")

        # Timeline wyjazdów na uczelnię
        if analyzer.uczelnia_schedule:
            st.markdown("## 🗓️ Harmonogram Zajęć na Uczelni")

            # Przygotuj dane do wykresu timeline
            timeline_data = []
            for event in analyzer.uczelnia_schedule:
                date_str, start_time, date_obj = analyzer._parse_datetime(
                    event['start_time'])
                _, end_time, _ = analyzer._parse_datetime(
                    event['end_time'])

                if date_obj:
                    timeline_data.append({
                        'Przedmiot': event['subject'],
                        'Typ': 'Laboratoria/Ćwiczenia' if event['type'] == 'L' else event['type'],
                        'Data': date_obj.strftime('%Y-%m-%d'),
                        'Godzina': f"{start_time} - {end_time}",
                        'Sala': event['room'],
                        'Prowadzący': event['instructor'] or 'Brak danych'
                    })

            if timeline_data:
                df_timeline = pd.DataFrame(timeline_data)

                # Wyświetl tabelę z zajęciami
                st.dataframe(df_timeline, width="stretch")

                # Wykres liczby zajęć w czasie
                df_timeline['Data'] = pd.to_datetime(df_timeline['Data'])
                daily_counts = df_timeline.groupby(
                    'Data').size().reset_index(name='Liczba zajęć')

                fig_timeline = px.line(
                    daily_counts,
                    x='Data',
                    y='Liczba zajęć',
                    title="Liczba zajęć na uczelni w czasie",
                    markers=True
                )
                st.plotly_chart(fig_timeline, width="stretch")

        # Szczegółowe statystyki według przedmiotów
        st.markdown("## 📚 Statystyki według przedmiotów")

        subjects_data = []
        for subject, data in analyzer.subjects.items():
            total_classes = data['wykłady'] + \
                data['laboratoria'] + data['e_cw']
            subjects_data.append({
                'Przedmiot': subject,
                'Wykłady': data['wykłady'],
                'Laboratoria': data['laboratoria'],
                'E-learning': data['e_cw'],
                'Łącznie': total_classes,
                'Prowadzący': ', '.join(list(data['prowadzący'])[:2]) + ('...' if len(data['prowadzący']) > 2 else ''),
                'Sale': ', '.join(list(data['sale'])[:2]) + ('...' if len(data['sale']) > 2 else '')
            })

        if subjects_data:
            df_subjects = pd.DataFrame(subjects_data)
            st.dataframe(df_subjects, width="stretch")

            # Wykres stacked bar dla przedmiotów
            fig_subjects = px.bar(
                df_subjects,
                x='Przedmiot',
                y=['Wykłady', 'Laboratoria', 'E-learning'],
                title="Rozkład zajęć według przedmiotów",
                barmode='stack'
            )
            fig_subjects.update_xaxes(tickangle=45)
            st.plotly_chart(fig_subjects, width="stretch")

        # Podsumowanie praktyczne
        st.markdown("## 💡 Praktyczne Podsumowanie")

        col1, col2 = st.columns(2)

        with col1:
            st.info(f"""
            **⏰ Tygodniowe obciążenie:**
            - Łącznie: ~{analyzer.time_stats['total_minutes']//15//60}h {(analyzer.time_stats['total_minutes']//15) % 60}min
            - Na uczelni: ~{analyzer.time_stats['uczelnia_minutes']//15//60}h {(analyzer.time_stats['uczelnia_minutes']//15) % 60}min
            - Zdalnie: ~{analyzer.time_stats['zdalne_minutes']//15//60}h {(analyzer.time_stats['zdalne_minutes']//15) % 60}min
            """)

        with col2:
            travel_days = len(set(analyzer._parse_datetime(event['start_time'])[2].strftime('%Y-%m-%d')
                                  for event in analyzer.uczelnia_schedule
                                  if analyzer._parse_datetime(event['start_time'])[2]))
            st.warning(f"""
            **🚗 Koszty dojazdów:**
            - {travel_days} dni wyjazdów w semestrze
            - ~{travel_days * 2}h podróży (1h w każdą stronę)
            - ~{travel_days/4:.1f} wyjazdu miesięcznie
            """)

    else:
        st.error("❌ Nie znaleziono żadnych wydarzeń w pliku!")

except FileNotFoundError:
    st.error("❌ Nie znaleziono pliku PlanZajec.ics")
    st.info("💡 Upewnij się, że plik PlanZajec.ics znajduje się w tym samym folderze co aplikacja")
except Exception as e:
    st.error(f"❌ Błąd podczas analizowania pliku: {str(e)}")
    st.info("💡 Sprawdź czy plik PlanZajec.ics jest poprawny")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    Stworzony dla studentów WSB 📚 | Jeśli masz pytania lub sugestie, daj znać! 
</div>
""", unsafe_allow_html=True)
