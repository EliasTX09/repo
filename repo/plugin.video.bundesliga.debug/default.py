import sys
import json
import urllib.request
import urllib.parse
import xbmcplugin
import xbmcgui
import re
from datetime import datetime
import pytz
import xbmcaddon
import xbmc
from resources.lib import daddylive
from resources.lib.jetextractors.extractors.daddylive import Daddylive
from resources.lib.jetextractors.models import JetLink
import requests
from urllib.parse import quote_plus, unquote_plus, parse_qsl




HANDLE = int(sys.argv[1])
BASE_URL = sys.argv[0]

# URLs für die verschiedenen Ligen
_JSON_URL_URLS = "https://raw.githubusercontent.com/EliasTX09/json/main/json.json"


# Bilder für die Ligen
IMAGES_JSON_URL =  "https://raw.githubusercontent.com/EliasTX09/json/main/IMAGES"


SENDER_JSON_URL = "https://raw.githubusercontent.com/EliasTX09/json/main/sender.json"

SENDER_M3U_URL = "https://raw.githubusercontent.com/EliasTX09/json/main/sender_test.m3u"

HEADER_STRING = (
    "|Referer=https://alldownplay.xyz/" +
    "&Origin=https://alldownplay.xyz" +
    "&Connection=Keep-Alive" +
    "&User-Agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
)


def play_stream(url):
    try:
        notify("Extrahiere Stream...")
        extractor = Daddylive()
        link = extractor.get_link(JetLink(url))

        stream_url = link.address.split('|')[0]  # reine URL ohne Header

        # Headerstring an die URL anhängen
        stream_url_with_headers = stream_url + HEADER_STRING

        notify(f"Extrahierte URL (mit Headers): {stream_url_with_headers}")

        li = xbmcgui.ListItem(path=stream_url_with_headers)
        li.setMimeType("application/vnd.apple.mpegurl")
        li.setProperty("inputstream", "inputstream.ffmpegdirect")
        li.setProperty("inputstream.ffmpegdirect.manifest_type", "hls")
        li.setProperty("inputstream.ffmpegdirect.stream_mode", "simple")
        li.setProperty("inputstream.ffmpegdirect.is_realtime_stream", "true")

        xbmcplugin.setResolvedUrl(HANDLE, True, li)
        notify("Stream wird abgespielt...")

    except Exception as e:
        notify(f"Fehler: {e}")

def is_excluded_from_bundesliga(item, league_name):
    fields = [
        item.get("title", ""),
        item.get("league", ""),
        item.get("sport", ""),
    ]
    fields = [f if isinstance(f, str) else "" for f in fields]
    content = " ".join(fields).lower()
    EXCLUDES = [
        "tipico bundesliga",
        "bundesliga women",
        "planet pure bundesliga women",
        "austria"
    ]
    # 2. Bundesliga nur ausschließen, wenn es die "Bundesliga" Liga ist
    if league_name == "Bundesliga":
        EXCLUDES.append("2. bundesliga")
    return any(excl in content for excl in EXCLUDES)

def notify(msg):
    xbmc.log(f"[Stream] {msg}", xbmc.LOGINFO)
    xbmcgui.Dialog().notification("Fussball", msg, xbmcgui.NOTIFICATION_INFO, 2000)

def build_url(query):
    return BASE_URL + '?' + urllib.parse.urlencode(query)

def play_daddylive_stream(stream_number):
    url = f"https://daddylive.dad/stream/stream-{stream_number}.php"
    
    m3u8_url, headers = daddylive.get_m3u8_and_headers(url)
    
    li = xbmcgui.ListItem(path=m3u8_url)
    li.setProperty("IsPlayable", "true")
    li.setProperty("inputstream.adaptive.manifest_type", "hls")

    if headers:
        li.setProperty("inputstream.adaptive.manifest_headers", json.dumps(headers))
        li.setProperty("inputstream.adaptive.stream_headers", json.dumps(headers))
    
    xbmcplugin.setResolvedUrl(HANDLE, True, li)




def load_json_from_url(url):
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read()
            return json.loads(data.decode("utf-8"))
    except Exception as e:
        xbmcgui.Dialog().notification("Fehler", f"JSON konnte nicht geladen werden:\n{str(e)}", xbmcgui.NOTIFICATION_ERROR)
        return None

# URLs und Senderliste laden
URLS = load_json_from_url(_JSON_URL_URLS) or {}
IMAGES = load_json_from_url(IMAGES_JSON_URL) or {}

def list_test_menu():

    test_sender_url = f"{BASE_URL}?action=list_test_daddy"
    li_test_sender = xbmcgui.ListItem(label="[COLORyellow]Sender Testweise[/COLOR]")
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=test_sender_url, listitem=li_test_sender, isFolder=True)

    xbmcplugin.endOfDirectory(HANDLE)



def list_test_daddy():
    json_url = "https://raw.githubusercontent.com/EliasTX09/json/main/sendertest.json"
    try:
        response = requests.get(json_url)
        response.raise_for_status()
        streams = response.json()
    except Exception as e:
        notify(f"Fehler beim Laden der JSON: {e}")
        streams = []

    for stream in streams:
        title = stream.get('name', 'Unbenannt')
        url = stream.get('stream_url')
        if not url:
            continue

        item_url = build_url({'action': 'play', 'url': url})
        li = xbmcgui.ListItem(title)
        li.setProperty('IsPlayable', 'true')

        thumbnail = stream.get('thumbnail')
        if thumbnail:
            li.setArt({'thumb': thumbnail})

        xbmcplugin.addDirectoryItem(handle=HANDLE, url=item_url, listitem=li, isFolder=False)

    xbmcplugin.endOfDirectory(HANDLE)


def list_m3u_senders():
    try:
        with urllib.request.urlopen(SENDER_M3U_URL) as response:
            m3u_content = response.read().decode("utf-8")

        lines = m3u_content.splitlines()
        # M3U Header entfernen (#EXTM3U)
        if lines[0].strip() == "#EXTM3U":
            lines = lines[1:]

        i = 0
        while i < len(lines):
            if lines[i].startswith("#EXTINF"):
                # Beispiel: #EXTINF:-1 tvg-logo="logo_url" group-title="Gruppe",Sender Name
                info_line = lines[i]
                stream_url = lines[i+1] if i + 1 < len(lines) else ""
                i += 2

                # Name aus EXTINF extrahieren (nach letztem Komma)
                name = info_line.split(",")[-1].strip()

                # Logo aus EXTINF extrahieren (optional)
                logo_match = re.search(r'tvg-logo="([^"]+)"', info_line)
                logo = logo_match.group(1) if logo_match else ""

                li = xbmcgui.ListItem(label=name)
                if logo:
                    li.setArt({"thumb": logo, "icon": logo, "fanart": logo})
                li.setProperty("IsPlayable", "true")
                li.setInfo("video", {"title": name})

                play_url = f"{BASE_URL}?action=play&url={urllib.parse.quote(stream_url)}"
                xbmcplugin.addDirectoryItem(handle=HANDLE, url=play_url, listitem=li, isFolder=False)

            else:
                i += 1

        xbmcplugin.endOfDirectory(HANDLE)

    except Exception as e:
        xbmcgui.Dialog().notification("Fehler", f"M3U konnte nicht geladen werden:\n{str(e)}", xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(HANDLE)



def list_sender():
    streams = load_json_from_url(SENDER_JSON_URL)
    if streams:
        for stream in streams:
            name = stream.get('name', 'Unbekannt')
            logo = stream.get('logo', '')
            url = stream.get('url', '')
            li = xbmcgui.ListItem(label=name)
            li.setArt({'icon': logo, 'thumb': logo})
            li.setProperty("IsPlayable", "false")  # Ist ein Ordner
            # Aufruf von show_streams mit Parametern
            directory_url = f'{sys.argv[0]}?action=show_streams&name={quote_plus(name)}&logo={quote_plus(logo)}&url={quote_plus(url)}'
            xbmcplugin.addDirectoryItem(handle=HANDLE, url=directory_url, listitem=li, isFolder=True)
    else:
        xbmcgui.Dialog().notification("Fehler", "Sender JSON konnte nicht geladen werden", xbmcgui.NOTIFICATION_ERROR)

    xbmcplugin.endOfDirectory(HANDLE)

def show_streams(params):
    name = params.get('name', [None])[0]
    url = params.get('url', [None])[0]
    logo = params.get('logo', [None])[0] if params.get('logo') else ''

    if not name or not url:
        xbmcgui.Dialog().notification("Fehler", "Senderdaten fehlen", xbmcgui.NOTIFICATION_ERROR)
        return

    prefix = "plugin://plugin.video.madtitansports/sportjetextractors/play?urls="
    if url.startswith(prefix):
        short_url = url[len(prefix):]
    else:
        short_url = url

    # 1. Stream (hellgrün lime oben, mit (!))
    label1 = f"[COLOR lime]{name} (!)[/COLOR]"  # hellgrün lime
    li1 = xbmcgui.ListItem(label=label1)
    li1.setArt({'thumb': logo, 'icon': logo, 'fanart': logo})
    li1.setProperty("IsPlayable", "true")
    play_url1 = f"{BASE_URL}?action=play&url={quote_plus(short_url)}"
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=play_url1, listitem=li1, isFolder=False)

    # 2. Stream (hellrot neon unten, ohne (!))
    label2 = f"[COLOR orange]{name}[/COLOR]"  # orange als neonrot-ähnlich
    li2 = xbmcgui.ListItem(label=label2)
    li2.setArt({'thumb': logo, 'icon': logo, 'fanart': logo})
    li2.setProperty("IsPlayable", "true")
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li2, isFolder=False)

    xbmcplugin.endOfDirectory(HANDLE)



def convert_time_string_with_pytz(et_string):
    try:
        match = re.search(r'(\d{1,2}):(\d{2}) ([AP]M)', et_string)
        if not match:
            return et_string

        hour, minute, period = int(match.group(1)), int(match.group(2)), match.group(3)

        if period == "PM" and hour != 12:
            hour += 12
        elif period == "AM" and hour == 12:
            hour = 0

        et = pytz.timezone("US/Eastern")
        cet = pytz.timezone("Europe/Berlin")

        now = datetime.now()
        dt_et = datetime(now.year, now.month, now.day, hour, minute)
        dt_et = et.localize(dt_et)
        dt_cet = dt_et.astimezone(cet)

        return dt_cet.strftime("%H:%M Uhr")
    except Exception:
        return et_string

# Ersetzt Uhrzeit im Titel
def replace_time_in_title(title):
    time_match = re.search(r'(\d{1,2}/\d{1,2} )?(\d{1,2}:\d{2} [AP]M)', title)
    if time_match:
        original_time = time_match.group(2)
        converted = convert_time_string_with_pytz(original_time)
        return title.replace(original_time, f"[COLORyellow]{converted}[/COLOR]")
    return title

def list_main_menu():
    for category in ["Männerligen", "Frauenligen"]:
        url = f"{BASE_URL}?action=list_category&category={urllib.parse.quote(category)}"
        li = xbmcgui.ListItem(label=category)
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=True)

    url = f"{BASE_URL}?action=list_sender"
    li = xbmcgui.ListItem(label="Sender")
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=True)

    # Neuer Test-Ordner
    url = f"{BASE_URL}?action=test_menu"
    li = xbmcgui.ListItem(label="[B][COLORorange]Test[/COLOR][/B]")
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(HANDLE)





def list_category(category):
    for league in URLS.keys():
        if ("Frauen" in league and category == "Frauenligen") or ("Frauen" not in league and category == "Männerligen"):
            url = f"{BASE_URL}?action=list_games&league={urllib.parse.quote(league)}"
            li = xbmcgui.ListItem(label=league)
            image = IMAGES.get(league)
            if image:
                li.setArt({"thumb": image, "icon": image, "poster": image})
            xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(HANDLE)

def belongs_to_league(item, league):
    fields = [
        item.get("title", ""),
        item.get("league", ""),
        item.get("sport", ""),
        item.get("type", ""),
        item.get("link", ""),
        item.get("thumbnail", "")
    ]
    fields = [f if isinstance(f, str) else "" for f in fields]
    content = " ".join(fields).lower()
    league_name = league.lower()

    if league_name == "2. bundesliga":
        # Flexibles Matching für 2. Bundesliga
        return "2" in content and "bundesliga" in content

    is_female = any(word in content for word in ["frau", "frauen", "women"])

    if "champions league" in league_name:
        return any(kw in content for kw in ["champions league", "champions-league"])

    if "frauen" in league_name and is_female:
        return league_name.replace(" frauen", "") in content
    if "frauen" not in league_name and not is_female:
        return league_name in content

    return False

def list_games_for_league(league):
    try:
        url = URLS.get(league)
        if not url:
            xbmcgui.Dialog().notification("Fehler", f"Keine URL für Liga '{league}' gefunden.", xbmcgui.NOTIFICATION_ERROR)
            return
        response = urllib.request.urlopen(url)
        data = json.loads(response.read())
        items = data.get("items", [])

        shown_titles = set()

        # Neu laden & Suche Items ...
        reload_item = xbmcgui.ListItem(label="[COLORred]--------- [COLOR khaki]Neu laden[/COLOR][COLORred] ---------[/COLOR]")
        xbmcplugin.addDirectoryItem(handle=HANDLE, url="plugin://plugin.video.madtitansports/refresh_menu", listitem=reload_item, isFolder=False)

        search_item = xbmcgui.ListItem(label="[COLORwhite][B][I]Vorherige Suchen[/COLOR][/B][/I]")
        search_item.setArt({
            "thumb": "https://magnetic.website/menu%20icons/wolfgirl%20mad%20titan%20sports%20icons/search.png",
            "fanart": "https://magnetic.website/Mad%20Titan/NEW%20MAD%20TITAN%20ICONS/fanart.jpg"
        })
        search_url = f"{BASE_URL}?pvr_sport_search=cache"
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=search_url, listitem=search_item, isFolder=True)

        for idx, item in enumerate(items):
            if item.get("type") != "item":
                continue
            if not belongs_to_league(item, league):
                continue

            # Filter nur für Bundesliga (nicht für 2. Bundesliga)
            if league == "Bundesliga" and is_excluded_from_bundesliga(item, league):
                continue

            title = item.get("title", "")
            title = replace_time_in_title(title)

            if title in shown_titles:
                continue
            shown_titles.add(title)

            stream_url = f"{BASE_URL}?action=streams&league={urllib.parse.quote(league)}&id={idx}"
            li = xbmcgui.ListItem(label=title)
            xbmcplugin.addDirectoryItem(handle=HANDLE, url=stream_url, listitem=li, isFolder=True)

        xbmcplugin.endOfDirectory(HANDLE)

    except Exception as e:
        xbmcgui.Dialog().notification("Fehler", f"Fehler bei {league}: {str(e)}", xbmcgui.NOTIFICATION_ERROR)



def list_streams(league, id):
    try:
        url = URLS.get(league)
        response = urllib.request.urlopen(url)
        data = json.loads(response.read())
        items = data.get("items", [])
        item = items[int(id)]
        links = item.get("link", [])

        if not isinstance(links, list):
            links = [links]

        if not links:
            raise Exception("Keine Streams gefunden.")

        thumb = item.get("thumbnail", "")

        # Scraper-Link anzeigen
        scraper_link = links[0]
        li_scraper = xbmcgui.ListItem(label="[COLORlime]SCRAPERS[/COLOR]")
        li_scraper.setProperty("IsPlayable", "false")
        if thumb:
            li_scraper.setArt({'thumb': thumb, 'icon': thumb})
        scraper_url = f"{BASE_URL}?action=play&url={urllib.parse.quote(scraper_link)}"
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=scraper_url, listitem=li_scraper, isFolder=False)

        # Normale Streams ab links[1:] als gelbe Ordner anzeigen
        for i, link in enumerate(links[1:]):
            # Versuche, den Sendernamen im Link zu extrahieren
            sender = None
            match = re.search(r'\[COLORyellow\](.*?)\[/COLOR\]', link)
            if match:
                sender = match.group(1)
            else:
                # Falls kein Farb-Tag, versuche den Namen aus dem Klammer-Inhalt zu holen
                match2 = re.search(r'\((.*?)\)', link)
                if match2:
                    sender = match2.group(1)
                else:
                    sender = f"Stream {i+1}"

            # Debug-Ausgabe (kann man später entfernen)
            print(f"Stream {i+1}: Sender-Name = {sender} | Link = {link}")

            li = xbmcgui.ListItem(label=f"[COLORyellow]{sender}[/COLOR]")
            if thumb:
                li.setArt({'thumb': thumb, 'icon': thumb})

            stream_options_url = (f"{BASE_URL}?action=list_stream_options&league={urllib.parse.quote(league)}"
                                  f"&id={id}&stream_index={i+1}")  # i+1 weil 0 Scraper

            xbmcplugin.addDirectoryItem(handle=HANDLE, url=stream_options_url, listitem=li, isFolder=True)

        xbmcplugin.endOfDirectory(HANDLE)

    except Exception as e:
        xbmcgui.Dialog().notification("Stream-Fehler", str(e), xbmcgui.NOTIFICATION_ERROR)



def list_stream_options(league, id, stream_index):
    try:
        url = URLS.get(league)
        response = urllib.request.urlopen(url)
        data = json.loads(response.read())
        items = data.get("items", [])
        item = items[int(id)]
        links = item.get("link", [])

        if not isinstance(links, list):
            links = [links]

        main_link = links[stream_index]  # z.B. plugin://...

        # Erster Stream: direkter Link ohne plugin:// (grün, mit "(!)")
        direct_url = extract_direct_url(main_link)  # z.B. https://daddylive.dad/stream/stream-558.php
        li_main = xbmcgui.ListItem(label=f"[COLOR=lime]{extract_sender_name(main_link)} (!)[/COLOR]")
        li_main.setProperty("IsPlayable", "true")
        li_main.setArt({'thumb': item.get("thumbnail", ""), 'icon': item.get("thumbnail", "")})

        play_url_main = f"{BASE_URL}?action=play&url={urllib.parse.quote(direct_url)}"

        # Zweiter Stream: kompletter plugin:// Link (orange)
        li_alt = xbmcgui.ListItem(label=f"[COLOR=orange]{extract_sender_name(main_link)}[/COLOR]")
        li_alt.setProperty("IsPlayable", "true")
        li_alt.setArt({'thumb': item.get("thumbnail", ""), 'icon': item.get("thumbnail", "")})

        play_url_alt = main_link  # kompletter plugin:// Link

        # Streams hinzufügen
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=play_url_main, listitem=li_main, isFolder=False)
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=play_url_alt, listitem=li_alt, isFolder=False)

        xbmcplugin.endOfDirectory(HANDLE)

    except Exception as e:
        xbmcgui.Dialog().notification("Fehler", str(e), xbmcgui.NOTIFICATION_ERROR)


def extract_sender_name(link):
    import re
    m = re.search(r'\[COLOR.*?\](.*?)\[/COLOR\]', link)
    if m:
        return m.group(1)
    else:
        return "Unbekannt"


def extract_direct_url(plugin_link):
    import urllib.parse
    parsed = urllib.parse.urlparse(plugin_link)
    query = urllib.parse.parse_qs(parsed.query)
    urls = query.get("urls")
    if urls:
        return urls[0]
    return plugin_link.replace("plugin://plugin.video.madtitansports/sportjetextractors/play?urls=", "").split("(")[0]



def router(paramstring):

    params = urllib.parse.parse_qs(paramstring)
    action = params.get("action", [None])[0]
    league = params.get("league", [None])[0]
    id = params.get("id", [None])[0]
    category = params.get("category", [None])[0]
    stream_url = params.get("url", [None])[0]
    headers = params.get("headers", [None])[0]
    stream_index = params.get("stream_index", [None])[0]

    if action == "list_games" and league:
        list_games_for_league(league)
    elif action == 'list_sender':
        list_sender()
    elif action == 'show_streams':
        show_streams(params)
    elif action == 'play' and stream_url:
        play_stream(urllib.parse.unquote_plus(stream_url))
    elif action == "list_category" and category:
        list_category(category)
    elif action == "list_m3u":
        list_m3u_senders()
    elif action == "list_stream_options" and league and id and stream_index:
        list_stream_options(league, id, int(stream_index))
    elif action == "streams" and league and id:
        list_streams(league, id)
    elif action == 'test_menu':
        list_test_menu()
    elif action == 'list_test_daddy':
        list_test_daddy()
    elif action == "play_daddy" and stream_url:
        play_daddylive_stream(stream_url)
    elif action == "enter_daddy_number":
        keyboard = xbmcgui.Dialog().input("Stream-Nummer eingeben", type=xbmcgui.INPUT_NUMERIC)
        if keyboard and keyboard.isdigit():
            xbmc.executebuiltin(f"RunPlugin({BASE_URL}?action=play_daddy&url={keyboard})")
        else:
            xbmcgui.Dialog().notification("Fehler", "Ungültige Eingabe", xbmcgui.NOTIFICATION_ERROR)
    else:
        list_main_menu()

if __name__ == "__main__":
    import sys
    router(sys.argv[2][1:])