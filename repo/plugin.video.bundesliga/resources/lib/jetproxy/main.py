from http.server import HTTPServer
from player import ProxyPlayer
import routing, xbmc, xbmcgui
from threading import Thread
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory

from server import MyServer

plugin = routing.Plugin()

def startProxy():
    def serve_forever(httpd):
        with httpd:
            httpd.serve_forever()
    
    webServer = HTTPServer(("127.0.0.1", 49777), MyServer)
    
    xbmc.log("JetProxy: starting server at http://127.0.0.1:49777"), xbmc.LOGINFO
    webServer.server_activate()
    thread = Thread(target=serve_forever, args=(webServer,))
    thread.setDaemon(True)
    thread.start()
    xbmc.log("JetProxy: server started!", xbmc.LOGINFO)

    return webServer

@plugin.route('/')
def index():
    addDirectoryItem(plugin.handle, plugin.url_for(play, "http://oscartv.mine.nu:25461/live/jmr1234/jmr1234/6139.m3u8"), ListItem("Example link"), False)
    addDirectoryItem(plugin.handle, plugin.url_for(test), ListItem("Test link"), False)
    endOfDirectory(plugin.handle)

@plugin.route("/test")
def test():
    link = xbmcgui.Dialog().input("Enter link")
    if not link:
        return
    play(link)

@plugin.route('/play/<path:url>')
def play(url):
    try:
        proxy = startProxy()
    except:
        proxy = None
        pass
    import sys
    import xbmcgui
    stream_url = "http://127.0.0.1:49777?url=" + url
    use_inputstream = xbmcgui.Dialog().yesno("JetProxy", "Use inputstream.ffmpegdirect for playback?")
    item = ListItem("JetProxy Stream", path=stream_url)
    item.setInfo('video', {'plot': "JetProxy Stream"})
    if use_inputstream:
        item.setProperty('inputstream', 'inputstream.ffmpegdirect')
        item.setMimeType('application/x-mpegURL')
        item.setProperty('inputstream.ffmpegdirect.is_realtime_stream', 'true')
        item.setProperty('inputstream.ffmpegdirect.stream_mode', 'timeshift')
        item.setProperty('inputstream.ffmpegdirect.manifest_type', 'hls')
    import xbmcplugin
    xbmcplugin.setResolvedUrl(plugin.handle, True, item)
    import xbmc
    xbmc.Player().play(stream_url, listitem=item)
    return True

if __name__ == '__main__':
    plugin.run()