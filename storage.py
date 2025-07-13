import json
from typing import Any

def save_state(filename: str, data: Any):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_state(filename: str) -> Any:
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Błąd JSON w pliku {filename}: {e}")
        return {'agents': [], 'tasks': []}
    except FileNotFoundError:
        print(f"Plik {filename} nie istnieje")
        return {'agents': [], 'tasks': []}
    except Exception as e:
        print(f"Błąd podczas wczytywania {filename}: {e}")
        return {'agents': [], 'tasks': []} 