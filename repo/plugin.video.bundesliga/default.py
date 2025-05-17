import sys
import json
import urllib.request
import urllib.parse
import xbmcplugin
import xbmcgui
import re
from datetime import datetime

HANDLE = int(sys.argv[1])
BASE_URL = sys.argv[0]

# URLs für die verschiedenen Ligen
URLS = {
    "Bundesliga": "https://magnetic.website/MAD_TITAN_SPORTS/SPORTS/LEAGUE/titansports_soccer.json",
    "2. Bundesliga": "https://magnetic.website/MAD_TITAN_SPORTS/SPORTS/LEAGUE/titansports_soccer.json",
    "Premier League": "https://magnetic.website/MAD_TITAN_SPORTS/SPORTS/LEAGUE/titansports_england_soccer.json",
    "La Liga": "https://magnetic.website/MAD_TITAN_SPORTS/SPORTS/LEAGUE/titansports_soccer.json",
    "Ligue 1": "https://magnetic.website/MAD_TITAN_SPORTS/SPORTS/LEAGUE/titansports_soccer.json",
    "Serie A": "https://magnetic.website/MAD_TITAN_SPORTS/SPORTS/LEAGUE/titansports_soccer.json",
    "Champions League": "https://magnetic.website/MAD_TITAN_SPORTS/SPORTS/LEAGUE/titansports_soccer.json",
    "Bundesliga Frauen": "https://magnetic.website/MAD_TITAN_SPORTS/SPORTS/LEAGUE/titansports_soccer.json",
    "2. Bundesliga Frauen": "https://magnetic.website/MAD_TITAN_SPORTS/SPORTS/LEAGUE/titansports_soccer.json",
    "Premier League Frauen": "https://magnetic.website/MAD_TITAN_SPORTS/SPORTS/LEAGUE/titansports_england_soccer.json",
    "La Liga Frauen": "https://magnetic.website/MAD_TITAN_SPORTS/SPORTS/LEAGUE/titansports_soccer.json",
    "Ligue 1 Frauen": "https://magnetic.website/MAD_TITAN_SPORTS/SPORTS/LEAGUE/titansports_soccer.json",
    "Serie A Frauen": "https://magnetic.website/MAD_TITAN_SPORTS/SPORTS/LEAGUE/titansports_soccer.json",
    "Champions League Frauen": "https://magnetic.website/MAD_TITAN_SPORTS/SPORTS/LEAGUE/titansports_soccer.json",
    "Europa League": "https://magnetic.website/MAD_TITAN_SPORTS/SPORTS/LEAGUE/titansports_soccer.json",
    "Europa League Frauen": "https://magnetic.website/MAD_TITAN_SPORTS/SPORTS/LEAGUE/titansports_soccer.json"
}

# Bilder für die Ligen
IMAGES = {
    "Bundesliga": "https://raw.githubusercontent.com/EliasTX09/resources/main/Ligen/bundesliga.png",
    "2. Bundesliga": "https://raw.githubusercontent.com/EliasTX09/resources/main/Ligen/bundesliga.png",
    "Premier League": "https://raw.githubusercontent.com/EliasTX09/resources/main/Ligen/Premiere.png",
    "La Liga": "https://raw.githubusercontent.com/EliasTX09/Jane/main/Laliga.png",
    "Ligue 1": "https://raw.githubusercontent.com/EliasTX09/resources/main/Ligen/ligue1.png",
    "Serie A": "https://raw.githubusercontent.com/EliasTX09/resources/main/Ligen/seriea.png",
    "Champions League": "https://raw.githubusercontent.com/EliasTX09/Jane/main/championsleauge.png",
    "Bundesliga Frauen": "https://raw.githubusercontent.com/EliasTX09/resources/main/Ligen/bundesliga.png",
    "2. Bundesliga Frauen": "https://raw.githubusercontent.com/EliasTX09/resources/main/Ligen/bundesliga.png",
    "Premier League Frauen": "https://raw.githubusercontent.com/EliasTX09/resources/main/Ligen/Premiere.png",
    "La Liga Frauen": "https://raw.githubusercontent.com/EliasTX09/resources/main/Ligen/Laliga.png",
    "Ligue 1 Frauen": "https://raw.githubusercontent.com/EliasTX09/resources/main/Ligen/ligue1.png",
    "Serie A Frauen": "https://raw.githubusercontent.com/EliasTX09/resources/main/Ligen/seriea.png",
    "Champions League Frauen": "https://raw.githubusercontent.com/EliasTX09/resources/main/Ligen/championsleauge.png",
    "Europa League": "https://raw.githubusercontent.com/EliasTX09/resources/main/Ligen/Europaleauge.png",
    "Europa League Frauen": "https://raw.githubusercontent.com/EliasTX09/resources/main/Ligen/Europaleauge.png"
}

SENDER = [
    {
        "name": "DAZN 1",
        "url": "plugin://plugin.video.madtitansports/sportjetextractors/play?urls=https://daddylive.mp/stream/stream-426.php",
        "image": "https://raw.githubusercontent.com/EliasTX09/resources/main/sender/dazn/DAZN1.png"
    },
    {
        "name": "DAZN 2",
        "url": "plugin://plugin.video.madtitansports/sportjetextractors/play?urls=https://daddylive.dad/stream/stream-427.php",
        "image": "https://raw.githubusercontent.com/EliasTX09/resources/main/sender/dazn/DAZN2.png"
    },
    {
        "name": "Sky Sport Bundesliga",
        "url": "plugin://plugin.video.madtitansports/sportjetextractors/play?urls=https://daddylive.dad/stream/stream-558.php",
        "image": "https://raw.githubusercontent.com/EliasTX09/resources/main/sender/sky/skybl1.png"
    },
     {
         "name": "Sky Sport Bundesliga 2",
         "url": "plugin://plugin.video.madtitansports/sportjetextractors/play?urls=https://daddylive.dad/stream/stream-19.php",
         "image": "https://raw.githubusercontent.com/EliasTX09/resources/main/sender/sky/skybl2.png"
     },
     {
         "name": "Sky Sport Bundesliga 3",
          "url": "plugin://plugin.video.madtitansports/sportjetextractors/play?urls=https://daddylive.dad/stream/stream-18.php",
         "image": "https://raw.githubusercontent.com/EliasTX09/resources/main/sender/sky/skybl3.png"
     },
     {
         "name": "Sky Sport Bundesliga 4",
         "url": "plugin://plugin.video.madtitansports/sportjetextractors/play?urls=https://daddylive.dad/stream/stream-21.php",
         "image": "https://raw.githubusercontent.com/EliasTX09/resources/main/sender/sky/skybl4.png"
     },
     {
         "name": "Sky Sport Bundesliga 5",
         "url": "plugin://plugin.video.madtitansports/sportjetextractors/play?urls=https://daddylive.dad/stream/stream-23.php",
         "image": "https://raw.githubusercontent.com/EliasTX09/resources/main/sender/sky/skybl5.png"
     },
     {
         "name": "Sky Sport Bundesliga 6",
         "url": "plugin://plugin.video.madtitansports/sportjetextractors/play?urls=https://daddylive.dad/stream/stream-17.php",
         "image": "https://raw.githubusercontent.com/EliasTX09/resources/main/sender/sky/skybl6.png"
     },
     {
         "name": "Sky Sport Bundesliga 7",
         "url": "plugin://plugin.video.madtitansports/sportjetextractors/play?urls=https://daddylive.dad/stream/stream-20.php",
         "image": "https://raw.githubusercontent.com/EliasTX09/resources/main/sender/sky/skybl7.png"
     },
     {
         "name": "Sky Sport Bundesliga 8",
         "url": "plugin://plugin.video.madtitansports/sportjetextractors/play?urls=https://daddylive.dad/stream/stream-25.php",
         "image": "https://raw.githubusercontent.com/EliasTX09/resources/main/sender/sky/skybl8.png"
     },
     {
         "name": "Sky Sport Bundesliga 9",
         "url": "plugin://plugin.video.madtitansports/sportjetextractors/play?urls=https://daddylive.dad/stream/stream-24.php",
         "image": "https://raw.githubusercontent.com/EliasTX09/resources/main/sender/sky/skybl9.png"
     },
     {
         "name": "Sky Sport Bundesliga 10",
         "url": "plugin://plugin.video.madtitansports/sportjetextractors/play?urls=https://daddylive.dad/stream/stream-22.php",
         "image": "https://raw.githubusercontent.com/EliasTX09/resources/main/sender/sky/skybl10.png"
     },
]


def list_sender():
    for sender in SENDER:
        li = xbmcgui.ListItem(label=sender["name"])
        li.setProperty("IsPlayable", "true")
        li.setArt({"thumb": sender["image"], "icon": sender["image"], "poster": sender["image"]})
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=sender["url"], listitem=li, isFolder=False)
    xbmcplugin.endOfDirectory(HANDLE)

def convert_time_string_manually(et_string):
    try:
        match = re.search(r'(\d{1,2}):(\d{2}) (\[AP]M)', et_string)
        if not match:
            return et_string
        hour, minute, period = int(match.group(1)), int(match.group(2)), match.group(3)
        if period == "PM" and hour != 12:
            hour += 12
        elif period == "AM" and hour == 12:
            hour = 0

        hour += 6
        if hour >= 24:
            hour -= 24

        return f"{hour:02}:{minute:02} Uhr"
    except Exception:
        return et_string

def replace_time_in_title(title):
    time_match = re.search(r'(\d{1,2}/\d{1,2} )?(\d{1,2}:\d{2} \[AP]M)', title)
    if time_match:
        original_time = time_match.group(2)
        converted = convert_time_string_manually(original_time)
        return title.replace(original_time, f"[COLORyellow]{converted}[/COLOR]")
    return title

def list_main_menu():
    for category in ["Männerligen", "Frauenligen"]:
        url = f"{BASE_URL}?action=list_category&category={urllib.parse.quote(category)}"
        li = xbmcgui.ListItem(label=category)
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=True)

    # Sender-Ordner hinzufügen
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

    is_female = any(word in content for word in ["frau", "frauen", "women"])
    league_name = league.lower()

    if "champions league" in league_name:
        return any(kw in content for kw in ["champions league", "champions-league"])

    if "frauen" in league_name and is_female:
        return league_name.replace(" frauen", "") in content
    if "frauen" not in league_name and not is_female:
        return league_name in content
    return False

def is_excluded_from_bundesliga(item):
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
        "2. bundesliga"
    ]
    return any(excl in content for excl in EXCLUDES)

def list_games_for_league(league):
    try:
        url = URLS.get(league)
        if not url:
            raise Exception("Keine URL für Liga gefunden.")
        response = urllib.request.urlopen(url)
        data = json.loads(response.read())
        items = data.get("items", [])

        shown_titles = set()

        # Immer zuerst: Reload + Suche
        reload_item = xbmcgui.ListItem(label="[COLORred]--------- [COLOR khaki]Neu laden[/COLOR][COLORred] ---------[/COLOR]")
        xbmcplugin.addDirectoryItem(
            handle=HANDLE,
            url="plugin://plugin.video.madtitansports/refresh_menu",
            listitem=reload_item,
            isFolder=False
        )

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
            if league == "Bundesliga" and is_excluded_from_bundesliga(item):
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
            match = re.search(r'\[COLOR.*?\](.*?)\[/COLOR\]', link)
            sender = match.group(1).split(":")[0].strip() if match else "Unbekannt"
            li = xbmcgui.ListItem(label=f"[COLORred]{sender}[/COLOR]")
            li.setProperty("IsPlayable", "true")
            xbmcplugin.addDirectoryItem(handle=HANDLE, url=link.split("(")[0], listitem=li, isFolder=False)

        xbmcplugin.endOfDirectory(HANDLE)

    except Exception as e:
        xbmcgui.Dialog().notification("Stream-Fehler", str(e), xbmcgui.NOTIFICATION_ERROR)

def router(paramstring):
    params = urllib.parse.parse_qs(paramstring)
    action = params.get("action", [None])[0]
    league = params.get("league", [None])[0]
    id = params.get("id", [None])[0]
    category = params.get("category", [None])[0]

    if action == "list_games" and league:
        list_games_for_league(league)
    elif action == "list_category":
        list_category(category)
    elif action == "list_sender":
        list_sender()
    elif action == "streams" and league and id:
        list_streams(league, id)
    else:
        list_main_menu()

if __name__ == "__main__":
    router(sys.argv[2][1:])
