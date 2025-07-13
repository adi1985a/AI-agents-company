# AI Agents Company Simulation

## Opis programu

Symulacja firmy z inteligentnymi agentami AI, którzy komunikują się ze sobą i wykonują zadania. Program zawiera graficzny interfejs użytkownika z wykresami aktywności, animacjami, listą zadań z ikonami statusów i możliwością zapisu/odczytu stanu.

## Funkcje

### 1. System agentów AI
- **Różne typy agentów**: Programista, Analityk danych, Generator obrazów, Analityk tekstu, CEO
- **Komunikacja między agentami**: Wiadomości tekstowe z logami w GUI
- **Automatyczne przydzielanie zadań**: Na podstawie opisu zadania i umiejętności agenta
- **Opcjonalna integracja z OpenAI API**: Dla bardziej inteligentnych odpowiedzi

### 2. Zarządzanie zadaniami
- **Priorytetowa kolejka zadań**: FIFO z obsługą priorytetów (CRITICAL, HIGH, MEDIUM, LOW)
- **Statusy zadań**: PENDING, IN_PROGRESS, COMPLETED, FAILED, BLOCKED
- **Lista zadań z ikonami**: Wizualne przedstawienie statusów zadań
- **Szczegółowe logowanie**: Każdy krok wykonania jest logowany w GUI

### 3. Interfejs graficzny
- **Wykresy aktywności**: Słupkowy wykres aktywności agentów i kołowy wykres statusów zadań
- **Lista zadań**: Tabela z ikonami statusów, agentami i priorytetami
- **Okno wyników**: Wyświetlanie i zapisywanie wyników (kod, tekst)
- **Animacje**: Podświetlenia przy aktualizacji statusów i komunikacji
- **Zapis/odczyt stanu**: Przyciski do zapisywania i wczytywania stanu z pliku JSON

## Jak uruchomić

1. Zainstaluj wymagane biblioteki:
```bash
pip install matplotlib
# Opcjonalnie dla OpenAI API:
# pip install openai
```

2. Uruchom program:
```bash
python main.py
```

## Jak używać

### Dodawanie nowych zadań
1. Wpisz tytuł zadania w pole "Title"
2. Opisz zadanie w polu "Description" (użyj słów kluczowych):
   - "kod" lub "code" → przydzieli do programisty
   - "analiz" lub "dane" → przydzieli do analityka
   - "obraz" lub "image" → przydzieli do generatora obrazów
   - "tekst" lub "text" → przydzieli do analityka tekstu
3. Wybierz priorytet zadania
4. Kliknij "Submit Task"

### Obserwowanie zadań
- **Lista zadań**: Prawy panel pokazuje wszystkie zadania z ikonami statusów
- **Ikony statusów**: ⏳ PENDING, 🔄 IN_PROGRESS, ✅ COMPLETED, ❌ FAILED, 🚫 BLOCKED
- **Odświeżanie**: Kliknij "Odśwież listę" aby zaktualizować widok

### Wyniki końcowe
- Kliknij "Pokaż wyniki" aby otworzyć okno z wynikami
- **Zakładka "Kod"**: Wyświetla wygenerowany kod (dla zadań kodowania)
- **Zakładka "Tekst"**: Wyświetla wszystkie wyniki agentów
- **Zapisywanie**: Przyciski "Zapisz kod" i "Zapisz tekst"

### Obserwowanie wykresów
- Otworzy się dodatkowe okno z wykresami
- Wykres aktywności agentów pokazuje liczbę wykonanych zadań
- Wykres statusów zadań pokazuje procentowy podział statusów

### Zapis/odczyt stanu
- Kliknij "Zapisz stan" aby zapisać aktualny stan do pliku JSON
- Kliknij "Wczytaj stan" aby wczytać stan z pliku JSON

## Typy agentów

### 1. Programista (Jan Nowak)
- **Słowa kluczowe**: "kod", "code", "program"
- **Umiejętności**: Python, kodowanie, debugowanie
- **Wyniki**: Generuje kod w Python

### 2. Analityk danych (Anna Kowalska)
- **Słowa kluczowe**: "analiz", "dane", "data"
- **Umiejętności**: Analiza danych, statystyka, Python
- **Wyniki**: Analiza wzorców i rekomendacje

### 3. Generator obrazów (Piotr Malinowski)
- **Słowa kluczowe**: "obraz", "image", "picture"
- **Umiejętności**: Generowanie obrazów, grafika, AI art
- **Wyniki**: Generuje obrazy zgodnie z opisem

### 4. Analityk tekstu (Katarzyna Wiśniewska)
- **Słowa kluczowe**: "tekst", "text", "content"
- **Umiejętności**: Analiza tekstu, NLP, tworzenie treści
- **Wyniki**: Analiza tekstu i główne tematy

### 5. CEO (Eleanor Wells)
- **Rola**: Zarządzanie i delegowanie zadań
- **Umiejętności**: Przywództwo, podejmowanie decyzji
- **Wyniki**: Podsumowania i strategiczne decyzje

## Integracja z lokalnym modelem Bielik 11B v2.3

Aby używać lokalnego modelu Bielik 11B v2.3 dla bardziej inteligentnych odpowiedzi:

### 1. Instalacja Ollama

```bash
# Pobierz i zainstaluj Ollama z: https://ollama.ai
# Następnie uruchom:
ollama pull SpeakLeash/bielik-11b-v2.3-instruct:Q4_K_M
```

### 2. Setup automatyczny

```bash
# Zainstaluj llama-cpp-python
pip install llama-cpp-python

# Uruchom skrypt setup
python setup_llama.py
```

### 3. Sprawdzenie modelu

Skrypt `setup_llama.py` automatycznie:
- Sprawdza czy Ollama jest zainstalowane
- Weryfikuje czy model Bielik jest dostępny
- Testuje czy model działa poprawnie

### 4. Ręczne sprawdzenie

```bash
# Sprawdź czy Ollama działa
ollama --version

# Sprawdź dostępne modele
ollama list

# Jeśli model nie jest dostępny, pobierz go
ollama pull SpeakLeash/bielik-11b-v2.3-instruct:Q4_K_M
```

### 5. Konfiguracja

Model będzie automatycznie używany przez agentów zamiast prostych odpowiedzi. Każdy agent otrzyma specjalizowany prompt w języku polskim:

- **Programista**: Generuje kod HTML/CSS/JavaScript
- **Analityk**: Przygotowuje raporty i analizy
- **Generator obrazów**: Opisuje obrazy i grafiki
- **Analityk tekstu**: Pisze artykuły i treści
- **CEO**: Przygotowuje strategiczne plany

### 6. Wymagania systemowe

- **RAM**: Minimum 8GB (zalecane 16GB+)
- **CPU**: Wielordzeniowy procesor
- **Dysk**: 5GB wolnego miejsca na model
- **Ollama**: Zainstalowane i działające

## Integracja z OpenAI API

Aby używać OpenAI API dla bardziej inteligentnych odpowiedzi:

1. Zainstaluj bibliotekę:
```bash
pip install openai
```

2. W pliku `agents.py` odkomentuj linie z OpenAI API i dodaj swój klucz API:
```python
client = openai.OpenAI(api_key="your-api-key")
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": task_description}]
)
return response.choices[0].message.content
```

## Priorytet modeli

Program używa modeli w następującej kolejności:
1. **Lokalny Llama 3.2 3B** (jeśli dostępny)
2. **OpenAI API** (jeśli skonfigurowane)
3. **Proste odpowiedzi** (fallback)

## Jak rozwijać agentów

### Dodawanie nowego typu agenta
1. W pliku `agents.py` dodaj nowy typ do enum `AgentType`:
```python
class AgentType(Enum):
    CODER = auto()
    ANALYST = auto()
    IMAGE_GEN = auto()
    TEXT_ANALYST = auto()
    BOSS = auto()
    NEW_TYPE = auto()  # Dodaj tutaj
```

2. W metodzie `decide()` dodaj logikę dla nowego typu:
```python
def decide(self, task_desc: str) -> str:
    if self.agent_type == AgentType.NEW_TYPE:
        if "słowo_kluczowe" in task_desc.lower():
            return "nowa_akcja"
```

3. W `generate_simple_response()` dodaj odpowiedź:
```python
def generate_simple_response(self, task_description: str) -> str:
    if self.agent_type == AgentType.NEW_TYPE:
        return f"{self.name}: Nowa odpowiedź dla {task_description}"
```

4. W `main.py` w metodzie `find_suitable_agent()` dodaj warunek:
```python
if agent.agent_type == AgentType.NEW_TYPE and "słowo_kluczowe" in task.description.lower():
    return agent
```

### Dodawanie nowego agenta
W funkcji `main()` w `main.py`:
```python
new_agent = AgentBase(
    id="new_agent1",
    name="Nowy Agent",
    role="Nowa Rola",
    agent_type=AgentType.NEW_TYPE,
    skills=["umiejętność1", "umiejętność2"],
    personality_traits=["cecha1", "cecha2"],
    preferred_tools=["narzędzie1", "narzędzie2"],
    collaborators=["agent1", "agent2"]
)
office.add_agent(new_agent)
```

## Struktura plików

- `main.py` - Główny plik z logiką symulacji
- `agents.py` - Definicje agentów i komunikacji
- `tasks.py` - Definicje zadań i statusów
- `storage.py` - Zapis/odczyt stanu
- `gui.py` - Interfejs graficzny z wykresami i listą zadań
- `README.md` - Ten plik z instrukcjami
- `requirements.txt` - Lista zależności

## Wymagania techniczne

- Python 3.7+
- matplotlib (dla wykresów)
- tkinter (wbudowany w Python)
- openai (opcjonalnie, dla AI API)

## Możliwe rozszerzenia

1. **Integracja z AI**: Dodanie OpenAI API dla bardziej inteligentnych odpowiedzi
2. **Więcej typów zadań**: Obsługa generowania obrazów, analizy tekstu
3. **Zaawansowane wykresy**: Wykresy czasowe, heatmapy
4. **Baza danych**: Przechowywanie historii w SQLite
5. **Sieć agentów**: Komunikacja przez HTTP/WebSocket
6. **Wizualizacja komunikacji**: Linie połączeń między agentami
7. **Real-time updates**: Aktualizacje w czasie rzeczywistym 