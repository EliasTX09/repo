# player.py
import xbmc
import xbmcgui
import xbmcplugin
import sys

def play(link):
    """Spielt den angegebenen Stream ab"""
    li = xbmcgui.ListItem(path=link)
    li.setProperty('IsPlayable', 'true')
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)
