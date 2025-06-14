import sys
import urllib.parse
import xbmc
import xbmcgui
import xbmcplugin
import requests

from resources.lib.jetextractors.extractors.daddylive import Daddylive
from resources.lib.jetextractors.models import JetLink

_handle = int(sys.argv[1])
_base_url = sys.argv[0]

# Header-String, der an die Stream-URL angehängt wird
HEADER_STRING = (
    "|Referer=https://alldownplay.xyz/" +
    "&Origin=https://alldownplay.xyz" +
    "&Connection=Keep-Alive" +
    "&User-Agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
)

def notify(msg):
    xbmc.log(f"[MADTITAN] {msg}", xbmc.LOGINFO)
    xbmcgui.Dialog().notification("Mad Titan", msg, xbmcgui.NOTIFICATION_INFO, 2000)

def build_url(query):
    return _base_url + '?' + urllib.parse.urlencode(query)

def list_menu():
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

        xbmcplugin.addDirectoryItem(handle=_handle, url=item_url, listitem=li, isFolder=False)

    xbmcplugin.endOfDirectory(_handle)

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

        xbmcplugin.setResolvedUrl(_handle, True, li)
        notify("Stream wird abgespielt...")

    except Exception as e:
        notify(f"Fehler: {e}")

def router(paramstring):
    params = dict(urllib.parse.parse_qsl(paramstring))
    action = params.get('action')

    if action == 'play' and 'url' in params:
        play_stream(params['url'])
    else:
        list_menu()

if __name__ == '__main__':
    router(sys.argv[2][1:] if len(sys.argv) > 2 else '')
