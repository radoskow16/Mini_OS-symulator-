#!/usr/bin/env python3
# mini-os — minimalistyczne środowisko desktopowe dla macOS
# Wymaga: PySide6, PySide6-WebEngine, opencv-python
import sys, os, json, random, time, shutil, hashlib, uuid, csv, re, platform, shlex, subprocess, contextlib, traceback
import weakref
from collections import OrderedDict
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, QUrl, QUrlQuery, QSize, QProcess, QPropertyAnimation, QEasingCurve, QPointF, QRectF
from PySide6.QtGui import QFont, QAction, QKeySequence, QPixmap, QPainter, QPen, QLinearGradient, QBrush, QPolygonF, QPainterPath, QColor, QRadialGradient, QIcon, QTransform, QSyntaxHighlighter, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QStackedWidget, QVBoxLayout, QHBoxLayout, QGraphicsOpacityEffect,
    QGridLayout, QLabel, QPushButton, QLineEdit, QFrame, QMessageBox, QFileDialog,
    QListWidget, QListWidgetItem, QListView, QSlider, QCheckBox, QComboBox, QScrollArea,
    QInputDialog, QProgressBar, QTabWidget, QTextEdit, QTableWidget, QTableWidgetItem, QDialog, QMenu, QGroupBox,
    QPlainTextEdit, QSplitter
)
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
    WEBENGINE_AVAILABLE = True
except Exception:
    WEBENGINE_AVAILABLE = False

try:
    import cv2
    from PySide6.QtGui import QImage
    CAMERA_AVAILABLE = True
except Exception:
    CAMERA_AVAILABLE = False

try:
    from openpyxl import Workbook, load_workbook
    XLSX_AVAILABLE = True
except Exception:
    XLSX_AVAILABLE = False

APP_NAME = "mini-os"
APP_VERSION = "1.0"
ROOT = Path.home() / "mini os"
LEGACY_ROOT = Path.home() / APP_NAME
DATA = ROOT / "data"
PHOTOS = ROOT / "photos"
LEGACY_PHOTOS_DIR = PHOTOS
SESSIONS = ROOT / "sessions"
WALLPAPERS_DIR = ROOT / "wallpapers"
LEGACY_WALLPAPERS_DIR = WALLPAPERS_DIR
PROFILE_STORAGE_ROOT = ROOT / "profile_data"
PROFILE_WALLPAPERS_DIR = PROFILE_STORAGE_ROOT / "default" / "wallpapers"
PROFILE_AVATARS_DIR = DATA / "profile_avatars"
BUNDLED_WALLPAPERS_DIR = Path(__file__).resolve().parent / "wallpapers"
BUNDLED_MINECRAFT_FILE = Path(__file__).resolve().parent / "MINECRAFT.html"

def migrate_legacy_storage():
    if not LEGACY_ROOT.is_dir() or LEGACY_ROOT == ROOT:
        return
    for source in LEGACY_ROOT.iterdir():
        destination = ROOT / source.name
        if source.is_dir():
            if destination.exists() and not destination.is_dir():
                continue
            destination.mkdir(parents=True, exist_ok=True)
            for child in source.iterdir():
                child_destination = destination / child.name
                if child.is_dir():
                    if not child_destination.exists():
                        shutil.copytree(child, child_destination)
                elif not child_destination.exists():
                    shutil.copy2(child, child_destination)
        elif not destination.exists():
            ROOT.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

migrate_legacy_storage()

APP_STORE = [
    {"id": "youtube", "name": "YouTube", "icon": "▶️", "url": "https://www.youtube.com", "category": "Wideo i muzyka"},
    {"id": "ytmusic", "name": "YT Music", "icon": "🎵", "url": "https://music.youtube.com", "category": "Wideo i muzyka"},
    {"id": "chatgpt", "name": "ChatGPT", "icon": "🤖", "url": "https://chatgpt.com", "category": "Narzędzia"},
    {"id": "gemini", "name": "Gemini", "icon": "✨", "url": "https://gemini.google.com", "category": "Narzędzia"},
    {"id": "netflix", "name": "Netflix", "icon": "🎬", "url": "https://www.netflix.com", "category": "Wideo i muzyka"},
    {"id": "grypl", "name": "Gry.pl", "icon": "🎮", "url": "https://www.gry.pl", "category": "Gry"},
    {"id": "minecraft", "name": "MINECRAFT", "icon": "⛏️", "local": True, "category": "Gry"},
    {"id": "whatsapp", "name": "WhatsApp", "icon": "💬", "url": "https://web.whatsapp.com", "category": "Społeczności"},
]
ADDITIONAL_WEBSITES = [
    # Wyszukiwanie i wiedza (10)
    ("google", "Google", "🔎", "https://www.google.com", "Wyszukiwanie i wiedza"),
    ("bing", "Bing", "🔍", "https://www.bing.com", "Wyszukiwanie i wiedza"),
    ("duckduckgo", "DuckDuckGo", "🦆", "https://duckduckgo.com", "Wyszukiwanie i wiedza"),
    ("yahoo", "Yahoo", "🟣", "https://search.yahoo.com", "Wyszukiwanie i wiedza"),
    ("startpage", "Startpage", "🔐", "https://www.startpage.com", "Wyszukiwanie i wiedza"),
    ("bravesearch", "Brave Search", "🦁", "https://search.brave.com", "Wyszukiwanie i wiedza"),
    ("wikipedia", "Wikipedia", "📚", "https://pl.wikipedia.org", "Wyszukiwanie i wiedza"),
    ("wiktionary", "Wikisłownik", "📖", "https://pl.wiktionary.org", "Wyszukiwanie i wiedza"),
    ("britannica", "Britannica", "📘", "https://www.britannica.com", "Wyszukiwanie i wiedza"),
    ("archive", "Internet Archive", "🗄️", "https://archive.org", "Wyszukiwanie i wiedza"),
    # Mapy i tłumaczenia (10)
    ("maps", "Google Maps", "🗺️", "https://maps.google.com", "Mapy i podróże"),
    ("openstreetmap", "OpenStreetMap", "🌍", "https://www.openstreetmap.org", "Mapy i podróże"),
    ("translate", "Google Tłumacz", "🌐", "https://translate.google.com", "Mapy i podróże"),
    ("deepl", "DeepL", "💬", "https://www.deepl.com/translator", "Mapy i podróże"),
    ("mapycz", "Mapy.cz", "🧭", "https://mapy.cz", "Mapy i podróże"),
    ("herewego", "HERE WeGo", "📍", "https://wego.here.com", "Mapy i podróże"),
    ("bingmaps", "Bing Maps", "🗺️", "https://www.bing.com/maps", "Mapy i podróże"),
    ("nasa", "NASA", "🚀", "https://www.nasa.gov", "Mapy i podróże"),
    ("imdb", "IMDb", "🎥", "https://www.imdb.com", "Mapy i podróże"),
    ("rottentomatoes", "Rotten Tomatoes", "🍅", "https://www.rottentomatoes.com", "Mapy i podróże"),
    # Społeczności (10)
    ("facebook", "Facebook", "ⓕ", "https://www.facebook.com", "Społeczności"),
    ("instagram", "Instagram", "📸", "https://www.instagram.com", "Społeczności"),
    ("x", "X", "𝕏", "https://x.com", "Społeczności"),
    ("tiktok", "TikTok", "♪", "https://www.tiktok.com", "Społeczności"),
    ("snapchat", "Snapchat", "👻", "https://www.snapchat.com", "Społeczności"),
    ("reddit", "Reddit", "🟠", "https://www.reddit.com", "Społeczności"),
    ("pinterest", "Pinterest", "📌", "https://www.pinterest.com", "Społeczności"),
    ("linkedin", "LinkedIn", "💼", "https://www.linkedin.com", "Społeczności"),
    ("discord", "Discord", "🎧", "https://discord.com/app", "Społeczności"),
    ("telegram", "Telegram Web", "✈️", "https://web.telegram.org", "Społeczności"),
    # Wideo i muzyka (10)
    ("twitch", "Twitch", "🟣", "https://www.twitch.tv", "Wideo i muzyka"),
    ("vimeo", "Vimeo", "▶️", "https://vimeo.com", "Wideo i muzyka"),
    ("soundcloud", "SoundCloud", "☁️", "https://soundcloud.com", "Wideo i muzyka"),
    ("spotify", "Spotify", "🟢", "https://open.spotify.com", "Wideo i muzyka"),
    ("applemusic", "Apple Music", "🎼", "https://music.apple.com", "Wideo i muzyka"),
    ("amazonmusic", "Amazon Music", "🎶", "https://music.amazon.com", "Wideo i muzyka"),
    ("deezer", "Deezer", "🎧", "https://www.deezer.com", "Wideo i muzyka"),
    ("bandcamp", "Bandcamp", "🎸", "https://bandcamp.com", "Wideo i muzyka"),
    ("mixcloud", "Mixcloud", "🎚️", "https://www.mixcloud.com", "Wideo i muzyka"),
    ("ted", "TED", "💡", "https://www.ted.com", "Wideo i muzyka"),
    # Polskie wiadomości (10)
    ("onet", "Onet", "📰", "https://www.onet.pl", "Polskie wiadomości"),
    ("wp", "WP", "📰", "https://www.wp.pl", "Polskie wiadomości"),
    ("interia", "Interia", "📰", "https://www.interia.pl", "Polskie wiadomości"),
    ("gazetapl", "Gazeta.pl", "🗞️", "https://www.gazeta.pl", "Polskie wiadomości"),
    ("tvn24", "TVN24", "📺", "https://tvn24.pl", "Polskie wiadomości"),
    ("polsatnews", "Polsat News", "📺", "https://www.polsatnews.pl", "Polskie wiadomości"),
    ("rmf24", "RMF24", "📻", "https://www.rmf24.pl", "Polskie wiadomości"),
    ("radiozet", "Radio ZET", "📻", "https://wiadomosci.radiozet.pl", "Polskie wiadomości"),
    ("pap", "PAP", "📰", "https://www.pap.pl", "Polskie wiadomości"),
    ("tvpinfo", "TVP Info", "📺", "https://www.tvp.info", "Polskie wiadomości"),
    # Światowe wiadomości (10)
    ("bbc", "BBC", "🌍", "https://www.bbc.com", "Światowe wiadomości"),
    ("reuters", "Reuters", "🌐", "https://www.reuters.com", "Światowe wiadomości"),
    ("apnews", "AP News", "📰", "https://apnews.com", "Światowe wiadomości"),
    ("guardian", "The Guardian", "🗞️", "https://www.theguardian.com", "Światowe wiadomości"),
    ("aljazeera", "Al Jazeera", "🌍", "https://www.aljazeera.com", "Światowe wiadomości"),
    ("dw", "DW", "🌐", "https://www.dw.com", "Światowe wiadomości"),
    ("france24", "France 24", "📺", "https://www.france24.com", "Światowe wiadomości"),
    ("euronews", "Euronews", "🌍", "https://www.euronews.com", "Światowe wiadomości"),
    ("npr", "NPR", "📻", "https://www.npr.org", "Światowe wiadomości"),
    ("nytimes", "The New York Times", "📰", "https://www.nytimes.com", "Światowe wiadomości"),
    # Zakupy (10)
    ("allegro", "Allegro", "🛍️", "https://allegro.pl", "Zakupy"),
    ("olx", "OLX", "♻️", "https://www.olx.pl", "Zakupy"),
    ("vinted", "Vinted", "👕", "https://www.vinted.pl", "Zakupy"),
    ("etsy", "Etsy", "🧶", "https://www.etsy.com", "Zakupy"),
    ("amazon", "Amazon", "📦", "https://www.amazon.com", "Zakupy"),
    ("ebay", "eBay", "🏷️", "https://www.ebay.com", "Zakupy"),
    ("ikea", "IKEA", "🪑", "https://www.ikea.com/pl/pl/", "Zakupy"),
    ("zalando", "Zalando", "👟", "https://www.zalando.pl", "Zakupy"),
    ("empik", "Empik", "📚", "https://www.empik.com", "Zakupy"),
    ("ceneo", "Ceneo", "🔖", "https://www.ceneo.pl", "Zakupy"),
    # Podróże i transport (10)
    ("booking", "Booking.com", "🏨", "https://www.booking.com", "Podróże i transport"),
    ("airbnb", "Airbnb", "🏠", "https://www.airbnb.com", "Podróże i transport"),
    ("skyscanner", "Skyscanner", "✈️", "https://www.skyscanner.net", "Podróże i transport"),
    ("tripadvisor", "Tripadvisor", "🧳", "https://www.tripadvisor.com", "Podróże i transport"),
    ("ryanair", "Ryanair", "✈️", "https://www.ryanair.com", "Podróże i transport"),
    ("lot", "LOT", "🛫", "https://www.lot.com", "Podróże i transport"),
    ("pkp", "PKP Intercity", "🚆", "https://www.intercity.pl", "Podróże i transport"),
    ("jakdojade", "Jakdojade", "🚋", "https://jakdojade.pl", "Podróże i transport"),
    ("flixbus", "FlixBus", "🚌", "https://www.flixbus.pl", "Podróże i transport"),
    ("rome2rio", "Rome2Rio", "🗺️", "https://www.rome2rio.com", "Podróże i transport"),
    # Nauka (10)
    ("khanacademy", "Khan Academy", "🎓", "https://pl.khanacademy.org", "Nauka"),
    ("coursera", "Coursera", "🎓", "https://www.coursera.org", "Nauka"),
    ("edx", "edX", "🏫", "https://www.edx.org", "Nauka"),
    ("duolingo", "Duolingo", "🦉", "https://www.duolingo.com", "Nauka"),
    ("quizlet", "Quizlet", "🗂️", "https://quizlet.com", "Nauka"),
    ("wolframalpha", "WolframAlpha", "➗", "https://www.wolframalpha.com", "Nauka"),
    ("geogebra", "GeoGebra", "📐", "https://www.geogebra.org", "Nauka"),
    ("scratch", "Scratch", "🐱", "https://scratch.mit.edu", "Nauka"),
    ("phet", "PhET", "🧪", "https://phet.colorado.edu", "Nauka"),
    ("brilliant", "Brilliant", "🧠", "https://brilliant.org", "Nauka"),
    # Praca i narzędzia (10)
    ("googledrive", "Google Drive", "📁", "https://drive.google.com", "Praca i narzędzia"),
    ("googledocs", "Google Docs", "📄", "https://docs.google.com", "Praca i narzędzia"),
    ("googlesheets", "Google Sheets", "📊", "https://sheets.google.com", "Praca i narzędzia"),
    ("googleslides", "Google Slides", "🖥️", "https://slides.google.com", "Praca i narzędzia"),
    ("gmail", "Gmail", "✉️", "https://mail.google.com", "Praca i narzędzia"),
    ("outlook", "Outlook", "📨", "https://outlook.live.com", "Praca i narzędzia"),
    ("onedrive", "OneDrive", "☁️", "https://onedrive.live.com", "Praca i narzędzia"),
    ("dropbox", "Dropbox", "📦", "https://www.dropbox.com", "Praca i narzędzia"),
    ("notion", "Notion", "📝", "https://www.notion.so", "Praca i narzędzia"),
    ("trello", "Trello", "📋", "https://trello.com", "Praca i narzędzia"),
    # Programowanie i gry (10)
    ("gitlab", "GitLab", "🦊", "https://gitlab.com", "Programowanie i gry"),
    ("stackoverflow", "Stack Overflow", "💻", "https://stackoverflow.com", "Programowanie i gry"),
    ("mdn", "MDN Web Docs", "📘", "https://developer.mozilla.org", "Programowanie i gry"),
    ("w3schools", "W3Schools", "🌐", "https://www.w3schools.com", "Programowanie i gry"),
    ("codepen", "CodePen", "🖊️", "https://codepen.io", "Programowanie i gry"),
    ("replit", "Replit", "🧑‍💻", "https://replit.com", "Programowanie i gry"),
    ("poki", "Poki", "🎮", "https://poki.com", "Programowanie i gry"),
    ("crazygames", "CrazyGames", "🕹️", "https://www.crazygames.com", "Programowanie i gry"),
    ("lichess", "Lichess", "♟️", "https://lichess.org", "Programowanie i gry"),
]
APP_STORE.extend({"id": item[0], "name": item[1], "icon": item[2], "url": item[3], "category": item[4]}
                 for item in ADDITIONAL_WEBSITES)
CURATED_WEBSITES_FILE = Path(__file__).resolve().parent / "curated_websites.json"
DIRECTORY_WEBSITES_FILE = Path(__file__).resolve().parent / "directory_websites.json"
for websites_file in (CURATED_WEBSITES_FILE, DIRECTORY_WEBSITES_FILE):
    try:
        websites = json.loads(websites_file.read_text(encoding="utf-8"))
        known_store_ids = {app["id"] for app in APP_STORE}
        APP_STORE.extend(
            app for app in websites
            if isinstance(app, dict) and app.get("id") not in known_store_ids
            and app.get("name") and app.get("url")
        )
    except (OSError, ValueError):
        continue
BUILTIN_DESKTOP_APPS = [
    {"id": "browser", "name": "Przeglądarka", "icon": "🌐", "color": "#183d70", "page": "browser"},
    {"id": "mini_store", "name": "mini_store", "icon": "🛍️", "color": "#176b52", "page": "mini_store"},
    {"id": "camera", "name": "Aparat", "icon": "📷", "color": "#493274", "page": "camera"},
    {"id": "settings", "name": "Ustawienia", "icon": "⚙", "color": "#30394d", "page": "settings"},
    {"id": "files", "name": "Moje pliki", "icon": "📁", "color": "#66501c", "page": "files"},
    {"id": "notepad", "name": "Notatnik", "icon": "📝", "color": "#315777", "page": "notepad"},
    {"id": "paint", "name": "Paint", "icon": "🎨", "color": "#7a3f22", "page": "paint"},
    {"id": "gallery", "name": "Galeria", "icon": "🖼", "color": "#343071", "page": "gallery"},
    {"id": "calculator", "name": "Kalkulator", "icon": "＋", "color": "#174d61", "page": "calculator"},
]
for folder in (ROOT, DATA, PHOTOS, SESSIONS):
    folder.mkdir(parents=True, exist_ok=True)

WALLPAPER_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"}

def install_builtin_wallpapers():
    WALLPAPERS_DIR.mkdir(parents=True, exist_ok=True)
    if not BUNDLED_WALLPAPERS_DIR.is_dir():
        return False
    sources = [source for source in BUNDLED_WALLPAPERS_DIR.iterdir()
               if source.is_file() and source.suffix.lower() in WALLPAPER_EXTENSIONS]
    if len(sources) < 9:
        return False
    for source in sources:
        destination = WALLPAPERS_DIR / source.name
        if not destination.exists() or destination.stat().st_size == 0:
            shutil.copy2(source, destination)
    return len([path for path in WALLPAPERS_DIR.iterdir()
                if path.is_file() and path.suffix.lower() in WALLPAPER_EXTENSIONS]) >= 9

def wallpapers_need_repair():
    expected = {
        Path(wallpaper_id.split(":", 1)[1]).name
        for _label, wallpaper_id in BUILTIN_WALLPAPERS
        if wallpaper_id.startswith("custom:")
    }
    if len(expected) < 9 or not WALLPAPERS_DIR.is_dir():
        return True
    existing = [path for path in WALLPAPERS_DIR.iterdir()
                if path.is_file() and path.suffix.lower() in WALLPAPER_EXTENSIONS]
    return len(existing) < 9 or any(
        not (WALLPAPERS_DIR / name).is_file()
        or (WALLPAPERS_DIR / name).stat().st_size == 0
        for name in expected
    )

SESSION_FILE = SESSIONS / "last_session.json"
SETTINGS_FILE = DATA / "settings.json"
USER_FILE = DATA / "user.json"
PROFILES_FILE = DATA / "profiles.json"

DEFAULT_SETTINGS = {
    "accent": "#5b8cff",
    "animations": True,
    "clock_24h": True,
    "theme": "dark",
    "language": "en",
    "high_contrast": False,
    "start_url": "https://www.google.com",
    "lock_wallpaper": "default",
    "home_wallpaper": "default",
    "app_order": [],
}

UI_EN_TRANSLATIONS = {
    "Pulpit": "Desktop", "Start": "Start", "Ustawienia": "Settings",
    "Wygląd": "Appearance", "Biurko i aplikacje": "Desktop & Apps",
    "Przeglądarka": "Browser", "Użytkownicy i profile": "Users & Profiles",
    "Ogólne": "General", "Informacje": "About", "Dostępność": "Accessibility",
    "Aktualizacje": "Software Update", "Aktualizacje mini-OS": "mini-OS Updates",
    "Zainstalowana wersja: mini-os 1.0": "Installed version: mini-os 1.0",
    "Automatyczne źródło aktualizacji nie jest skonfigurowane.": "No automatic update source is configured.",
    "Sprawdź aktualizacje": "Check for updates",
    "Dostępnych jest 100 dodatkowych języków. Tłumaczenia interfejsu są obecnie dostępne po angielsku i polsku; pozostałe języki używają angielskiego interfejsu.": "100 additional languages are available. The interface is currently translated into English and Polish; other selections use the English interface.",
    "Nie skonfigurowano serwera wydań mini-OS, więc aplikacja nie może automatycznie sprawdzić nowszej wersji.": "No mini-OS release server is configured, so the app cannot check for a newer version automatically.",
    "Tło i motyw": "Wallpaper & Theme", "Motyw systemu": "System appearance",
    "Jasny": "Light", "Ciemny": "Dark", "Krótka animacja uruchamiania": "Startup animation",
    "Zegar 24-godzinny": "24-hour clock", "Tło ekranu blokady (logowania)": "Lock screen wallpaper",
    "Tło ekranu głównego (pulpitu)": "Desktop wallpaper", "Pulpit i aplikacje": "Desktop & Apps",
    "Kolejność aplikacji na pulpicie": "Desktop app order", "↑  Przenieś wyżej": "↑  Move up",
    "↓  Przenieś niżej": "↓  Move down", "Usuń aplikację": "Remove app",
    "Ustawienia startowe": "Startup settings", "Adres startowy przeglądarki": "Browser start page",
    "Profile": "Profiles", "Wybierz profil do edycji": "Choose a profile to edit",
    "Dodaj profil": "Add profile", "Usuń profil": "Delete profile", "Zdjęcie profilu": "Profile picture",
    "Wybierz zdjęcie z Galerii…": "Choose picture from Gallery…", "Usuń zdjęcie": "Remove picture",
    "System": "System", "Zapisz ustawienia": "Save settings",
    "Przywróć ustawienia fabryczne": "Restore factory settings",
    "Informacje o systemie": "System information", "Nazwa systemu": "System name",
    "Wersja systemu": "System version", "Nazwa komputera": "Computer name",
    "Ostatni zapis sesji": "Last session save", "Edytor kodu": "Code editor",
    "Język interfejsu": "Interface language", "Duży kontrast": "High contrast",
    "Witaj w mini-os": "Welcome to mini-os", "Zaloguj się": "Sign in",
    "Wybierz profil": "Choose a profile", "Hasło": "Password", "Zdjęcia": "Photos",
    "Dokumenty": "Documents", "Pobrane": "Downloads", "Otwórz plik": "Open file",
    "Zapisz jako…": "Save as…", "Nowy": "New", "Utwórz plik": "Create file",
    "Nowy folder": "New folder", "Importuj pliki": "Import files", "Odśwież": "Refresh",
    "Folder wyżej": "Parent folder", "Wklej": "Paste", "Kopiuj": "Copy", "Wytnij": "Cut",
    "Zmień nazwę": "Rename", "Usuń": "Delete", "Otwórz w Paint": "Open in Paint",
    "Zrób zdjęcie": "Take photo", "Włącz aparat": "Start camera", "Wyłącz aparat": "Stop camera",
    "Wyszukaj": "Search", "Zainstaluj": "Install", "Zainstalowana": "Installed",
    "Przeglądarka internetowa": "Web browser", "Moje pliki": "My Files", "Notatnik": "Notepad",
    "Galeria": "Gallery", "Aparat": "Camera", "Kalkulator": "Calculator", "Paint": "Paint",
    "Wyloguj z profilu": "Log out", "Uruchom ponownie": "Restart", "Wyłącz mini-OS": "Shut Down mini-OS",
    "Wróć do mini-OS": "Return to mini-OS", "Sesja i zapis": "Session & Save",
    "mini_store": "mini_store", "Otwórz": "Open", "Zapisz": "Save", "Anuluj": "Cancel",
}

ADDITIONAL_LANGUAGES = [
    ("af", "Afrikaans"), ("sq", "Shqip"), ("am", "አማርኛ"), ("ar", "العربية"),
    ("hy", "Հայերեն"), ("az", "Azərbaycan"), ("eu", "Euskara"), ("be", "Беларуская"),
    ("bn", "বাংলা"), ("bs", "Bosanski"), ("bg", "Български"), ("ca", "Català"),
    ("ceb", "Cebuano"), ("zh", "中文"), ("co", "Corsu"), ("hr", "Hrvatski"),
    ("cs", "Čeština"), ("da", "Dansk"), ("nl", "Nederlands"), ("eo", "Esperanto"),
    ("et", "Eesti"), ("fi", "Suomi"), ("fr", "Français"), ("gl", "Galego"),
    ("ka", "ქართული"), ("de", "Deutsch"), ("el", "Ελληνικά"), ("gu", "ગુજરાતી"),
    ("ht", "Kreyòl ayisyen"), ("ha", "Hausa"), ("haw", "ʻŌlelo Hawaiʻi"), ("he", "עברית"),
    ("hi", "हिन्दी"), ("hu", "Magyar"), ("is", "Íslenska"), ("ig", "Igbo"),
    ("id", "Bahasa Indonesia"), ("ga", "Gaeilge"), ("it", "Italiano"), ("ja", "日本語"),
    ("jv", "Basa Jawa"), ("kn", "ಕನ್ನಡ"), ("kk", "Қазақша"), ("km", "ខ្មែរ"),
    ("rw", "Kinyarwanda"), ("ko", "한국어"), ("ku", "Kurdî"), ("ky", "Кыргызча"),
    ("lo", "ລາວ"), ("la", "Latina"), ("lv", "Latviešu"), ("lt", "Lietuvių"),
    ("lb", "Lëtzebuergesch"), ("mk", "Македонски"), ("mg", "Malagasy"), ("ms", "Bahasa Melayu"),
    ("ml", "മലയാളം"), ("mt", "Malti"), ("mi", "Māori"), ("mr", "मराठी"),
    ("mn", "Монгол"), ("my", "မြန်မာ"), ("ne", "नेपाली"), ("no", "Norsk"),
    ("ny", "Chichewa"), ("ps", "پښتو"), ("fa", "فارسی"), ("pt", "Português"),
    ("pa", "ਪੰਜਾਬੀ"), ("ro", "Română"), ("ru", "Русский"), ("sm", "Gagana Samoa"),
    ("gd", "Gàidhlig"), ("sr", "Српски"), ("st", "Sesotho"), ("sn", "chiShona"),
    ("sd", "سنڌي"), ("si", "සිංහල"), ("sk", "Slovenčina"), ("sl", "Slovenščina"),
    ("so", "Soomaali"), ("es", "Español"), ("su", "Basa Sunda"), ("sw", "Kiswahili"),
    ("sv", "Svenska"), ("tl", "Tagalog"), ("tg", "Тоҷикӣ"), ("ta", "தமிழ்"),
    ("te", "తెలుగు"), ("th", "ไทย"), ("tr", "Türkçe"), ("uk", "Українська"),
    ("ur", "اردو"), ("uz", "Oʻzbekcha"), ("vi", "Tiếng Việt"), ("cy", "Cymraeg"),
    ("xh", "isiXhosa"), ("yi", "ייִדיש"), ("yo", "Yorùbá"), ("zu", "isiZulu"),
]
BUILTIN_WALLPAPERS = [
    ("Domyślne tło", "default"),
    ("Zorza polarna", "custom:01-aurora.png"),
    ("Ocean", "custom:02-ocean.png"),
    ("Zachód słońca", "custom:03-sunset.png"),
    ("Fioletowa orbita", "custom:04-violet-orbit.png"),
    ("Leśny zmierzch", "custom:05-forest.png"),
    ("Pustynny wieczór", "custom:06-desert.png"),
    ("Grafit", "custom:07-graphite.png"),
    ("Cyber błękit", "custom:08-cyber-blue.png"),
    ("Różowy blask", "custom:09-rose.png"),
]
LIGHT_BUILTIN_WALLPAPERS = [
    ("Jasna — Poranny blask", "light:dawn"),
    ("Jasna — Lodowy błękit", "light:ice"),
    ("Jasna — Szałwia", "light:sage"),
    ("Jasna — Lawenda", "light:lavender"),
    ("Jasna — Piaskowe wydmy", "light:sand"),
    ("Jasna — Mięta", "light:mint"),
    ("Jasna — Różowa mgiełka", "light:rose"),
    ("Jasna — Perłowe chmury", "light:cloud"),
    ("Jasna — Brzoskwinia", "light:peach"),
]
LIGHT_WALLPAPER_PALETTES = {
    "light:dawn": ("#fff5dc", "#f6d8bb", "#f4c997", "#fffdf7"),
    "light:ice": ("#eef9ff", "#cfe8f5", "#a5d4e8", "#f9fdff"),
    "light:sage": ("#f1f7ed", "#d5e6cf", "#a8c6a0", "#fbfdf8"),
    "light:lavender": ("#f7f2ff", "#e2d7f5", "#c2afe8", "#fdfaff"),
    "light:sand": ("#fff8e9", "#ead8b8", "#d6bb8c", "#fffdf6"),
    "light:mint": ("#edfff8", "#cbeee1", "#91d5bd", "#f8fffc"),
    "light:rose": ("#fff3f6", "#f4d5df", "#e6afc2", "#fffafd"),
    "light:cloud": ("#f6faff", "#dce8f4", "#b8cee4", "#ffffff"),
    "light:peach": ("#fff5ee", "#f6d5c5", "#eab39a", "#fffdfa"),
}

def paint_light_wallpaper(painter, rect, wallpaper_id):
    palette = LIGHT_WALLPAPER_PALETTES.get(wallpaper_id)
    if not palette:
        painter.fillRect(rect, QColor("#f4f6fb"))
        return
    top, bottom, accent, highlight = palette
    width, height = max(1, rect.width()), max(1, rect.height())
    gradient = QLinearGradient(rect.left(), rect.top(), rect.right(), rect.bottom())
    gradient.setColorAt(0, QColor(top))
    gradient.setColorAt(1, QColor(bottom))
    painter.fillRect(rect, QBrush(gradient))
    painter.setPen(Qt.PenStyle.NoPen)

    index = [item_id for _label, item_id in LIGHT_BUILTIN_WALLPAPERS].index(wallpaper_id)
    orb = QColor(highlight)
    orb.setAlpha(185)
    painter.setBrush(orb)
    painter.drawEllipse(QRectF(rect.left() + width * (0.66 - (index % 3) * 0.16),
                               rect.top() + height * (0.08 + (index % 2) * 0.08),
                               min(width, height) * (0.33 if index % 2 else 0.25),
                               min(width, height) * (0.33 if index % 2 else 0.25)))

    wave_color = QColor(accent)
    wave_color.setAlpha(92)
    wave = QPainterPath(QPointF(rect.left(), rect.top() + height * (0.72 + (index % 3) * 0.035)))
    wave.cubicTo(rect.left() + width * 0.24, rect.top() + height * 0.56,
                 rect.left() + width * 0.38, rect.top() + height * 0.84,
                 rect.left() + width * 0.59, rect.top() + height * 0.70)
    wave.cubicTo(rect.left() + width * 0.79, rect.top() + height * 0.56,
                 rect.left() + width * 0.89, rect.top() + height * 0.80,
                 rect.right(), rect.top() + height * 0.64)
    wave.lineTo(rect.right(), rect.bottom())
    wave.lineTo(rect.left(), rect.bottom())
    wave.closeSubpath()
    painter.setBrush(wave_color)
    painter.drawPath(wave)

    lower_color = QColor(accent)
    lower_color.setAlpha(125)
    lower = QPainterPath(QPointF(rect.left(), rect.top() + height * (0.88 - (index % 2) * 0.025)))
    lower.cubicTo(rect.left() + width * 0.25, rect.top() + height * 0.76,
                  rect.left() + width * 0.46, rect.top() + height * 0.99,
                  rect.left() + width * 0.68, rect.top() + height * 0.83)
    lower.cubicTo(rect.left() + width * 0.84, rect.top() + height * 0.72,
                  rect.left() + width * 0.92, rect.top() + height * 0.91,
                  rect.right(), rect.top() + height * 0.80)
    lower.lineTo(rect.right(), rect.bottom())
    lower.lineTo(rect.left(), rect.bottom())
    lower.closeSubpath()
    painter.setBrush(lower_color)
    painter.drawPath(lower)

def light_wallpaper_icon(wallpaper_id, size=QSize(160, 90)):
    pixmap = QPixmap(size)
    pixmap.fill(Qt.GlobalColor.white)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    paint_light_wallpaper(painter, pixmap.rect(), wallpaper_id)
    painter.end()
    return QIcon(pixmap)

def image_fingerprint(path):
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as image_file:
            for chunk in iter(lambda: image_file.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()

def builtin_wallpaper_filenames():
    return {
        Path(wallpaper_id.split(":", 1)[1]).name
        for _label, wallpaper_id in BUILTIN_WALLPAPERS
        if wallpaper_id.startswith("custom:")
    }

def profile_storage_dir(profile_id):
    safe_id = hashlib.sha256(str(profile_id).encode("utf-8")).hexdigest()[:24]
    return PROFILE_STORAGE_ROOT / safe_id

def profile_user_directories(profile_id):
    user_root = profile_storage_dir(profile_id) / "Użytkownik"
    return {
        "root": user_root,
        "downloads": user_root / "Pobrane",
        "documents": user_root / "Dokumenty",
        "pictures": user_root / "Zdjęcia",
    }

def ensure_profile_user_directories(profile_id):
    directories = profile_user_directories(profile_id)
    for key in ("downloads", "documents", "pictures"):
        directories[key].mkdir(parents=True, exist_ok=True)

    # Move existing profile photos into the visible Zdjęcia folder without
    # overwriting any files the user may already have there.
    profile_root = profile_storage_dir(profile_id)
    legacy_photos = profile_root / "photos"
    migration_marker = profile_root / ".user_photos_migrated"
    if legacy_photos.is_dir() and not migration_marker.exists():
        migration_complete = True
        for source in legacy_photos.iterdir():
            if source.is_file() and source.suffix.lower() in WALLPAPER_EXTENSIONS:
                destination = directories["pictures"] / source.name
                if not destination.exists():
                    try:
                        shutil.copy2(source, destination)
                    except OSError:
                        migration_complete = False
        if migration_complete:
            try:
                migration_marker.write_text("1", encoding="utf-8")
            except OSError:
                pass
    return directories

def wallpaper_image_path(filename):
    filename = Path(filename).name
    if filename in builtin_wallpaper_filenames():
        return WALLPAPERS_DIR / filename
    return PROFILE_WALLPAPERS_DIR / filename
STYLE = """
QWidget { background: #10131b; color: #f4f6fb; font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial; }
QLabel { color: #f4f6fb; }
QLineEdit, QComboBox, QListWidget {
  background: #1b2130; color: #f4f6fb; border: 1px solid #30394d;
  border-radius: 12px; padding: 12px; font-size: 17px;
}
QPushButton {
  background: #222a3a; color: #f6f7fb; border: 1px solid #30394d;
  border-radius: 16px; padding: 15px 20px; font-size: 18px; min-height: 28px;
}
QPushButton:hover { background: #303b51; }
QPushButton:pressed { background: #3a4b69; }
QPushButton:checked { background: #40577e; border: 1px solid #8caeff; }
QPushButton#accent { background: #5b8cff; color: white; border: 0; font-weight: 600; }
QPushButton#tile { min-height: 125px; font-size: 22px; font-weight: 600; }
QFrame#panel { background: #171c27; border: 1px solid #293246; border-radius: 22px; }
QProgressBar { background: #252c3b; border: 0; border-radius: 5px; height: 8px; }
QProgressBar::chunk { background: #5b8cff; border-radius: 5px; }
QSlider::groove:horizontal { height: 8px; background: #30394d; border-radius: 4px; }
QSlider::handle:horizontal { background: #5b8cff; width: 20px; margin: -6px 0; border-radius: 10px; }
"""

LIGHT_THEME_BACKGROUNDS = {
    "#10131b": "#f4f6fb", "#1b2130": "#ffffff", "#222a3a": "#e8edf5",
    "#303b51": "#d8e1ef", "#3a4b69": "#cad4e2", "#40577e": "#dbeafe",
    "#171c27": "#ffffff", "#252c3b": "#e5eaf2", "#080a0f": "#f8fafc",
    "#0b0e15": "#edf1f7", "#202634": "#e8edf5", "#242424": "#e5eaf2",
}

LIGHT_THEME_FOREGROUNDS = {
    "#f4f6fb": "#202b3d", "#f6f7fb": "#202b3d", "#aab4ca": "#536175",
    "#a9b3c8": "#536175", "#8e9ab2": "#536175", "#cbd4e8": "#3a465b",
    "#9ba8bd": "#566478", "#b8b8b8": "#6b7280", "#ffffff": "#263449",
    "#fff": "#263449", "white": "#263449", "whitesmoke": "#263449",
    "ivory": "#263449",
}

def themed_stylesheet(stylesheet, light_mode):
    if not light_mode:
        return stylesheet
    # Convert color declarations by their role: a light foreground becomes
    # dark text, while a dark surface becomes a light surface. A global string
    # replacement conflated identical foreground/background colors and made
    # light mode render dark panels with dark text.
    def convert_color(match):
        property_name, value = match.group(1), match.group(2)
        is_background = property_name.lower().startswith("background")
        table = LIGHT_THEME_BACKGROUNDS if is_background else LIGHT_THEME_FOREGROUNDS
        replacement = table.get(value.lower())
        if replacement:
            return f"{property_name}{replacement}"
        if value.startswith("#"):
            color = QColor(value)
            if not color.isValid():
                return match.group(0)
            if is_background and color.lightnessF() < 0.78:
                # Keep app tiles recognizable by hue, while softening dark
                # store colors into a light pastel surface.
                amount = 0.82
                red = round(color.red() + (255 - color.red()) * amount)
                green = round(color.green() + (255 - color.green()) * amount)
                blue = round(color.blue() + (255 - color.blue()) * amount)
                return f"{property_name}#{red:02x}{green:02x}{blue:02x}"
            if not is_background and color.lightnessF() > 0.62:
                return f"{property_name}#263449"
        return match.group(0)

    return re.sub(
        r"(?i)(\b(?:background(?:-color)?|color)\s*:\s*)(#[0-9a-f]{3,8}|white|whitesmoke|ivory)",
        convert_color,
        stylesheet,
    )


def app_tile_stylesheet(brand_color, light_mode):
    brand = QColor(brand_color)
    if not brand.isValid():
        brand = QColor("#52627a")
    if light_mode:
        # Keep a hint of each app's brand while giving every tile a calm,
        # readable surface in the light theme.
        amount = 0.90
        red = round(brand.red() + (255 - brand.red()) * amount)
        green = round(brand.green() + (255 - brand.green()) * amount)
        blue = round(brand.blue() + (255 - brand.blue()) * amount)
        return (
            f"QPushButton#tile {{ background:#{red:02x}{green:02x}{blue:02x}; color:#263449; "
            f"border:1px solid #d9e1ed; border-left:4px solid {brand.name()}; "
            "border-radius:16px; padding:10px; font-size:18px; font-weight:600; }"
            "QPushButton#tile:hover { background:#eef4fc; border:1px solid #8caeff; "
            "border-left:4px solid #477be2; }"
        )
    return (
        f"QPushButton#tile {{ background:{brand.name()}; color:#ffffff; border:0; "
        "border-radius:16px; padding:10px; font-size:18px; font-weight:600; }"
        "QPushButton#tile:hover { border:2px solid #8caeff; }"
    )


def set_webview_theme(page, light_mode):
    """Ask Chromium to apply the selected color scheme to the loaded website."""
    if not page or not WEBENGINE_AVAILABLE:
        return
    try:
        page.settings().setAttribute(
            QWebEngineSettings.WebAttribute.ForceDarkMode,
            not light_mode,
        )
        page.setBackgroundColor(QColor("#ffffff" if light_mode else "#10131b"))
        page.setProperty("miniOsLightTheme", bool(light_mode))
        if not page.property("miniOsThemeLoadHook"):
            page.setProperty("miniOsThemeLoadHook", True)
            page.loadFinished.connect(lambda _ok, target=page: apply_web_document_theme(target))
        apply_web_document_theme(page)
    except (AttributeError, RuntimeError):
        pass


def apply_web_document_theme(page):
    """Set the document's native control scheme after each page navigation."""
    try:
        scheme = "light" if page.property("miniOsLightTheme") else "dark"
        script = (
            "(() => { const scheme = '" + scheme + "'; "
            "if (!document.documentElement) return; "
            "document.documentElement.style.colorScheme = scheme; "
            "let meta = document.querySelector('meta[name=\"color-scheme\"]'); "
            "if (!meta) { meta = document.createElement('meta'); meta.name = 'color-scheme'; "
            "document.head && document.head.appendChild(meta); } "
            "if (meta) meta.content = scheme; })();"
        )
        page.runJavaScript(script)
    except (AttributeError, RuntimeError):
        pass

class MiniOSPage(QWidget):
    """A regular app page with an optional image or built-in wallpaper behind its widgets."""
    def __init__(self, name):
        super().__init__()
        self.page_name = name
        self.wallpaper_id = "default"
        self.light_mode = False

    def set_wallpaper(self, wallpaper_id):
        self.wallpaper_id = wallpaper_id or "default"
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        wallpaper_id = self.wallpaper_id
        if wallpaper_id.startswith("light:"):
            paint_light_wallpaper(painter, rect, wallpaper_id)
            return
        if wallpaper_id.startswith("custom:"):
            filename = Path(wallpaper_id.split(":", 1)[1]).name
            pixmap = QPixmap(str(wallpaper_image_path(filename)))
            if not pixmap.isNull() and self.width() > 0 and self.height() > 0:
                scaled = pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                painter.drawPixmap((self.width() - scaled.width()) // 2, (self.height() - scaled.height()) // 2, scaled)
                if self.light_mode:
                    painter.fillRect(rect, QColor(255, 255, 255, 178))
                else:
                    painter.fillRect(rect, QColor(0, 0, 0, 55))
                return
            wallpaper_id = "default"

        if self.page_name == "boot" or wallpaper_id == "default":
            background = "#000000" if self.page_name == "boot" else "#f4f6fb" if self.light_mode else "#10131b"
            painter.fillRect(rect, QColor(background))
            return

        width, height = max(1, self.width()), max(1, self.height())
        background = QLinearGradient(0, 0, 0, height)
        if wallpaper_id == "aurora":
            background.setColorAt(0.0, QColor("#071321")); background.setColorAt(1.0, QColor("#163c52"))
            painter.fillRect(rect, QBrush(background))
            glow = QRadialGradient(QPointF(width * 0.55, height * 0.35), max(width, height) * 0.65)
            glow.setColorAt(0.0, QColor(40, 210, 171, 135)); glow.setColorAt(0.45, QColor(58, 151, 188, 75)); glow.setColorAt(1.0, QColor(10, 30, 54, 0))
            painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(QBrush(glow))
            painter.drawEllipse(QRectF(0, -height * 0.5, width, height * 1.45))
        elif wallpaper_id == "sunset":
            background.setColorAt(0.0, QColor("#30245e")); background.setColorAt(0.52, QColor("#d45c78")); background.setColorAt(1.0, QColor("#f2a05c"))
            painter.fillRect(rect, QBrush(background))
            painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(QColor("#ffd69a"))
            painter.drawEllipse(QRectF(width * 0.68, height * 0.12, min(width, height) * 0.18, min(width, height) * 0.18))
            painter.setBrush(QColor("#6b426d")); painter.drawPolygon(QPolygonF([QPointF(0,height*.72),QPointF(width*.25,height*.38),QPointF(width*.48,height*.75),QPointF(width*.7,height*.46),QPointF(width,height*.78),QPointF(width,height),QPointF(0,height)]))
            painter.setBrush(QColor("#352f59")); painter.drawPolygon(QPolygonF([QPointF(0,height*.86),QPointF(width*.34,height*.59),QPointF(width*.58,height*.88),QPointF(width*.82,height*.63),QPointF(width,height*.82),QPointF(width,height),QPointF(0,height)]))
        elif wallpaper_id == "mountains":
            background.setColorAt(0.0, QColor("#081526")); background.setColorAt(0.6, QColor("#293d62")); background.setColorAt(1.0, QColor("#687492"))
            painter.fillRect(rect, QBrush(background))
            painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(QColor("#e5e9ef")); painter.drawEllipse(QRectF(width*.76,height*.12,38,38))
            painter.setBrush(QColor("#334767")); painter.drawPolygon(QPolygonF([QPointF(0,height*.77),QPointF(width*.26,height*.34),QPointF(width*.48,height*.78),QPointF(width*.69,height*.43),QPointF(width,height*.8),QPointF(width,height),QPointF(0,height)]))
            painter.setBrush(QColor("#172b47")); painter.drawPolygon(QPolygonF([QPointF(0,height*.9),QPointF(width*.32,height*.57),QPointF(width*.55,height*.88),QPointF(width*.8,height*.6),QPointF(width,height*.87),QPointF(width,height),QPointF(0,height)]))
        elif wallpaper_id == "ocean":
            background.setColorAt(0.0, QColor("#092746")); background.setColorAt(0.5, QColor("#116a83")); background.setColorAt(1.0, QColor("#40b5a3"))
            painter.fillRect(rect, QBrush(background))
            painter.setPen(Qt.PenStyle.NoPen)
            for index, (color, y) in enumerate(((QColor(34,145,167,150),.59),(QColor(22,111,145,175),.72),(QColor(10,65,105,210),.84))):
                wave = QPainterPath(QPointF(0, height*y))
                wave.cubicTo(width*.22,height*(y-.12),width*.36,height*(y+.12),width*.56,height*y)
                wave.cubicTo(width*.76,height*(y-.12),width*.88,height*(y+.09),width,height*(y-.02))
                wave.lineTo(width,height); wave.lineTo(0,height); wave.closeSubpath()
                painter.setBrush(color); painter.drawPath(wave)
        else:
            painter.fillRect(rect, QColor("#10131b"))

        # Light mode brightens older dark wallpapers so the dark UI text stays readable.
        if self.light_mode:
            painter.fillRect(rect, QColor(255, 255, 255, 178))
        else:
            painter.fillRect(rect, QColor(0, 0, 0, 28))

def read_json(path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback

def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

class ProfileCropCanvas(QWidget):
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.original_pixmap = QPixmap()
        self.rotated_pixmap = QPixmap()
        self.rotation = 0
        self.zoom = 1.0
        self.offset = QPointF(0, 0)
        self._drag_pos = None
        self.setFixedSize(360, 360)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.set_image(pixmap)

    def set_image(self, pixmap):
        self.original_pixmap = pixmap
        self.rotated_pixmap = pixmap
        self.rotation = 0
        self.zoom = 1.0
        self.offset = QPointF(0, 0)
        self.update()

    def set_rotation(self, angle):
        self.rotation = angle % 360
        self.rotated_pixmap = self.original_pixmap.transformed(
            QTransform().rotate(self.rotation), Qt.TransformationMode.SmoothTransformation
        )
        self.clamp_offset()
        self.update()

    def set_zoom(self, zoom):
        self.zoom = max(1.0, float(zoom))
        self.clamp_offset()
        self.update()

    def center_image(self):
        self.offset = QPointF(0, 0)
        self.update()

    def scaled_pixmap(self, width, height):
        if self.rotated_pixmap.isNull() or width < 1 or height < 1:
            return QPixmap()
        scale = max(width / self.rotated_pixmap.width(), height / self.rotated_pixmap.height()) * self.zoom
        return self.rotated_pixmap.scaled(
            max(width, round(self.rotated_pixmap.width() * scale)),
            max(height, round(self.rotated_pixmap.height() * scale)),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def clamp_offset(self):
        scaled = self.scaled_pixmap(self.width(), self.height())
        if scaled.isNull():
            return
        max_x = max(0, (scaled.width() - self.width()) / 2)
        max_y = max(0, (scaled.height() - self.height()) / 2)
        self.offset = QPointF(
            max(-max_x, min(max_x, self.offset.x())),
            max(-max_y, min(max_y, self.offset.y())),
        )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        circle = QPainterPath()
        circle.addEllipse(QRectF(self.rect()))
        painter.setClipPath(circle)
        painter.fillRect(self.rect(), QColor("#171c27"))
        scaled = self.scaled_pixmap(self.width(), self.height())
        if not scaled.isNull():
            x = round((self.width() - scaled.width()) / 2 + self.offset.x())
            y = round((self.height() - scaled.height()) / 2 + self.offset.y())
            painter.drawPixmap(x, y, scaled)
        painter.setClipping(False)
        painter.setPen(QPen(QColor("#d6deef"), 3))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(self.rect().adjusted(2, 2, -2, -2))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            delta = event.pos() - self._drag_pos
            self.offset += QPointF(delta.x(), delta.y())
            self._drag_pos = event.pos()
            self.clamp_offset()
            self.update()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def render_avatar(self, output_size=512):
        result = QPixmap(output_size, output_size)
        result.fill(Qt.GlobalColor.transparent)
        painter = QPainter(result)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        circle = QPainterPath()
        circle.addEllipse(QRectF(0, 0, output_size, output_size))
        painter.setClipPath(circle)
        scale = max(output_size / self.rotated_pixmap.width(), output_size / self.rotated_pixmap.height()) * self.zoom
        scaled = self.rotated_pixmap.scaled(
            max(output_size, round(self.rotated_pixmap.width() * scale)),
            max(output_size, round(self.rotated_pixmap.height() * scale)),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        ratio = output_size / max(1, self.width())
        x = round((output_size - scaled.width()) / 2 + self.offset.x() * ratio)
        y = round((output_size - scaled.height()) / 2 + self.offset.y() * ratio)
        painter.drawPixmap(x, y, scaled)
        painter.end()
        return result

class PaintCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.document_size = QSize(1600, 900)
        self.layers = []
        self.active_layer_index = 0
        self.zoom = 0.62
        self.tool = "brush"
        self.color = QColor("#202634")
        self.brush_size = 8
        self.fill_shapes = False
        self._drawing = False
        self._start_point = QPointF()
        self._last_point = QPointF()
        self._current_point = QPointF()
        self.selection_shape = None
        self.selection_rect = QRectF()
        self._selection_action = None
        self._selection_start_rect = QRectF()
        self._floating_selection = None
        self.clipboard_pixmap = QPixmap()
        self.undo_stack = []
        self.redo_stack = []
        self._replace_layers_with_document(None)
        self.setMouseTracking(True)
        self.set_zoom(self.zoom)

    @property
    def image(self):
        return self.layers[self.active_layer_index]["image"]

    @image.setter
    def image(self, pixmap):
        if self.layers:
            self.layers[self.active_layer_index]["image"] = pixmap

    def _new_layer(self, name, fill_color=None):
        pixmap = QPixmap(self.document_size)
        pixmap.fill(fill_color if fill_color is not None else Qt.GlobalColor.transparent)
        return {
            "id": uuid.uuid4().hex,
            "name": name,
            "image": pixmap,
            "visible": True,
            "opacity": 100,
        }

    def _replace_layers_with_document(self, pixmap):
        background = self._new_layer("Tło", QColor("#ffffff"))
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(
                self.document_size, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            painter = QPainter(background["image"])
            painter.drawPixmap((background["image"].width() - scaled.width()) // 2,
                               (background["image"].height() - scaled.height()) // 2, scaled)
            painter.end()
            background["name"] = "Obraz"
        self.layers = [background]
        self.active_layer_index = 0
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.clear_selection()

    def layer_index(self, layer_id):
        return next((index for index, layer in enumerate(self.layers) if layer["id"] == layer_id), -1)

    def set_zoom(self, zoom):
        self.zoom = max(0.2, min(2.0, float(zoom)))
        self.setFixedSize(round(self.image.width() * self.zoom), round(self.image.height() * self.zoom))
        self.update()

    def set_tool(self, tool):
        self.tool = tool

    def set_color(self, color):
        self.color = QColor(color)
        self.update()

    def set_brush_size(self, size):
        self.brush_size = max(1, int(size))

    def set_fill_shapes(self, filled):
        self.fill_shapes = bool(filled)

    def set_document(self, pixmap):
        self._replace_layers_with_document(pixmap)
        self.set_zoom(self.zoom)

    def add_layer(self, name=None):
        name = name or f"Warstwa {len(self.layers) + 1}"
        self.layers.append(self._new_layer(name))
        self.active_layer_index = len(self.layers) - 1
        self.clear_selection()
        self.update()
        return self.active_layer_index

    def remove_active_layer(self):
        if len(self.layers) <= 1:
            return False
        removed = self.layers.pop(self.active_layer_index)
        self.undo_stack = [entry for entry in self.undo_stack if entry[0] != removed["id"]]
        self.redo_stack = [entry for entry in self.redo_stack if entry[0] != removed["id"]]
        self.active_layer_index = min(self.active_layer_index, len(self.layers) - 1)
        self.clear_selection()
        self.update()
        return True

    def set_active_layer(self, index):
        if 0 <= index < len(self.layers):
            self.active_layer_index = index
            self.clear_selection()
            self.update()

    def move_active_layer(self, direction):
        destination = self.active_layer_index + direction
        if 0 <= destination < len(self.layers):
            layer = self.layers.pop(self.active_layer_index)
            self.layers.insert(destination, layer)
            self.active_layer_index = destination
            self.clear_selection()
            self.update()
            return True
        return False

    def set_layer_visible(self, index, visible):
        if 0 <= index < len(self.layers):
            self.layers[index]["visible"] = bool(visible)
            self.update()

    def set_layer_opacity(self, index, opacity):
        if 0 <= index < len(self.layers):
            self.layers[index]["opacity"] = max(0, min(100, int(opacity)))
            self.update()

    def composite_image(self):
        result = QPixmap(self.document_size)
        result.fill(Qt.GlobalColor.transparent)
        painter = QPainter(result)
        for layer in self.layers:
            if layer["visible"]:
                painter.setOpacity(layer["opacity"] / 100.0)
                painter.drawPixmap(0, 0, layer["image"])
        painter.end()
        return result

    def remember_undo(self):
        self.undo_stack.append((self.layers[self.active_layer_index]["id"], self.image.copy()))
        if len(self.undo_stack) > 30:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self):
        while self.undo_stack:
            layer_id, snapshot = self.undo_stack.pop()
            index = self.layer_index(layer_id)
            if index >= 0:
                self.redo_stack.append((layer_id, self.layers[index]["image"].copy()))
                self.layers[index]["image"] = snapshot
                self.update()
                return

    def redo(self):
        while self.redo_stack:
            layer_id, snapshot = self.redo_stack.pop()
            index = self.layer_index(layer_id)
            if index >= 0:
                self.undo_stack.append((layer_id, self.layers[index]["image"].copy()))
                self.layers[index]["image"] = snapshot
                self.update()
                return

    def new_document(self):
        self._replace_layers_with_document(None)
        self.set_zoom(self.zoom)

    def selection_path(self, rect=None, shape=None):
        rect = (rect if rect is not None else self.selection_rect).normalized()
        shape = shape if shape is not None else self.selection_shape
        path = QPainterPath()
        if shape == "ellipse":
            path.addEllipse(rect)
        elif shape == "rectangle":
            path.addRect(rect)
        return path

    def clear_selection(self):
        self.selection_shape = None
        self.selection_rect = QRectF()
        self._selection_action = None
        self._floating_selection = None

    def extract_selection(self):
        if self.selection_shape is None:
            return QPixmap(), QRectF()
        bounds = self.selection_rect.toAlignedRect().intersected(self.image.rect())
        if bounds.isEmpty():
            return QPixmap(), QRectF()
        result = QPixmap(bounds.size())
        result.fill(Qt.GlobalColor.transparent)
        painter = QPainter(result)
        clip = self.selection_path().translated(QPointF(-bounds.x(), -bounds.y()))
        painter.setClipPath(clip)
        painter.drawPixmap(-bounds.x(), -bounds.y(), self.image)
        painter.end()
        return result, QRectF(bounds)

    def erase_selection_pixels(self, path):
        painter = QPainter(self.image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillPath(path, QColor(0, 0, 0, 0))
        painter.end()

    def copy_selection(self):
        pixmap, _bounds = self.extract_selection()
        if pixmap.isNull():
            return False
        self.clipboard_pixmap = pixmap
        return True

    def cut_selection(self):
        if not self.copy_selection():
            return False
        return self.delete_selection()

    def delete_selection(self):
        if self.selection_shape is None:
            return False
        self.remember_undo()
        self.erase_selection_pixels(self.selection_path())
        self.clear_selection()
        self.update()
        return True

    def paste_selection(self):
        if self.clipboard_pixmap.isNull():
            return False
        self.remember_undo()
        x = (self.image.width() - self.clipboard_pixmap.width()) // 2
        y = (self.image.height() - self.clipboard_pixmap.height()) // 2
        painter = QPainter(self.image)
        painter.drawPixmap(x, y, self.clipboard_pixmap)
        painter.end()
        self.selection_shape = "rectangle"
        self.selection_rect = QRectF(x, y, self.clipboard_pixmap.width(), self.clipboard_pixmap.height())
        self.update()
        return True

    def image_point(self, point):
        return QPointF(
            max(0, min(self.image.width() - 1, point.x() / self.zoom)),
            max(0, min(self.image.height() - 1, point.y() / self.zoom)),
        )

    def drawing_pen(self):
        color = QColor(self.color)
        width = self.brush_size if self.tool != "pencil" else 1
        cap = Qt.PenCapStyle.SquareCap if self.tool == "pencil" else Qt.PenCapStyle.RoundCap
        join = Qt.PenJoinStyle.MiterJoin if self.tool == "pencil" else Qt.PenJoinStyle.RoundJoin
        return QPen(color, width, Qt.PenStyle.SolidLine, cap, join)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        tile = 24
        painter.fillRect(self.rect(), QColor("#ffffff"))
        for y in range(0, self.height(), tile):
            for x in range(0, self.width(), tile):
                if ((x // tile) + (y // tile)) % 2:
                    painter.fillRect(x, y, tile, tile, QColor("#e9edf3"))
        for layer in self.layers:
            if layer["visible"]:
                painter.setOpacity(layer["opacity"] / 100.0)
                painter.drawPixmap(self.rect(), layer["image"])
        painter.setOpacity(1.0)

        if self._floating_selection is not None and not self._floating_selection.isNull():
            painter.save()
            painter.scale(self.zoom, self.zoom)
            painter.drawPixmap(round(self.selection_rect.x()), round(self.selection_rect.y()), self._floating_selection)
            painter.restore()

        if self._drawing and self.tool in {"line", "rectangle", "ellipse"}:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            pen = QPen(self.color, max(1, round(self.brush_size * self.zoom)),
                       Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(QBrush(self.color) if self.fill_shapes and self.tool != "line" else Qt.BrushStyle.NoBrush)
            start = QPointF(self._start_point.x() * self.zoom, self._start_point.y() * self.zoom)
            end = QPointF(self._current_point.x() * self.zoom, self._current_point.y() * self.zoom)
            if self.tool == "line":
                painter.drawLine(start, end)
            else:
                rect = QRectF(start, end).normalized()
                painter.drawRect(rect) if self.tool == "rectangle" else painter.drawEllipse(rect)

        if self.selection_shape is not None:
            painter.save()
            painter.scale(self.zoom, self.zoom)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor("#ffffff"), 3 / self.zoom, Qt.PenStyle.DashLine))
            painter.drawPath(self.selection_path())
            painter.setPen(QPen(QColor("#111827"), 1 / self.zoom, Qt.PenStyle.DashLine))
            painter.drawPath(self.selection_path())
            painter.restore()

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        point = self.image_point(QPointF(event.pos().x(), event.pos().y()))
        self._drawing = True
        self._start_point = point
        self._last_point = point
        self._current_point = point
        if self.tool in {"select_rectangle", "select_ellipse"}:
            if self.selection_shape and self.selection_path().contains(point):
                self.remember_undo()
                source_path = self.selection_path()
                self._floating_selection, bounds = self.extract_selection()
                if self._floating_selection.isNull():
                    self._drawing = False
                    self._floating_selection = None
                    return
                self.selection_rect = bounds
                self._selection_start_rect = QRectF(bounds)
                self.erase_selection_pixels(source_path)
                self._selection_action = "move"
            else:
                self.selection_shape = "ellipse" if self.tool == "select_ellipse" else "rectangle"
                self.selection_rect = QRectF(point, point)
                self._selection_action = "create"
            self.update()
            return
        if self.tool in {"brush", "pencil", "eraser"}:
            self.remember_undo()
            painter = QPainter(self.image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, self.tool != "pencil")
            if self.tool == "eraser":
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.setPen(self.drawing_pen())
            painter.drawPoint(point)
            painter.end()
        self.update()

    def mouseMoveEvent(self, event):
        if not self._drawing:
            return
        point = self.image_point(QPointF(event.pos().x(), event.pos().y()))
        self._current_point = point
        if self._selection_action == "create":
            self.selection_rect = QRectF(self._start_point, point).normalized()
            self.update()
            return
        if self._selection_action == "move":
            delta = point - self._start_point
            moved = self._selection_start_rect.translated(delta)
            max_x = max(0, self.image.width() - moved.width())
            max_y = max(0, self.image.height() - moved.height())
            self.selection_rect = QRectF(
                max(0, min(max_x, moved.x())),
                max(0, min(max_y, moved.y())),
                moved.width(), moved.height(),
            )
            self.update()
            return
        if self.tool in {"brush", "pencil", "eraser"}:
            painter = QPainter(self.image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, self.tool != "pencil")
            if self.tool == "eraser":
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.setPen(self.drawing_pen())
            painter.drawLine(self._last_point, point)
            painter.end()
            self._last_point = point
        self.update()

    def mouseReleaseEvent(self, event):
        if not self._drawing:
            return
        self._current_point = self.image_point(QPointF(event.pos().x(), event.pos().y()))
        if self._selection_action == "create":
            self.selection_rect = QRectF(self._start_point, self._current_point).normalized()
            if self.selection_rect.width() < 1 or self.selection_rect.height() < 1:
                self.clear_selection()
        elif self._selection_action == "move" and self._floating_selection is not None:
            delta = self._current_point - self._start_point
            moved = self._selection_start_rect.translated(delta)
            max_x = max(0, self.image.width() - moved.width())
            max_y = max(0, self.image.height() - moved.height())
            self.selection_rect = QRectF(
                max(0, min(max_x, moved.x())),
                max(0, min(max_y, moved.y())),
                moved.width(), moved.height(),
            )
            painter = QPainter(self.image)
            painter.drawPixmap(round(self.selection_rect.x()), round(self.selection_rect.y()), self._floating_selection)
            painter.end()
            self._floating_selection = None
        self._selection_action = None
        if self.tool in {"select_rectangle", "select_ellipse"}:
            self._drawing = False
            self.update()
            return
        if self.tool in {"line", "rectangle", "ellipse"}:
            self.remember_undo()
            painter = QPainter(self.image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(self.color, self.brush_size, Qt.PenStyle.SolidLine,
                                Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            painter.setBrush(QBrush(self.color) if self.fill_shapes and self.tool != "line" else Qt.BrushStyle.NoBrush)
            rect = QRectF(self._start_point, self._current_point).normalized()
            if self.tool == "line":
                painter.drawLine(self._start_point, self._current_point)
            elif self.tool == "rectangle":
                painter.drawRect(rect)
            else:
                painter.drawEllipse(rect)
            painter.end()
        self._drawing = False
        self.update()

class MiniOS(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("mini-os")
        self.setMinimumSize(850, 620)
        legacy_settings = read_json(SETTINGS_FILE, DEFAULT_SETTINGS.copy())
        legacy_settings = {**DEFAULT_SETTINGS, **legacy_settings}
        self.settings = legacy_settings.copy()
        legacy_user = read_json(USER_FILE, {"username": "Użytkownik", "password": ""})
        stored_profiles = read_json(PROFILES_FILE, {})
        profile_rows = stored_profiles.get("profiles", []) if isinstance(stored_profiles, dict) else []
        valid_profile_rows = [row for row in profile_rows if isinstance(row, dict)] if isinstance(profile_rows, list) else []
        migrate_legacy_profile_data = not any(row.get("storage_version") == 1 for row in valid_profile_rows)
        self.profiles = []
        used_ids = set()
        for row in valid_profile_rows:
            profile_id = str(row.get("id") or uuid.uuid4().hex)
            while profile_id in used_ids:
                profile_id = uuid.uuid4().hex
            used_ids.add(profile_id)
            self.profiles.append({
                "id": profile_id,
                "username": str(row.get("username") or "Użytkownik").strip() or "Użytkownik",
                "password": str(row.get("password") or ""),
                "mark": str(row.get("mark") or "◉").strip() or "◉",
                "avatar": str(row.get("avatar") or ""),
                "settings": row.get("settings") if isinstance(row.get("settings"), dict) else None,
                "storage_version": int(row.get("storage_version") or 0),
            })
        if not self.profiles:
            self.profiles = [{
                "id": uuid.uuid4().hex,
                "username": str(legacy_user.get("username") or "Użytkownik").strip() or "Użytkownik",
                "password": str(legacy_user.get("password") or ""),
                "mark": str(legacy_user.get("mark") or "◉").strip() or "◉",
                "avatar": str(legacy_user.get("avatar") or ""),
                "settings": None,
                "storage_version": 0,
            }]
        saved_profile_id = stored_profiles.get("last_profile_id") if isinstance(stored_profiles, dict) else None
        if not any(profile["id"] == saved_profile_id for profile in self.profiles):
            saved_profile_id = self.profiles[0]["id"]
        self.active_profile_id = saved_profile_id
        self.user = self.profile_by_id(self.active_profile_id).copy()
        for profile in self.profiles:
            if not isinstance(profile.get("settings"), dict):
                profile["settings"] = (
                    legacy_settings.copy() if profile["id"] == self.active_profile_id
                    else DEFAULT_SETTINGS.copy()
                )
            else:
                profile["settings"] = {**DEFAULT_SETTINGS, **profile["settings"]}
            profile["storage_version"] = 1
            ensure_profile_user_directories(profile["id"])

        global PHOTOS, PROFILE_WALLPAPERS_DIR
        active_storage = profile_storage_dir(self.active_profile_id)
        active_user_directories = ensure_profile_user_directories(self.active_profile_id)
        PHOTOS = active_user_directories["pictures"]
        PROFILE_WALLPAPERS_DIR = active_storage / "wallpapers"
        PHOTOS.mkdir(parents=True, exist_ok=True)
        PROFILE_WALLPAPERS_DIR.mkdir(parents=True, exist_ok=True)
        if migrate_legacy_profile_data:
            for legacy_folder, destination in (
                (LEGACY_PHOTOS_DIR, PHOTOS),
                (LEGACY_WALLPAPERS_DIR, PROFILE_WALLPAPERS_DIR),
            ):
                if legacy_folder.is_dir():
                    for source in legacy_folder.iterdir():
                        if (source.is_file()
                                and source.suffix.lower() in WALLPAPER_EXTENSIONS
                                and (legacy_folder != LEGACY_WALLPAPERS_DIR
                                     or source.name not in builtin_wallpaper_filenames())):
                            target = destination / source.name
                            if not target.exists():
                                shutil.copy2(source, target)
        self.user = self.profile_by_id(self.active_profile_id).copy()
        self.settings = self.user["settings"].copy()
        self.username = self.user["username"]
        self.profile_mark = self.user["mark"]
        self.persist_profiles()
        self.session = read_json(SESSION_FILE, {})
        self.wallpaper_repair_needed = wallpapers_need_repair()
        self.camera = None
        self.camera_timer = None
        self.auto_theme_timer = QTimer(self)
        self.auto_theme_timer.setInterval(180000)
        self.auto_theme_timer.timeout.connect(self.sample_auto_theme_camera)
        self._auto_theme_light = False
        self._auto_theme_candidate = None
        self._auto_theme_candidate_count = 0
        self._camera_preview_active = False
        self.browser = None
        self.store_icon_manager = QNetworkAccessManager(self)
        self.store_icon_cache = OrderedDict()
        self.store_icon_pending = {}
        self.store_icon_widgets = {}
        self.app_browser = None
        self.web_profile = None
        self.browser_page = None
        self.browser_layout = None
        self.current_app = "home"
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.pages = {}
        self.make_boot_page()
        self.make_login()
        self.make_home()
        self.make_start_menu()
        self.make_browser()
        self.make_installed_app_view()
        self.make_store()
        self.make_games()
        self.make_camera()
        self.make_settings()
        self.make_files()
        self.make_notepad()
        self.make_session()
        self.make_gallery()
        self.make_photo_viewer()
        self.make_wallpaper_picker()
        self.make_profile_picker()
        self.make_profile_crop_page()
        self.make_calculator()
        self.make_paint()
        self.make_paint_gallery()
        self._start_return_page = "home"
        self.apply_wallpapers()
        self.apply_language()
        self.show_page("boot")
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
        self.apply_theme()
        QTimer.singleShot(100, self.begin_startup)

    def page(self, name):
        w = MiniOSPage(name)
        w.setObjectName(name)
        layout = QVBoxLayout(w)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)
        self.pages[name] = w
        self.stack.addWidget(w)
        return w, layout

    def profile_by_id(self, profile_id):
        return next((profile for profile in self.profiles if profile["id"] == profile_id), None)

    def profile_icon(self, profile, size=48):
        pixmap = QPixmap()
        avatar_name = Path(profile.get("avatar", "")).name
        if avatar_name:
            pixmap = QPixmap(str(PROFILE_AVATARS_DIR / avatar_name))
        if not pixmap.isNull():
            target = QSize(size, size)
            scaled = pixmap.scaled(target, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                   Qt.TransformationMode.SmoothTransformation)
            x = max(0, (scaled.width() - size) // 2)
            y = max(0, (scaled.height() - size) // 2)
            pixmap = scaled.copy(x, y, size, size)
        else:
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#30394d"))
            painter.drawEllipse(1, 1, size - 2, size - 2)
            painter.setPen(QColor("#f4f6fb"))
            painter.setFont(QFont("Arial", max(12, size // 2), QFont.Weight.Bold))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, profile.get("mark", "◉"))
            painter.end()
        return QIcon(pixmap)

    def profile_avatar_pixmap(self, profile, size=64):
        icon = self.profile_icon(profile, size)
        return icon.pixmap(size, size)

    def update_profile_identity_widgets(self):
        if hasattr(self, "home_user_label"):
            self.home_user_label.setText(self.username)
            self.home_avatar_label.setPixmap(self.profile_avatar_pixmap(self.user, 44))
        if hasattr(self, "start_menu_subtitle"):
            self.start_menu_subtitle.setText("mini-os  ·  " + self.username)
            self.start_menu_avatar_label.setPixmap(self.profile_avatar_pixmap(self.user, 64))

    def persist_profiles(self):
        write_json(PROFILES_FILE, {
            "profiles": self.profiles,
            "last_profile_id": self.active_profile_id,
        })

    def activate_profile(self, profile_id):
        global PHOTOS, PROFILE_WALLPAPERS_DIR
        profile = self.profile_by_id(profile_id)
        if not profile:
            return False
        self.active_profile_id = profile_id
        self.user = profile.copy()
        self.username = profile["username"]
        self.profile_mark = profile.get("mark", "◉")
        self.settings = {**DEFAULT_SETTINGS, **profile.get("settings", {})}
        if self.settings.get("theme") == "auto":
            self._auto_theme_light = False
        self.configure_app_color_scheme()
        if getattr(self, "browser", None) is not None:
            self.set_browser_profile(profile_id)
        storage = profile_storage_dir(profile_id)
        user_directories = ensure_profile_user_directories(profile_id)
        PHOTOS = user_directories["pictures"]
        PROFILE_WALLPAPERS_DIR = storage / "wallpapers"
        PHOTOS.mkdir(parents=True, exist_ok=True)
        PROFILE_WALLPAPERS_DIR.mkdir(parents=True, exist_ok=True)
        self.persist_profiles()
        if hasattr(self, "lock_wallpaper_combo"):
            self.refresh_wallpaper_controls()
            self.anim_check.setChecked(self.settings.get("animations", True))
            self.clock_check.setChecked(self.settings.get("clock_24h", True))
            self.start_url_input.setText(self.settings.get("start_url", "https://www.google.com"))
            self.apply_wallpapers()
            if hasattr(self, "theme_combo"):
                self.theme_combo.blockSignals(True)
                theme_index = self.theme_combo.findData(self.settings.get("theme", "dark"))
                self.theme_combo.setCurrentIndex(theme_index if theme_index >= 0 else 0)
                self.theme_combo.blockSignals(False)
            self.apply_theme()
            if self.settings.get("theme") == "auto":
                QTimer.singleShot(500, self.start_auto_theme_detection)
            else:
                self.stop_auto_theme_detection()
        if hasattr(self, "camera_hint"):
            self.camera_hint.setText(f"Zdjęcia będą zapisywane w Galerii profilu „{self.username}”.")
        if hasattr(self, "files_current_directory"):
            self.files_current_directory = user_directories["root"]
            self.refresh_files()
        if hasattr(self, "installed_apps_pages"):
            self.refresh_installed_apps()
        if hasattr(self, "home_clock"):
            self.update_clock()
        return True

    def refresh_wallpaper_controls(self):
        for setting_key, combo in (
            ("lock_wallpaper", self.lock_wallpaper_combo),
            ("home_wallpaper", self.home_wallpaper_combo),
        ):
            self.populate_wallpaper_options(combo)
            combo.blockSignals(True)
            selected = self.settings.get(setting_key, "default")
            index = combo.findData(selected)
            if index < 0:
                selected = "default"
                self.settings[setting_key] = selected
                index = combo.findData(selected)
            combo.setCurrentIndex(max(0, index))
            combo.blockSignals(False)
        active_profile = self.profile_by_id(self.active_profile_id)
        active_profile["settings"] = self.settings.copy()
        self.user = active_profile.copy()
        self.persist_profiles()

    def refresh_profile_lists(self, settings_profile_id=None, login_profile_id=None):
        if settings_profile_id is None:
            settings_profile_id = self.active_profile_id
        if login_profile_id is None:
            login_profile_id = self.active_profile_id
        if hasattr(self, "settings_profile_combo"):
            combo = self.settings_profile_combo
            combo.setIconSize(QSize(42, 42))
            combo.blockSignals(True)
            combo.clear()
            for profile in self.profiles:
                combo.addItem(self.profile_icon(profile), profile["username"], profile["id"])
            index = combo.findData(settings_profile_id)
            combo.setCurrentIndex(index if index >= 0 else 0)
            combo.blockSignals(False)
        if hasattr(self, "login_profile_combo"):
            combo = self.login_profile_combo
            combo.setIconSize(QSize(42, 42))
            combo.blockSignals(True)
            combo.clear()
            for profile in self.profiles:
                combo.addItem(self.profile_icon(profile), profile["username"], profile["id"])
            index = combo.findData(login_profile_id)
            combo.setCurrentIndex(index if index >= 0 else 0)
            combo.blockSignals(False)

    def load_profile_editor(self, _index=None):
        profile = self.profile_by_id(self.settings_profile_combo.currentData())
        if profile:
            self.user_input.setText(profile["username"])
            self.profile_avatar_preview.setPixmap(self.profile_avatar_pixmap(profile, 72))
            self.pass_input.clear()

    def add_profile(self):
        name, accepted = QInputDialog.getText(self, "Dodaj profil", "Nazwa nowego profilu:")
        if not accepted:
            return
        name = name.strip()
        if not name:
            QMessageBox.information(self, "Dodaj profil", "Podaj nazwę profilu.")
            return
        if any(profile["username"].casefold() == name.casefold() for profile in self.profiles):
            QMessageBox.information(self, "Dodaj profil", "Profil o takiej nazwie już istnieje.")
            return
        profile = {
            "id": uuid.uuid4().hex,
            "username": name,
            "password": "",
            "mark": "◉",
            "avatar": "",
            "settings": DEFAULT_SETTINGS.copy(),
            "storage_version": 1,
        }
        self.profiles.append(profile)
        ensure_profile_user_directories(profile["id"])
        self.persist_profiles()
        self.refresh_profile_lists(settings_profile_id=profile["id"], login_profile_id=self.active_profile_id)
        self.load_profile_editor()
        QMessageBox.information(self, "Dodaj profil", "Profil został dodany. Hasło możesz ustawić poniżej.")

    def delete_profile(self):
        profile_id = self.settings_profile_combo.currentData()
        profile = self.profile_by_id(profile_id)
        if not profile:
            return
        if profile_id == self.active_profile_id:
            QMessageBox.information(self, "Usuń profil", "Nie można usunąć profilu, na którym jesteś teraz zalogowany.")
            return
        answer = QMessageBox.question(
            self, "Usuń profil", f"Czy usunąć profil „{profile['username']}”?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.profiles = [row for row in self.profiles if row["id"] != profile_id]
        self.persist_profiles()
        self.refresh_profile_lists(settings_profile_id=self.active_profile_id, login_profile_id=self.active_profile_id)
        self.load_profile_editor()

    def make_boot_page(self):
        w, root = self.page("boot")
        w.setStyleSheet("background:#000000;")
        root.setContentsMargins(24, 28, 24, 28)
        root.setSpacing(18)
        root.addStretch(1)

        class GradientWordmark(QWidget):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setMinimumHeight(86)
                self.setMaximumHeight(100)

            def paintEvent(self, event):
                painter = QPainter(self)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
                font = QFont("Arial", 58, QFont.Weight.Black)
                font.setBold(True)
                font.setItalic(True)
                path = QPainterPath()
                path.addText(QPointF(0, 0), font, "MINI_OS")
                bounds = path.boundingRect()
                path.translate(
                    (self.width() - bounds.width()) / 2 - bounds.x(),
                    (self.height() - bounds.height()) / 2 - bounds.y()
                )
                bounds = path.boundingRect()
                gradient = QLinearGradient(bounds.left(), bounds.top(), bounds.left(), bounds.bottom())
                gradient.setColorAt(0.0, Qt.GlobalColor.white)
                gradient.setColorAt(0.42, Qt.GlobalColor.white)
                gradient.setColorAt(0.76, Qt.GlobalColor.lightGray)
                gradient.setColorAt(1.0, Qt.GlobalColor.darkGray)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(gradient))
                painter.drawPath(path)
                painter.end()

        self.boot_logo = GradientWordmark()
        opacity = QGraphicsOpacityEffect(self.boot_logo)
        self.boot_logo.setGraphicsEffect(opacity)
        self.boot_pulse = QPropertyAnimation(opacity, b"opacity", self)
        self.boot_pulse.setDuration(1500)
        self.boot_pulse.setStartValue(0.72)
        self.boot_pulse.setEndValue(1.0)
        self.boot_pulse.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.boot_pulse.setLoopCount(-1)
        root.addWidget(self.boot_logo)

        class LoadingImageMark(QWidget):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setFixedSize(245, 245)

            def paintEvent(self, event):
                painter = QPainter(self)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                gradient = QLinearGradient(0, 8, 0, 235)
                gradient.setColorAt(0.0, Qt.GlobalColor.white)
                gradient.setColorAt(0.58, Qt.GlobalColor.lightGray)
                gradient.setColorAt(1.0, Qt.GlobalColor.darkGray)
                pen = QPen(QBrush(gradient), 5)
                pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(12, 10, 220, 220)
                painter.drawPolyline(QPolygonF([
                    QPointF(24, 218), QPointF(82, 76),
                    QPointF(151, 218), QPointF(188, 163),
                    QPointF(211, 218), QPointF(226, 195)
                ]))
                painter.end()

        self.boot_image_mark = LoadingImageMark()
        mark_opacity = QGraphicsOpacityEffect(self.boot_image_mark)
        self.boot_image_mark.setGraphicsEffect(mark_opacity)
        self.boot_mark_pulse = QPropertyAnimation(mark_opacity, b"opacity", self)
        self.boot_mark_pulse.setDuration(1900)
        self.boot_mark_pulse.setStartValue(0.58)
        self.boot_mark_pulse.setEndValue(1.0)
        self.boot_mark_pulse.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.boot_mark_pulse.setLoopCount(-1)
        root.addWidget(self.boot_image_mark, 0, Qt.AlignmentFlag.AlignHCenter)

        self.boot_loading_label = QLabel("AUTONAPRAWA" if self.wallpaper_repair_needed else "LOADING")
        self.boot_loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.boot_loading_label.setStyleSheet("color:#ffffff; font-size:34px; font-weight:400; letter-spacing:1px;")
        root.addWidget(self.boot_loading_label)
        self.boot_repair_note = QLabel("Proszę czekać — przygotowuję tapety…" if self.wallpaper_repair_needed else "")
        self.boot_repair_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.boot_repair_note.setStyleSheet("color:#b8b8b8; font-size:18px;")
        root.addWidget(self.boot_repair_note)
        root.addSpacing(8)
        self.boot_progress = QProgressBar()
        self.boot_progress.setRange(0, 100)
        self.boot_progress.setValue(0)
        self.boot_progress.setTextVisible(False)
        self.boot_progress.setFixedHeight(20)
        self.boot_progress.setMaximumWidth(520)
        self.boot_progress.setStyleSheet("QProgressBar { background:#242424; border:0; border-radius:10px; } QProgressBar::chunk { background:qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #ffffff, stop:1 #777777); border-radius:10px; }")
        root.addWidget(self.boot_progress, 0, Qt.AlignmentFlag.AlignHCenter)
        self.boot_percent = QLabel("0%")
        self.boot_percent.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.boot_percent.setStyleSheet("color:#ffffff; font-size:54px; font-weight:300;")
        root.addWidget(self.boot_percent)
        self.boot_progress_animation = QPropertyAnimation(self.boot_progress, b"value", self)
        self.boot_progress_animation.setDuration(2600)
        self.boot_progress_animation.setStartValue(0)
        self.boot_progress_animation.setEndValue(100)
        self.boot_progress_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.boot_progress_animation.valueChanged.connect(
            lambda value: self.boot_percent.setText(f"{value}%")
        )
        self.boot_progress_animation.finished.connect(self.finish_boot_animation)
        root.addStretch(1)

    def title_row(self, title):
        row = QHBoxLayout()
        back = QPushButton("←  Pulpit")
        back.clicked.connect(lambda: self.show_page("home"))
        back.setMaximumWidth(170)
        start = QPushButton("☰  Start")
        start.clicked.connect(self.open_start_menu)
        label = QLabel(title)
        label.setFont(QFont("Arial", 25, QFont.Weight.Bold))
        row.addWidget(back)
        row.addWidget(start)
        row.addWidget(label, 1)
        return row

    def make_login(self):
        w, root = self.page("login")
        root.addStretch(1)
        card = QFrame(); card.setObjectName("panel"); card.setMaximumWidth(520)
        cl = QVBoxLayout(card); cl.setContentsMargins(38, 34, 38, 34); cl.setSpacing(18)
        logo = QLabel("◈"); logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("font-size: 58px; color: #5b8cff;")
        name = QLabel("mini-os"); name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setFont(QFont("Arial", 34, QFont.Weight.Bold))
        sub = QLabel("Mały system. Wielkie możliwości."); sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.login_profile_combo = QComboBox()
        self.login_profile_combo.setIconSize(QSize(42, 42))
        for profile in self.profiles:
            self.login_profile_combo.addItem(self.profile_icon(profile), profile["username"], profile["id"])
        self.login_profile_combo.setCurrentIndex(max(0, self.login_profile_combo.findData(self.active_profile_id)))
        self.login_pass = QLineEdit(); self.login_pass.setPlaceholderText("Hasło"); self.login_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_pass.returnPressed.connect(self.login)
        self.login_profile_combo.currentIndexChanged.connect(lambda _index: self.login_pass.clear())
        go = QPushButton("Zaloguj się"); go.setObjectName("accent"); go.clicked.connect(self.login)
        power_actions = QHBoxLayout()
        restart = QPushButton("Uruchom ponownie")
        restart.clicked.connect(self.restart_mini_os)
        shutdown = QPushButton("Wyłącz mini-OS")
        shutdown.setStyleSheet("QPushButton { background:#8f3038; }")
        shutdown.clicked.connect(self.close)
        power_actions.addWidget(restart)
        power_actions.addWidget(shutdown)
        hint = QLabel("Hasła profili można ustawić w Ustawieniach. Profil bez hasła nie wymaga wpisywania hasła.")
        hint.setWordWrap(True); hint.setStyleSheet("color:#a9b3c8; font-size:13px;")
        cl.addWidget(logo); cl.addWidget(name); cl.addWidget(sub)
        cl.addWidget(QLabel("Wybierz profil")); cl.addWidget(self.login_profile_combo)
        cl.addWidget(self.login_pass); cl.addWidget(go)
        cl.addLayout(power_actions)
        cl.addWidget(hint)
        outer = QHBoxLayout(); outer.addStretch(1); outer.addWidget(card); outer.addStretch(1)
        root.addLayout(outer); root.addStretch(1)

    def make_home(self):
        w, root = self.page("home")
        top = QHBoxLayout()
        self.home_clock = QLabel("--:--")
        self.home_clock.setFont(QFont("Arial", 40, QFont.Weight.Light))
        self.home_date = QLabel("")
        self.home_date.setStyleSheet("color:#aab4ca; font-size:16px;")
        clock_col = QVBoxLayout(); clock_col.addWidget(self.home_clock); clock_col.addWidget(self.home_date)
        top.addLayout(clock_col); top.addStretch(1)
        self.home_avatar_label = QLabel()
        self.home_avatar_label.setFixedSize(44, 44)
        self.home_avatar_label.setScaledContents(True)
        self.home_user_label = QLabel(self.username); self.home_user_label.setStyleSheet("font-size:17px; color:#cbd4e8;")
        top.addWidget(self.home_avatar_label)
        top.addWidget(self.home_user_label)
        root.addLayout(top)
        welcome = QLabel("Witaj w mini-os")
        welcome.setFont(QFont("Arial", 22, QFont.Weight.DemiBold))
        root.addWidget(welcome)
        self.home_app_pages = QStackedWidget()
        self.installed_apps_pages = []
        self.installed_apps_per_page = 8
        self.home_app_pages.currentChanged.connect(self.update_home_page_controls)
        root.addWidget(self.home_app_pages, 1)
        bottom = QHBoxLayout()
        self.home_status = QLabel("Sesja zapisywana automatycznie")
        self.home_status.setStyleSheet("color:#8e9ab2;")
        bottom.addWidget(self.home_status); bottom.addStretch(1)
        previous_apps = QPushButton("←")
        previous_apps.setToolTip("Poprzednia strona aplikacji")
        previous_apps.clicked.connect(lambda: self.change_home_apps_page(-1))
        self.home_prev_apps_button = previous_apps
        self.home_page_label = QLabel("1 / 2")
        next_apps = QPushButton("→")
        next_apps.setToolTip("Następna strona aplikacji")
        next_apps.clicked.connect(lambda: self.change_home_apps_page(1))
        self.home_next_apps_button = next_apps
        bottom.addWidget(previous_apps)
        bottom.addWidget(self.home_page_label)
        bottom.addWidget(next_apps)
        start_btn = QPushButton("☰  Menu Start")
        start_btn.setObjectName("accent")
        start_btn.clicked.connect(self.open_start_menu)
        bottom.addWidget(start_btn)
        root.addLayout(bottom)
        self.refresh_installed_apps()

    def make_start_menu(self):
        w, root = self.page("start_menu")
        root.addStretch(1)
        heading = QLabel("Menu Start")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading.setFont(QFont("Arial", 38, QFont.Weight.Bold))
        self.start_menu_avatar_label = QLabel()
        self.start_menu_avatar_label.setFixedSize(64, 64)
        self.start_menu_avatar_label.setScaledContents(True)
        self.start_menu_subtitle = QLabel("mini-os  ·  " + self.username)
        self.start_menu_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.start_menu_subtitle.setStyleSheet("color:#aab4ca; font-size:18px;")
        root.addWidget(heading)
        root.addWidget(self.start_menu_avatar_label, 0, Qt.AlignmentFlag.AlignHCenter)
        root.addWidget(self.start_menu_subtitle)

        actions = QGridLayout()
        actions.setSpacing(16)
        resume = QPushButton("Wróć do mini-OS")
        resume.setObjectName("accent")
        resume.clicked.connect(self.close_start_menu)
        logout = QPushButton("Wyloguj z profilu")
        logout.clicked.connect(self.logout)
        session = QPushButton("Sesja i zapis")
        session.clicked.connect(lambda: self.show_page("session"))
        restart = QPushButton("Uruchom ponownie")
        restart.clicked.connect(self.restart_mini_os)
        shutdown = QPushButton("Wyłącz mini-OS")
        shutdown.setStyleSheet("QPushButton { background:#8f3038; }")
        shutdown.clicked.connect(self.close)
        store = QPushButton("🛍  mini_store")
        store.clicked.connect(lambda: self.show_page("mini_store"))
        for button in (resume, store, session, logout, restart, shutdown):
            button.setMinimumSize(260, 90)
        actions.addWidget(resume, 0, 0)
        actions.addWidget(store, 0, 1)
        actions.addWidget(session, 1, 0)
        actions.addWidget(logout, 1, 1)
        actions.addWidget(restart, 2, 0)
        actions.addWidget(shutdown, 2, 1)
        root.addLayout(actions, 0)
        root.addStretch(2)

    def open_start_menu(self):
        if self.current_app != "start_menu":
            self._start_return_page = self.current_app
            self.save_session()
        self.update_profile_identity_widgets()
        self.show_page("start_menu")

    def close_start_menu(self):
        destination = self._start_return_page if self._start_return_page in self.pages else "home"
        self.show_page(destination)

    def make_browser(self):
        w, root = self.page("browser"); root.addLayout(self.title_row("Przeglądarka internetowa"))
        bar = QHBoxLayout()
        self.url = QLineEdit(self.settings.get("start_url", "https://www.google.com"))
        self.url.setPlaceholderText("Wpisz adres strony lub wyszukiwane hasło")
        self.url.returnPressed.connect(self.navigate)
        back = QPushButton("←"); back.clicked.connect(lambda: self.browser.back() if self.browser else None)
        forward = QPushButton("→"); forward.clicked.connect(lambda: self.browser.forward() if self.browser else None)
        reload_btn = QPushButton("↻"); reload_btn.clicked.connect(lambda: self.browser.reload() if self.browser else None)
        go = QPushButton("Otwórz"); go.setObjectName("accent"); go.clicked.connect(self.navigate)
        for x in (back, forward, reload_btn): x.setMaximumWidth(64); bar.addWidget(x)
        bar.addWidget(self.url, 1); bar.addWidget(go); root.addLayout(bar)
        self.browser_layout = root
        if WEBENGINE_AVAILABLE:
            self.browser = QWebEngineView()
            root.addWidget(self.browser, 1)
            self.set_browser_profile(self.active_profile_id)
        else:
            note = QLabel("Do działania przeglądarki zainstaluj PySide6-WebEngine:\npython3 -m pip install PySide6-WebEngine\n\nNastępnie uruchom ponownie mini-os.")
            note.setAlignment(Qt.AlignmentFlag.AlignCenter); note.setWordWrap(True); root.addWidget(note, 1)

    def make_installed_app_view(self):
        _page, root = self.page("installed_app_view")
        root.setContentsMargins(7, 5, 7, 5)
        root.setSpacing(4)
        app_bar = QHBoxLayout()
        app_bar.setContentsMargins(5, 0, 5, 0)
        self.app_bar_label = QLabel("Aplikacja")
        self.app_bar_label.setStyleSheet("font-size:12px; color:#9ba8bd;")
        exit_app = QPushButton("×  Wyjdź")
        exit_app.setFixedHeight(28)
        exit_app.setStyleSheet("QPushButton { padding:2px 10px; min-height:0; font-size:12px; border-radius:8px; }")
        exit_app.clicked.connect(self.confirm_exit_installed_app)
        app_bar.addWidget(self.app_bar_label, 1)
        app_bar.addWidget(exit_app)
        root.addLayout(app_bar)
        if WEBENGINE_AVAILABLE:
            self.app_browser = QWebEngineView()
            root.addWidget(self.app_browser, 1)
            if self.web_profile:
                self._attach_app_page()

    def confirm_exit_installed_app(self):
        answer = QMessageBox.question(
            self, "Wyjść z aplikacji?", "Czy chcesz zamknąć tę aplikację?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.show_page("home")

    def open_browser(self):
        if self.browser:
            last_url = self.settings.get("browser_last_url") or self.settings.get("start_url", "https://www.google.com")
            # Older versions stored an installed app's URL as the browser's last page.
            last_app_id = self.settings.get("browser_last_app")
            last_app = next((app for app in APP_STORE if app["id"] == last_app_id), None)
            if last_app and (last_app.get("url") == last_url or last_url.endswith("/MINECRAFT.html")):
                last_url = self.settings.get("start_url", "https://www.google.com")
                self.settings["browser_last_url"] = last_url
                profile = self.profile_by_id(self.active_profile_id)
                if profile:
                    profile.setdefault("settings", {})["browser_last_url"] = last_url
                    self.persist_profiles()
            self.browser.setUrl(QUrl(last_url))
        self.show_page("browser")

    def _attach_app_page(self):
        self.app_page = QWebEnginePage(self.web_profile, self.app_browser)
        self.app_browser.setPage(self.app_page)
        self.app_page.settings().setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        set_webview_theme(self.app_page, self.is_light_theme())
        self.app_page.featurePermissionRequested.connect(self.allow_app_feature)
        self.app_page.fullScreenRequested.connect(lambda request: request.accept())

    def make_store(self):
        _page, root = self.page("mini_store")
        bar = QHBoxLayout()
        back = QPushButton("←  Menu Start")
        back.clicked.connect(lambda: self.show_page("start_menu"))
        title = QLabel("mini_store")
        title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        bar.addWidget(back)
        bar.addWidget(title, 1)
        root.addLayout(bar)
        intro = QLabel("Wybierz aplikację, aby dodać ją na drugą stronę pulpitu.")
        intro.setStyleSheet("color:#aab4ca;")
        root.addWidget(intro)
        filters = QHBoxLayout()
        self.store_search = QLineEdit()
        self.store_search.setPlaceholderText("Szukaj aplikacji lub strony…")
        self.store_page = 0
        self.store_page_size = 48
        self.store_search.textChanged.connect(self.reset_store_page)
        self.store_category_combo = QComboBox()
        self.store_category_combo.addItem("Wszystkie kategorie", "")
        for category in sorted({app.get("category", "Aplikacje") for app in APP_STORE}):
            self.store_category_combo.addItem(category, category)
        self.store_category_combo.currentIndexChanged.connect(self.reset_store_page)
        filters.addWidget(self.store_search, 1)
        filters.addWidget(self.store_category_combo)
        root.addLayout(filters)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.store_grid = QGridLayout(content)
        self.store_grid.setSpacing(14)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)
        store_navigation = QHBoxLayout()
        self.store_previous_button = QPushButton("← Poprzednia")
        self.store_previous_button.clicked.connect(lambda: self.change_store_page(-1))
        self.store_page_label = QLabel("1 / 1")
        self.store_page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.store_next_button = QPushButton("Następna →")
        self.store_next_button.clicked.connect(lambda: self.change_store_page(1))
        store_navigation.addStretch(1)
        store_navigation.addWidget(self.store_previous_button)
        store_navigation.addWidget(self.store_page_label)
        store_navigation.addWidget(self.store_next_button)
        store_navigation.addStretch(1)
        root.addLayout(store_navigation)
        self.refresh_store_cards()

    def reset_store_page(self, *_args):
        self.store_page = 0
        self.refresh_store_cards()

    def change_store_page(self, offset):
        self.store_page += offset
        self.refresh_store_cards()

    def installed_apps_path(self):
        return profile_storage_dir(self.active_profile_id) / "apps" / "installed.json"

    def installed_apps(self):
        data = read_json(self.installed_apps_path(), {})
        installed = data.get("installed", []) if isinstance(data, dict) else []
        if "libreoffice" in installed:
            installed = ["whatsapp" if app_id == "libreoffice" else app_id for app_id in installed]
            installed = list(dict.fromkeys(installed))
            write_json(self.installed_apps_path(), {"installed": installed})
        return installed

    def refresh_installed_apps(self):
        if not hasattr(self, "installed_apps_pages"):
            return
        old_index = self.home_app_pages.currentIndex()
        for page in self.installed_apps_pages:
            self.home_app_pages.removeWidget(page)
            page.deleteLater()
        self.installed_apps_pages = []
        catalog = self.desktop_app_catalog()
        for start in range(0, len(catalog), self.installed_apps_per_page):
            page = QWidget()
            grid = QGridLayout(page)
            grid.setSpacing(14)
            self.installed_apps_pages.append(page)
            self.home_app_pages.addWidget(page)
            for index, app in enumerate(catalog[start:start + self.installed_apps_per_page]):
                color = app.get("color") or {"youtube":"#8e2630", "ytmusic":"#762944", "chatgpt":"#17614e", "gemini":"#334b86", "netflix":"#941b24", "grypl":"#315d35", "minecraft":"#4d6731", "whatsapp":"#176b52"}.get(app["id"], "#30394d")
                button = QPushButton(f"{app['icon']}\n{app['name']}") if app.get("page") or app.get("generic_icon") or app.get("url") else QPushButton(app["name"])
                button.setObjectName("tile")
                button.setMinimumHeight(110)
                button.setProperty("miniOsTileBrandColor", color)
                button.setStyleSheet(app_tile_stylesheet(color, self.is_light_theme()))
                if app.get("page"):
                    target_page = app["page"]
                    button.clicked.connect(self.open_browser if target_page == "browser" else lambda checked=False, target=target_page: self.show_page(target))
                else:
                    icon = QPixmap() if app.get("generic_icon") else self.store_icon_pixmap(app, QSize(44, 44))
                    if not icon.isNull():
                        button.setIcon(QIcon(icon))
                        button.setIconSize(QSize(44, 44))
                    if app.get("url") and not app.get("generic_icon"):
                        self.register_store_icon_widget(app, button)
                    button.clicked.connect(lambda checked=False, selected=app: self.launch_store_app(selected))
                grid.addWidget(button, index // 4, index % 4)
        self.home_app_pages.setCurrentIndex(min(max(0, old_index), self.home_app_pages.count() - 1))
        self.update_home_page_controls()
        if hasattr(self, "app_order_list"):
            self.refresh_app_order_list(catalog)

    def desktop_app_catalog(self):
        installed = self.installed_apps()
        apps_by_id = {app["id"]: app for app in APP_STORE}
        catalog = [dict(app) for app in BUILTIN_DESKTOP_APPS]
        catalog.extend(dict(apps_by_id[app_id]) for app_id in installed if app_id in apps_by_id)
        by_id = {app["id"]: app for app in catalog}
        ordered = []
        seen = set()
        configured_order = self.settings.get("app_order", [])
        if isinstance(configured_order, list):
            for app_id in configured_order:
                if app_id in by_id and app_id not in seen:
                    ordered.append(by_id[app_id])
                    seen.add(app_id)
        ordered.extend(app for app in catalog if app["id"] not in seen)
        return ordered

    def refresh_app_order_list(self, catalog=None):
        if not hasattr(self, "app_order_list"):
            return
        if catalog is None:
            catalog = self.desktop_app_catalog()
        selected_id = self.app_order_list.currentItem().data(Qt.ItemDataRole.UserRole) if self.app_order_list.currentItem() else None
        self.app_order_list.clear()
        selected_row = 0
        for row, app in enumerate(catalog):
            item = QListWidgetItem(f"{app['icon']}  {app['name']}")
            item.setData(Qt.ItemDataRole.UserRole, app["id"])
            self.app_order_list.addItem(item)
            if app["id"] == selected_id:
                selected_row = row
        if self.app_order_list.count():
            self.app_order_list.setCurrentRow(selected_row)
        self.update_remove_app_button()

    def update_remove_app_button(self, *_args):
        if not hasattr(self, "remove_app_button"):
            return
        item = self.app_order_list.currentItem()
        app_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        self.remove_app_button.setEnabled(app_id in self.installed_apps())

    def remove_desktop_app(self):
        item = self.app_order_list.currentItem()
        if not item:
            return
        app_id = item.data(Qt.ItemDataRole.UserRole)
        self.uninstall_store_app(app_id)

    def uninstall_store_app(self, app_id):
        installed = self.installed_apps()
        if app_id not in installed:
            QMessageBox.information(self, "Aplikacje", "Aplikacje systemowe są częścią mini-OS i nie można ich odinstalować.")
            return
        app = next((entry for entry in APP_STORE if entry["id"] == app_id), None)
        app_name = app["name"] if app else str(app_id)
        answer = QMessageBox.question(
            self,
            "Usuń aplikację",
            f"Czy odinstalować „{app_name}” z profilu „{self.username}”?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        write_json(self.installed_apps_path(), {"installed": [installed_id for installed_id in installed if installed_id != app_id]})
        if hasattr(self, "app_order_list"):
            self.settings["app_order"] = [
                self.app_order_list.item(row).data(Qt.ItemDataRole.UserRole)
                for row in range(self.app_order_list.count())
                if self.app_order_list.item(row).data(Qt.ItemDataRole.UserRole) != app_id
            ]
        active_profile = self.profile_by_id(self.active_profile_id)
        active_profile["settings"] = self.settings.copy()
        self.persist_profiles()
        if app_id == "minecraft":
            minecraft_file = profile_storage_dir(self.active_profile_id) / "apps" / "MINECRAFT.html"
            try:
                minecraft_file.unlink(missing_ok=True)
            except OSError as error:
                QMessageBox.warning(self, "Usuń aplikację", f"Nie udało się usunąć lokalnego pliku MINECRAFT.html.\n{error}")
        self.refresh_store_cards()
        self.refresh_installed_apps()
        self.home_status.setText(f"Usunięto aplikację {app_name}.")

    def move_app_order_item(self, offset):
        current_row = self.app_order_list.currentRow()
        target_row = current_row + offset
        if current_row < 0 or not 0 <= target_row < self.app_order_list.count():
            return
        item = self.app_order_list.takeItem(current_row)
        self.app_order_list.insertItem(target_row, item)
        self.app_order_list.setCurrentRow(target_row)

    def change_home_apps_page(self, offset):
        target = self.home_app_pages.currentIndex() + offset
        if 0 <= target < self.home_app_pages.count():
            self.home_app_pages.setCurrentIndex(target)

    def update_home_page_controls(self, *_args):
        if not hasattr(self, "home_page_label"):
            return
        current = self.home_app_pages.currentIndex()
        total = self.home_app_pages.count()
        self.home_page_label.setText(f"{current + 1} / {total}")
        self.home_prev_apps_button.setEnabled(current > 0)
        self.home_next_apps_button.setEnabled(current < total - 1)

    def refresh_store_cards(self):
        if not hasattr(self, "store_grid"):
            return
        while self.store_grid.count():
            item = self.store_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        installed = self.installed_apps()
        query = self.store_search.text().strip().casefold() if hasattr(self, "store_search") else ""
        category_filter = self.store_category_combo.currentData() if hasattr(self, "store_category_combo") else ""
        visible_apps = [app for app in APP_STORE
                        if (not category_filter or app.get("category", "Aplikacje") == category_filter)
                        and (not query or query in (app["name"] + " " + app.get("category", "Aplikacje") + " " + app.get("url", "") + " " + app.get("description", "")).casefold())]
        page_count = max(1, (len(visible_apps) + self.store_page_size - 1) // self.store_page_size)
        self.store_page = max(0, min(self.store_page, page_count - 1))
        if hasattr(self, "store_page_label"):
            self.store_page_label.setText(f"{self.store_page + 1} / {page_count}  ·  {len(visible_apps)} aplikacji")
            self.store_previous_button.setEnabled(self.store_page > 0)
            self.store_next_button.setEnabled(self.store_page < page_count - 1)
        start = self.store_page * self.store_page_size
        page_apps = visible_apps[start:start + self.store_page_size]
        for index, app in enumerate(page_apps):
            card = QFrame()
            card.setObjectName("panel")
            layout = QVBoxLayout(card)
            icon = QLabel(app["icon"])
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon.setStyleSheet("font-size:40px; background:transparent;")
            pixmap = QPixmap() if app.get("generic_icon") else self.store_icon_pixmap(app, QSize(64, 64))
            if not pixmap.isNull():
                icon.setPixmap(pixmap)
            if app.get("url") and not app.get("generic_icon"):
                self.register_store_icon_widget(app, icon)
            name = QLabel(app["name"])
            name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name.setFont(QFont("Arial", 18, QFont.Weight.Bold))
            description = QLabel(app.get("description", ""))
            description.setAlignment(Qt.AlignmentFlag.AlignCenter)
            description.setWordWrap(True)
            description.setMaximumHeight(48)
            description.setStyleSheet("color:#aab4ca; font-size:12px; background:transparent;")
            button = QPushButton("Otwórz" if app["id"] in installed else "Zainstaluj")
            button.clicked.connect(lambda checked=False, selected=app: self.install_or_open_store_app(selected))
            layout.addWidget(icon)
            layout.addWidget(name)
            if app.get("description"):
                layout.addWidget(description)
            layout.addWidget(button)
            if app["id"] in installed:
                remove = QPushButton("Usuń")
                remove.clicked.connect(lambda checked=False, selected_id=app["id"]: self.uninstall_store_app(selected_id))
                layout.addWidget(remove)
            self.store_grid.addWidget(card, index // 3, index % 3)

    def register_store_icon_widget(self, app, widget):
        self.store_icon_widgets.setdefault(app["id"], []).append(weakref.ref(widget))

    def store_icon_pixmap(self, app, size):
        if not app.get("url"):
            return QPixmap()
        pixmap = self.store_icon_cache.get(app["id"])
        if pixmap is not None:
            self.store_icon_cache.move_to_end(app["id"])
        cache_dir = ROOT / "store_icons"
        cache_file = cache_dir / f"{app['id']}.png"
        if pixmap is None and cache_file.is_file():
            pixmap = QPixmap(str(cache_file))
            if pixmap.isNull():
                pixmap = None
            else:
                self.store_icon_cache[app["id"]] = pixmap
                self.store_icon_cache.move_to_end(app["id"])
                self.trim_store_icon_cache()
        if pixmap is None and app["id"] not in self.store_icon_pending:
            host = QUrl(app["url"]).host()
            if host:
                query = QUrlQuery()
                query.addQueryItem("domain", host)
                query.addQueryItem("sz", "128")
                favicon_url = QUrl("https://www.google.com/s2/favicons")
                favicon_url.setQuery(query)
                request = QNetworkRequest(favicon_url)
                request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,
                                     QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy)
                reply = self.store_icon_manager.get(request)
                self.store_icon_pending[app["id"]] = reply
                reply.setProperty("store_app_id", app["id"])
                reply.finished.connect(lambda current=reply: self.store_icon_loaded(current))
        if pixmap is None or pixmap.isNull():
            return QPixmap()
        return pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)

    def store_icon_loaded(self, reply):
        app_id = reply.property("store_app_id")
        self.store_icon_pending.pop(app_id, None)
        pixmap = QPixmap()
        if reply.error() == QNetworkReply.NetworkError.NoError:
            pixmap.loadFromData(bytes(reply.readAll()))
        reply.deleteLater()
        if pixmap.isNull():
            return
        self.store_icon_cache[app_id] = pixmap
        self.store_icon_cache.move_to_end(app_id)
        self.trim_store_icon_cache()
        cache_dir = ROOT / "store_icons"
        cache_dir.mkdir(parents=True, exist_ok=True)
        pixmap.save(str(cache_dir / f"{app_id}.png"), "PNG")
        live_widgets = []
        for widget_ref in self.store_icon_widgets.get(app_id, []):
            widget = widget_ref()
            if widget is None:
                continue
            live_widgets.append(widget_ref)
            try:
                if isinstance(widget, QLabel):
                    widget.setText("")
                    widget.setPixmap(pixmap.scaled(QSize(64, 64), Qt.AspectRatioMode.KeepAspectRatio,
                                                   Qt.TransformationMode.SmoothTransformation))
                elif isinstance(widget, QPushButton):
                    app = next((entry for entry in APP_STORE if entry["id"] == app_id), None)
                    if app:
                        widget.setText(app["name"])
                    widget.setIcon(QIcon(pixmap))
                    widget.setIconSize(QSize(44, 44))
            except RuntimeError:
                continue
        self.store_icon_widgets[app_id] = live_widgets

    def trim_store_icon_cache(self):
        while len(self.store_icon_cache) > 256:
            self.store_icon_cache.popitem(last=False)

    def install_or_open_store_app(self, app):
        if app["id"] in self.installed_apps():
            self.launch_store_app(app)
            return
        apps_dir = profile_storage_dir(self.active_profile_id) / "apps"
        apps_dir.mkdir(parents=True, exist_ok=True)
        if app.get("local"):
            if not BUNDLED_MINECRAFT_FILE.is_file():
                QMessageBox.warning(self, "mini_store", "Nie znaleziono dołączonego pliku MINECRAFT.html.")
                return
            shutil.copy2(BUNDLED_MINECRAFT_FILE, apps_dir / "MINECRAFT.html")
        installed = self.installed_apps()
        installed.append(app["id"])
        write_json(self.installed_apps_path(), {"installed": installed})
        self.refresh_store_cards()
        self.refresh_installed_apps()
        ordered_app_ids = [desktop_app["id"] for desktop_app in self.desktop_app_catalog()]
        installed_page = ordered_app_ids.index(app["id"]) // self.installed_apps_per_page
        self.home_app_pages.setCurrentIndex(installed_page)
        self.home_status.setText(
            f"Zainstalowano {app['name']} — skrót jest na stronie {installed_page + 1} pulpitu."
        )

    def launch_store_app(self, app):
        if app.get("native_app"):
            app_paths = (Path("/Applications/LibreOffice.app"), Path.home() / "Applications" / "LibreOffice.app")
            installed_app = next((path for path in app_paths if path.is_dir()), None)
            if installed_app is None:
                QMessageBox.information(
                    self, "LibreOffice",
                    "Nie znaleziono aplikacji LibreOffice na tym Macu. Zainstaluj LibreOffice, a potem uruchom go ponownie z tego kafelka.",
                )
                return
            QProcess.startDetached("/usr/bin/open", [str(installed_app)])
            return
        if not self.browser or not self.app_browser:
            QMessageBox.information(self, app["name"], "Przeglądarka wymaga PySide6-WebEngine.")
            return
        profile = self.profile_by_id(self.active_profile_id)
        if profile:
            profile.setdefault("settings", {})["browser_last_app"] = app["id"]
            self.settings["browser_last_app"] = app["id"]
            self.persist_profiles()
        self.app_bar_label.setText(app["name"])
        if app.get("local"):
            path = profile_storage_dir(self.active_profile_id) / "apps" / "MINECRAFT.html"
            if not path.is_file():
                QMessageBox.warning(self, app["name"], "Plik gry nie jest zainstalowany.")
                return
            self.app_browser.setUrl(QUrl.fromLocalFile(str(path)))
        else:
            self.app_browser.setUrl(QUrl(app["url"]))
        self.show_page("installed_app_view")

    def make_office(self):
        _page, root = self.page("office")
        bar = QHBoxLayout()
        back = QPushButton("←  Pulpit")
        back.clicked.connect(lambda: self.show_page("home"))
        title = QLabel("mini Office")
        title.setFont(QFont("Arial", 26, QFont.Weight.Bold))
        new_doc = QPushButton("Nowy")
        new_doc.clicked.connect(self.office_new_document)
        open_doc = QPushButton("Otwórz")
        open_doc.clicked.connect(self.office_open_document)
        save_doc = QPushButton("Zapisz jako…")
        save_doc.setObjectName("accent")
        save_doc.clicked.connect(self.office_save_document)
        bar.addWidget(back)
        bar.addWidget(title, 1)
        bar.addWidget(new_doc)
        bar.addWidget(open_doc)
        bar.addWidget(save_doc)
        root.addLayout(bar)
        self.office_tabs = QTabWidget()
        self.office_document = QTextEdit()
        self.office_document.setPlaceholderText("Zacznij pisać dokument…")
        self.office_tabs.addTab(self.office_document, "Dokument")
        sheet_page = QWidget()
        sheet_layout = QVBoxLayout(sheet_page)
        sheet_actions = QHBoxLayout()
        add_row = QPushButton("＋ Wiersz")
        add_row.clicked.connect(lambda: self.office_sheet.setRowCount(self.office_sheet.rowCount() + 1))
        add_column = QPushButton("＋ Kolumna")
        add_column.clicked.connect(self.office_add_sheet_column)
        sheet_actions.addWidget(add_row)
        sheet_actions.addWidget(add_column)
        sheet_actions.addStretch(1)
        sheet_layout.addLayout(sheet_actions)
        formula_row = QHBoxLayout()
        formula_row.addWidget(QLabel("fx"))
        self.office_formula = QLineEdit()
        self.office_formula.setPlaceholderText("Wpisz wartość lub formułę, np. =SUM(A1:A4)")
        self.office_formula.editingFinished.connect(self.office_apply_formula)
        formula_row.addWidget(self.office_formula, 1)
        sheet_layout.addLayout(formula_row)
        self.office_sheet = QTableWidget(20, 8)
        self.office_sheet.setHorizontalHeaderLabels([chr(ord("A") + i) for i in range(8)])
        self.office_sheet.setVerticalHeaderLabels([str(i + 1) for i in range(20)])
        self._office_sheet_updating = False
        self.office_sheet.itemChanged.connect(self.office_sheet_item_changed)
        self.office_sheet.currentCellChanged.connect(self.office_update_formula_bar)
        sheet_layout.addWidget(self.office_sheet, 1)
        self.office_tabs.addTab(sheet_page, "Arkusz")
        presentation = QWidget()
        presentation_layout = QHBoxLayout(presentation)
        slide_side = QVBoxLayout()
        self.office_slide_list = QListWidget()
        self.office_slides = [{"title": "Slajd 1", "body": ""}]
        self.office_slide_list.addItem("Slajd 1")
        self.office_slide_list.setCurrentRow(0)
        slide_buttons = QHBoxLayout()
        add_slide = QPushButton("＋")
        add_slide.setToolTip("Dodaj slajd")
        add_slide.clicked.connect(self.office_add_slide)
        delete_slide = QPushButton("−")
        delete_slide.setToolTip("Usuń slajd")
        delete_slide.clicked.connect(self.office_delete_slide)
        slide_buttons.addWidget(add_slide)
        slide_buttons.addWidget(delete_slide)
        slide_side.addWidget(self.office_slide_list, 1)
        slide_side.addLayout(slide_buttons)
        presentation_layout.addLayout(slide_side, 1)
        slide_editor = QVBoxLayout()
        self.office_slide_title = QLineEdit("Slajd 1")
        self.office_slide_title.setPlaceholderText("Tytuł slajdu")
        self.office_slide_title.textChanged.connect(self.office_update_slide)
        self.office_slide_body = QTextEdit()
        self.office_slide_body.setPlaceholderText("Treść slajdu…")
        self.office_slide_body.textChanged.connect(self.office_update_slide)
        self.office_slide_image = QLabel("Brak obrazu")
        self.office_slide_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.office_slide_image.setMinimumHeight(120)
        self.office_slide_image.setStyleSheet("background:#0b0e15; border:1px solid #30394d; border-radius:10px; color:#aab4ca;")
        image_actions = QHBoxLayout()
        add_image = QPushButton("Dodaj obraz…")
        add_image.clicked.connect(self.office_add_slide_image)
        remove_image = QPushButton("Usuń obraz")
        remove_image.clicked.connect(self.office_remove_slide_image)
        image_actions.addWidget(add_image)
        image_actions.addWidget(remove_image)
        image_actions.addStretch(1)
        slide_editor.addWidget(self.office_slide_title)
        slide_editor.addWidget(self.office_slide_body, 1)
        slide_editor.addLayout(image_actions)
        slide_editor.addWidget(self.office_slide_image)
        presentation_layout.addLayout(slide_editor, 3)
        self.office_slide_list.currentRowChanged.connect(self.office_select_slide)
        self.office_tabs.addTab(presentation, "Prezentacja")
        root.addWidget(self.office_tabs, 1)
        self.office_status = QLabel("Dokumenty zapisują się w folderze profilu mini-OS.")
        self.office_status.setStyleSheet("color:#aab4ca;")
        root.addWidget(self.office_status)

    def office_add_sheet_column(self):
        count = self.office_sheet.columnCount()
        self.office_sheet.insertColumn(count)
        self.office_sheet.setHorizontalHeaderItem(count, QTableWidgetItem(self.office_column_name(count)))

    def office_column_name(self, column):
        result = ""
        number = column + 1
        while number:
            number, remainder = divmod(number - 1, 26)
            result = chr(65 + remainder) + result
        return result

    def office_raw_cell(self, row, column):
        item = self.office_sheet.item(row, column)
        if not item:
            return ""
        formula = item.data(Qt.ItemDataRole.UserRole)
        return formula if isinstance(formula, str) and formula.startswith("=") else item.text()

    def office_calculate_cell(self, row, column, seen=None):
        seen = set() if seen is None else seen
        key = (row, column)
        if key in seen:
            raise ValueError("cykl")
        seen.add(key)
        raw = self.office_raw_cell(row, column).strip()
        if not raw.startswith("="):
            seen.remove(key)
            return float(raw.replace(",", ".")) if raw else 0.0
        expression = raw[1:]

        def cell_value(match):
            column_name, row_number = match.group(1).upper(), int(match.group(2))
            col_number = 0
            for char in column_name:
                col_number = col_number * 26 + ord(char) - 64
            return str(self.office_calculate_cell(row_number - 1, col_number - 1, seen))

        def sum_range(match):
            first, last = match.group(1).split(":", 1)
            cells = []
            for address in (first, last):
                parsed = re.fullmatch(r"([A-Z]+)(\d+)", address.strip(), re.I)
                if not parsed:
                    raise ValueError("zakres")
                column_name, row_number = parsed.group(1).upper(), int(parsed.group(2))
                col_number = 0
                for char in column_name:
                    col_number = col_number * 26 + ord(char) - 64
                cells.append((row_number - 1, col_number - 1))
            (row1, col1), (row2, col2) = cells
            values = [self.office_calculate_cell(r, c, seen)
                      for r in range(min(row1,row2), max(row1,row2)+1)
                      for c in range(min(col1,col2), max(col1,col2)+1)]
            return str(sum(values))

        expression = re.sub(r"SUM\(([A-Z]+\d+:[A-Z]+\d+)\)", sum_range, expression, flags=re.I)
        expression = re.sub(r"\b([A-Z]+\d+)\b", cell_value, expression, flags=re.I)
        if not re.fullmatch(r"[0-9eE.+*/() \-]+", expression):
            raise ValueError("formuła")
        value = eval(expression, {"__builtins__": {}}, {})
        seen.remove(key)
        return float(value)

    def office_sheet_item_changed(self, item):
        if self._office_sheet_updating:
            return
        raw = item.text().strip()
        self._office_sheet_updating = True
        item.setData(Qt.ItemDataRole.UserRole, raw if raw.startswith("=") else None)
        self._office_sheet_updating = False
        self.office_recalculate_sheet()
        self.office_update_formula_bar()

    def office_recalculate_sheet(self):
        self._office_sheet_updating = True
        try:
            for row in range(self.office_sheet.rowCount()):
                for column in range(self.office_sheet.columnCount()):
                    item = self.office_sheet.item(row, column)
                    if not item:
                        continue
                    formula = item.data(Qt.ItemDataRole.UserRole)
                    if isinstance(formula, str) and formula.startswith("="):
                        try:
                            result = self.office_calculate_cell(row, column)
                            item.setText(f"{result:g}")
                        except Exception:
                            item.setText("#BŁĄD")
        finally:
            self._office_sheet_updating = False

    def office_update_formula_bar(self, *_args):
        item = self.office_sheet.currentItem()
        value = self.office_raw_cell(item.row(), item.column()) if item else ""
        self.office_formula.blockSignals(True)
        self.office_formula.setText(value)
        self.office_formula.blockSignals(False)

    def office_apply_formula(self):
        row, column = self.office_sheet.currentRow(), self.office_sheet.currentColumn()
        if row < 0 or column < 0:
            return
        item = self.office_sheet.item(row, column)
        if item is None:
            item = QTableWidgetItem()
            self.office_sheet.setItem(row, column, item)
        item.setText(self.office_formula.text())

    def office_current_slides(self):
        row = self.office_slide_list.currentRow()
        if 0 <= row < len(self.office_slides):
            old = self.office_slides[row]
            self.office_slides[row] = {"title": self.office_slide_title.text(), "body": self.office_slide_body.toPlainText(), "image": old.get("image")}

    def office_update_slide(self, *_args):
        row = self.office_slide_list.currentRow()
        if 0 <= row < len(self.office_slides):
            old = self.office_slides[row]
            self.office_slides[row] = {"title": self.office_slide_title.text(), "body": self.office_slide_body.toPlainText(), "image": old.get("image")}
            item = self.office_slide_list.item(row)
            if item:
                item.setText(self.office_slides[row]["title"] or f"Slajd {row + 1}")

    def office_select_slide(self, row):
        if 0 <= row < len(self.office_slides):
            self.office_slide_title.blockSignals(True)
            self.office_slide_body.blockSignals(True)
            self.office_slide_title.setText(self.office_slides[row]["title"])
            self.office_slide_body.setPlainText(self.office_slides[row]["body"])
            self.office_slide_title.blockSignals(False)
            self.office_slide_body.blockSignals(False)
            self.office_refresh_slide_image()

    def office_add_slide(self):
        self.office_current_slides()
        number = len(self.office_slides) + 1
        self.office_slides.append({"title": f"Slajd {number}", "body": "", "image": None})
        self.office_slide_list.addItem(f"Slajd {number}")
        self.office_slide_list.setCurrentRow(len(self.office_slides) - 1)

    def office_delete_slide(self):
        row = self.office_slide_list.currentRow()
        if len(self.office_slides) <= 1 or row < 0:
            return
        self.office_slides.pop(row)
        self.office_slide_list.takeItem(row)
        self.office_slide_list.setCurrentRow(min(row, len(self.office_slides) - 1))

    def office_new_document(self):
        self.office_document.clear()
        self.office_sheet.clearContents()
        self.office_sheet.setRowCount(20)
        self.office_sheet.setColumnCount(8)
        self.office_sheet.setHorizontalHeaderLabels([chr(ord("A") + i) for i in range(8)])
        self.office_sheet.setVerticalHeaderLabels([str(i + 1) for i in range(20)])
        self.office_slides = [{"title": "Slajd 1", "body": "", "image": None}]
        self.office_slide_list.clear()
        self.office_slide_list.addItem("Slajd 1")
        self.office_slide_list.setCurrentRow(0)
        self.office_slide_title.setText("Slajd 1")
        self.office_slide_body.clear()
        self.office_refresh_slide_image()
        self.office_status.setText("Utworzono nowy dokument.")

    def office_add_slide_image(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Wybierz obraz slajdu", str(Path.home()),
            "Obrazy (*.png *.jpg *.jpeg *.webp *.bmp *.gif)")
        if not filename:
            return
        source = Path(filename)
        images_dir = profile_storage_dir(self.active_profile_id) / "apps" / "office" / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        image_path = images_dir / f"{uuid.uuid4().hex[:8]}_{source.name}"
        try:
            shutil.copy2(source, image_path)
            row = self.office_slide_list.currentRow()
            if row < 0:
                return
            self.office_current_slides()
            self.office_slides[row]["image"] = str(image_path)
            self.office_refresh_slide_image()
        except Exception as error:
            QMessageBox.warning(self, "mini Office", f"Nie udało się dodać obrazu: {error}")

    def office_remove_slide_image(self):
        row = self.office_slide_list.currentRow()
        if 0 <= row < len(self.office_slides):
            self.office_slides[row]["image"] = None
            self.office_refresh_slide_image()

    def office_refresh_slide_image(self):
        row = self.office_slide_list.currentRow()
        image = self.office_slides[row].get("image") if 0 <= row < len(self.office_slides) else None
        pixmap = QPixmap(str(image)) if image else QPixmap()
        if pixmap.isNull():
            self.office_slide_image.setPixmap(QPixmap())
            self.office_slide_image.setText("Brak obrazu")
            return
        self.office_slide_image.setText("")
        self.office_slide_image.setPixmap(pixmap.scaled(QSize(620, 220), Qt.AspectRatioMode.KeepAspectRatio,
                                                        Qt.TransformationMode.SmoothTransformation))

    def office_open_document(self):
        office_dir = profile_storage_dir(self.active_profile_id) / "apps" / "office"
        office_dir.mkdir(parents=True, exist_ok=True)
        filename, _ = QFileDialog.getOpenFileName(self, "Otwórz dokument", str(office_dir),
            "Dokumenty (*.txt *.md);;Arkusze (*.csv *.xlsx);;Prezentacje mini Office (*.json);;Wszystkie pliki (*)")
        if not filename:
            return
        try:
            path = Path(filename)
            if path.suffix.lower() == ".csv":
                with path.open(encoding="utf-8-sig", newline="") as handle:
                    rows = list(csv.reader(handle))
                self.office_sheet.setRowCount(max(20, len(rows)))
                self.office_sheet.setColumnCount(max(8, max((len(row) for row in rows), default=0)))
                self.office_sheet.clearContents()
                for r, row in enumerate(rows):
                    for c, value in enumerate(row):
                        self.office_sheet.setItem(r, c, QTableWidgetItem(value))
                self.office_recalculate_sheet()
                self.office_tabs.setCurrentIndex(1)
            elif path.suffix.lower() == ".xlsx":
                if not XLSX_AVAILABLE:
                    raise RuntimeError("Brakuje biblioteki openpyxl. Zainstaluj zależności z requirements.txt.")
                workbook = load_workbook(path, data_only=False, read_only=True)
                worksheet = workbook.active
                self.office_sheet.setRowCount(max(20, worksheet.max_row))
                self.office_sheet.setColumnCount(max(8, worksheet.max_column))
                self.office_sheet.clearContents()
                for r, values in enumerate(worksheet.iter_rows(values_only=True)):
                    for c, value in enumerate(values):
                        if value is not None:
                            self.office_sheet.setItem(r, c, QTableWidgetItem(str(value)))
                workbook.close()
                self.office_recalculate_sheet()
                self.office_tabs.setCurrentIndex(1)
            elif path.suffix.lower() == ".json":
                data = json.loads(path.read_text(encoding="utf-8"))
                self.office_slides = data.get("slides", [{"title":"Slajd 1","body":"","image":None}])
                if not self.office_slides:
                    self.office_slides = [{"title":"Slajd 1","body":"","image":None}]
                self.office_slide_list.clear()
                for slide in self.office_slides:
                    self.office_slide_list.addItem(slide.get("title", "Slajd"))
                self.office_slide_list.setCurrentRow(0)
                self.office_tabs.setCurrentIndex(2)
            else:
                self.office_document.setPlainText(path.read_text(encoding="utf-8"))
                self.office_tabs.setCurrentIndex(0)
            self.office_status.setText(f"Otwarto: {path.name}")
        except Exception as error:
            QMessageBox.warning(self, "mini Office", f"Nie udało się otworzyć pliku: {error}")

    def office_save_document(self):
        office_dir = profile_storage_dir(self.active_profile_id) / "apps" / "office"
        office_dir.mkdir(parents=True, exist_ok=True)
        tab = self.office_tabs.currentIndex()
        filters = ("Dokument tekstowy (*.txt)", "Arkusz Excel (*.xlsx);;Arkusz CSV (*.csv)", "Prezentacja mini Office (*.json)")
        default_name = ("Dokument.txt", "Arkusz.csv", "Prezentacja.json")[tab]
        filename, _ = QFileDialog.getSaveFileName(self, "Zapisz dokument", str(office_dir / default_name), filters[tab])
        if not filename:
            return
        path = Path(filename)
        try:
            if tab == 0:
                path.write_text(self.office_document.toPlainText(), encoding="utf-8")
            elif tab == 1:
                if path.suffix.lower() == ".xlsx":
                    if not XLSX_AVAILABLE:
                        raise RuntimeError("Brakuje biblioteki openpyxl. Zainstaluj zależności z requirements.txt.")
                    workbook = Workbook()
                    worksheet = workbook.active
                    worksheet.title = "Arkusz1"
                    for row in range(self.office_sheet.rowCount()):
                        for column in range(self.office_sheet.columnCount()):
                            value = self.office_raw_cell(row, column)
                            if value:
                                worksheet.cell(row + 1, column + 1, value)
                    workbook.save(path)
                else:
                    if path.suffix.lower() != ".csv":
                        path = path.with_suffix(".csv")
                    with path.open("w", encoding="utf-8", newline="") as handle:
                        writer = csv.writer(handle)
                        for row in range(self.office_sheet.rowCount()):
                            writer.writerow([self.office_raw_cell(row, col) for col in range(self.office_sheet.columnCount())])
            else:
                self.office_current_slides()
                path.write_text(json.dumps({"slides": self.office_slides}, ensure_ascii=False, indent=2), encoding="utf-8")
            self.office_status.setText(f"Zapisano: {path.name}")
        except Exception as error:
            QMessageBox.warning(self, "mini Office", f"Nie udało się zapisać pliku: {error}")

    def set_browser_profile(self, profile_id):
        if not WEBENGINE_AVAILABLE or self.browser is None:
            return
        user_directories = ensure_profile_user_directories(profile_id)
        browser_data = profile_storage_dir(profile_id) / "browser"
        profile_path = browser_data / "profile"
        cache_path = browser_data / "cache"
        profile_path.mkdir(parents=True, exist_ok=True)
        cache_path.mkdir(parents=True, exist_ok=True)

        # Migrate the former shared browser data once to the profile active on upgrade.
        migration_marker = ROOT / "browser" / ".profile_data_migrated"
        if not migration_marker.exists():
            legacy_root = ROOT / "browser"
            for source, destination in ((legacy_root / "profile", profile_path), (legacy_root / "cache", cache_path)):
                if source.is_dir() and not any(destination.iterdir()):
                    shutil.copytree(source, destination, dirs_exist_ok=True)
            migration_marker.parent.mkdir(parents=True, exist_ok=True)
            migration_marker.write_text(str(profile_id), encoding="utf-8")

        old_page, old_profile = self.browser_page, self.web_profile
        old_app_page = getattr(self, "app_page", None)
        self.web_profile = QWebEngineProfile(f"mini-os-{profile_id}", self)
        self.web_profile.setPersistentStoragePath(str(profile_path))
        self.web_profile.setCachePath(str(cache_path))
        self.web_profile.setDownloadPath(str(user_directories["downloads"]))
        self.web_profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        # WhatsApp Web blocks QtWebEngine's identifying token even when its
        # bundled Chromium is new enough. Present a standard desktop Chrome UA.
        self.web_profile.setHttpUserAgent(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.browser_page = QWebEnginePage(self.web_profile, self.browser)
        self.browser.setPage(self.browser_page)
        set_webview_theme(self.browser_page, self.is_light_theme())
        self.web_profile.downloadRequested.connect(
            lambda download, owner_id=profile_id: self.handle_browser_download(download, owner_id)
        )
        self.browser.urlChanged.connect(self.remember_browser_url)
        self.browser.setUrl(QUrl(self.settings.get("browser_last_url") or self.settings.get("start_url", "https://www.google.com")))
        if self.app_browser:
            self._attach_app_page()
        if old_page:
            old_page.deleteLater()
        if old_app_page:
            old_app_page.deleteLater()
        if old_profile:
            old_profile.deleteLater()

    def handle_browser_download(self, download, profile_id):
        try:
            downloads_dir = ensure_profile_user_directories(profile_id)["downloads"]
            filename = Path(download.suggestedFileName() or download.downloadFileName() or "pobrany_plik").name
            if filename in {"", ".", ".."}:
                filename = "pobrany_plik"
            destination = self.files_unique_destination(downloads_dir / filename)
            download.setDownloadDirectory(str(downloads_dir))
            download.setDownloadFileName(destination.name)
            download.accept()
        except Exception as error:
            try:
                download.cancel()
            except Exception:
                pass
            QMessageBox.warning(self, "Pobieranie", f"Nie można zapisać pliku w folderze Pobrane:\n{error}")

    def remember_browser_url(self, qurl):
        if hasattr(self, "url"):
            self.url.setText(qurl.toString())
        if not qurl.isValid() or qurl.scheme() in ("", "about"):
            return
        profile = self.profile_by_id(self.active_profile_id)
        if profile:
            profile.setdefault("settings", {}).update(browser_last_url=qurl.toString())
            self.settings["browser_last_url"] = qurl.toString()
            self.persist_profiles()

    def allow_app_feature(self, url, feature):
        if feature == QWebEnginePage.Feature.MouseLock:
            self.app_page.setFeaturePermission(url, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)

    def navigate(self):
        if not self.browser: return
        text = self.url.text().strip()
        if not text: return
        if " " in text or "." not in text.split("/")[0]:
            from urllib.parse import quote
            text = "https://www.google.com/search?q=" + quote(text)
        elif not text.startswith(("http://", "https://")):
            text = "https://" + text
        self.browser.setUrl(QUrl(text))

    def make_games(self):
        w, root = self.page("games"); root.addLayout(self.title_row("Gry"))
        intro = QLabel("Wybierz krótką grę. Wszystkie sterowania są duże i wygodne w dotyku.")
        intro.setStyleSheet("color:#aab4ca;"); root.addWidget(intro)
        grid = QGridLayout(); grid.setSpacing(14)
        b1 = QPushButton("🎯\n\nKliknij cel\n\nSprawdź refleks")
        b2 = QPushButton("🧠\n\nZapamiętaj\n\nGra pamięciowa")
        b3 = QPushButton("🎲\n\nZgadnij liczbę\n\n1–20")
        for b in (b1,b2,b3): b.setObjectName("tile")
        b1.clicked.connect(self.play_click_game); b2.clicked.connect(self.play_memory_game); b3.clicked.connect(self.play_guess_game)
        grid.addWidget(b1,0,0); grid.addWidget(b2,0,1); grid.addWidget(b3,0,2)
        root.addLayout(grid); root.addStretch(1)

    def play_click_game(self):
        start = time.time()
        count = {"n": 0}
        dlg = QMessageBox(self); dlg.setWindowTitle("Kliknij cel"); dlg.setText("Kliknij przycisk tyle razy, ile dasz radę w 10 sekund.")
        btn = QPushButton("START")
        dlg.addButton(btn, QMessageBox.ButtonRole.AcceptRole)
        dlg.exec()
        game = QMessageBox(self); game.setWindowTitle("Kliknij cel"); game.setText("Gotowy? Klikaj!")
        hit = QPushButton("TRAF!")
        game.addButton(hit, QMessageBox.ButtonRole.AcceptRole)
        timer = QTimer(self); timer.setSingleShot(True)
        hit.clicked.connect(lambda: count.__setitem__("n", count["n"]+1))
        timer.timeout.connect(lambda: (game.done(0), QMessageBox.information(self,"Wynik",f"Twój wynik: {count['n']} kliknięć.")))
        timer.start(10000); game.exec(); timer.stop()

    def play_memory_game(self):
        seq = [random.randint(1, 9) for _ in range(5)]
        QMessageBox.information(self, "Zapamiętaj", "Zapamiętaj tę sekwencję:\n\n" + "   ".join(map(str,seq)))
        answer, ok = QInputDialog.getText(self, "Twoja kolej", "Wpisz cyfry bez spacji:")
        if ok:
            if answer.replace(" ","") == "".join(map(str,seq)):
                QMessageBox.information(self,"Wynik","Świetnie! Sekwencja poprawna.")
            else:
                QMessageBox.information(self,"Wynik","Tym razem nie. Sekwencja to: " + "".join(map(str,seq)))

    def play_guess_game(self):
        target = random.randint(1,20)
        for _ in range(5):
            n, ok = QInputDialog.getInt(self,"Zgadnij liczbę","Wybierz liczbę od 1 do 20:",1,1,20)
            if not ok: return
            if n == target:
                QMessageBox.information(self,"Wynik","Brawo! Udało się."); return
            QMessageBox.information(self,"Podpowiedź","Za mało!" if n < target else "Za dużo!")
        QMessageBox.information(self,"Koniec",f"Przegrana runda. Wylosowana liczba: {target}")

    def make_camera(self):
        w, root = self.page("camera"); root.addLayout(self.title_row("Aparat"))
        self.camera_preview = QLabel("Podgląd aparatu pojawi się tutaj.")
        self.camera_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_preview.setMinimumHeight(300)
        self.camera_preview.setStyleSheet("background:#080a0f; border-radius:20px; color:#aab4ca;")
        root.addWidget(self.camera_preview, 1)
        controls = QHBoxLayout()
        start = QPushButton("Włącz aparat"); start.setObjectName("accent"); start.clicked.connect(self.start_camera)
        shot = QPushButton("●  Zrób zdjęcie"); shot.clicked.connect(self.take_photo)
        stop = QPushButton("Wyłącz aparat"); stop.clicked.connect(self.stop_camera)
        controls.addWidget(start); controls.addWidget(shot); controls.addWidget(stop); root.addLayout(controls)
        self.camera_hint = QLabel(f"Zdjęcia będą zapisywane w Galerii profilu „{self.username}”.")
        self.camera_hint.setWordWrap(True); self.camera_hint.setStyleSheet("color:#aab4ca;")
        root.addWidget(self.camera_hint)

    def start_camera(self):
        if not CAMERA_AVAILABLE:
            QMessageBox.warning(self,"Brak modułu kamery","Zainstaluj moduł kamery poleceniem:\npython3 -m pip install opencv-python"); return
        if self.camera is None:
            self.camera = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
        if not self.camera.isOpened():
            self.camera.release(); self.camera = None
            QMessageBox.warning(self,"Brak dostępu","Nie udało się otworzyć kamery. Sprawdź uprawnienia macOS: Ustawienia systemowe → Prywatność i ochrona → Kamera."); return
        self._camera_preview_active = True
        if self.camera_timer is None:
            self.camera_timer = QTimer(self); self.camera_timer.timeout.connect(self.update_camera)
        self.camera_timer.start(33)
        if self.settings.get("theme") == "auto":
            self.start_auto_theme_detection()

    def update_camera(self):
        if self.camera is None: return
        ok, frame = self.camera.read()
        if not ok: return
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        img = QImage(frame.data, w, h, ch*w, QImage.Format.Format_RGB888).copy()
        self.camera_preview.setPixmap(QPixmap.fromImage(img).scaled(self.camera_preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def take_photo(self):
        if self.camera is None or not self.camera.isOpened():
            QMessageBox.information(self,"Aparat","Najpierw włącz aparat."); return
        ok, frame = self.camera.read()
        if not ok:
            QMessageBox.warning(self,"Aparat","Nie udało się zrobić zdjęcia."); return
        filename = PHOTOS / ("mini-os_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".jpg")
        cv2.imwrite(str(filename), frame)
        self.camera_hint.setText(f"Zapisano zdjęcie: {filename}")

    def stop_camera(self, force=False):
        if self.camera_timer: self.camera_timer.stop()
        self._camera_preview_active = False
        if self.camera is not None:
            self.camera.release(); self.camera = None
        self.camera_preview.clear(); self.camera_preview.setText("Aparat wyłączony.")
        if force:
            self.auto_theme_timer.stop()

    def make_settings(self):
        w, root = self.page("settings"); root.addLayout(self.title_row("Ustawienia"))
        settings_row = QHBoxLayout()
        self.settings_categories = QListWidget()
        self.settings_categories.setFixedWidth(205)
        self.settings_categories.setStyleSheet(
            "QListWidget { background:transparent; border:none; padding:8px; }"
            "QListWidget::item { padding:10px 8px; border-radius:8px; }"
            "QListWidget::item:selected { background:#477be0; color:white; }"
        )
        self.settings_panel = QStackedWidget()
        settings_row.addWidget(self.settings_categories)
        settings_row.addWidget(self.settings_panel, 1)
        root.addLayout(settings_row, 1)

        active_category_layout = [None]

        def category(title, icon):
            self.settings_categories.addItem(f"{icon}  {title}")
            page = QWidget()
            page_layout = QVBoxLayout(page)
            page_layout.setContentsMargins(18, 14, 18, 14)
            page_layout.setSpacing(14)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setWidget(page)
            self.settings_panel.addWidget(scroll)
            active_category_layout[0] = page_layout
            return page_layout

        def section(title):
            group = QGroupBox(title)
            group.setStyleSheet("QGroupBox { font-size:16px; font-weight:700; border:1px solid rgba(140,150,175,90); border-radius:12px; margin-top:10px; padding:12px; } QGroupBox::title { subcontrol-origin:margin; left:12px; padding:0 6px; }")
            group_lay = QVBoxLayout(group)
            group_lay.setSpacing(10)
            active_category_layout[0].addWidget(group, 1)
            return group_lay

        category("Wygląd", "◐")
        lay = section("Tło i motyw")
        lay.addWidget(QLabel("Motyw systemu"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Automatyczny — wykrywaj jasność kamerą", "auto")
        self.theme_combo.addItem("Jasny", "light")
        self.theme_combo.addItem("Ciemny", "dark")
        theme_index = self.theme_combo.findData(self.settings.get("theme", "dark"))
        self.theme_combo.setCurrentIndex(theme_index if theme_index >= 0 else 0)
        self.theme_combo.currentIndexChanged.connect(
            lambda _index: self.update_theme_mode(self.theme_combo.currentData())
        )
        lay.addWidget(self.theme_combo)
        self.auto_theme_status = QLabel(
            "Tryb automatyczny mierzy jasność kamery przy uruchomieniu i co 3 minuty. Kamera jest zwalniana między pomiarami."
        )
        self.auto_theme_status.setWordWrap(True)
        self.auto_theme_status.setStyleSheet("color:#aab4ca;")
        lay.addWidget(self.auto_theme_status)
        self.anim_check = QCheckBox("Krótka animacja uruchamiania")
        self.anim_check.setChecked(self.settings.get("animations", True)); lay.addWidget(self.anim_check)
        self.clock_check = QCheckBox("Zegar 24-godzinny")
        self.clock_check.setChecked(self.settings.get("clock_24h", True)); lay.addWidget(self.clock_check)

        lay.addWidget(QLabel("Tło ekranu blokady (logowania)"))
        self.lock_wallpaper_combo = self.make_wallpaper_control(lay, "lock_wallpaper", "lock")
        lay.addWidget(QLabel("Tło ekranu głównego (pulpitu)"))
        self.home_wallpaper_combo = self.make_wallpaper_control(lay, "home_wallpaper", "home")

        category("Dostępność", "◉")
        lay = section("Dostępność")
        lay.addWidget(QLabel("Język interfejsu"))
        self.language_combo = QComboBox()
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("Polski", "pl")
        for language_code, language_name in ADDITIONAL_LANGUAGES:
            self.language_combo.addItem(language_name, language_code)
        language_index = self.language_combo.findData(self.settings.get("language", "en"))
        self.language_combo.setCurrentIndex(language_index if language_index >= 0 else 0)
        self.language_combo.currentIndexChanged.connect(self.change_interface_language)
        lay.addWidget(self.language_combo)
        language_note = QLabel("Dostępnych jest 100 dodatkowych języków. Tłumaczenia interfejsu są obecnie dostępne po angielsku i polsku; pozostałe języki używają angielskiego interfejsu.")
        language_note.setWordWrap(True)
        language_note.setStyleSheet("color:#aab4ca;")
        lay.addWidget(language_note)
        self.high_contrast_check = QCheckBox("Duży kontrast")
        self.high_contrast_check.setChecked(self.settings.get("high_contrast", False))
        self.high_contrast_check.toggled.connect(self.change_high_contrast)
        lay.addWidget(self.high_contrast_check)

        category("Biurko i aplikacje", "▦")
        lay = section("Pulpit i aplikacje")
        lay.addWidget(QLabel("Kolejność aplikacji na pulpicie"))
        app_order_note = QLabel("Zaznacz aplikację i użyj strzałek, aby zmienić jej położenie. Aplikacje ze sklepu możesz tu też odinstalować. Zmiany kolejności zastosują się po naciśnięciu „Zapisz ustawienia” i zapiszą się dla zalogowanego profilu; aplikacje systemowe są chronione.")
        app_order_note.setWordWrap(True)
        app_order_note.setStyleSheet("color:#aab4ca;")
        lay.addWidget(app_order_note)
        app_order_row = QHBoxLayout()
        self.app_order_list = QListWidget()
        self.app_order_list.currentRowChanged.connect(self.update_remove_app_button)
        app_order_row.addWidget(self.app_order_list, 1)
        app_order_buttons = QVBoxLayout()
        move_up = QPushButton("↑  Przenieś wyżej")
        move_up.clicked.connect(lambda: self.move_app_order_item(-1))
        move_down = QPushButton("↓  Przenieś niżej")
        move_down.clicked.connect(lambda: self.move_app_order_item(1))
        self.remove_app_button = QPushButton("Usuń aplikację")
        self.remove_app_button.setStyleSheet("QPushButton { background:#8f3038; }")
        self.remove_app_button.clicked.connect(self.remove_desktop_app)
        app_order_buttons.addWidget(move_up)
        app_order_buttons.addWidget(move_down)
        app_order_buttons.addWidget(self.remove_app_button)
        app_order_buttons.addStretch(1)
        app_order_row.addLayout(app_order_buttons)
        lay.addLayout(app_order_row, 1)
        self.refresh_app_order_list()

        category("Przeglądarka", "◎")
        lay = section("Ustawienia startowe")
        lay.addWidget(QLabel("Adres startowy przeglądarki"))
        self.start_url_input = QLineEdit(self.settings.get("start_url", "https://www.google.com")); lay.addWidget(self.start_url_input)

        category("Użytkownicy i profile", "◉")
        lay = section("Profile")
        profile_settings_note = QLabel("Tapety, ustawienia i zdjęcia Galerii są zapisywane osobno dla każdego profilu. Te ustawienia dotyczą aktualnie zalogowanego profilu.")
        profile_settings_note.setWordWrap(True)
        profile_settings_note.setStyleSheet("color:#aab4ca;")
        lay.addWidget(profile_settings_note)
        lay.addWidget(QLabel("Wybierz profil do edycji"))
        profile_row = QHBoxLayout()
        self.settings_profile_combo = QComboBox()
        profile_row.addWidget(self.settings_profile_combo, 1)
        add_profile_button = QPushButton("Dodaj profil")
        add_profile_button.clicked.connect(self.add_profile)
        profile_row.addWidget(add_profile_button)
        delete_profile_button = QPushButton("Usuń profil")
        delete_profile_button.clicked.connect(self.delete_profile)
        profile_row.addWidget(delete_profile_button)
        lay.addLayout(profile_row)
        self.user_input = QLineEdit(self.username); self.user_input.setPlaceholderText("Nazwa profilu"); lay.addWidget(self.user_input)
        lay.addWidget(QLabel("Zdjęcie profilu"))
        avatar_row = QHBoxLayout()
        self.profile_avatar_preview = QLabel()
        self.profile_avatar_preview.setFixedSize(72, 72)
        self.profile_avatar_preview.setScaledContents(True)
        avatar_row.addWidget(self.profile_avatar_preview)
        choose_avatar = QPushButton("Wybierz zdjęcie z Galerii…")
        choose_avatar.clicked.connect(self.open_profile_picker)
        avatar_row.addWidget(choose_avatar, 1)
        clear_avatar = QPushButton("Usuń zdjęcie")
        clear_avatar.clicked.connect(self.clear_profile_avatar)
        avatar_row.addWidget(clear_avatar)
        lay.addLayout(avatar_row)
        self.pass_input = QLineEdit(); self.pass_input.setPlaceholderText("Nowe hasło (puste = bez zmiany)"); self.pass_input.setEchoMode(QLineEdit.EchoMode.Password); lay.addWidget(self.pass_input)
        self.refresh_profile_lists(self.active_profile_id, self.active_profile_id)
        self.settings_profile_combo.currentIndexChanged.connect(self.load_profile_editor)
        self.load_profile_editor()

        category("Ogólne", "⚙")
        lay = section("System")
        info = QLabel(f"Dane mini-os są przechowywane lokalnie w folderze:\n{ROOT}\n\nPrzeglądarka i aparat mogą wymagać zgody systemu macOS.")
        info.setWordWrap(True); info.setStyleSheet("color:#aab4ca;"); lay.addWidget(info)
        save = QPushButton("Zapisz ustawienia"); save.setObjectName("accent"); save.clicked.connect(self.save_settings); lay.addWidget(save)
        reset = QPushButton("Przywróć ustawienia fabryczne")
        reset.setStyleSheet("QPushButton { background:#8f3038; }")
        reset.clicked.connect(self.factory_reset)
        lay.addWidget(reset)

        category("Aktualizacje", "↻")
        lay = section("Aktualizacje mini-OS")
        self.update_version_label = QLabel(f"Zainstalowana wersja: {APP_NAME} {APP_VERSION}")
        lay.addWidget(self.update_version_label)
        self.update_status_label = QLabel(
            "Automatyczne źródło aktualizacji nie jest skonfigurowane."
        )
        self.update_status_label.setWordWrap(True)
        lay.addWidget(self.update_status_label)
        check_updates = QPushButton("Sprawdź aktualizacje")
        check_updates.clicked.connect(self.check_for_updates)
        lay.addWidget(check_updates)

        category("Informacje", "ⓘ")
        lay = section("Informacje o systemie")
        self.system_info_labels = {}
        for key, caption in (
            ("name", "Nazwa systemu"),
            ("version", "Wersja systemu"),
            ("computer", "Nazwa komputera"),
            ("mini_os", "System"),
            ("saved_at", "Ostatni zapis sesji"),
        ):
            info_row = QHBoxLayout()
            caption_label = QLabel(caption)
            caption_label.setMinimumWidth(190)
            value_label = QLabel("Odczytywanie…")
            value_label.setWordWrap(True)
            value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            info_row.addWidget(caption_label)
            info_row.addWidget(value_label, 1)
            lay.addLayout(info_row)
            self.system_info_labels[key] = value_label
        self.refresh_system_info()

        lay.addStretch(1)
        self.settings_categories.currentRowChanged.connect(self.settings_panel.setCurrentIndex)
        self.settings_categories.currentRowChanged.connect(lambda _row: self.refresh_system_info())
        self.settings_categories.setCurrentRow(0)

    def check_for_updates(self):
        message = "Nie skonfigurowano serwera wydań mini-OS, więc aplikacja nie może automatycznie sprawdzić nowszej wersji."
        self.update_status_label.setProperty("miniOsOriginalText", message)
        self.update_status_label.setText(
            UI_EN_TRANSLATIONS.get(message, message) if self.settings.get("language", "en") == "en" else message
        )

    def refresh_system_info(self):
        labels = getattr(self, "system_info_labels", None)
        if not labels:
            return
        host_os = "macOS" if platform.system() == "Darwin" else platform.system() or "Nieznany"
        system_version = platform.mac_ver()[0] if host_os == "macOS" else platform.release()
        labels["name"].setText(host_os)
        labels["version"].setText(system_version or "Nieznana")
        labels["computer"].setText(platform.node() or "Nieznany")
        labels["mini_os"].setText(f"{APP_NAME} {APP_VERSION}")

        session = read_json(SESSION_FILE, {})
        saved_at = session.get("saved_at") if isinstance(session, dict) else None
        if saved_at:
            try:
                saved_date = datetime.fromisoformat(str(saved_at).replace("Z", "+00:00"))
                if saved_date.tzinfo:
                    saved_date = saved_date.astimezone()
                saved_text = saved_date.strftime("%d.%m.%Y, %H:%M:%S")
            except (TypeError, ValueError):
                saved_text = str(saved_at)
        else:
            saved_text = "Brak zapisanego stanu"
        labels["saved_at"].setText(saved_text)

    def apply_language(self):
        if not hasattr(self, "settings"):
            return
        english = self.settings.get("language", "en") != "pl"
        item_role = int(Qt.ItemDataRole.UserRole) + 50

        def translated(original):
            if not english:
                return original
            if original in UI_EN_TRANSLATIONS:
                return UI_EN_TRANSLATIONS[original]
            if "\n" in original:
                return "\n".join(UI_EN_TRANSLATIONS.get(part, part) for part in original.split("\n"))
            for polish, english_text in UI_EN_TRANSLATIONS.items():
                if original.endswith(polish):
                    return original[:-len(polish)] + english_text
            return original

        for widget in self.findChildren(QWidget):
            if isinstance(widget, QGroupBox):
                original = widget.property("miniOsOriginalText")
                if original is None:
                    original = widget.title()
                    widget.setProperty("miniOsOriginalText", original)
                widget.setTitle(translated(original))
            elif isinstance(widget, (QLabel, QPushButton, QCheckBox)):
                original = widget.property("miniOsOriginalText")
                if original is None:
                    original = widget.text()
                    widget.setProperty("miniOsOriginalText", original)
                widget.setText(translated(original))
            if isinstance(widget, QLineEdit):
                original = widget.property("miniOsOriginalPlaceholder")
                if original is None:
                    original = widget.placeholderText()
                    widget.setProperty("miniOsOriginalPlaceholder", original)
                widget.setPlaceholderText(translated(original))
            if isinstance(widget, QComboBox):
                widget.blockSignals(True)
                for index in range(widget.count()):
                    original = widget.itemData(index, item_role)
                    if original is None:
                        original = widget.itemText(index)
                        widget.setItemData(index, original, item_role)
                    widget.setItemText(index, translated(original))
                widget.blockSignals(False)
            if isinstance(widget, QListWidget):
                for index in range(widget.count()):
                    item = widget.item(index)
                    original = item.data(item_role)
                    if original is None:
                        original = item.text()
                        item.setData(item_role, original)
                    item.setText(translated(original))

    def change_interface_language(self, _index=None):
        if not hasattr(self, "language_combo"):
            return
        self.settings["language"] = self.language_combo.currentData() or "en"
        self.apply_language()

    def change_high_contrast(self, enabled):
        self.settings["high_contrast"] = bool(enabled)
        self.apply_theme()

    def is_light_theme(self):
        mode = self.settings.get("theme", "dark")
        return mode == "light" or (mode == "auto" and self._auto_theme_light)

    def configure_app_color_scheme(self):
        """Set Qt and Chromium to the explicitly resolved mini-OS scheme."""
        light_mode = self.is_light_theme()
        app = QApplication.instance()
        if app is None:
            return light_mode
        try:
            hints = app.styleHints()
            scheme_enum = getattr(Qt, "ColorScheme", None)
            if scheme_enum is not None:
                setter = getattr(hints, "setColorScheme", None)
                if callable(setter):
                    setter(scheme_enum.Light if light_mode else scheme_enum.Dark)
        except (AttributeError, RuntimeError):
            pass
        return light_mode

    def update_theme_mode(self, theme_mode):
        if theme_mode not in {"auto", "light", "dark"}:
            theme_mode = "dark"
        previous_theme_mode = self.settings.get("theme", "dark")
        previous_light_mode = self.is_light_theme()
        if theme_mode == "auto" and previous_theme_mode != "auto":
            self._auto_theme_light = previous_light_mode
        self.settings["theme"] = theme_mode
        light_mode = self.configure_app_color_scheme()
        self.apply_resolved_theme(light_mode)
        if theme_mode == "auto":
            self.start_auto_theme_detection()
        else:
            self.stop_auto_theme_detection()

    def apply_resolved_theme(self, light_mode):
        # Preset wallpapers belong to their matching theme. Keep user-added
        # wallpapers, but replace an incompatible built-in choice with the
        # adaptive default when switching themes.
        dark_wallpaper_files = builtin_wallpaper_filenames()
        for setting_key in ("lock_wallpaper", "home_wallpaper"):
            wallpaper_id = self.settings.get(setting_key, "default")
            is_light_preset = isinstance(wallpaper_id, str) and wallpaper_id.startswith("light:")
            is_dark_preset = (
                isinstance(wallpaper_id, str)
                and wallpaper_id.startswith("custom:")
                and Path(wallpaper_id.split(":", 1)[1]).name in dark_wallpaper_files
            )
            if (light_mode and is_dark_preset) or (not light_mode and is_light_preset):
                self.settings[setting_key] = "default"
        profile = self.profile_by_id(self.active_profile_id)
        if profile:
            profile["settings"] = self.settings.copy()
            self.persist_profiles()
        for control, setting_key in (
            (getattr(self, "lock_wallpaper_combo", None), "lock_wallpaper"),
            (getattr(self, "home_wallpaper_combo", None), "home_wallpaper"),
        ):
            if control is not None:
                self.populate_wallpaper_options(control)
                control.blockSignals(True)
                index = control.findData(self.settings.get(setting_key, "default"))
                control.setCurrentIndex(index if index >= 0 else 0)
                control.blockSignals(False)
        if "login" in self.pages:
            self.pages["login"].set_wallpaper(self.settings.get("lock_wallpaper", "default"))
        if "home" in self.pages:
            self.pages["home"].set_wallpaper(self.settings.get("home_wallpaper", "default"))
        self.apply_theme()
        # Chromium applies ForceDarkMode to the next navigation. Reload the
        # current pages so both the regular browser and installed web apps
        # adopt the newly selected theme immediately.
        for view in (getattr(self, "browser", None), getattr(self, "app_browser", None)):
            if view is not None and view.url().isValid():
                view.reload()

    def start_auto_theme_detection(self):
        if self.settings.get("theme") != "auto":
            return
        if not CAMERA_AVAILABLE:
            if hasattr(self, "auto_theme_status"):
                self.auto_theme_status.setText("Tryb automatyczny wymaga OpenCV i dostępu do kamery.")
            return
        self._auto_theme_candidate = None
        self._auto_theme_candidate_count = 0
        self.auto_theme_timer.start()
        if hasattr(self, "auto_theme_status"):
            self.auto_theme_status.setText("Kamera jest włączana na krótki pomiar przy starcie i co 3 minuty.")
        QTimer.singleShot(500, self.sample_auto_theme_camera)

    def stop_auto_theme_detection(self):
        self.auto_theme_timer.stop()
        self._auto_theme_candidate = None
        self._auto_theme_candidate_count = 0
        if hasattr(self, "auto_theme_status"):
            self.auto_theme_status.setText("Motyw ręczny nie używa kamery do zmiany wyglądu.")

    def sample_auto_theme_camera(self):
        if self.settings.get("theme") != "auto" or not CAMERA_AVAILABLE:
            return
        capture = self.camera if self._camera_preview_active else None
        owns_capture = capture is None
        try:
            if owns_capture:
                capture = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
            if capture is None or not capture.isOpened():
                if hasattr(self, "auto_theme_status"):
                    self.auto_theme_status.setText(
                        "Nie udało się odczytać kamery. Sprawdź zgodę w Ustawieniach systemowych → Prywatność i ochrona → Kamera."
                    )
                return
            # AVFoundation may return a dark startup frame. Read several frames
            # during this brief session and use their average for a stable result.
            brightness_samples = []
            for _ in range(8):
                ok, frame = capture.read()
                if ok and frame is not None:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    brightness_samples.append(float(cv2.mean(gray)[0]))
            if not brightness_samples:
                if hasattr(self, "auto_theme_status"):
                    self.auto_theme_status.setText("Kamera została otwarta, ale nie zwróciła obrazu.")
                return
            brightness = sum(brightness_samples) / len(brightness_samples)
        except Exception as exc:
            if hasattr(self, "auto_theme_status"):
                self.auto_theme_status.setText(f"Błąd odczytu kamery: {exc}")
            return
        finally:
            if owns_capture and capture is not None:
                capture.release()

        current_light = self._auto_theme_light
        target_light = True if brightness >= 132 else False if brightness <= 92 else current_light
        if target_light == current_light:
            self._auto_theme_candidate = None
            self._auto_theme_candidate_count = 0
            if hasattr(self, "auto_theme_status"):
                state = "jasne" if current_light else "ciemne"
                self.auto_theme_status.setText(f"Pomiar kamery: {brightness:.0f}/255 — otoczenie {state}; następny za 3 minuty.")
            return
        self._auto_theme_light = target_light
        self.configure_app_color_scheme()
        self.apply_resolved_theme(target_light)
        state = "jasne" if target_light else "ciemne"
        if hasattr(self, "auto_theme_status"):
            self.auto_theme_status.setText(f"Pomiar kamery: {brightness:.0f}/255 — włączono motyw {state}; następny za 3 minuty.")

    def make_wallpaper_control(self, layout, setting_key, target):
        combo = QComboBox()
        combo.setIconSize(QSize(64, 40))
        self.populate_wallpaper_options(combo)

        saved = self.settings.get(setting_key, "default")
        if isinstance(saved, str) and saved.startswith("custom:"):
            filename = Path(saved.split(":", 1)[1]).name
            if not wallpaper_image_path(filename).is_file():
                saved = "default"
        index = combo.findData(saved)
        combo.setCurrentIndex(index if index >= 0 else 0)

        row = QHBoxLayout()
        row.addWidget(combo, 1)
        upload = QPushButton("Wgraj własne tło z Galerii…")
        upload.clicked.connect(lambda checked=False, key=setting_key, owner=target: self.open_wallpaper_picker(key, owner))
        row.addWidget(upload)
        layout.addLayout(row)
        combo.currentIndexChanged.connect(lambda _index, key=setting_key, control=combo: self.update_wallpaper_setting(key, control))
        return combo

    def populate_wallpaper_options(self, combo):
        """Refresh wallpaper choices and show presets for the active theme only."""
        combo.blockSignals(True)
        combo.clear()
        light_mode = self.is_light_theme()
        combo.addItem("Domyślne tło", "default")
        if light_mode:
            for label, wallpaper_id in LIGHT_BUILTIN_WALLPAPERS:
                combo.addItem(light_wallpaper_icon(wallpaper_id), label, wallpaper_id)
        else:
            for label, wallpaper_id in BUILTIN_WALLPAPERS:
                if wallpaper_id == "default":
                    continue
                filename = Path(wallpaper_id.split(":", 1)[1]).name
                combo.addItem(self.image_icon(WALLPAPERS_DIR / filename), label, wallpaper_id)

        builtin_files = builtin_wallpaper_filenames()
        wallpaper_files = PROFILE_WALLPAPERS_DIR.iterdir() if PROFILE_WALLPAPERS_DIR.is_dir() else []
        custom_fingerprints = set()
        for path in sorted(wallpaper_files, key=lambda item: item.name.lower()):
            if path.is_file() and path.suffix.lower() in WALLPAPER_EXTENSIONS and path.name not in builtin_files:
                fingerprint = image_fingerprint(path)
                if fingerprint and fingerprint in custom_fingerprints:
                    continue
                if fingerprint:
                    custom_fingerprints.add(fingerprint)
                combo.addItem(self.image_icon(path), f"Własne: {path.stem}", f"custom:{path.name}")
        combo.blockSignals(False)

    def update_wallpaper_setting(self, setting_key, combo):
        wallpaper_id = combo.currentData()
        if not wallpaper_id:
            return
        self.settings[setting_key] = wallpaper_id
        active_profile = self.profile_by_id(self.active_profile_id)
        active_profile["settings"] = self.settings.copy()
        self.user = active_profile.copy()
        self.persist_profiles()
        self.apply_wallpapers()

    def make_wallpaper_picker(self):
        w, root = self.page("wallpaper_picker")
        bar = QHBoxLayout()
        back = QPushButton("←  Ustawienia")
        back.clicked.connect(lambda: self.show_page("settings"))
        back.setMaximumWidth(190)
        self.wallpaper_picker_title = QLabel("Galeria mini-OS — wybierz tapetę")
        self.wallpaper_picker_title.setFont(QFont("Arial", 25, QFont.Weight.Bold))
        bar.addWidget(back)
        bar.addWidget(self.wallpaper_picker_title, 1)
        root.addLayout(bar)

        self.wallpaper_picker_list = QListWidget()
        self.configure_thumbnail_grid(self.wallpaper_picker_list)
        self.wallpaper_picker_list.itemClicked.connect(self.select_wallpaper_from_gallery)
        root.addWidget(self.wallpaper_picker_list, 1)

        import_button = QPushButton("Dodaj obraz z komputera…")
        import_button.clicked.connect(self.import_wallpaper_file)
        root.addWidget(import_button)
        self._wallpaper_picker_setting = "home_wallpaper"
        self._wallpaper_picker_target = "home"

    def open_wallpaper_picker(self, setting_key, target):
        self._wallpaper_picker_setting = setting_key
        self._wallpaper_picker_target = target
        screen = "ekran blokady" if target == "lock" else "ekran główny"
        self.wallpaper_picker_title.setText(f"Wybierz tapetę — {screen}")
        self.refresh_wallpaper_picker()
        self.show_page("wallpaper_picker")

    def refresh_wallpaper_picker(self):
        self.wallpaper_picker_list.clear()
        builtin_files = builtin_wallpaper_filenames()
        gallery_images = sorted(
            (path for path in PHOTOS.iterdir()
             if path.is_file() and path.suffix.lower() in WALLPAPER_EXTENSIONS),
            key=lambda item: item.name.lower(),
        ) if PHOTOS.is_dir() else []
        custom_images = sorted(
            (path for path in PROFILE_WALLPAPERS_DIR.iterdir()
             if path.is_file() and path.suffix.lower() in WALLPAPER_EXTENSIONS
             and path.name not in builtin_files),
            key=lambda item: item.name.lower(),
        ) if PROFILE_WALLPAPERS_DIR.is_dir() else []

        # Show gallery originals first, then only distinct user wallpapers.
        images = []
        fingerprints = set()
        for path in gallery_images + custom_images:
            fingerprint = image_fingerprint(path)
            if fingerprint and fingerprint in fingerprints:
                continue
            if fingerprint:
                fingerprints.add(fingerprint)
            images.append(path)

        for path in images:
            icon = self.image_icon(path)
            if icon.isNull():
                continue
            item = QListWidgetItem(icon, path.stem)
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            self.wallpaper_picker_list.addItem(item)

    def select_wallpaper_from_gallery(self, item):
        source = Path(item.data(Qt.ItemDataRole.UserRole))
        if not source.is_file() or QPixmap(str(source)).isNull():
            QMessageBox.warning(self, "Wybór tapety", "Nie można wczytać wybranego obrazu.")
            self.refresh_wallpaper_picker()
            return

        wallpaper_path = source
        if source.resolve().parent != PROFILE_WALLPAPERS_DIR.resolve():
            PROFILE_WALLPAPERS_DIR.mkdir(parents=True, exist_ok=True)
            fingerprint = image_fingerprint(source)
            if not fingerprint:
                QMessageBox.warning(self, "Wybór tapety", "Nie udało się odczytać wybranego obrazu.")
                return
            filename = f"gallery_{fingerprint[:20]}{source.suffix.lower()}"
            wallpaper_path = PROFILE_WALLPAPERS_DIR / filename
            if not wallpaper_path.exists():
                try:
                    shutil.copy2(source, wallpaper_path)
                except OSError as error:
                    QMessageBox.warning(self, "Wybór tapety", f"Nie udało się zapisać tapety:\n{error}")
                    return

        wallpaper_id = f"custom:{wallpaper_path.name}"
        self.add_wallpaper_option(wallpaper_path, f"Własne: {source.stem}", wallpaper_id)
        self.settings[self._wallpaper_picker_setting] = wallpaper_id
        active_profile = self.profile_by_id(self.active_profile_id)
        active_profile["settings"] = self.settings.copy()
        self.user = active_profile.copy()
        self.persist_profiles()
        target_combo = self.lock_wallpaper_combo if self._wallpaper_picker_target == "lock" else self.home_wallpaper_combo
        target_combo.setCurrentIndex(target_combo.findData(wallpaper_id))
        self.apply_wallpapers()
        self.show_page("settings")

    def add_wallpaper_option(self, path, label, wallpaper_id):
        icon = self.image_icon(path)
        for combo in (self.lock_wallpaper_combo, self.home_wallpaper_combo):
            if combo.findData(wallpaper_id) < 0:
                combo.addItem(icon, label, wallpaper_id)

    def refresh_wallpaper_option_icons(self):
        for combo in (self.lock_wallpaper_combo, self.home_wallpaper_combo):
            for index in range(combo.count()):
                wallpaper_id = combo.itemData(index)
                if isinstance(wallpaper_id, str) and wallpaper_id.startswith("custom:"):
                    filename = Path(wallpaper_id.split(":", 1)[1]).name
                    combo.setItemIcon(index, self.image_icon(wallpaper_image_path(filename)))

    def import_wallpaper_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Dodaj obraz do Galerii mini-OS",
            str(Path.home()),
            "Obrazy (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tif *.tiff)",
        )
        if not path:
            return
        if QPixmap(path).isNull():
            QMessageBox.warning(self, "Własne tło", "Nie można wczytać wybranego obrazu.")
            return
        source = Path(path)
        PHOTOS.mkdir(parents=True, exist_ok=True)
        fingerprint = image_fingerprint(source)
        if not fingerprint:
            QMessageBox.warning(self, "Własne tło", "Nie udało się odczytać wybranego obrazu.")
            return
        filename = f"imported_{fingerprint[:20]}{source.suffix.lower()}"
        destination = PHOTOS / filename
        try:
            if not destination.exists():
                shutil.copy2(source, destination)
        except OSError as error:
            QMessageBox.warning(self, "Własne tło", f"Nie udało się zapisać obrazu:\n{error}")
            return
        self.refresh_gallery()
        self.refresh_wallpaper_picker()

    def make_profile_picker(self):
        _page, root = self.page("profile_picker")
        bar = QHBoxLayout()
        back = QPushButton("←  Ustawienia")
        back.setMaximumWidth(190)
        back.clicked.connect(lambda: self.show_page("settings"))
        title = QLabel("Galeria mini-OS — wybierz zdjęcie profilu")
        title.setFont(QFont("Arial", 25, QFont.Weight.Bold))
        bar.addWidget(back)
        bar.addWidget(title, 1)
        root.addLayout(bar)
        self.profile_picker_list = QListWidget()
        self.configure_thumbnail_grid(self.profile_picker_list)
        self.profile_picker_list.itemClicked.connect(self.select_profile_avatar)
        root.addWidget(self.profile_picker_list, 1)
        self.profile_picker_hint = QLabel("Wybierz zdjęcie z Galerii mini-OS.")
        self.profile_picker_hint.setStyleSheet("color:#aab4ca;")
        root.addWidget(self.profile_picker_hint)
        self._profile_picker_profile_id = self.active_profile_id

    def make_profile_crop_page(self):
        _page, root = self.page("profile_crop")
        bar = QHBoxLayout()
        back = QPushButton("←  Galeria")
        back.setMaximumWidth(190)
        back.clicked.connect(lambda: self.show_page("profile_picker"))
        title = QLabel("Dopasuj zdjęcie profilu")
        title.setFont(QFont("Arial", 25, QFont.Weight.Bold))
        bar.addWidget(back)
        bar.addWidget(title, 1)
        root.addLayout(bar)
        root.addStretch(1)

        self.profile_crop_canvas = ProfileCropCanvas(QPixmap())
        root.addWidget(self.profile_crop_canvas, 0, Qt.AlignmentFlag.AlignHCenter)
        hint = QLabel("Przeciągnij obraz, aby go wycentrować")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color:#aab4ca;")
        root.addWidget(hint)

        controls = QHBoxLayout()
        center = QPushButton("Wyśrodkuj")
        center.clicked.connect(self.profile_crop_canvas.center_image)
        rotate_left = QPushButton("↶  Obróć w lewo")
        rotate_right = QPushButton("Obróć w prawo  ↷")
        rotate_left.clicked.connect(lambda: self.profile_crop_canvas.set_rotation(self.profile_crop_canvas.rotation - 90))
        rotate_right.clicked.connect(lambda: self.profile_crop_canvas.set_rotation(self.profile_crop_canvas.rotation + 90))
        controls.addWidget(center)
        controls.addWidget(rotate_left)
        controls.addWidget(rotate_right)
        root.addLayout(controls)

        zoom_row = QHBoxLayout()
        zoom_row.addStretch(1)
        zoom_row.addWidget(QLabel("Powiększenie"))
        self.profile_crop_zoom = QSlider(Qt.Orientation.Horizontal)
        self.profile_crop_zoom.setRange(100, 300)
        self.profile_crop_zoom.setValue(100)
        self.profile_crop_zoom.setMaximumWidth(380)
        self.profile_crop_zoom.valueChanged.connect(self.update_profile_crop_zoom)
        zoom_row.addWidget(self.profile_crop_zoom)
        self.profile_crop_zoom_label = QLabel("100%")
        self.profile_crop_zoom_label.setMinimumWidth(55)
        zoom_row.addWidget(self.profile_crop_zoom_label)
        zoom_row.addStretch(1)
        root.addLayout(zoom_row)

        actions = QHBoxLayout()
        actions.addStretch(1)
        cancel = QPushButton("Anuluj")
        cancel.clicked.connect(lambda: self.show_page("profile_picker"))
        save = QPushButton("Zapisz zdjęcie")
        save.setObjectName("accent")
        save.clicked.connect(self.save_cropped_profile_avatar)
        actions.addWidget(cancel)
        actions.addWidget(save)
        root.addLayout(actions)
        root.addStretch(1)

    def update_profile_crop_zoom(self, value):
        self.profile_crop_canvas.set_zoom(value / 100)
        self.profile_crop_zoom_label.setText(f"{value}%")

    def open_profile_picker(self):
        self._profile_picker_profile_id = self.settings_profile_combo.currentData()
        self.refresh_profile_picker()
        self.show_page("profile_picker")

    def refresh_profile_picker(self):
        self.profile_picker_list.clear()
        photos = sorted(
            (path for path in PHOTOS.iterdir()
             if path.is_file() and path.suffix.lower() in WALLPAPER_EXTENSIONS),
            key=lambda item: item.name.lower(), reverse=True,
        ) if PHOTOS.is_dir() else []
        for path in photos:
            icon = self.image_icon(path)
            if icon.isNull():
                continue
            item = QListWidgetItem(icon, path.stem)
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            self.profile_picker_list.addItem(item)
        self.profile_picker_hint.setText(
            "Kliknij miniaturę, aby ustawić zdjęcie profilu."
            if self.profile_picker_list.count()
            else "Galeria jest pusta. Dodaj zdjęcie w aplikacji Galeria lub Aparat."
        )

    def select_profile_avatar(self, item):
        profile = self.profile_by_id(self._profile_picker_profile_id)
        source = Path(item.data(Qt.ItemDataRole.UserRole))
        if not profile or not source.is_file() or QPixmap(str(source)).isNull():
            QMessageBox.warning(self, "Zdjęcie profilu", "Nie można wczytać wybranego zdjęcia.")
            self.refresh_profile_picker()
            return
        self._profile_crop_profile_id = profile["id"]
        self.profile_crop_canvas.set_image(QPixmap(str(source)))
        self.profile_crop_zoom.setValue(100)
        self.update_profile_crop_zoom(100)
        self.show_page("profile_crop")

    def save_cropped_profile_avatar(self):
        profile = self.profile_by_id(self._profile_crop_profile_id)
        if not profile:
            QMessageBox.warning(self, "Zdjęcie profilu", "Nie znaleziono wybranego profilu.")
            self.show_page("settings")
            return
        PROFILE_AVATARS_DIR.mkdir(parents=True, exist_ok=True)
        avatar_name = f"avatar_{uuid.uuid4().hex}.png"
        destination = PROFILE_AVATARS_DIR / avatar_name
        try:
            if not self.profile_crop_canvas.render_avatar().save(str(destination), "PNG"):
                raise OSError("Nie można zapisać przyciętego obrazu.")
        except OSError as error:
            QMessageBox.warning(self, "Zdjęcie profilu", f"Nie udało się zapisać zdjęcia:\n{error}")
            return
        profile["avatar"] = avatar_name
        self.persist_profiles()
        if profile["id"] == self.active_profile_id:
            self.user = profile.copy()
            write_json(USER_FILE, self.user)
            self.update_profile_identity_widgets()
        self.refresh_profile_lists(self._profile_picker_profile_id, self.active_profile_id)
        self.load_profile_editor()
        self.show_page("settings")

    def clear_profile_avatar(self):
        profile = self.profile_by_id(self.settings_profile_combo.currentData())
        if not profile:
            return
        profile["avatar"] = ""
        self.persist_profiles()
        if profile["id"] == self.active_profile_id:
            self.user = profile.copy()
            write_json(USER_FILE, self.user)
            self.update_profile_identity_widgets()
        self.refresh_profile_lists(profile["id"], self.active_profile_id)
        self.load_profile_editor()

    def apply_wallpapers(self):
        if not hasattr(self, "pages"):
            return
        if "login" in self.pages:
            self.pages["login"].setStyleSheet("background:transparent; QLabel { background:transparent; }")
            self.pages["login"].set_wallpaper(self.settings.get("lock_wallpaper", "default"))
        if "home" in self.pages:
            self.pages["home"].setStyleSheet("background:transparent; QLabel { background:transparent; }")
            self.pages["home"].set_wallpaper(self.settings.get("home_wallpaper", "default"))

    def save_settings(self, silent=False):
        profile_id = self.settings_profile_combo.currentData()
        profile = self.profile_by_id(profile_id)
        if not profile:
            if not silent:
                QMessageBox.warning(self, "Ustawienia", "Wybierz profil do zapisania.")
            return
        new_name = self.user_input.text().strip()
        if not new_name:
            if not silent:
                QMessageBox.information(self, "Ustawienia", "Nazwa profilu nie może być pusta.")
            return
        if any(row["id"] != profile_id and row["username"].casefold() == new_name.casefold() for row in self.profiles):
            if not silent:
                QMessageBox.information(self, "Ustawienia", "Profil o takiej nazwie już istnieje.")
            return
        new_pass = self.pass_input.text()
        profile["username"] = new_name
        profile_settings = {**DEFAULT_SETTINGS, **profile.get("settings", {})}
        profile["settings"] = profile_settings
        if new_pass:
            profile["password"] = new_pass
        self.settings["animations"] = self.anim_check.isChecked()
        self.settings["clock_24h"] = self.clock_check.isChecked()
        self.settings["theme"] = self.theme_combo.currentData() or "dark"
        self.settings["language"] = self.language_combo.currentData() or "en"
        self.settings["high_contrast"] = self.high_contrast_check.isChecked()
        self.settings["start_url"] = self.start_url_input.text().strip() or "https://www.google.com"
        self.settings["app_order"] = [
            self.app_order_list.item(row).data(Qt.ItemDataRole.UserRole)
            for row in range(self.app_order_list.count())
        ]
        active_profile = self.profile_by_id(self.active_profile_id)
        active_profile["settings"] = self.settings.copy()
        self.persist_profiles()
        if profile_id == self.active_profile_id:
            self.user = profile.copy()
            self.username = new_name
            write_json(USER_FILE, self.user)
            self.update_profile_identity_widgets()
            self.refresh_installed_apps()
        self.refresh_profile_lists(profile_id, self.active_profile_id)
        self.pass_input.clear()
        self.apply_theme()
        if not silent:
            QMessageBox.information(self,"Ustawienia","Zapisano ustawienia profilu i systemu. Nowy adres startowy będzie używany po ponownym otwarciu przeglądarki.")

    def make_files(self):
        w, root = self.page("files"); root.addLayout(self.title_row("Moje pliki"))
        self.files_current_directory = profile_user_directories(self.active_profile_id)["root"]
        self.files_clipboard = None
        self.files_path_label = QLabel()
        self.files_path_label.setWordWrap(True)
        self.files_path_label.setStyleSheet("color:#aab4ca;")
        root.addWidget(self.files_path_label)
        self.file_list = QListWidget()
        self.file_list.itemDoubleClicked.connect(self.open_file_list_item)
        self.file_list.currentItemChanged.connect(self.update_files_paint_button)
        root.addWidget(self.file_list,1)

        navigation = QHBoxLayout()
        self.files_parent_button = QPushButton("↑  Folder wyżej")
        self.files_parent_button.clicked.connect(self.files_go_parent)
        self.files_open_button = QPushButton("Otwórz")
        self.files_open_button.clicked.connect(self.open_selected_file)
        refresh = QPushButton("Odśwież")
        refresh.clicked.connect(self.refresh_files)
        new_folder = QPushButton("Nowy folder")
        new_folder.clicked.connect(self.files_create_folder)
        new_file = QPushButton("Utwórz plik")
        new_file.clicked.connect(self.files_create_file)
        import_files = QPushButton("Importuj pliki")
        import_files.clicked.connect(self.files_import)
        for button in (self.files_parent_button, self.files_open_button, refresh,
                       new_folder, new_file, import_files):
            button.setMinimumHeight(42)
            navigation.addWidget(button)
        root.addLayout(navigation)

        actions = QHBoxLayout()
        rename = QPushButton("Zmień nazwę")
        rename.clicked.connect(self.files_rename_selected)
        copy = QPushButton("Kopiuj")
        copy.clicked.connect(lambda checked=False: self.files_set_clipboard("copy"))
        cut = QPushButton("Wytnij")
        cut.clicked.connect(lambda checked=False: self.files_set_clipboard("cut"))
        self.files_paste_button = QPushButton("Wklej")
        self.files_paste_button.clicked.connect(self.files_paste)
        delete = QPushButton("Usuń")
        delete.setStyleSheet("QPushButton { background:#8f3038; }")
        delete.clicked.connect(self.files_delete_selected)
        self.files_paint_button = QPushButton("Otwórz w Paint")
        self.files_paint_button.setEnabled(False)
        self.files_paint_button.clicked.connect(self.open_selected_image_in_paint)
        for button in (rename, copy, cut, self.files_paste_button, delete, self.files_paint_button):
            button.setMinimumHeight(42)
            actions.addWidget(button)
        actions.addStretch(1)
        root.addLayout(actions)
        self.files_status_label = QLabel("Wybierz obraz, aby otworzyć go w Paint; dwukrotne kliknięcie otwiera plik.")
        self.files_status_label.setStyleSheet("color:#aab4ca;")
        root.addWidget(self.files_status_label)
        self.refresh_files()

    def files_path_is_managed(self, path):
        try:
            root_path = ROOT.resolve()
            target = Path(path).resolve()
            return os.path.commonpath((str(root_path), str(target))) == str(root_path)
        except (OSError, ValueError):
            return False

    def files_selected_path(self):
        item = self.file_list.currentItem() if hasattr(self, "file_list") else None
        return Path(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def update_files_paint_button(self, *_args):
        if not hasattr(self, "files_paint_button"):
            return
        path = self.files_selected_path()
        image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tif", ".tiff"}
        self.files_paint_button.setEnabled(
            bool(path and path.is_file() and path.suffix.lower() in image_extensions)
        )

    def files_safe_name(self, name):
        name = name.strip()
        if not name or name in {".", ".."} or "/" in name or "\\" in name:
            QMessageBox.information(self, "Moje pliki", "Podaj nazwę bez ścieżki i separatorów folderów.")
            return None
        return name

    def refresh_files(self):
        if not hasattr(self,"file_list"): return
        self.file_list.clear()
        current = self.files_current_directory
        if not self.files_path_is_managed(current) or not current.is_dir():
            current = ROOT
            self.files_current_directory = current
        self.files_path_label.setText(f"Folder: {current}")
        self.files_parent_button.setEnabled(current != ROOT)
        self.files_paste_button.setEnabled(bool(self.files_clipboard))
        try:
            entries = sorted(current.iterdir(), key=lambda path: (not path.is_dir(), path.name.casefold()))
        except OSError as error:
            QMessageBox.warning(self, "Moje pliki", f"Nie można wyświetlić tego folderu:\n{error}")
            return
        for p in entries:
            if not self.files_path_is_managed(p):
                continue
            if p.is_dir():
                label = "📁  " + p.name
            else:
                suffix = p.suffix.lower()
                icon = "📝" if suffix in {".txt", ".json", ".md", ".csv", ".log", ".py", ".html", ".htm", ".c", ".h", ".cc", ".cpp", ".cxx", ".hpp", ".xml", ".yaml", ".yml", ".ini", ".cfg", ".toml", ".js", ".css"} else "🖼️" if suffix in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tif", ".tiff"} else "📄"
                try:
                    size = p.stat().st_size
                    size_label = f"  ·  {size / 1024:.1f} KB" if size < 1024 * 1024 else f"  ·  {size / (1024 * 1024):.1f} MB"
                except OSError:
                    size_label = ""
                label = f"{icon}  {p.name}{size_label}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, str(p)); self.file_list.addItem(item)
        clipboard = self.files_clipboard
        if clipboard:
            self.files_status_label.setText(f"{clipboard['operation_label']}: {clipboard['path'].name} · wybierz folder i kliknij Wklej.")
        else:
            self.files_status_label.setText("Wybierz obraz i kliknij „Otwórz w Paint”, aby go edytować.")

    def files_go_parent(self):
        current = self.files_current_directory
        if current != ROOT:
            parent = current.parent
            self.files_current_directory = parent if self.files_path_is_managed(parent) else ROOT
            self.refresh_files()

    def open_file_list_item(self, item):
        self.open_file_explorer_path(Path(item.data(Qt.ItemDataRole.UserRole)))

    def open_selected_file(self):
        path = self.files_selected_path()
        if path is None:
            QMessageBox.information(self, "Moje pliki", "Wybierz plik lub folder do otwarcia.")
            return
        self.open_file_explorer_path(path)

    def open_file_explorer_path(self, path):
        if not self.files_path_is_managed(path):
            QMessageBox.warning(self, "Moje pliki", "Można otwierać tylko pliki i foldery przechowywane w mini-OS.")
            return
        if path.is_dir():
            self.files_current_directory = path
            self.refresh_files()
        elif path.is_file():
            image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tif", ".tiff"}
            if path.suffix.lower() in image_extensions:
                pixmap = QPixmap(str(path))
                if pixmap.isNull():
                    QMessageBox.warning(self, "Moje pliki", f"Nie można wyświetlić obrazu:\n{path.name}")
                    return
                self.current_photo_path = path
                self.current_photo_pixmap = pixmap
                self.photo_back_page = "files"
                self.photo_back_button.setText("←  Moje pliki")
                self.photo_delete_button.hide()
                self.photo_title.setText(path.name)
                self.show_page("photo_viewer")
                self.fit_photo_image()
            else:
                self.open_file_in_notepad(path)
        else:
            QMessageBox.information(self, "Moje pliki", "Ten element już nie istnieje. Odśwież listę.")

    def files_create_folder(self):
        name, accepted = QInputDialog.getText(self, "Nowy folder", "Nazwa folderu:")
        if not accepted:
            return
        name = self.files_safe_name(name)
        if name is None:
            return
        destination = self.files_current_directory / name
        if destination.exists():
            QMessageBox.information(self, "Nowy folder", "Element o tej nazwie już istnieje.")
            return
        try:
            destination.mkdir()
        except OSError as error:
            QMessageBox.warning(self, "Nowy folder", f"Nie można utworzyć folderu:\n{error}")
            return
        self.refresh_files()

    def files_create_file(self):
        name, accepted = QInputDialog.getText(
            self,
            "Utwórz plik",
            "Nazwa pliku razem z wybranym rozszerzeniem (np. notatka.txt lub dane.json):",
            text="Nowy plik",
        )
        if not accepted:
            return
        name = self.files_safe_name(name)
        if name is None:
            return
        destination = self.files_current_directory / name
        try:
            with destination.open("xb"):
                pass
        except FileExistsError:
            QMessageBox.information(self, "Utwórz plik", "Plik o tej nazwie już istnieje.")
            return
        except OSError as error:
            QMessageBox.warning(self, "Utwórz plik", f"Nie można utworzyć pliku:\n{error}")
            return
        self.refresh_files()
        self.files_status_label.setText(f"Utworzono pusty plik: {destination.name}")

    def open_selected_image_in_paint(self):
        path = self.files_selected_path()
        if path is None or not self.files_path_is_managed(path) or not path.is_file():
            self.files_status_label.setText("Wybierz obraz z plików mini-OS.")
            return
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            QMessageBox.warning(self, "Paint Studio", f"Nie można otworzyć obrazu:\n{path.name}")
            return
        self.paint_canvas.set_document(pixmap)
        self.refresh_paint_layers()
        self.paint_name_input.setText(path.stem)
        self.paint_status.setText(f"Otwarto obraz z Moich plików: {path.name}")
        self.show_page("paint")

    def files_import(self):
        paths, _selected_filter = QFileDialog.getOpenFileNames(
            self, "Importuj pliki do mini-OS", str(Path.home()), "Wszystkie pliki (*)"
        )
        if not paths:
            return
        failures = []
        for source_name in paths:
            source = Path(source_name)
            try:
                destination = self.files_unique_destination(self.files_current_directory / source.name)
                shutil.copy2(source, destination)
            except OSError as error:
                failures.append(f"{source.name}: {error}")
        self.refresh_files()
        if failures:
            QMessageBox.warning(self, "Import plików", "Nie udało się skopiować niektórych plików:\n" + "\n".join(failures[:8]))

    def files_rename_selected(self):
        source = self.files_selected_path()
        if source is None:
            QMessageBox.information(self, "Zmień nazwę", "Najpierw wybierz plik lub folder.")
            return
        name, accepted = QInputDialog.getText(self, "Zmień nazwę", "Nowa nazwa:", text=source.name)
        if not accepted:
            return
        name = self.files_safe_name(name)
        if name is None or name == source.name:
            return
        destination = source.with_name(name)
        if destination.exists():
            QMessageBox.information(self, "Zmień nazwę", "Element o tej nazwie już istnieje.")
            return
        try:
            source.rename(destination)
        except OSError as error:
            QMessageBox.warning(self, "Zmień nazwę", f"Nie można zmienić nazwy:\n{error}")
            return
        self.refresh_files()

    def files_delete_selected(self):
        path = self.files_selected_path()
        if path is None:
            QMessageBox.information(self, "Usuń", "Najpierw wybierz plik lub folder.")
            return
        kind = "folder i całą jego zawartość" if path.is_dir() else "plik"
        answer = QMessageBox.question(
            self, "Usuń element", f"Czy na pewno usunąć {kind} „{path.name}”?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            if path.is_symlink() or not path.is_dir():
                path.unlink()
            else:
                shutil.rmtree(path)
        except OSError as error:
            QMessageBox.warning(self, "Usuń element", f"Nie można usunąć elementu:\n{error}")
            return
        if self.files_clipboard and self.files_clipboard["path"] == path:
            self.files_clipboard = None
        self.refresh_files()

    def files_set_clipboard(self, operation):
        path = self.files_selected_path()
        if path is None:
            QMessageBox.information(self, "Moje pliki", "Najpierw wybierz plik lub folder.")
            return
        if not self.files_path_is_managed(path):
            QMessageBox.warning(self, "Moje pliki", "Ten element jest poza folderem mini-OS.")
            return
        operation_label = "Skopiowano" if operation == "copy" else "Wycięto"
        self.files_clipboard = {"path": path, "operation": operation, "operation_label": operation_label}
        self.refresh_files()

    def files_unique_destination(self, destination):
        if not destination.exists():
            return destination
        is_directory = destination.is_dir()
        suffix = "" if is_directory else destination.suffix
        base_name = destination.name if is_directory else destination.stem
        for number in range(2, 10000):
            candidate = destination.with_name(f"{base_name} ({number}){suffix}")
            if not candidate.exists():
                return candidate
        raise OSError("Nie można znaleźć wolnej nazwy dla kopiowanego pliku.")

    def files_paste(self):
        clipboard = self.files_clipboard
        if not clipboard:
            return
        source = clipboard["path"]
        if not source.exists() or not self.files_path_is_managed(source):
            QMessageBox.warning(self, "Wklej", "Skopiowany element już nie istnieje.")
            self.files_clipboard = None
            self.refresh_files()
            return
        current = self.files_current_directory.resolve()
        resolved_source = source.resolve()
        if resolved_source.parent == current:
            QMessageBox.information(self, "Wklej", "Ten element znajduje się już w bieżącym folderze.")
            return
        if source.is_dir() and (current == resolved_source or resolved_source in current.parents):
            QMessageBox.information(self, "Wklej", "Nie można wkleić folderu do niego samego ani do jego podfolderu.")
            return
        try:
            destination = self.files_unique_destination(self.files_current_directory / source.name)
            if clipboard["operation"] == "cut":
                shutil.move(str(source), str(destination))
                self.files_clipboard = None
            elif source.is_dir():
                shutil.copytree(source, destination, symlinks=True)
            else:
                shutil.copy2(source, destination, follow_symlinks=False)
        except OSError as error:
            QMessageBox.warning(self, "Wklej", f"Nie można wkleić elementu:\n{error}")
            return
        self.refresh_files()

    def open_file_in_notepad(self, path):
        if self.notepad_open_file(path):
            self.show_page("notepad")

    def make_notepad(self):
        _page, root = self.page("notepad")
        root.addLayout(self.title_row("Notatnik"))
        actions = QHBoxLayout()
        new_button = QPushButton("Nowy")
        new_button.clicked.connect(self.notepad_new)
        open_button = QPushButton("Otwórz plik")
        open_button.clicked.connect(self.notepad_choose_file)
        save_button = QPushButton("Zapisz")
        save_button.setObjectName("accent")
        save_button.clicked.connect(self.notepad_save)
        save_as_button = QPushButton("Zapisz jako…")
        save_as_button.clicked.connect(self.notepad_save_as)
        for button in (new_button, open_button, save_button, save_as_button):
            actions.addWidget(button)
        actions.addStretch(1)
        root.addLayout(actions)

        self.notepad_file_path = None
        self.notepad_is_loading = False
        self.notepad_is_dirty = False
        self.notepad_editor = QTextEdit()
        self.notepad_editor.setAcceptRichText(False)
        self.notepad_editor.setFont(QFont("Menlo", 14))
        self.notepad_editor.setPlaceholderText("Wpisz tekst albo otwórz plik .txt, .json i inne pliki tekstowe…")
        self.notepad_editor.textChanged.connect(self.notepad_text_changed)
        root.addWidget(self.notepad_editor, 1)
        self.notepad_status = QLabel("Nowy dokument · zapis UTF-8")
        self.notepad_status.setStyleSheet("color:#aab4ca;")
        root.addWidget(self.notepad_status)

        for title, shortcut, callback in (
            ("Nowy", QKeySequence.StandardKey.New, self.notepad_new),
            ("Otwórz", QKeySequence.StandardKey.Open, self.notepad_choose_file),
            ("Zapisz", QKeySequence.StandardKey.Save, self.notepad_save),
        ):
            action = QAction(title, self.pages["notepad"])
            action.setShortcut(shortcut)
            action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            action.triggered.connect(callback)
            self.pages["notepad"].addAction(action)

    def notepad_update_status(self):
        if self.notepad_file_path:
            label = str(self.notepad_file_path)
        else:
            label = "Nowy dokument"
        if self.notepad_is_dirty:
            label += "  •  niezapisane zmiany"
        self.notepad_status.setText(f"{label}  ·  UTF-8")

    def notepad_text_changed(self):
        if not self.notepad_is_loading:
            self.notepad_is_dirty = True
            self.notepad_update_status()

    def notepad_confirm_discard(self):
        if not self.notepad_is_dirty:
            return True
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Niezapisane zmiany")
        dialog.setText("Dokument ma niezapisane zmiany. Czy zapisać je przed kontynuowaniem?")
        dialog.setIcon(QMessageBox.Icon.Warning)
        save_button = dialog.addButton("Zapisz", QMessageBox.ButtonRole.AcceptRole)
        discard_button = dialog.addButton("Odrzuć zmiany", QMessageBox.ButtonRole.DestructiveRole)
        dialog.addButton("Anuluj", QMessageBox.ButtonRole.RejectRole)
        dialog.exec()
        if dialog.clickedButton() == save_button:
            return self.notepad_save()
        return dialog.clickedButton() == discard_button

    def notepad_new(self):
        if not self.notepad_confirm_discard():
            return
        self.notepad_is_loading = True
        self.notepad_editor.clear()
        self.notepad_file_path = None
        self.notepad_is_dirty = False
        self.notepad_is_loading = False
        self.notepad_update_status()
        self.notepad_editor.setFocus()

    def notepad_choose_file(self):
        start_dir = str(
            self.notepad_file_path.parent if self.notepad_file_path
            else profile_user_directories(self.active_profile_id)["documents"]
        )
        path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Otwórz plik tekstowy",
            start_dir,
            "Pliki tekstowe i dane (*.txt *.json *.md *.csv *.tsv *.log *.py *.html *.htm *.css *.js *.xml *.yaml *.yml *.ini *.cfg *.toml *.sh *.sql *.svg *.env *.rst *.properties);;Wszystkie pliki (*)",
        )
        if path:
            self.notepad_open_file(path)

    def notepad_open_file(self, path, ask_before_replace=True):
        if ask_before_replace and not self.notepad_confirm_discard():
            return False
        path = Path(path)
        try:
            raw = path.read_bytes()
            has_utf16_bom = raw.startswith((b"\xff\xfe", b"\xfe\xff"))
            if not has_utf16_bom and b"\0" in raw[:8192]:
                raise ValueError("To wygląda na plik binarny, którego Notatnik nie może wyświetlić.")
            try:
                content = raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                content = raw.decode("utf-16") if has_utf16_bom else raw.decode("cp1250")
        except (OSError, UnicodeError, ValueError) as error:
            QMessageBox.warning(self, "Notatnik", f"Nie można otworzyć pliku:\n{error}")
            return False
        self.notepad_is_loading = True
        self.notepad_editor.setPlainText(content)
        self.notepad_file_path = path
        self.notepad_is_dirty = False
        self.notepad_is_loading = False
        self.notepad_update_status()
        self.notepad_editor.setFocus()
        return True

    def notepad_save(self):
        if self.notepad_file_path is None or not self.files_path_is_managed(self.notepad_file_path):
            return self.notepad_save_as()
        try:
            with self.notepad_file_path.open("w", encoding="utf-8", newline="") as text_file:
                text_file.write(self.notepad_editor.toPlainText())
        except OSError as error:
            QMessageBox.warning(self, "Notatnik", f"Nie można zapisać pliku:\n{error}")
            return False
        self.notepad_is_dirty = False
        self.notepad_update_status()
        return True

    def choose_internal_save_path(self, initial_directory, initial_filename, title, default_extension=""):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumSize(620, 480)
        layout = QVBoxLayout(dialog)
        path_label = QLabel()
        path_label.setWordWrap(True)
        layout.addWidget(path_label)
        folder_list = QListWidget()
        layout.addWidget(folder_list, 1)
        filename_label = QLabel("Nazwa pliku:")
        layout.addWidget(filename_label)
        filename_input = QLineEdit(initial_filename)
        layout.addWidget(filename_input)

        current = Path(initial_directory)
        if not self.files_path_is_managed(current) or not current.is_dir():
            current = ROOT
        state = {"directory": current, "path": None}

        navigation = QHBoxLayout()
        up_button = QPushButton("↑  Folder wyżej")
        new_folder_button = QPushButton("Nowy folder")
        cancel_button = QPushButton("Anuluj")
        save_button = QPushButton("Zapisz tutaj")
        save_button.setObjectName("accent")
        navigation.addWidget(up_button)
        navigation.addWidget(new_folder_button)
        navigation.addStretch(1)
        navigation.addWidget(cancel_button)
        navigation.addWidget(save_button)
        layout.addLayout(navigation)

        def refresh_folders():
            directory = state["directory"]
            path_label.setText(f"Folder docelowy: {directory}")
            up_button.setEnabled(directory != ROOT)
            folder_list.clear()
            try:
                folders = sorted(
                    (entry for entry in directory.iterdir()
                     if entry.is_dir() and self.files_path_is_managed(entry)),
                    key=lambda entry: entry.name.casefold(),
                )
            except OSError as error:
                QMessageBox.warning(dialog, "Zapis pliku", f"Nie można wyświetlić folderu:\n{error}")
                return
            for folder in folders:
                item = QListWidgetItem("📁  " + folder.name)
                item.setData(Qt.ItemDataRole.UserRole, str(folder))
                folder_list.addItem(item)
            if not folders:
                path_label.setText(f"Folder docelowy: {directory}\nBrak podfolderów.")

        def open_folder(item):
            folder = Path(item.data(Qt.ItemDataRole.UserRole))
            if folder.is_dir() and self.files_path_is_managed(folder):
                state["directory"] = folder
                refresh_folders()

        def go_up():
            directory = state["directory"]
            if directory != ROOT:
                parent = directory.parent
                state["directory"] = parent if self.files_path_is_managed(parent) else ROOT
                refresh_folders()

        def create_folder():
            folder_name, accepted = QInputDialog.getText(dialog, "Nowy folder", "Nazwa folderu:")
            if not accepted:
                return
            folder_name = folder_name.strip()
            if not folder_name or folder_name in {".", ".."} or "/" in folder_name or "\\" in folder_name:
                QMessageBox.information(dialog, "Nowy folder", "Podaj nazwę folderu bez separatorów ścieżki.")
                return
            target = state["directory"] / folder_name
            try:
                target.mkdir()
            except FileExistsError:
                QMessageBox.information(dialog, "Nowy folder", "Folder o tej nazwie już istnieje.")
            except OSError as error:
                QMessageBox.warning(dialog, "Nowy folder", f"Nie można utworzyć folderu:\n{error}")
            else:
                refresh_folders()

        def accept_save():
            filename = filename_input.text().strip()
            if (not filename or filename in {".", ".."} or "/" in filename
                    or "\\" in filename or Path(filename).name != filename):
                QMessageBox.information(dialog, "Zapis pliku", "Podaj poprawną nazwę pliku.")
                return
            if default_extension and not Path(filename).suffix:
                filename += default_extension
            target = state["directory"] / filename
            if target.is_dir():
                QMessageBox.information(dialog, "Zapis pliku", "Ta nazwa wskazuje na istniejący folder.")
                return
            if target.exists():
                answer = QMessageBox.question(
                    dialog, "Zastąpić plik?", f"Plik „{filename}” już istnieje. Czy go zastąpić?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if answer != QMessageBox.StandardButton.Yes:
                    return
            state["path"] = target
            dialog.accept()

        folder_list.itemDoubleClicked.connect(open_folder)
        up_button.clicked.connect(go_up)
        new_folder_button.clicked.connect(create_folder)
        cancel_button.clicked.connect(dialog.reject)
        save_button.clicked.connect(accept_save)
        refresh_folders()
        filename_input.setFocus()
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return False
        return state["path"]

    def notepad_save_as(self):
        filename = self.notepad_file_path.name if self.notepad_file_path else "Nowy plik.txt"
        if self.notepad_file_path and self.files_path_is_managed(self.notepad_file_path):
            start_directory = self.notepad_file_path.parent
        else:
            start_directory = profile_user_directories(self.active_profile_id)["documents"]
        path = self.choose_internal_save_path(
            start_directory, filename, "Zapisz Notatnik wewnątrz mini-OS", ".txt"
        )
        if not path:
            return False
        previous_path = self.notepad_file_path
        self.notepad_file_path = path
        if self.notepad_save():
            return True
        self.notepad_file_path = previous_path
        self.notepad_update_status()
        return False

    def make_session(self):
        w, root = self.page("session"); root.addLayout(self.title_row("Sesja"))
        panel = QFrame(); panel.setObjectName("panel")
        lay = QVBoxLayout(panel); lay.setContentsMargins(30,30,30,30); lay.setSpacing(18)
        label = QLabel("💾  Zapisywanie sesji"); label.setFont(QFont("Arial",26,QFont.Weight.Bold))
        self.session_status = QLabel("Twoja sesja jest zapisywana automatycznie przy zamykaniu aplikacji.")
        self.session_status.setWordWrap(True)
        self.session_details = QLabel("")
        save = QPushButton("Zapisz sesję teraz"); save.setObjectName("accent"); save.clicked.connect(self.save_session)
        restore = QPushButton("Pokaż ostatnią zapisaną sesję"); restore.clicked.connect(self.show_session_details)
        lay.addWidget(label); lay.addWidget(self.session_status); lay.addWidget(self.session_details); lay.addWidget(save); lay.addWidget(restore)
        root.addWidget(panel); root.addStretch(1)
        self.show_session_details()

    def show_session_details(self):
        self.session = read_json(SESSION_FILE,{})
        if self.session:
            self.session_details.setText(f"Ostatni zapis: {self.session.get('saved_at','brak danych')}\nOstatnia aplikacja: {self.session.get('last_app','pulpit')}\nUżytkownik: {self.session.get('username','Użytkownik')}")
        else:
            self.session_details.setText("Nie ma jeszcze zapisanej sesji.")

    def make_gallery(self):
        w, root = self.page("gallery"); root.addLayout(self.title_row("Galeria"))
        self.gallery_list = QListWidget()
        self.configure_thumbnail_grid(self.gallery_list)
        self.gallery_list.itemClicked.connect(self.gallery_open)
        root.addWidget(self.gallery_list,1)
        row = QHBoxLayout()
        refresh = QPushButton("Odśwież zdjęcia"); refresh.clicked.connect(self.refresh_gallery)
        open_photos = QPushButton("Otwórz folder zdjęć"); open_photos.clicked.connect(lambda: self.open_path(PHOTOS))
        row.addWidget(refresh); row.addWidget(open_photos); root.addLayout(row)
        self.refresh_gallery()

    def make_photo_viewer(self):
        w, root = self.page("photo_viewer")
        bar = QHBoxLayout()
        back = QPushButton("←  Galeria")
        back.clicked.connect(self.close_photo_viewer)
        back.setMaximumWidth(170)
        self.photo_back_button = back
        start = QPushButton("☰  Start")
        start.clicked.connect(self.open_start_menu)
        self.photo_title = QLabel("Zdjęcie")
        self.photo_title.setFont(QFont("Arial", 25, QFont.Weight.Bold))
        bar.addWidget(back)
        bar.addWidget(start)
        bar.addWidget(self.photo_title, 1)
        root.addLayout(bar)

        self.photo_image_label = QLabel("Wybierz zdjęcie w Galerii.")
        self.photo_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_image_label.setMinimumSize(1, 1)
        self.photo_image_label.setStyleSheet("background:#080a0f; border-radius:16px; color:#aab4ca;")
        root.addWidget(self.photo_image_label, 1)

        actions = QHBoxLayout()
        delete = QPushButton("Usuń zdjęcie")
        delete.setStyleSheet("QPushButton { background:#8f3038; }")
        delete.clicked.connect(self.delete_current_photo)
        self.photo_delete_button = delete
        actions.addStretch(1)
        actions.addWidget(delete)
        root.addLayout(actions)
        self.current_photo_path = None
        self.current_photo_pixmap = QPixmap()
        self.photo_back_page = "gallery"

    def close_photo_viewer(self):
        destination = self.photo_back_page if self.photo_back_page in self.pages else "gallery"
        self.show_page(destination)

    def refresh_gallery(self):
        if not hasattr(self,"gallery_list"): return
        self.gallery_list.clear()
        image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tif", ".tiff"}
        for p in sorted((path for path in PHOTOS.iterdir() if path.is_file() and path.suffix.lower() in image_extensions), reverse=True):
            item = QListWidgetItem(self.image_icon(p), p.name)
            item.setData(Qt.ItemDataRole.UserRole,str(p))
            self.gallery_list.addItem(item)

    def configure_thumbnail_grid(self, widget):
        widget.setViewMode(QListView.ViewMode.IconMode)
        widget.setFlow(QListView.Flow.LeftToRight)
        widget.setMovement(QListView.Movement.Static)
        widget.setResizeMode(QListView.ResizeMode.Adjust)
        widget.setWrapping(True)
        widget.setWordWrap(True)
        widget.setIconSize(QSize(160, 90))
        widget.setGridSize(QSize(190, 132))
        widget.setSpacing(8)

    def image_icon(self, path):
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            return QIcon()
        thumbnail_size = QSize(160, 90)
        scaled = pixmap.scaled(
            thumbnail_size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        x = max(0, (scaled.width() - thumbnail_size.width()) // 2)
        y = max(0, (scaled.height() - thumbnail_size.height()) // 2)
        return QIcon(scaled.copy(x, y, thumbnail_size.width(), thumbnail_size.height()))

    def gallery_open(self,item):
        path = Path(item.data(Qt.ItemDataRole.UserRole))
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            QMessageBox.warning(self, "Nie można otworzyć zdjęcia", f"Plik nie jest prawidłowym lub obsługiwanym obrazem:\n{path.name}")
            return
        self.current_photo_path = path
        self.current_photo_pixmap = pixmap
        self.photo_back_page = "gallery"
        self.photo_back_button.setText("←  Galeria")
        self.photo_delete_button.show()
        self.photo_title.setText(path.name)
        self.show_page("photo_viewer")
        self.fit_photo_image()

    def fit_photo_image(self):
        if self.current_photo_pixmap and not self.current_photo_pixmap.isNull():
            size = self.photo_image_label.size()
            if not size.isEmpty():
                self.photo_image_label.setPixmap(self.current_photo_pixmap.scaled(
                    size, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))

    def delete_current_photo(self):
        path = self.current_photo_path
        return_page = self.photo_back_page if self.photo_back_page in self.pages else "gallery"
        if path is None or not path.is_file():
            QMessageBox.information(self, "Galeria", "Nie znaleziono zdjęcia do usunięcia.")
            self.show_page(return_page)
            return
        answer = QMessageBox.question(
            self, "Usuń zdjęcie", f"Czy na pewno usunąć zdjęcie „{path.name}”?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            path.unlink()
        except OSError as error:
            QMessageBox.warning(self, "Nie można usunąć zdjęcia", str(error))
            return
        self.current_photo_path = None
        self.current_photo_pixmap = QPixmap()
        self.photo_image_label.clear()
        self.refresh_gallery()
        self.show_page(return_page)

    def open_path(self,path):
        import subprocess
        subprocess.Popen(["open", str(path)])

    def make_calculator(self):
        w, root = self.page("calculator"); root.addLayout(self.title_row("Kalkulator"))
        self.calc_display = QLineEdit(); self.calc_display.setPlaceholderText("Wpisz działanie, np. (12 + 8) / 2"); self.calc_display.setMinimumHeight(60); root.addWidget(self.calc_display)
        grid = QGridLayout(); keys = ["7","8","9","÷","4","5","6","×","1","2","3","−","0",".","(",")","+","=","C"]
        for i,k in enumerate(keys):
            b = QPushButton(k); b.setMinimumHeight(65); b.clicked.connect(lambda checked=False, key=k:self.calc_key(key))
            grid.addWidget(b,i//4,i%4)
        root.addLayout(grid); root.addStretch(1)

    def calc_key(self,key):
        if key == "C": self.calc_display.clear(); return
        if key == "=":
            expr = self.calc_display.text().replace("×","*").replace("÷","/").replace("−","-")
            if any(c not in "0123456789.+-*/() " for c in expr):
                self.calc_display.setText("Nieprawidłowe działanie"); return
            try: self.calc_display.setText(str(eval(expr, {"__builtins__":{}}, {})))
            except Exception: self.calc_display.setText("Błąd")
            return
        self.calc_display.setText(self.calc_display.text()+key)

    def make_paint(self):
        _page, root = self.page("paint")
        _page.setStyleSheet("""
            QPushButton { padding: 7px 10px; font-size: 14px; min-height: 22px; border-radius: 10px; }
            QPushButton:hover { background: #303b51; }
            QPushButton:checked { background: #40577e; border: 1px solid #8caeff; }
            QPushButton#accent { background: #5b8cff; color: white; border: 0; font-weight: 600; }
            QLineEdit { padding: 7px 10px; font-size: 14px; }
        """)
        title_bar = QHBoxLayout()
        back = QPushButton("←  Pulpit")
        back.setMaximumWidth(150)
        back.clicked.connect(lambda: self.show_page("home"))
        title = QLabel("Paint Studio")
        title.setFont(QFont("Arial", 25, QFont.Weight.Bold))
        self.paint_name_input = QLineEdit("mój_rysunek")
        self.paint_name_input.setPlaceholderText("Nazwa rysunku")
        self.paint_name_input.setMaximumWidth(250)
        save = QPushButton("Zapisz…")
        save.setObjectName("accent")
        self.paint_save_menu = QMenu(save)
        gallery_save_action = self.paint_save_menu.addAction("Zapisz w Galerii")
        gallery_save_action.triggered.connect(self.save_paint_to_gallery)
        files_save_action = self.paint_save_menu.addAction("Zapisz w Plikach…")
        files_save_action.triggered.connect(self.save_paint_to_files)
        save.setMenu(self.paint_save_menu)
        self.paint_save_button = save
        title_bar.addWidget(back)
        title_bar.addWidget(title, 1)
        title_bar.addWidget(QLabel("Plik"))
        title_bar.addWidget(self.paint_name_input)
        title_bar.addWidget(save)
        root.addLayout(title_bar)

        actions = QHBoxLayout()
        new_button = QPushButton("Nowy")
        new_button.clicked.connect(self.new_paint_document)
        open_button = QPushButton("Otwórz z Galerii")
        open_button.clicked.connect(self.open_paint_gallery)
        undo_button = QPushButton("↶  Cofnij")
        undo_button.clicked.connect(self.paint_canvas_undo)
        redo_button = QPushButton("Ponów  ↷")
        redo_button.clicked.connect(self.paint_canvas_redo)
        actions.addWidget(new_button)
        actions.addWidget(open_button)
        actions.addWidget(undo_button)
        actions.addWidget(redo_button)
        actions.addStretch(1)
        actions.addWidget(QLabel("Powiększenie"))
        self.paint_zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.paint_zoom_slider.setRange(25, 150)
        self.paint_zoom_slider.setValue(62)
        self.paint_zoom_slider.setMaximumWidth(220)
        self.paint_zoom_slider.valueChanged.connect(self.update_paint_zoom)
        actions.addWidget(self.paint_zoom_slider)
        self.paint_zoom_label = QLabel("62%")
        self.paint_zoom_label.setMinimumWidth(48)
        actions.addWidget(self.paint_zoom_label)
        root.addLayout(actions)

        workspace = QHBoxLayout()
        workspace.setSpacing(10)
        tool_panel = QFrame()
        tool_panel.setObjectName("panel")
        tool_panel.setFixedWidth(132)
        tools_layout = QVBoxLayout(tool_panel)
        tools_layout.setContentsMargins(9, 12, 9, 12)
        tools_layout.setSpacing(7)
        tools_layout.addWidget(QLabel("NARZĘDZIA"))
        self.paint_canvas = PaintCanvas()
        self.paint_tool_buttons = {}
        tools = [
            ("brush", "🖌", "Pędzel"), ("pencil", "✎", "Ołówek"),
            ("eraser", "▱", "Gumka"), ("line", "╱", "Linia"),
            ("rectangle", "▪", "Kwadrat / prostokąt"), ("ellipse", "○", "Elipsa"),
            ("select_rectangle", "▧", "Zaznaczenie prostokątne"),
            ("select_ellipse", "◌", "Zaznaczenie eliptyczne"),
        ]
        tool_grid = QGridLayout()
        tool_grid.setSpacing(6)
        for index, (tool, symbol, label) in enumerate(tools):
            button = QPushButton(symbol)
            button.setToolTip(label)
            button.setAccessibleName(label)
            button.setCheckable(True)
            button.setFixedSize(48, 44)
            button.setStyleSheet("QPushButton { padding: 0; min-height: 0; font-size: 23px; border-radius: 10px; } QPushButton:checked { background:#40577e; border:1px solid #8caeff; }")
            button.setChecked(tool == "brush")
            button.clicked.connect(lambda checked=False, value=tool: self.set_paint_tool(value))
            self.paint_tool_buttons[tool] = button
            tool_grid.addWidget(button, index // 2, index % 2)
        tools_layout.addLayout(tool_grid)
        tools_layout.addWidget(QLabel("ZAZNACZENIE"))
        selection_actions = QGridLayout()
        for index, (symbol, label, callback) in enumerate((
            ("⧉", "Kopiuj", self.paint_copy_selection),
            ("✂", "Wytnij", self.paint_cut_selection),
            ("▣", "Wklej", self.paint_paste_selection),
            ("⌫", "Usuń", self.paint_delete_selection),
        )):
            action = QPushButton(symbol)
            action.setToolTip(label)
            action.setAccessibleName(label)
            action.setFixedSize(48, 36)
            action.setStyleSheet("QPushButton { padding: 0; min-height: 0; font-size: 19px; border-radius: 9px; }")
            action.clicked.connect(callback)
            selection_actions.addWidget(action, index // 2, index % 2)
        deselect = QPushButton("×")
        deselect.setToolTip("Odznacz")
        deselect.setAccessibleName("Odznacz")
        deselect.setFixedHeight(34)
        deselect.setStyleSheet("QPushButton { padding: 0; min-height: 0; font-size: 20px; border-radius: 9px; }")
        deselect.clicked.connect(self.paint_clear_selection)
        selection_actions.addWidget(deselect, 2, 0, 1, 2)
        tools_layout.addLayout(selection_actions)
        tools_layout.addStretch(1)
        self.paint_status = QLabel("Gotowe — wybierz narzędzie i rysuj.")
        self.paint_status.setWordWrap(True)
        self.paint_status.setStyleSheet("color:#aab4ca; font-size:13px;")
        tools_layout.addWidget(self.paint_status)
        workspace.addWidget(tool_panel)

        self.paint_scroll = QScrollArea()
        self.paint_scroll.setWidgetResizable(False)
        self.paint_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.paint_scroll.setStyleSheet("QScrollArea { background:#0b0e15; border:1px solid #30394d; border-radius:16px; }")
        self.paint_scroll.setWidget(self.paint_canvas)
        workspace.addWidget(self.paint_scroll, 1)

        properties = QFrame()
        properties.setObjectName("panel")
        properties.setFixedWidth(190)
        props = QVBoxLayout(properties)
        props.addWidget(QLabel("USTAWIENIA"))
        props.addWidget(QLabel("Rozmiar narzędzia"))
        self.paint_size_label = QLabel("8 px")
        props.addWidget(self.paint_size_label)
        self.paint_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.paint_size_slider.setRange(1, 80)
        self.paint_size_slider.setValue(8)
        self.paint_size_slider.valueChanged.connect(self.update_paint_brush_size)
        props.addWidget(self.paint_size_slider)
        self.paint_fill_check = QCheckBox("Wypełnij kształty")
        self.paint_fill_check.toggled.connect(self.paint_canvas.set_fill_shapes)
        props.addWidget(self.paint_fill_check)
        props.addSpacing(12)
        props.addWidget(QLabel("Kolor"))
        self.paint_color_preview = QLabel("   ")
        self.paint_color_preview.setFixedHeight(32)
        self.paint_color_preview.setStyleSheet("background:#202634; border:1px solid #76829b; border-radius:8px;")
        props.addWidget(self.paint_color_preview)
        self.paint_hex_input = QLineEdit("#202634")
        self.paint_hex_input.setPlaceholderText("#RRGGBB")
        self.paint_hex_input.editingFinished.connect(self.apply_paint_hex_color)
        props.addWidget(self.paint_hex_input)
        props.addWidget(QLabel("Paleta"))
        palette = [
            "#111827", "#ffffff", "#ef4444", "#f97316", "#f59e0b", "#eab308",
            "#84cc16", "#22c55e", "#14b8a6", "#06b6d4", "#3b82f6", "#6366f1",
            "#8b5cf6", "#d946ef", "#ec4899", "#a16207", "#64748b", "#000000",
        ]
        palette_grid = QGridLayout()
        palette_grid.setSpacing(6)
        for index, color in enumerate(palette):
            swatch = QPushButton()
            swatch.setFixedSize(34, 34)
            swatch.setToolTip(color)
            swatch.setStyleSheet(f"QPushButton {{ background:{color}; border:1px solid #7d879b; border-radius:8px; padding:0; }} QPushButton:hover {{ border:2px solid white; }}")
            swatch.clicked.connect(lambda checked=False, value=color: self.set_paint_color(value))
            palette_grid.addWidget(swatch, index // 4, index % 4)
        props.addLayout(palette_grid)
        props.addStretch(1)
        workspace.addWidget(properties)

        layer_panel = QFrame()
        layer_panel.setObjectName("panel")
        layer_panel.setFixedWidth(190)
        layer_layout = QVBoxLayout(layer_panel)
        layer_layout.addWidget(QLabel("WARSTWY"))
        self.paint_layer_list = QListWidget()
        self.paint_layer_list.setMinimumHeight(160)
        self.paint_layer_list.setMaximumHeight(250)
        self.paint_layer_list.currentRowChanged.connect(self.paint_select_layer_row)
        self.paint_layer_list.itemChanged.connect(self.paint_layer_visibility_changed)
        layer_layout.addWidget(self.paint_layer_list, 1)
        layer_buttons = QGridLayout()
        add_layer = QPushButton("＋  Nowa")
        add_layer.clicked.connect(self.paint_add_layer)
        remove_layer = QPushButton("−  Usuń")
        remove_layer.clicked.connect(self.paint_remove_layer)
        layer_up = QPushButton("↑")
        layer_up.setToolTip("Przenieś warstwę wyżej")
        layer_up.clicked.connect(lambda: self.paint_move_layer(1))
        layer_down = QPushButton("↓")
        layer_down.setToolTip("Przenieś warstwę niżej")
        layer_down.clicked.connect(lambda: self.paint_move_layer(-1))
        layer_buttons.addWidget(add_layer, 0, 0)
        layer_buttons.addWidget(remove_layer, 0, 1)
        layer_buttons.addWidget(layer_up, 1, 0)
        layer_buttons.addWidget(layer_down, 1, 1)
        layer_layout.addLayout(layer_buttons)
        self.paint_layer_name = QLineEdit()
        self.paint_layer_name.setPlaceholderText("Nazwa warstwy")
        layer_layout.addWidget(self.paint_layer_name)
        rename_layer = QPushButton("Zmień nazwę")
        rename_layer.clicked.connect(self.paint_rename_layer)
        layer_layout.addWidget(rename_layer)
        layer_layout.addWidget(QLabel("Krycie warstwy"))
        self.paint_layer_opacity_label = QLabel("100%")
        layer_layout.addWidget(self.paint_layer_opacity_label)
        self.paint_layer_opacity = QSlider(Qt.Orientation.Horizontal)
        self.paint_layer_opacity.setRange(0, 100)
        self.paint_layer_opacity.setValue(100)
        self.paint_layer_opacity.valueChanged.connect(self.paint_set_layer_opacity)
        layer_layout.addWidget(self.paint_layer_opacity)
        workspace.addWidget(layer_panel)
        root.addLayout(workspace, 1)
        self.refresh_paint_layers()

        self.paint_shortcuts = []
        for shortcut, callback in (
            (QKeySequence.StandardKey.Undo, self.paint_canvas_undo),
            (QKeySequence.StandardKey.Redo, self.paint_canvas_redo),
            (QKeySequence.StandardKey.Save, self.show_paint_save_menu),
            (QKeySequence.StandardKey.Open, self.open_paint_gallery),
            (QKeySequence.StandardKey.Copy, self.paint_copy_selection),
            (QKeySequence.StandardKey.Cut, self.paint_cut_selection),
            (QKeySequence.StandardKey.Paste, self.paint_paste_selection),
            (QKeySequence("Delete"), self.paint_delete_selection),
        ):
            action = QAction(self)
            action.setShortcut(QKeySequence(shortcut))
            action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            action.triggered.connect(callback)
            self.pages["paint"].addAction(action)
            self.paint_shortcuts.append(action)

    def make_paint_gallery(self):
        _page, root = self.page("paint_gallery")
        bar = QHBoxLayout()
        back = QPushButton("←  Paint")
        back.setMaximumWidth(170)
        back.clicked.connect(lambda: self.show_page("paint"))
        title = QLabel("Otwórz rysunek z Galerii")
        title.setFont(QFont("Arial", 25, QFont.Weight.Bold))
        bar.addWidget(back)
        bar.addWidget(title, 1)
        root.addLayout(bar)
        self.paint_gallery_list = QListWidget()
        self.configure_thumbnail_grid(self.paint_gallery_list)
        self.paint_gallery_list.itemClicked.connect(self.open_paint_gallery_item)
        root.addWidget(self.paint_gallery_list, 1)
        self.paint_gallery_hint = QLabel("Wybierz miniaturę, aby otworzyć obraz w Paint Studio.")
        self.paint_gallery_hint.setStyleSheet("color:#aab4ca;")
        root.addWidget(self.paint_gallery_hint)

    def refresh_paint_gallery(self):
        self.paint_gallery_list.clear()
        photos = sorted(
            (path for path in PHOTOS.iterdir()
             if path.is_file() and path.suffix.lower() in WALLPAPER_EXTENSIONS),
            key=lambda item: item.stat().st_mtime, reverse=True,
        ) if PHOTOS.is_dir() else []
        for path in photos:
            icon = self.image_icon(path)
            if icon.isNull():
                continue
            item = QListWidgetItem(icon, path.stem)
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            self.paint_gallery_list.addItem(item)
        if hasattr(self, "paint_gallery_hint"):
            self.paint_gallery_hint.setText(
                "Wybierz miniaturę, aby otworzyć obraz w Paint Studio."
                if self.paint_gallery_list.count()
                else "Galeria jest pusta. Zapisz rysunek lub dodaj zdjęcie w mini-OS."
            )

    def open_paint_gallery(self):
        self.refresh_paint_gallery()
        self.show_page("paint_gallery")

    def open_paint_gallery_item(self, item):
        source = Path(item.data(Qt.ItemDataRole.UserRole))
        pixmap = QPixmap(str(source))
        if pixmap.isNull():
            self.paint_status.setText("Nie można otworzyć wybranego obrazu.")
            self.refresh_paint_gallery()
            return
        self.paint_canvas.set_document(pixmap)
        self.refresh_paint_layers()
        self.paint_name_input.setText(source.stem)
        self.paint_status.setText(f"Otwarto: {source.name}")
        self.show_page("paint")

    def refresh_paint_layers(self):
        if not hasattr(self, "paint_layer_list"):
            return
        widget = self.paint_layer_list
        widget.blockSignals(True)
        widget.clear()
        for index in range(len(self.paint_canvas.layers) - 1, -1, -1):
            layer = self.paint_canvas.layers[index]
            item = QListWidgetItem(layer["name"])
            item.setData(Qt.ItemDataRole.UserRole, index)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if layer["visible"] else Qt.CheckState.Unchecked)
            widget.addItem(item)
        active_row = len(self.paint_canvas.layers) - 1 - self.paint_canvas.active_layer_index
        widget.setCurrentRow(active_row)
        widget.blockSignals(False)
        self.paint_layer_name.setText(self.paint_canvas.layers[self.paint_canvas.active_layer_index]["name"])
        self.paint_layer_opacity.blockSignals(True)
        opacity = self.paint_canvas.layers[self.paint_canvas.active_layer_index]["opacity"]
        self.paint_layer_opacity.setValue(opacity)
        self.paint_layer_opacity_label.setText(f"{opacity}%")
        self.paint_layer_opacity.blockSignals(False)

    def paint_select_layer_row(self, row):
        if row < 0:
            return
        item = self.paint_layer_list.item(row)
        if item is None:
            return
        index = item.data(Qt.ItemDataRole.UserRole)
        self.paint_canvas.set_active_layer(index)
        self.paint_layer_name.setText(self.paint_canvas.layers[index]["name"])
        opacity = self.paint_canvas.layers[index]["opacity"]
        self.paint_layer_opacity.blockSignals(True)
        self.paint_layer_opacity.setValue(opacity)
        self.paint_layer_opacity_label.setText(f"{opacity}%")
        self.paint_layer_opacity.blockSignals(False)

    def paint_layer_visibility_changed(self, item):
        index = item.data(Qt.ItemDataRole.UserRole)
        visible = item.checkState() == Qt.CheckState.Checked
        self.paint_canvas.set_layer_visible(index, visible)
        self.paint_status.setText("Warstwa widoczna." if visible else "Warstwa ukryta.")

    def paint_add_layer(self):
        index = self.paint_canvas.add_layer()
        self.refresh_paint_layers()
        self.paint_layer_name.setText(self.paint_canvas.layers[index]["name"])
        self.paint_status.setText("Dodano nową przezroczystą warstwę.")

    def paint_remove_layer(self):
        if not self.paint_canvas.remove_active_layer():
            self.paint_status.setText("Dokument musi mieć co najmniej jedną warstwę.")
            return
        self.refresh_paint_layers()
        self.paint_status.setText("Usunięto warstwę.")

    def paint_move_layer(self, direction):
        if self.paint_canvas.move_active_layer(direction):
            self.refresh_paint_layers()
            self.paint_status.setText("Zmieniono kolejność warstw.")

    def paint_rename_layer(self):
        name = self.paint_layer_name.text().strip()
        if not name:
            self.paint_status.setText("Wpisz nazwę warstwy.")
            return
        layer = self.paint_canvas.layers[self.paint_canvas.active_layer_index]
        layer["name"] = name
        self.refresh_paint_layers()
        self.paint_status.setText(f"Zmieniono nazwę warstwy na: {name}")

    def paint_set_layer_opacity(self, value):
        self.paint_canvas.set_layer_opacity(self.paint_canvas.active_layer_index, value)
        self.paint_layer_opacity_label.setText(f"{value}%")

    def paint_copy_selection(self):
        self.paint_status.setText(
            "Skopiowano zaznaczenie." if self.paint_canvas.copy_selection()
            else "Najpierw zaznacz fragment obrazu."
        )

    def paint_cut_selection(self):
        self.paint_status.setText(
            "Wycięto zaznaczenie." if self.paint_canvas.cut_selection()
            else "Najpierw zaznacz fragment obrazu."
        )

    def paint_paste_selection(self):
        self.paint_status.setText(
            "Wklejono zaznaczenie na aktywną warstwę." if self.paint_canvas.paste_selection()
            else "Schowek jest pusty. Skopiuj lub wytnij zaznaczenie."
        )

    def paint_delete_selection(self):
        self.paint_status.setText(
            "Usunięto zaznaczenie." if self.paint_canvas.delete_selection()
            else "Najpierw zaznacz fragment obrazu."
        )

    def paint_clear_selection(self):
        self.paint_canvas.clear_selection()
        self.paint_canvas.update()
        self.paint_status.setText("Usunięto obrys zaznaczenia.")

    def set_paint_tool(self, tool):
        self.paint_canvas.set_tool(tool)
        for name, button in self.paint_tool_buttons.items():
            button.setChecked(name == tool)
        labels = {
            "brush": "Pędzel", "pencil": "Ołówek", "eraser": "Gumka",
            "line": "Linia", "rectangle": "Prostokąt", "ellipse": "Elipsa",
            "select_rectangle": "Zaznaczenie prostokątne",
            "select_ellipse": "Zaznaczenie eliptyczne",
        }
        self.paint_status.setText(f"Wybrane narzędzie: {labels.get(tool, tool)}")

    def set_paint_color(self, color):
        selected = QColor(color)
        if not selected.isValid():
            return
        self.paint_canvas.set_color(selected)
        self.paint_hex_input.setText(selected.name())
        self.paint_color_preview.setStyleSheet(f"background:{selected.name()}; border:1px solid #76829b; border-radius:8px;")

    def apply_paint_hex_color(self):
        selected = QColor(self.paint_hex_input.text().strip())
        if selected.isValid():
            self.set_paint_color(selected)
        else:
            self.paint_hex_input.setText(self.paint_canvas.color.name())
            self.paint_status.setText("Wpisz kolor w formacie #RRGGBB.")

    def update_paint_brush_size(self, value):
        self.paint_canvas.set_brush_size(value)
        self.paint_size_label.setText(f"{value} px")

    def update_paint_zoom(self, value):
        self.paint_canvas.set_zoom(value / 100)
        self.paint_zoom_label.setText(f"{value}%")

    def paint_canvas_undo(self):
        self.paint_canvas.undo()
        self.paint_status.setText("Cofnięto ostatnią zmianę.")

    def paint_canvas_redo(self):
        self.paint_canvas.redo()
        self.paint_status.setText("Ponowiono zmianę.")

    def new_paint_document(self):
        self.paint_canvas.new_document()
        self.refresh_paint_layers()
        self.paint_name_input.setText("nowy_rysunek")
        self.paint_status.setText("Utworzono nowy pusty dokument z jedną warstwą tła.")

    def show_paint_save_menu(self):
        if hasattr(self, "paint_save_menu") and hasattr(self, "paint_save_button"):
            position = self.paint_save_button.mapToGlobal(self.paint_save_button.rect().bottomLeft())
            self.paint_save_menu.exec(position)

    def save_paint_to_gallery(self):
        raw_name = Path(self.paint_name_input.text().strip()).name
        safe_name = "".join(character if character.isalnum() or character in " -_" else "_" for character in raw_name)
        safe_name = safe_name.strip(" ._") or "mini_os_rysunek"
        if safe_name.lower().endswith(".png"):
            safe_name = safe_name[:-4]
        PHOTOS.mkdir(parents=True, exist_ok=True)
        destination = PHOTOS / f"{safe_name}.png"
        suffix = 2
        while destination.exists():
            destination = PHOTOS / f"{safe_name}_{suffix}.png"
            suffix += 1
        if not self.paint_canvas.composite_image().save(str(destination), "PNG"):
            self.paint_status.setText("Nie udało się zapisać rysunku.")
            return
        self.paint_name_input.setText(destination.stem)
        self.paint_status.setText(f"Zapisano w Galerii: {destination.name}")
        self.refresh_gallery()
        self.refresh_paint_gallery()

    def save_paint_to_files(self):
        raw_name = Path(self.paint_name_input.text().strip()).name
        safe_name = "".join(character if character.isalnum() or character in " -_" else "_" for character in raw_name)
        safe_name = safe_name.strip(" ._") or "mini_os_rysunek"
        if safe_name.lower().endswith(".png"):
            safe_name = safe_name[:-4]
        path = self.choose_internal_save_path(
            profile_user_directories(self.active_profile_id)["pictures"],
            f"{safe_name}.png",
            "Zapisz rysunek w folderze mini-OS",
            ".png",
        )
        if not path:
            return
        if path.suffix.lower() != ".png":
            path = path.with_suffix(".png")
            if path.exists():
                answer = QMessageBox.question(
                    self, "Zastąpić plik?", f"Plik „{path.name}” już istnieje. Czy go zastąpić?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if answer != QMessageBox.StandardButton.Yes:
                    return
        if not self.paint_canvas.composite_image().save(str(path), "PNG"):
            QMessageBox.warning(self, "Paint Studio", "Nie udało się zapisać obrazu w folderze mini-OS.")
            return
        self.paint_name_input.setText(path.stem)
        self.paint_status.setText(f"Zapisano w Plikach: {path.relative_to(ROOT)}")

    def begin_startup(self):
        if not self.wallpaper_repair_needed:
            self.start_boot_animation()
            return

        self.boot_loading_label.setText("AUTONAPRAWA")
        self.boot_repair_note.setText("Proszę czekać — przygotowuję tapety…")
        self.boot_pulse.start()
        self.boot_mark_pulse.start()
        self._wallpaper_repair_timer = QTimer(self)
        self._wallpaper_repair_timer.setSingleShot(True)
        self._wallpaper_repair_timer.timeout.connect(self.finish_wallpaper_repair)
        self._wallpaper_repair_timer.start(3000)

    def finish_wallpaper_repair(self):
        self.boot_pulse.stop()
        self.boot_mark_pulse.stop()
        try:
            if not install_builtin_wallpapers() or wallpapers_need_repair():
                raise OSError("Nie udało się przywrócić kompletu dziewięciu tapet.")
            self.wallpaper_repair_needed = False
            self.refresh_wallpaper_option_icons()
            self.apply_wallpapers()
        except OSError as error:
            QMessageBox.warning(
                self, "Autonaprawa tapet",
                f"Nie udało się przygotować tapet. Mini-OS uruchomi się z domyślnym tłem.\n\n{error}"
            )
        self.boot_loading_label.setText("LOADING")
        self.boot_repair_note.clear()
        self.start_boot_animation()

    def start_boot_animation(self):
        if not self.settings.get("animations", True):
            self.boot_pulse.stop()
            self.boot_mark_pulse.stop()
            self.boot_progress_animation.stop()
            self.boot_progress.setValue(100)
            self.boot_percent.setText("100%")
            self.show_page("login")
            QTimer.singleShot(500, self.start_auto_theme_detection)
            return
        self.boot_pulse.start()
        self.boot_mark_pulse.start()
        self.boot_progress_animation.stop()
        self.boot_progress.setValue(0)
        self.boot_percent.setText("0%")
        self.boot_progress_animation.start()

    def finish_boot_animation(self):
        self.boot_pulse.stop()
        self.boot_mark_pulse.stop()
        self.show_page("login")
        QTimer.singleShot(500, self.start_auto_theme_detection)

    def login(self):
        profile_id = self.login_profile_combo.currentData()
        profile = self.profile_by_id(profile_id)
        if not profile:
            QMessageBox.warning(self, "Logowanie", "Wybierz istniejący profil.")
            return
        saved_password = profile.get("password", "")
        if saved_password and self.login_pass.text() != saved_password:
            QMessageBox.warning(self,"Logowanie","Nieprawidłowe hasło."); return
        self.activate_profile(profile_id)
        write_json(USER_FILE, self.user)
        self.refresh_profile_lists(self.active_profile_id, self.active_profile_id)
        self.load_profile_editor()
        if self.browser:
            self.browser.setUrl(QUrl(self.settings.get("browser_last_url") or self.settings.get("start_url", "https://www.google.com")))
        self.update_profile_identity_widgets()
        self.login_pass.clear()
        self.show_page("home")

    def logout(self):
        self.save_session()
        self.stop_camera()
        self.refresh_profile_lists(self.settings_profile_combo.currentData(), self.active_profile_id)
        self.login_pass.clear()
        self.show_page("login")

    def restart_mini_os(self):
        self.save_session()
        self.stop_camera(force=True)
        script_path = Path(__file__).resolve()
        result = QProcess.startDetached(
            sys.executable, [str(script_path)], str(script_path.parent)
        )
        started = result[0] if isinstance(result, tuple) else result
        if not started:
            QMessageBox.warning(self, "Ponowne uruchomienie", "Nie udało się uruchomić mini-OS ponownie.")
            return
        self.close()

    def factory_reset(self):
        answer = QMessageBox.warning(
            self,
            "Przywróć ustawienia fabryczne",
            "Ta operacja usunie wszystkie dane mini-OS z folderu:\n"
            f"{ROOT}\n\n"
            "Zostaną usunięte ustawienia, konto i hasło, sesje, logowania i dane "
            "przeglądarki, zdjęcia oraz pliki zapisane w tym folderze. Tej operacji "
            "nie można cofnąć.\n\nCzy kontynuować?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self.stop_camera(force=True)
        script_path = Path(__file__).resolve()
        result = QProcess.startDetached(
            sys.executable,
            [str(script_path), "--factory-reset-after", str(os.getpid())],
            str(script_path.parent),
        )
        started = result[0] if isinstance(result, tuple) else result
        if not started:
            QMessageBox.warning(self, "Przywracanie ustawień", "Nie udało się rozpocząć przywracania ustawień fabrycznych.")
            return
        self.close()

    def show_page(self,name):
        if name not in self.pages: return
        if self.current_app == "settings" and name in {"home", "start_menu"}:
            self.save_settings(silent=True)
        self.apply_language()
        if self.current_app == "camera" and name != "camera" and self._camera_preview_active:
            self.stop_camera()
        self.current_app = name
        self.stack.setCurrentWidget(self.pages[name])
        if name == "home": self.update_clock()
        if name == "mini_store": self.refresh_store_cards()
        if name == "camera": pass
        if name == "gallery": self.refresh_gallery()
        if name == "files": self.refresh_files()
        self.showFullScreen()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_app == "photo_viewer":
            self.fit_photo_image()

    def update_clock(self):
        now = datetime.now()
        fmt = "%H:%M" if self.settings.get("clock_24h",True) else "%I:%M %p"
        if hasattr(self,"home_clock"): self.home_clock.setText(now.strftime(fmt))
        if hasattr(self,"home_date"):
            months = ["stycznia","lutego","marca","kwietnia","maja","czerwca","lipca","sierpnia","września","października","listopada","grudnia"]
            days = ["poniedziałek","wtorek","środa","czwartek","piątek","sobota","niedziela"]
            self.home_date.setText(f"{days[now.weekday()]}, {now.day} {months[now.month-1]} {now.year}")

    def apply_theme(self):
        app = QApplication.instance()
        if app is None:
            return
        light_mode = self.configure_app_color_scheme()
        stylesheet = themed_stylesheet(STYLE, light_mode)
        if self.settings.get("high_contrast", False):
            contrast_color = "#111111" if light_mode else "#ffffff"
            stylesheet += f"\nQLabel,QCheckBox,QGroupBox {{ color:{contrast_color}; }} QWidget {{ border-color:{contrast_color}; }} QPushButton {{ border:2px solid {contrast_color}; color:{contrast_color}; }} QLineEdit,QComboBox,QListWidget,QTextEdit,QPlainTextEdit {{ border:2px solid {contrast_color}; }}"
        app.setStyleSheet(stylesheet)
        set_webview_theme(getattr(self, "browser_page", None), light_mode)
        set_webview_theme(getattr(self, "app_page", None), light_mode)
        for widget in app.allWidgets():
            current_style = widget.styleSheet()
            boot_page = self.pages.get("boot")
            if boot_page is not None and (widget is boot_page or boot_page.isAncestorOf(widget)):
                # Keep the loading screen identical in both themes: its black
                # background, white labels, metallic logo, and progress bar
                # are part of the boot design rather than app theme styling.
                continue
            has_base_style = widget.property("mini_os_theme_style_ready")
            last_theme_style = widget.property("mini_os_theme_last_style")
            if not has_base_style:
                base_style = current_style
                widget.setProperty("mini_os_theme_base_style", base_style)
                widget.setProperty("mini_os_theme_style_ready", True)
            else:
                base_style = widget.property("mini_os_theme_base_style") or ""
                if current_style != last_theme_style:
                    base_style = current_style
                    widget.setProperty("mini_os_theme_base_style", base_style)
            themed_style = themed_stylesheet(base_style, light_mode)
            if current_style != themed_style:
                widget.setStyleSheet(themed_style)
            widget.setProperty("mini_os_theme_last_style", themed_style)
        # Tile styles are rebuilt from their brand colors so they do not keep
        # the old theme's dark backgrounds after a live theme switch.
        for widget in app.allWidgets():
            if widget.objectName() == "tile":
                brand_color = widget.property("miniOsTileBrandColor") or "#52627a"
                widget.setStyleSheet(app_tile_stylesheet(brand_color, light_mode))
        for page in self.pages.values():
            page.light_mode = light_mode
            page.update()

    def save_session(self):
        data = {
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "last_app": self.current_app,
            "username": self.username,
            "profile_id": self.active_profile_id,
            "window_state": "fullscreen",
        }
        write_json(SESSION_FILE,data)
        self.session = data
        if hasattr(self,"session_status"): self.session_status.setText("Sesja została zapisana.")
        if hasattr(self,"home_status"): self.home_status.setText("Sesja zapisana: " + data["saved_at"].replace("T"," "))
        self.show_session_details()

    def keyPressEvent(self,event):
        if self.current_app == "boot":
            event.accept()
            return
        if event.key() == Qt.Key.Key_Escape:
            if self.current_app == "start_menu":
                self.close_start_menu()
            elif self.current_app == "installed_app_view":
                self.confirm_exit_installed_app()
            elif self.current_app != "home":
                self.show_page("home")
            else:
                self.showNormal()
            return
        if event.matches(QKeySequence.StandardKey.Quit):
            self.close(); return
        super().keyPressEvent(event)

    def closeEvent(self,event):
        self.save_session()
        self.stop_camera(force=True)
        event.accept()

def wait_for_process_exit(pid, timeout=60):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except OSError:
            return True
        time.sleep(0.1)
    return False

def clear_factory_data():
    shutil.rmtree(ROOT, ignore_errors=True)
    for folder in (ROOT, DATA, LEGACY_PHOTOS_DIR, SESSIONS):
        folder.mkdir(parents=True, exist_ok=True)

def main():
    reset_pid = None
    if len(sys.argv) >= 3 and sys.argv[1] == "--factory-reset-after":
        try:
            reset_pid = int(sys.argv[2])
        except ValueError:
            reset_pid = -1
        if reset_pid < 1 or not wait_for_process_exit(reset_pid):
            app = QApplication([sys.argv[0]])
            QMessageBox.critical(None, "Przywracanie ustawień", "Nie udało się bezpiecznie zamknąć poprzedniej sesji. Żadne dane nie zostały usunięte.")
            return 1
        clear_factory_data()

    app = QApplication([sys.argv[0]])
    app.setApplicationName("mini-os")
    window = MiniOS()
    window.showFullScreen()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
