# mini-os

Minimalistyczne środowisko desktopowe w Pythonie dla macOS. To aplikacja działająca w oknie pełnoekranowym, a nie samodzielny system operacyjny.

## Funkcje
- Wiele profili użytkowników z listą wyboru na ekranie logowania. Profile mają osobne ustawienia, tapety i Galerie zdjęć. W Ustawieniach można dodawać profile, zmieniać ich nazwy, ustawiać osobne hasła i wybierać zdjęcie profilu z Galerii mini-OS. Zdjęcie dopasowuje się na pełnoekranowej stronie mini-OS: można je wycentrować, obrócić i powiększyć. Gotowy avatar jest okrągły i widoczny na ekranie logowania, pulpicie oraz w Menu Start.
- Dziewięć tapet obrazkowych dla motywu ciemnego oraz dziewięć jasnych, pastelowych tapet wbudowanych; w Ustawieniach widać presety pasujące do aktualnego motywu. Własne obrazy można dodawać niezależnie od motywu. Tapetę ekranu logowania i pulpitu ustawia się osobno, a domyślne tło dopasowuje się do jasnego lub ciemnego motywu.
- Przy uruchamianiu mini-OS sprawdza komplet dziewięciu tapet. Jeśli któregoś brakuje, na kilka sekund pokazuje „AUTONAPRAWA”, odtwarza folder `~/mini os/wallpapers` i uzupełnia brakujące obrazy.
- Pełnoekranowy ekran uruchamiania w czarnym stylu z metalicznym gradientem na logo i ikonie, płynnie animowanym paskiem postępu, procentami i delikatnym pulsowaniem; animacje można wyłączyć w Ustawieniach.
- Pełnoekranowe Menu Start zapisuje sesję przy otwieraniu i zawiera wejście do widoku sesji oraz opcje powrotu, wylogowania, ponownego uruchomienia i zamknięcia mini-OS. Wyłączanie i ponowne uruchomienie są też dostępne z ekranu logowania.
- W Ustawieniach można osobno zmieniać tło ekranu logowania i pulpitu. Przycisk własnej tapety otwiera galerię mini-OS z miniaturami zdjęć; wbudowane tapety są ukryte w tej galerii. Kliknięcie zdjęcia ustawia je jako tło, a zdjęcia dodane z komputera pojawiają się również w zwykłej Galerii. To samo zdjęcie nie jest dodawane ponownie przy kolejnym wyborze.
- Pulpit z dużymi kafelkami, w tym mini_store zamiast systemowego kafelka Gry oraz Paint Studio zamiast kafelka Sesja, zegarem i datą po polsku. W Ustawieniach można zmieniać kolejność aplikacji na pulpicie i odinstalowywać aplikacje ze sklepu; kolejność oraz zainstalowane aplikacje są osobne dla każdego profilu. Aplikacje systemowe są chronione. Widok Sesji jest dostępny w Menu Start.
- Pełnoekranowe widoki aplikacji; Esc wraca do pulpitu.
- Przeglądarka oparta na Chromium przez Qt WebEngine; jej schemat kolorów jest synchronizowany z motywem mini-OS i przekazywany stronom obsługującym `prefers-color-scheme`, a otwarte strony są przeładowywane przy zmianie motywu.
- Sesje logowania i dane stron w przeglądarce są zachowywane w `~/mini os/browser` między uruchomieniami.
- Ustawienia zawierają przywracanie ustawień fabrycznych; po potwierdzeniu usuwa ono wszystkie dane z `~/mini os` i uruchamia aplikację ponownie.
- W Ustawieniach znajduje się sekcja Dostępność z wyborem języka interfejsu (angielski, polski i 100 dodatkowych języków) oraz przełącznikiem dużego kontrastu. Domyślnym językiem nowych profili jest angielski; tłumaczenia są dostępne po polsku i angielsku, pozostałe języki korzystają z angielskiego interfejsu.
- Ustawienia zawierają zakładkę Aktualizacje. Przy starcie aplikacja sprawdza najnowszy commit repozytorium GitHub `radoskow16/Mini_OS-symulator-`; pobieranie i podmiana plików programu następuje wyłącznie po kliknięciu „Aktualizuj”. Pliki są pobierane do folderu uruchomieniowego mini-OS, a dane użytkowników w `~/mini os` pozostają oddzielone. Po aktualizacji można ponownie uruchomić aplikację.
- W Ustawieniach można wybrać motyw jasny, ciemny lub automatyczny. Tryb automatyczny mierzy jasność kamery przy uruchomieniu i ponownie co 3 minuty; kamera jest zwalniana między pomiarami. Nie odczytuje wyglądu macOS, a wybór motywu jest zapisany osobno dla każdego profilu.
- Wbudowany Notatnik (poza sklepem) do tworzenia, otwierania i zapisywania plików tekstowych: TXT, JSON, Markdown, CSV, kodu i konfiguracji. Otwieranie i zapisywanie nowych plików zaczyna się w folderze Dokumenty; „Zapisz jako” pozwala wybrać inny folder w mini-OS. Moje pliki pozwala otwierać tekst dwukrotnym kliknięciem. Notatnik ma systemowe skróty Nowy/Otwórz/Zapisz i ostrzega przed utratą niezapisanych zmian.
- Eksplorator „Moje pliki” działa wewnątrz mini-OS: można przeglądać foldery danych, otwierać tekst w Notatniku i obrazy w podglądzie, tworzyć foldery i pliki, importować, zmieniać nazwy, kopiować, wycinać, wklejać oraz usuwać elementy. Operacje usuwania wymagają potwierdzenia.
- Każdy profil ma własne foldery „Pobrane”, „Dokumenty” i „Zdjęcia” w swoim katalogu użytkownika. Nowe notatki zapisują się domyślnie w Dokumentach, Paint zapisuje obrazy w Zdjęciach, a przeglądarka i aplikacje webowe pobierają pliki do Pobranych. Kafelek Paint jest dostępny również w Menu Start.
- mini_store jest dostępny w Menu Start i zawiera ponad 8 500 opisanych stron internetowych oraz YouTube, YT Music, ChatGPT, Gemini, Netflix, Gry.pl, WhatsApp i lokalną grę MINECRAFT. Dodatkowe wpisy są przechowywane w `curated_websites.json` i `directory_websites.json`; mają czytelne nazwy, kategorie, opisy i favicony z ikoną zastępczą na czas ładowania. Katalog jest podzielony na strony po 48 pozycji, a wyszukiwarka przeszukuje również opisy. Przy zainstalowanych aplikacjach dostępny jest przycisk „Usuń”; zainstalowane skróty pojawiają się na kolejnych stronach pulpitu, po osiem na stronę. Aplikacje internetowe uruchamiają się w pełnoekranowym widoku bez pasków przeglądarki, z jednym małym przyciskiem wyjścia wymagającym potwierdzenia; Minecraft otrzymuje zgodę na blokowanie myszy. Przeglądarka zachowuje swój własny ostatnio otwarty adres i zawsze pokazuje pasek adresu.
- Paint Studio: rysowanie pędzlem i ołówkiem, gumka, linie, prostokąty i elipsy, paleta oraz własny kolor, rozmiar narzędzia, wypełnianie kształtów, cofanie/ponawianie, zoom i menu zapisu z wyborem Galerii albo folderu wewnątrz mini-OS. Zaznaczenie prostokątne i eliptyczne można przesuwać, kopiować, wycinać, wklejać i usuwać. Panel warstw pozwala dodawać, usuwać, nazywać, ukrywać, zmieniać krycie i kolejność warstw; obrazy są zapisywane jako PNG. Przyciski narzędzi mają kompaktowe, same ikony z podpowiedziami po najechaniu.
- Zdjęcia z kamery i obrazy Painta trafiają do folderu „Zdjęcia” aktywnego profilu; Galeria pokazuje ich miniatury, a kliknięcie otwiera pełnoekranowy widok wewnątrz mini-OS. Zdjęcie można usunąć z poziomu podglądu.
- Ustawienia i profile w `~/mini os/data`, a zapis sesji w `~/mini os/sessions`.
- Obsługa klawiatury i myszy; przyciski są duże i nadają się do obsługi dotykiem.

## Instalacja

Zalecany jest Python 3.11 lub 3.12 oraz PySide6 6.8 lub nowszy. Otwórz Terminal w folderze z plikami i wykonaj:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python mini_os.py
```

Jeśli instalacja `PySide6-WebEngine` nie powiedzie się na Twojej wersji Pythona/macOS, użyj wersji Pythona wspieranej przez aktualne wydanie PySide6.

## Kamera na macOS
Przy pierwszym użyciu macOS może poprosić o zgodę na dostęp do kamery. Jeśli nie pojawi się monit, sprawdź:
**Ustawienia systemowe → Prywatność i ochrona → Kamera**.
Na macOS kamera korzysta z backendu AVFoundation OpenCV.

## Dane
Aplikacja tworzy automatycznie:
- `~/mini os/data/` — profile i ich ustawienia
- `~/mini os/profile_data/` — osobne dane profili, tapety i katalog `Użytkownik` z folderami Pobrane, Dokumenty i Zdjęcia
- `~/mini os/sessions/` — zapis ostatniej sesji
- `~/mini os/browser/` — profil przeglądarki, ciasteczka i dane stron
- `~/mini os/wallpapers/` — wspólne pliki dziewięciu wbudowanych tapet; wybór tapety oraz własne obrazy są przypisane do profilu

Przy pierwszym uruchomieniu tej wersji dotychczasowe zdjęcia i własne tapety zostaną skopiowane do profilu używanego ostatnio.

## Uwagi
- Przeglądarka internetowa wymaga połączenia z internetem.
- Zapis sesji zapisuje użytkownika, ostatnią aplikację i czas zapisu; nie przywraca automatycznie wszystkich stanów stron internetowych.
- Hasło przechowywane jest lokalnie w pliku profilu w postaci zwykłego tekstu. Nie używaj tu hasła, którego używasz w innych usługach.
- Katalog witryn pochodzi z projektu [I Love Free Website Directory](https://github.com/ilovefree-com/free-website-directory) na licencji Apache-2.0; usunięto z niego pozycje prowadzące do GitHuba. Tekst licencji dołączono w `third_party/ILOVEFREE_DIRECTORY_LICENSE.txt`. Linki prowadzą do zewnętrznych serwisów i ich dostępność zależy od tych stron.
- Wyjście z pełnego ekranu: `Esc` (na pulpicie przełącza do zwykłego okna). Zamknięcie aplikacji: standardowy przycisk zamknięcia okna lub skrót systemowy.
