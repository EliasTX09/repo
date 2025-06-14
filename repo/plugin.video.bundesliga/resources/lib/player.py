import urllib.parse
import xbmc
import xbmcgui
import xbmcplugin

def play_stream(addon_handle, stream_url_with_headers: str):
    """
    Spielt einen HLS-Stream mit eingebetteten Headern ab.
    
    Beispiel:
        https://example.com/stream.m3u8|Referer=https://site.com&User-Agent=XYZ
    """
    try:
        parts = stream_url_with_headers.split('|')
        stream_url = parts[0]
        raw_headers = '|'.join(parts[1:]) if len(parts) > 1 else ''

        if raw_headers:
            headers_pairs = raw_headers.split('&')
            headers_formatted = "\r\n".join(h.replace('=', ': ', 1) for h in headers_pairs if '=' in h)
        else:
            headers_formatted = ''

        list_item = xbmcgui.ListItem(path=stream_url)
        list_item.setMimeType('application/vnd.apple.mpegurl')
        list_item.setProperty('IsPlayable', 'true')
        list_item.setProperty('inputstream', 'inputstream.ffmpegdirect')
        list_item.setProperty('inputstream.ffmpegdirect.manifest_type', 'hls')
        list_item.setProperty('inputstream.ffmpegdirect.stream_mode', 'simple')
        list_item.setProperty('inputstream.ffmpegdirect.is_realtime_stream', 'true')

        if headers_formatted:
            list_item.setProperty('inputstream.ffmpegdirect.stream_headers', headers_formatted)

        xbmcplugin.setResolvedUrl(addon_handle, True, listitem=list_item)
    except Exception as e:
        xbmcgui.Dialog().notification("Fehler", str(e), xbmcgui.NOTIFICATION_ERROR)
