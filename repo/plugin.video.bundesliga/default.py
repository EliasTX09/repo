
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

# ==============================
# Konfigurierbare Konstanten
# ==============================

_JSON_URL_URLS = "https://raw.githubusercontent.com/EliasTX09/json/main/Others/FOOTBALL_LEAUGES.json"
IMAGES_JSON_URL = "https://raw.githubusercontent.com/EliasTX09/json/main/Others/PICTURES"
SENDER_JSON_URL = "https://raw.githubusercontent.com/EliasTX09/json/main/IPTV/SENDER.json"
M4U_SOURCE_URL = "https://raw.githubusercontent.com/EliasTX09/json/main/IPTV/IPTV_LINK.json"
IPTV_SETTINGS_URL = "https://raw.githubusercontent.com/EliasTX09/json/main/IPTV/IPTV_SETUP.xml"



HEADER_STRING = (
    "|Referer=https://alldownplay.xyz/"
    "&Origin=https://alldownplay.xyz"
    "&Connection=Keep-Alive"
    "&User-Agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
)

BASE_URL = sys.argv[0]

######################################################################################################################################
######################################################################################################################################
####                                          JSONS UND HEADERS                                                                   ####
######################################################################################################################################
######################################################################################################################################




def get_source_url():
    addon = xbmcaddon.Addon()
    mode = addon.getSetting("m4u_mode") or "f"  # Standard: f
    return M4U_SOURCE_URL

######################################################################################################################################
######################################################################################################################################
####                                                       JSONS LADEN                                                            ####
######################################################################################################################################
######################################################################################################################################
def load_json_from_url(url):
    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        xbmc.log(f"[M4U] Fehler beim Laden der JSON: {e}", xbmc.LOGERROR)
        return []


# URLs und Senderliste laden
URLS = load_json_from_url(_JSON_URL_URLS) or {}
IMAGES = load_json_from_url(IMAGES_JSON_URL) or {}
######################################################################################################################################
######################################################################################################################################
####                                                   MENÜS LISTEN                                                               ####
######################################################################################################################################
######################################################################################################################################

#------------------------------------------------MAIN MENU---------------------------------------------------------------------------#

def list_main_menu():
    for category in ["Männerligen", "Frauenligen"]:
        url = f"{BASE_URL}?action=list_category&category={urllib.parse.quote(category)}"
        li = xbmcgui.ListItem(label=category)

        if category == "Männerligen":
            icon = "https://cdn.futwiz.com/assets/img/fifa21/faces/84125165.png"
        else:
            icon = "https://upload.wikimedia.org/wikipedia/commons/3/30/Brighton_%26_Hove_Albion_Women_v_Manchester_United_Women_Shortcut.png"

        # setArt() ist für beide Kategorien gleich
        li.setArt({
            'thumb': icon,
            'icon': icon,
            'poster': icon,
        })

        xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=True)





    url = f"{BASE_URL}?action=list_channels"
    li = xbmcgui.ListItem(label="[COLOR lime]Sender[/COLOR]")
    icon = "https://cdn-icons-png.flaticon.com/512/168/168843.png"

# Bild setzen
    li.setArt({
    'thumb': icon,
    'icon': icon,
    'poster': icon,})
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=True)


    li = xbmcgui.ListItem(label="[B][COLORyellow]TV Menu Setup[/COLOR][/B]")
    url = f"{sys.argv[0]}?action=configure_iptv_simple"
    icon = "https://techeasy.ca/wp-content/uploads/2023/07/Tv-Setup-1024x683.jpg"

# Bild setzen
    li.setArt({
    'thumb': icon,
    'icon': icon,
    'poster': icon,})    
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=False)



    #///////////TESTORDNER\\\\\\\\\\\\\#
    #url = f"{BASE_URL}?action="
    #li = xbmcgui.ListItem(label="[B][COLORorange]Test[/COLOR][/B]")
    #xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(HANDLE)

#----------------------------------------------------TEST MENU-------------------------------------------------------------------------#

def list_test_menu():

    test_sender_url = f"{BASE_URL}?action=list_test_daddy"
    li_test_sender = xbmcgui.ListItem(label="[COLORyellow]Sender Testweise[/COLOR]")
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=test_sender_url, listitem=li_test_sender, isFolder=True)

    xbmcplugin.endOfDirectory(HANDLE)


######################################################################################################################################
######################################################################################################################################
####                                                ZEIT UMWANDELN                                                                ####
######################################################################################################################################
######################################################################################################################################

#-------------------------------------------UMWANDELN---------------------------------#

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

#--------------------------ZEIT IM TITEL EINSETZEN--------------------------------------#

def replace_time_in_title(title):
    time_match = re.search(r'(\d{1,2}/\d{1,2} )?(\d{1,2}:\d{2} [AP]M)', title)
    if time_match:
        original_time = time_match.group(2)
        converted = convert_time_string_with_pytz(original_time)
        return title.replace(original_time, f"[COLORyellow]{converted}[/COLOR]")
    return title

######################################################################################################################################
######################################################################################################################################
####                                                       LISTEN                                                                 ####
######################################################################################################################################
######################################################################################################################################

#--------------------------------------------STREAMS LISTEN-----------------------------------------------#

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

#--------------------------------------DDY SENDER-------------------------------------------#


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

#------------------------------------IPTV SETUP--------------------------------------------#


def configure_iptv_simple():
    import xbmcgui, xbmcvfs, os, urllib.request, xbmc

    try:
        url = IPTV_SETTINGS_URL
        addon_data_path = xbmcvfs.translatePath("special://userdata/addon_data/pvr.iptvsimple/")
        settings_file = os.path.join(addon_data_path, "instance-settings-2.xml")

        # Sicherstellen, dass der Zielordner existiert
        if not xbmcvfs.exists(addon_data_path):
            xbmcvfs.mkdirs(addon_data_path)

        # Datei von der URL herunterladen
        response = urllib.request.urlopen(url, timeout=5)
        content = response.read()

        # Datei im angegebenen Verzeichnis speichern
        with xbmcvfs.File(settings_file, 'w') as f:
            f.write(content)

    except Exception as e:
        # Optional: Fehlerprotokollierung oder Debugging
        xbmc.log(f"Fehler bei der IPTV-Konfiguration: {str(e)}", xbmc.LOGERROR)
        pass  # Alle Fehler vollständig unterdrücken – keine Meldung im Dialog

    # Erfolgsdialog anzeigen
    xbmcgui.Dialog().ok("✅ IPTV Simple", "Konfiguration erfolgreich geladen.\nKodi wird jetzt beendet.")

    # Kodi sicher beenden
    xbmc.restart()


#------------------------------------M4U SENDER---------------------------------------------#

def list_channels():
    
    url = f"{BASE_URL}?action=list_sender"
    li = xbmcgui.ListItem(label="ERSATZ")
    xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=True)
    
    # Quelle fest holen (z. B. aus GitHub verlinkter JSON)
    M4U_URL = get_source_url()
    master_data = load_json_from_url(M4U_URL)
    if not master_data:
        xbmcgui.Dialog().notification("Fehler", "Konnte Senderliste nicht laden", xbmcgui.NOTIFICATION_ERROR)
        return

    source_urls = master_data.get("sources", [])
    if not source_urls:
        xbmcgui.Dialog().notification("Fehler", "Keine Quellen gefunden", xbmcgui.NOTIFICATION_ERROR)
        return

    for source_url in source_urls:
        channels = load_json_from_url(source_url)
        if not channels:
            continue

        for channel in channels:
            name = channel.get('title', 'Unbenannt')
            logo = channel.get('thumbnail', '') or channel.get('logo', '')
            url = build_url({'action': 'list_qualities_direct', 'data': quote_plus(json.dumps(channel))})
            li = xbmcgui.ListItem(label=name)
            li.setArt({'icon': logo, 'thumb': logo})
            li.setProperty("IsPlayable", "false")
            xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(HANDLE)


#------------------------------------FUSSBALL SPIELE----------------------------------------#

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
        
######################################################################################################################################
######################################################################################################################################
####                                                   FILTER                                                                     ####
######################################################################################################################################
######################################################################################################################################

#--------------------------------------------SPIELE IN LIGA ORDNEN----------------------------------#
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


#------------------------------------------------BUNDESLIGA FILTER---------------------------#

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

#---------------------------------------MÄNNER UND FRAUEN SORTIEREN-----------------------------------------------#

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

#-------------------------------------STREAMOPTIONEN---------------------------------------------------------------#

def list_qualities_direct(params):
    data = params.get("data", [None])[0]
    if not data:
        return

    try:
        channel = json.loads(unquote_plus(data))
    except Exception:
        xbmcgui.Dialog().notification("Fehler", "Ungültige Senderdaten", xbmcgui.NOTIFICATION_ERROR)
        return

    # Durch alle Keys iterieren und passende name/link Paare finden
    i = 1
    colors = ["lime", "orange", "yellow", "cyan", "red", "magenta"]  # wechselnde Farben
    while True:
        link_key = f"link({i})"
        name_key = f"name({i})"

        url = channel.get(link_key)
        name = channel.get(name_key)

        if not url or not name:
            break  # Ende, wenn kein weiteres Paar existiert

        # Farbe auswählen (rotiert durch die Liste)
        color = colors[(i - 1) % len(colors)]
        label = f"[COLOR {color}]{name}[/COLOR]"

        li = xbmcgui.ListItem(label=label)
        li.setProperty("IsPlayable", "true")

        play_url = build_url({'action': 'play_stream_simple', 'stream': url})
        xbmcplugin.addDirectoryItem(handle=HANDLE, url=play_url, listitem=li, isFolder=False)

        i += 1

    xbmcplugin.endOfDirectory(HANDLE)




#----------------------------------------GRÜN UND ROT HAUPT UND NEBENSTREAM----------------------------#

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


######################################################################################################################################
######################################################################################################################################
####                                                 EXTRAHIEREN                                                                  ####
######################################################################################################################################
######################################################################################################################################

#-----------------------------------------SENDERNAME FÜR M3U8-----------------------#

def extract_sender_name(link):
    import re
    m = re.search(r'\[COLOR.*?\](.*?)\[/COLOR\]', link)
    if m:
        return m.group(1)
    else:
        return "Unbekannt"

#--------------------------------PUREN LINK EXTRAHIEREN------------------------------#

def extract_direct_url(plugin_link):
    import urllib.parse
    parsed = urllib.parse.urlparse(plugin_link)
    query = urllib.parse.parse_qs(parsed.query)
    urls = query.get("urls")
    if urls:
        return urls[0]
    return plugin_link.replace("plugin://plugin.video.madtitansports/sportjetextractors/play?urls=", "").split("(")[0]

######################################################################################################################################
######################################################################################################################################
####                                                   ABSPIELEN                                                                  ####
######################################################################################################################################
######################################################################################################################################

#-------------------------------------M3U8------------------------------------------#
from http.server import HTTPServer
from threading import Thread

# JetProxy importieren
from resources.lib.jetproxy.server import MyServer

def play_m3u8(stream_url):
    # Proxy-Server starten (einmalig – optional mit try/except, falls er schon läuft)
    server = HTTPServer(("127.0.0.1", 49777), MyServer)

    def run_server():
        with server:
            server.serve_forever()

    thread = Thread(target=run_server)
    thread.setDaemon(True)
    thread.start()

    xbmc.log("JetProxy: Server läuft auf http://127.0.0.1:49777", xbmc.LOGINFO)

    # Übergabe der URL an JetProxy
    proxy_url = f"http://127.0.0.1:49777/proxy?url={stream_url}"

    # Kodi-Player starten
    list_item = xbmcgui.ListItem(path=proxy_url)
    list_item.setProperty("IsPlayable", "true")

    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, list_item)



#-----------------------------------MIT EXTRACTOR---------------------------------#


def play_stream(url):
    try:
        notify("Extrahiere Stream...")
        extractor = Daddylive()
        link = extractor.get_link(JetLink(url))

        stream_url = link.address.split('|')[0]  # reine URL ohne Header

        # Headerstring an die URL anhängen
        stream_url_with_headers = stream_url + HEADER_STRING

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

#----------------------------------------Normal ohne header-------------------------#

def play_stream_simple(params):
    stream_url = params.get('stream', [None])[0]
    if not stream_url:
        xbmcgui.Dialog().notification("Fehler", "Keine Stream-URL übergeben", xbmcgui.NOTIFICATION_ERROR)
        return

    li = xbmcgui.ListItem(path=stream_url)
    li.setProperty("IsPlayable", "true")
    xbmcplugin.setResolvedUrl(HANDLE, True, li)


######################################################################################################################################
######################################################################################################################################
####                                             ROUTER                                                                           ####
######################################################################################################################################
######################################################################################################################################

def router(paramstring):
    import urllib.parse

    params = urllib.parse.parse_qs(paramstring)

    action = params.get("action", [None])[0]
    league = params.get("league", [None])[0]
    id = params.get("id", [None])[0]
    category = params.get("category", [None])[0]
    stream_url = params.get("url", [None])[0]
    headers = params.get("headers", [None])[0]
    stream = params.get("stream", [None])[0]
    stream_index = params.get("stream_index", [None])[0]

    if action == "list_games" and league:
        list_games_for_league(league)

    elif action == "list_sender":
        list_sender()

    elif action == "show_streams":
        show_streams(params)

    elif action == "play" and stream_url:
        play_stream(urllib.parse.unquote_plus(stream_url))

    elif action == "list_category" and category:
        list_category(category)

    elif action == "streams" and league and id:
        list_streams(league, id)

    elif action == "list_channels":
        list_channels()

    elif action == "list_qualities_direct":
        list_qualities_direct(params)

    elif action == "configure_iptv_simple":
        configure_iptv_simple()

    elif action == "play_stream_simple" and stream:
        play_stream_simple(params)

    elif action == "test_menu":
        list_test_menu()

    elif action == "enter_daddy_number":
        keyboard = xbmcgui.Dialog().input("Stream-Nummer eingeben", type=xbmcgui.INPUT_NUMERIC)
        if keyboard and keyboard.isdigit():
            xbmc.executebuiltin(f"RunPlugin({BASE_URL}?action=play_daddy&url={keyboard})")
        else:
            xbmcgui.Dialog().notification("Fehler", "Ungültige Eingabe", xbmcgui.NOTIFICATION_ERROR)

    else:
        list_main_menu()

# Einstiegspunkt
if __name__ == "__main__":
    import sys
    router(sys.argv[2][1:])


