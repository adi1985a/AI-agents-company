#!/usr/bin/env python3
"""
Skrypt do konfiguracji modelu Bielik 11B v2.3
"""

import os
import sys
import subprocess
import requests
from pathlib import Path

def install_llama_cpp():
    """Instaluje llama-cpp-python"""
    print("Instalowanie llama-cpp-python...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "llama-cpp-python"])
        print("✅ llama-cpp-python zainstalowane pomyślnie")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Błąd podczas instalacji: {e}")
        return False

def check_ollama():
    """Sprawdza czy Ollama jest zainstalowane i dostępne"""
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Ollama jest zainstalowane: {result.stdout.strip()}")
            return True
        else:
            print("❌ Ollama nie jest zainstalowane lub nie działa")
            return False
    except FileNotFoundError:
        print("❌ Ollama nie jest zainstalowane")
        print("Zainstaluj Ollama z: https://ollama.ai")
        return False

def check_bielik_model():
    """Sprawdza czy model Bielik jest dostępny w Ollama"""
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if result.returncode == 0:
            if "bielik" in result.stdout.lower():
                print("✅ Model Bielik jest dostępny w Ollama")
                return True
            else:
                print("❌ Model Bielik nie jest dostępny w Ollama")
                return False
        else:
            print("❌ Nie udało się sprawdzić listy modeli Ollama")
            return False
    except Exception as e:
        print(f"❌ Błąd podczas sprawdzania modeli: {e}")
        return False

def pull_bielik_model():
    """Pobiera model Bielik do Ollama"""
    print("Pobieranie modelu Bielik 11B v2.3...")
    print("To może potrwać kilka minut...")
    
    try:
        result = subprocess.run([
            "ollama", "pull", "SpeakLeash/bielik-11b-v2.3-instruct:Q4_K_M"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Model Bielik został pobrany pomyślnie")
            return True
        else:
            print(f"❌ Błąd podczas pobierania modelu: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Błąd podczas pobierania modelu: {e}")
        return False

def test_model():
    """Testuje czy model Bielik działa poprawnie"""
    try:
        from llama_cpp import Llama
        
        print("Testowanie modelu Bielik...")
        llm = Llama(
            model_path="SpeakLeash/bielik-11b-v2.3-instruct:Q4_K_M",
            n_ctx=2048,
            n_threads=4,
            verbose=False
        )
        
        response = llm("Napisz 'Cześć'", max_tokens=10)
        print("✅ Model Bielik działa poprawnie!")
        return True
        
    except Exception as e:
        print(f"❌ Błąd podczas testowania modelu: {e}")
        return False

def main():
    """Główna funkcja setup"""
    print("=== Setup Bielik 11B v2.3 ===\n")
    
    # 1. Sprawdź Ollama
    if not check_ollama():
        print("\n📋 Instrukcje instalacji Ollama:")
        print("1. Wejdź na: https://ollama.ai")
        print("2. Pobierz i zainstaluj Ollama")
        print("3. Uruchom ponownie: python setup_llama.py")
        return
    
    # 2. Sprawdź czy model jest dostępny
    if not check_bielik_model():
        print("\nPobieranie modelu Bielik...")
        if not pull_bielik_model():
            print("\n📋 Instrukcje ręcznego pobierania:")
            print("1. Otwórz terminal/command prompt")
            print("2. Uruchom: ollama pull SpeakLeash/bielik-11b-v2.3-instruct:Q4_K_M")
            print("3. Poczekaj na pobranie (może potrwać kilka minut)")
            print("4. Uruchom ponownie: python setup_llama.py")
            return
    
    # 3. Instaluj llama-cpp-python
    if not install_llama_cpp():
        return
    
    # 4. Testuj model
    if test_model():
        print("\n🎉 Setup zakończony pomyślnie!")
        print("Model: SpeakLeash/bielik-11b-v2.3-instruct:Q4_K_M")
        print("Możesz teraz uruchomić program z lokalnym modelem Bielik.")
    else:
        print("\n❌ Setup nie powiódł się.")

if __name__ == "__main__":
    main() 