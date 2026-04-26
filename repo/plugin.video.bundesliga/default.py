# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import requests
from datetime import datetime, timezone, timedelta
import json
import urllib.parse

ADDON = xbmcaddon.Addon()
ADDON_NAME = ADDON.getAddonInfo('name')
HANDLE = int(sys.argv[1])

JSON_URL = "https://magnetic.website/MAD_TITAN_SPORTS/SPORTS/LEAGUE/titansports_all_soccer_events.json"
M3U_URL  = "https://raw.githubusercontent.com/EliasTX09/json/refs/heads/main/KODI1.m3u"

# ====================== LIGEN ======================
LIGEN = {
    "All": "🌍 Alle Spiele heute",
    "Germany - Bundesliga": "🇩🇪 Bundesliga",
    "Germany - Bundesliga 2": "🇩🇪 2. Bundesliga",
    "Germany - 3. Liga": "🇩🇪 3. Liga",
    "Germany - Frauen-Bundesliga": "🇩🇪 Frauen-Bundesliga",
    "Spain - La Liga": "🇪🇸 La Liga",
    "Italy - Serie A": "🇮🇹 Serie A",
    "France - Ligue 1": "🇫🇷 Ligue 1",
    "England - Premier League": "🇬🇧 Premier League",
    "Champions League": "🏆 Champions League",
    "Europa League": "🏆 Europa League",
    "Netherlands - Eredivisie": "🇳🇱 Eredivisie",
    "Portugal - Primeira Liga": "🇵🇹 Primeira Liga",
    "Turkey - Super Lig": "🇹🇷 Süper Lig"
}

# Cache für M3U
M3U_DICT = None

def load_m3u():
    global M3U_DICT
    if M3U_DICT is not None:
        return M3U_DICT

    try:
        r = requests.get(M3U_URL, timeout=10)
        r.raise_for_status()
        lines = r.text.splitlines()

        m3u_dict = {}
        i = 0
        while i < len(lines):
            if lines[i].startswith('#EXTINF'):
                name = lines[i].split(',', 1)[-1].strip()
                if i + 1 < len(lines) and lines[i+1].startswith('http'):
                    m3u_dict[name] = lines[i+1].strip()
            i += 1

        M3U_DICT = m3u_dict
        xbmc.log(f"[TitanSports] M3U geladen: {len(m3u_dict)} Kanäle", xbmc.LOGINFO)
        return m3u_dict
    except Exception as e:
        xbmc.log(f"[TitanSports ERROR] M3U laden fehlgeschlagen: {e}", xbmc.LOGERROR)
        return {}


def build_url(query):
    return sys.argv[0] + '?' + '&'.join([f"{k}={urllib.parse.quote(str(v))}" for k, v in query.items()])


def unix_to_german_time(unix_ts):
    try:
        dt_utc = datetime.fromtimestamp(unix_ts, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        is_cest = (now.month > 3 and now.month < 11)
        offset = timedelta(hours=2) if is_cest else timedelta(hours=1)
        dt_german = dt_utc + offset
        return dt_german.strftime('%d.%m.%Y %H:%M Uhr')
    except:
        return "Zeit unbekannt"


def load_json():
    try:
        r = requests.get(JSON_URL, timeout=15)
        r.raise_for_status()
        data = r.json()
        items = data if isinstance(data, list) else data.get('items', [])
        xbmc.log(f"[TitanSports DEBUG] JSON geladen: {len(items)} Events", xbmc.LOGINFO)
        return items
    except Exception as e:
        xbmc.log(f"[TitanSports ERROR] JSON Error: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification(ADDON_NAME, "JSON nicht erreichbar", xbmcgui.NOTIFICATION_ERROR)
        return []


def is_league_match(league_key: str, title: str) -> bool:
    if not title:
        return False
    t = title.lower()
    key = urllib.parse.unquote(league_key).lower().strip().replace("%20", " ")

    if key == "all":
        return True
    if key == "germany - bundesliga":
        if "germany - bundesliga" in t or "bundesliga :" in t or "bundesliga:" in t:
            return not any(x in t for x in ["austrian", "austria", "österreich", "2. bundesliga", "bundesliga 2", "3. liga", "frauen"])
    if key == "germany - bundesliga 2":
        return any(x in t for x in ["2. bundesliga", "bundesliga 2"])
    if key == "germany - 3. liga":
        return "3. liga" in t
    if key == "germany - frauen-bundesliga":
        return any(x in t for x in ["frauen-bundesliga", "frauen bundesliga"])
    if key == "spain - la liga":
        return "la liga" in t or "laliga" in t
    if key == "italy - serie a":
        return "serie a" in t
    if key == "france - ligue 1":
        return "ligue 1" in t
    if key == "england - premier league":
        return "premier league" in t
    if key == "champions league":
        return "champions league" in t
    if key == "europa league":
        return "europa league" in t

    return False


def show_main_menu():
    xbmcplugin.setContent(HANDLE, 'files')
    for key, name in LIGEN.items():
        li = xbmcgui.ListItem(label=name)
        url = build_url({'action': 'matches', 'league': key})
        xbmcplugin.addDirectoryItem(HANDLE, url, li, isFolder=True)
    xbmcplugin.endOfDirectory(HANDLE)


def show_matches(league_key):
    xbmcplugin.setContent(HANDLE, 'videos')
    items = load_json()
    found = 0

    for item in items:
        raw_title = item.get('title', '')
        guidedata = item.get('guidedata', [{}])[0]
        unix_ts = guidedata.get('starttime')
        channels = item.get('channels', [])

        if not unix_ts:
            continue
        if not is_league_match(league_key, raw_title):
            continue

        found += 1
        german_time = unix_to_german_time(unix_ts)

        clean_title = raw_title.split('|')[-1].strip() if '|' in raw_title else raw_title
        clean_title = clean_title.replace('[COLORaqua]', '').replace('[/COLOR]', '').replace('[COLORyellow]', '').replace('[/COLOR]', '')

        label = f"{clean_title} • {german_time}"

        li = xbmcgui.ListItem(label=label)
        li.setInfo('video', {
            'title': clean_title,
            'plot': f"Zeit: {german_time}\n{len(channels)} Sender verfügbar"
        })

        url = build_url({
            'action': 'sender',
            'title': clean_title,
            'time': german_time,
            'channels': json.dumps(channels, ensure_ascii=False)
        })

        xbmcplugin.addDirectoryItem(HANDLE, url, li, isFolder=True)

    if found == 0:
        li = xbmcgui.ListItem(f"Keine Spiele für '{LIGEN.get(league_key, league_key)}' gefunden.")
        xbmcplugin.addDirectoryItem(HANDLE, "", li, isFolder=False)

    xbmcplugin.endOfDirectory(HANDLE)


def show_sender(title, time, channels_json):
    xbmc.log(f"[TitanSports DEBUG] show_sender gestartet | Spiel: {title}", xbmc.LOGINFO)

    try:
        channels = json.loads(channels_json) if channels_json and channels_json != '[]' else []
    except Exception as e:
        xbmc.log(f"[TitanSports ERROR] JSON decode fehlgeschlagen: {e}", xbmc.LOGERROR)
        channels = []

    m3u_dict = load_m3u()
    displayed = 0

    xbmcplugin.setContent(HANDLE, 'videos')

    for ch in channels:
        ch_name = ch.get('channel_name', 'Unbekannter Sender')

        stream_url = m3u_dict.get(ch_name)
        if not stream_url:
            for m_name, url in m3u_dict.items():
                if ch_name.lower() in m_name.lower() or m_name.lower() in ch_name.lower():
                    stream_url = url
                    break

        if stream_url:
            displayed += 1
            li = xbmcgui.ListItem(label=ch_name)
            li.setInfo('video', {'title': ch_name, 'plot': f"{title}\nZeit: {time}"})
            li.setProperty('IsPlayable', 'true')

            play_url = build_url({'action': 'play', 'url': stream_url})
            xbmcplugin.addDirectoryItem(HANDLE, play_url, li, isFolder=False)
        else:
            li = xbmcgui.ListItem(label=f"{ch_name} [COLORred](kein Stream)[/COLOR]")
            xbmcplugin.addDirectoryItem(HANDLE, "", li, isFolder=False)

    xbmc.log(f"[TitanSports DEBUG] {displayed} Sender mit Stream angezeigt", xbmc.LOGINFO)

    if displayed == 0:
        xbmcgui.Dialog().ok(ADDON_NAME, f"[B]{title}[/B]\n\n📅 {time}\n\nKeine abspielbaren Sender gefunden.")

    xbmcplugin.endOfDirectory(HANDLE)


def play_stream(stream_url):
    xbmc.log(f"[TitanSports] Starte Stream: {stream_url[:100]}...", xbmc.LOGINFO)
    li = xbmcgui.ListItem(path=stream_url)
    xbmcplugin.setResolvedUrl(HANDLE, True, li)


def main():
    paramstring = sys.argv[2][1:] if len(sys.argv) > 2 else ""
    args = dict(urllib.parse.parse_qsl(paramstring))

    action = args.get('action')
    xbmc.log(f"[TitanSports DEBUG] main() Action = {action}", xbmc.LOGINFO)

    if action == 'matches':
        show_matches(args.get('league', 'All'))
    elif action == 'sender':
        show_sender(
            args.get('title', ''),
            args.get('time', ''),
            args.get('channels', '[]')
        )
    elif action == 'play':
        play_stream(args.get('url', ''))
    else:
        show_main_menu()


if __name__ == '__main__':
    main()