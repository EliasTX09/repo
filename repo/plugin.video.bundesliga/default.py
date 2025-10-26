# -*- coding: utf-8 -*-
import sys
import urllib.parse
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
from resources.lib import api  # ✅ Richtig eingebunden für Kodi 21+

ADDON = xbmcaddon.Addon()
HANDLE = int(sys.argv[1])
BASE_URL = sys.argv[0]

xbmc.log("default.py: Addon gestartet.", xbmc.LOGINFO)


# ===============================
# Hilfsfunktionen
# ===============================
def build_url(query):
    """Erstellt Plugin-URL mit Parametern."""
    return BASE_URL + '?' + urllib.parse.urlencode(query)


# ===============================
# Senderliste (Hauptmenü)
# ===============================
def list_senders():
    xbmc.log("default.list_senders: Lade Sender...", xbmc.LOGINFO)
    try:
        data = api.load_json(api.get_main_source())
        if not data:
            xbmcgui.Dialog().ok("Fehler", "Keine Sender gefunden.")
            return

        for idx, item in enumerate(data):
            title = item.get("title", f"Sender {idx}")
            thumb = item.get("thumbnail", "")
            has_multi = any(k.startswith("link(") for k in item.keys())

            url = build_url({
                'action': 'list_streams',
                'item_id': idx,
                'source': api.get_main_source()
            })

            # 🎬 EPG abrufen
            epg_info = api.get_epg_info(item.get("id", ""))
            if epg_info:
                now_title = epg_info.get("title", "Keine Daten")
                next_title = epg_info.get("next_title", "Keine Daten")
                display_title = (
                    f"[COLOR orange]{title}[/COLOR]  |  [COLOR red]Jetzt:[/COLOR] {now_title}  |  [COLOR green]Danach:[/COLOR] {next_title}"
                )
                desc = f"Jetzt: {now_title}\nDanach: {next_title}"
            else:
                display_title = f"[COLOR orange]{title}[/COLOR]  |  [COLOR gray]Keine EPG-Daten[/COLOR]"
                desc = "Keine EPG-Daten verfügbar."

            li = xbmcgui.ListItem(label=display_title)
            li.setArt({'thumb': thumb, 'icon': thumb})
            li.setProperty("IsPlayable", "false")
            li.setInfo("video", {"title": title, "plot": desc})

            xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=has_multi)

        xbmcplugin.endOfDirectory(HANDLE)

    except Exception as e:
        xbmc.log(f"default.list_senders Fehler: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().ok("Fehler", f"Senderliste konnte nicht geladen werden:\n{e}")


# ===============================
# Unterstreams anzeigen
# ===============================
def list_streams(source, item_id):
    xbmc.log(f"default.list_streams: source={source}, item_id={item_id}", xbmc.LOGINFO)
    try:
        items = api.get_items(source)
        item = next((x for x in items if str(x["id"]) == str(item_id)), None)
        if not item:
            xbmcgui.Dialog().ok("Fehler", "Sender nicht gefunden.")
            return

        streams = item.get("multi", [])
        if not streams:
            xbmcgui.Dialog().ok("Fehler", "Keine Streams gefunden.")
            return

        for s in streams:
            li = xbmcgui.ListItem(label=s["title"])
            li.setArt({'thumb': s.get("thumbnail", ""), 'icon': s.get("thumbnail", "")})
            li.setProperty("IsPlayable", "true")

            url = build_url({'action': 'play', 'url': s["url"]})
            xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=False)

        xbmcplugin.endOfDirectory(HANDLE)

    except Exception as e:
        xbmc.log(f"default.list_streams Fehler: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().ok("Fehler", f"Stream-Liste konnte nicht geladen werden:\n{e}")


# ===============================
# Stream abspielen
# ===============================
def play_stream(url):
    xbmc.log(f"default.play_stream: Starte Wiedergabe: {url}", xbmc.LOGINFO)
    try:
        li = xbmcgui.ListItem(path=url)
        li.setProperty("inputstream", "inputstream.ffmpegdirect")
        li.setProperty("inputstream.ffmpegdirect.is_realtime_stream", "true")
        xbmcplugin.setResolvedUrl(HANDLE, True, li)
    except Exception as e:
        xbmc.log(f"default.play_stream Fehler: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().ok("Fehler", f"Stream konnte nicht gestartet werden:\n{e}")


# ===============================
# Router
# ===============================
def router(paramstring):
    params = dict(urllib.parse.parse_qsl(paramstring))
    action = params.get('action')

    if action is None:
        list_senders()
    elif action == 'list_streams':
        list_streams(params.get('source'), params.get('item_id'))
    elif action == 'play':
        play_stream(params.get('url'))
    else:
        xbmcgui.Dialog().ok("Fehler", f"Unbekannte Aktion: {action}")


if __name__ == '__main__':
    router(sys.argv[2][1:])
