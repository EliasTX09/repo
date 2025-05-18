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



HANDLE = int(sys.argv[1])
BASE_URL = sys.argv[0]

# URLs für die verschiedenen Ligen
_JSON_URL_URLS = "https://raw.githubusercontent.com/EliasTX09/json/main/json.json"


# Bilder für die Ligen
IMAGES_JSON_URL =  "https://raw.githubusercontent.com/EliasTX09/json/main/IMAGES"


SENDER_JSON_URL = "https://raw.githubusercontent.com/EliasTX09/json/main/sender.json"



def play_stream(raw_url):
    # raw_url ist z.B.: "http://example.com/stream.m3u8|User-Agent=MyAgent"
    url, *header_part = raw_url.split("|")
    headers = {}

    if header_part:
        # header_part[0] = "User-Agent=MyAgent"
        # evtl. mehrere Header durch & getrennt (z.B. User-Agent=xxx&Referer=yyy)
        for h in header_part[0].split("&"):
            if "=" in h:
                key, value = h.split("=", 1)
                headers[key] = value

    li = xbmcgui.ListItem(path=url)
    li.setProperty("IsPlayable", "true")

    # Header über Kodi-Property setzen (funktioniert bei manchen InputStream-Addons)
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

def list_sender():
    streams = load_json_from_url(SENDER_JSON_URL)
    if not streams:
        xbmcgui.Dialog().notification("Fehler", "Sender JSON konnte nicht geladen werden", xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(HANDLE)
        return

    for stream in streams:
        name = stream.get("name", "Unbekannt")
        logo = stream.get("logo", "")
        url = stream.get("url", "")

        li = xbmcgui.ListItem(label=name)
        li.setArt({"thumb": logo, "icon": logo, "fanart": logo})
        li.setProperty("IsPlayable", "true")
        li.setInfo("video", {"title": name})

        xbmcplugin.addDirectoryItem(
            handle=HANDLE,
            url=f"{BASE_URL}?action=play&url={urllib.parse.quote(url)}",
            listitem=li,
            isFolder=False
        )

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

    if action == "list_games" and league:
        list_games_for_league(league)
    elif action == "list_category":
        list_category(category)
    elif action == "list_sender":
        list_sender()
    elif action == "streams" and league and id:
        list_streams(league, id)
    elif action == "play" and stream_url:
        play_stream(stream_url)
    else:
        list_main_menu()




if __name__ == "__main__":
    router(sys.argv[2][1:])
