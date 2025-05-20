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




HANDLE = int(sys.argv[1])
BASE_URL = sys.argv[0]

# URLs für die verschiedenen Ligen
_JSON_URL_URLS = "https://raw.githubusercontent.com/EliasTX09/json/main/json.json"


# Bilder für die Ligen
IMAGES_JSON_URL =  "https://raw.githubusercontent.com/EliasTX09/json/main/IMAGES"


SENDER_JSON_URL = "https://raw.githubusercontent.com/EliasTX09/json/main/sender.json"

SENDER_M3U_URL = "https://raw.githubusercontent.com/EliasTX09/json/main/sender_test.m3u"




def play_stream(raw_url, raw_headers=None):
    # raw_url z.B. "http://example.com/stream.m3u8"
    # raw_headers: JSON-codierter String mit Headern

    headers = {}

    # Wenn Header als JSON-String mitgegeben wird, parsen
    if raw_headers:
        try:
            headers = json.loads(urllib.parse.unquote(raw_headers))
        except Exception as e:
            xbmc.log(f"Fehler beim Parsen der Header: {str(e)}", xbmc.LOGERROR)

    li = xbmcgui.ListItem(path=raw_url)
    li.setProperty("IsPlayable", "true")

    if headers:
        li.setProperty("inputstream.adaptive.manifest_headers", json.dumps(headers))
        li.setProperty("inputstream.adaptive.stream_headers", json.dumps(headers))

    xbmcplugin.setResolvedUrl(HANDLE, True, li)



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

def show_custom_stream_input():
    keyboard = xbmc.Keyboard('', 'Gib eine Stream-ID ein (z. B. 426)')
    keyboard.doModal()
    if keyboard.isConfirmed():
        stream_id = keyboard.getText()
        if stream_id.isdigit():
            stream_url = f"https://daddylive.dad/stream/stream-{stream_id}.php"
            play_url = f"plugin://plugin.video.madtitansports/sportjetextractors/play?urls={stream_url}"
            xbmc.executebuiltin(f'PlayMedia({play_url})')
        else:
            xbmcgui.Dialog().notification('Ungültige Eingabe', 'Nur Zahlen erlaubt.', xbmcgui.NOTIFICATION_ERROR)


def list_test_menu():
   
    daddy_input_url = f"{BASE_URL}?action=enter_daddy_number"
    li_input = xbmcgui.ListItem(label="[COLORlightblue]DaddyLive Streamnummer eingeben[/COLOR]")
    li_input.setProperty("IsPlayable", "false")
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=daddy_input_url, listitem=li_input, isFolder=False)

    # Eintrag: Test Sender (M3U)
    url_m3u = f"{BASE_URL}?action=list_m3u"
    li_m3u = xbmcgui.ListItem(label="[COLORyellow]Test Sender (NUR ELIAS!!!)[/COLOR]")
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=url_m3u, listitem=li_m3u, isFolder=True)

    url = f"{BASE_URL}?action=show_stream_info"
    li = xbmcgui.ListItem(label="Stream Test")
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=False)
    xbmcplugin.endOfDirectory(HANDLE)
    
    # Eintrag: Stream durch Zahl öffnen
    input_url = f"{BASE_URL}?action=open_number_input"
    li_input = xbmcgui.ListItem(label="[COLORlime]Zahl eingeben für Stream[/COLOR]")
    li_input.setArt({'icon': '', 'thumb': '', 'fanart': ''})
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=input_url, listitem=li_input, isFolder=False)

    xbmcplugin.endOfDirectory(HANDLE)

def show_stream_info():
    number = xbmcgui.Dialog().input("Stream Test")
    if not number:
        return
    
    m3u8_url = f"https://ddy6new.newkso.ru/ddy6/premium{number}/mono.m3u8"
    headers = {
        "Referer": "https://alldownplay.xyz/",
        "Origin": "https://alldownplay.xyz",
        "Connection": "Keep-Alive",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
    }
    
    # Header als String formatiert
    headers_str = "\n".join(f"{k}: {v}" for k, v in headers.items())
    
    message = f"M3U8 URL:\n{m3u8_url}\n\nHeaders:\n{headers_str}"
    xbmcgui.Dialog().textviewer("Stream Info", message)

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
            li = xbmcgui.ListItem(label=stream['name'])
            li.setArt({'icon': stream.get('logo', ''), 'thumb': stream.get('logo', '')})
            url = stream['url']
            li.setProperty("IsPlayable", "true")
            xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=False)
    else:
        xbmcgui.Dialog().notification("Fehler", "Sender JSON konnte nicht geladen werden", xbmcgui.NOTIFICATION_ERROR)


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



def open_number_input():
    keyboard = xbmcgui.Dialog().input("Stream-Nummer eingeben", type=xbmcgui.INPUT_NUMERIC)
    if keyboard:
        stream_number = keyboard.strip()
        if stream_number.isdigit():
            stream_url = f"https://daddylive.dad/stream/stream-{stream_number}.php"
            plugin_url = f"plugin://plugin.video.madtitansports/sportjetextractors/play?urls={stream_url}"
            xbmc.executebuiltin(f'RunPlugin({plugin_url})')
        else:
            xbmcgui.Dialog().notification("Fehler", "Ungültige Zahl eingegeben!", xbmcgui.NOTIFICATION_ERROR)




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

        for link in links:
            # Ursprüngliche URL ohne Header-Anhang
            base_link = link.split("(")[0]
            url = f"{BASE_URL}?action=play&url={urllib.parse.quote(base_link)}"

            match = re.search(r'\[COLOR.*?\](.*?)\[/COLOR\]', link)
            sender = match.group(1).split(":")[0].strip() if match else "Unbekannt"

            li = xbmcgui.ListItem(label=f"[COLORred]{sender}[/COLOR]")
            li.setProperty("IsPlayable", "true")
            xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=False)

        xbmcplugin.endOfDirectory(HANDLE)

    except Exception as e:
        xbmcgui.Dialog().notification("Stream-Fehler", str(e), xbmcgui.NOTIFICATION_ERROR)


def router(paramstring):
    params = urllib.parse.parse_qs(paramstring)
    action = params.get("action", [None])[0]
    league = params.get("league", [None])[0]
    id = params.get("id", [None])[0]
    category = params.get("category", [None])[0]
    stream_url = params.get("url", [None])[0]
    headers = params.get("headers", [None])[0]  # Neu: Header-Parameter

    if action == "list_games" and league:
        list_games_for_league(league)
    elif action == "list_category":
        list_category(category)
    elif action == "list_sender":
        list_sender()
    elif action == "list_m3u":
        list_m3u_senders()
    elif action == "streams" and league and id:
        list_streams(league, id)
    elif action == "play" and stream_url:
        play_stream(stream_url, raw_headers=headers)
    elif action == "test_menu":
        list_test_menu()
    elif action == "open_number_input":
        open_number_input()
    elif action == "show_stream_info":
        show_stream_info()
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
    router(sys.argv[2][1:])
