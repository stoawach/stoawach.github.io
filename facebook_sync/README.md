Facebook Sync for Stowarzyszenie Wachniewskiej

Automatyczne pobieranie postów z Facebooka i ich publikacja na stronie stowarzyszenia.
Funkcjonalności

    Pobieranie postów z określonego profilu na Facebooku.
    Zapisywanie postów w formacie Markdown w folderze _services.
    Pobieranie obrazów w wysokiej jakości i zapisywanie w images/posts.
    Generowanie powiązanych postów na podstawie tagów i treści.
    Dodawanie linków do udostępniania postów na Facebooku.

Wymagania

    Python 3.8 lub nowszy
    Konto programisty Facebooka z dostępem do API
    Klucz dostępu (ACCESS_TOKEN) i ID profilu (PROFILE_ID)

Instalacja

    Klonowanie repozytorium

git clone https://github.com/mijapa/stoawach.github.io.git
cd stoawach.github.io/facebook_sync

Instalacja wymaganych bibliotek Zainstaluj biblioteki wymagane przez projekt:

pip install -r requirements.txt

Konfiguracja pliku secrets.json W folderze facebook_sync utwórz plik secrets.json:

    {
        "facebook_token": "TWÓJ_TOKEN_DOSTĘPU",
        "profile_id": "ID_PROFILU"
    }

Użycie

    Przejdź do folderu facebook_sync:

cd facebook_sync

Uruchom synchronizację:

    python main.py

    Posty zostaną zapisane w folderze _services, a obrazy w images/posts.

Struktura projektu

    facebook_sync/
    ├── main.py                  # Główna logika programu
    ├── utils/                   # Funkcje pomocnicze
    │   ├── facebook_api.py      # Obsługa API Facebooka
    │   ├── file_utils.py        # Operacje na plikach i obrazach
    │   ├── post_utils.py        # Przetwarzanie postów i generowanie plików Markdown
    │   └── text_utils.py        # Operacje na tekście
    _services/                   # Folder na wygenerowane pliki Markdown
    images/posts/                # Folder na pobrane obrazy          # Folder na pobrane obrazy
