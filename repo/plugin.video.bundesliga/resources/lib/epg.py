import os
import gzip
import time
import requests
import xbmc
import xml.etree.ElementTree as ET

EPG_URL = "https://epgshare01.online/epgshare01/epg_ripper_DE1.xml.gz"
EPG_CACHE = xbmc.translatePath("special://profile/addon_data/plugin.video.bundesliga/epg.xml")
EPG_MAX_AGE_HOURS = 72


def ensure_epg():
    """Lädt EPG neu, wenn älter als 72 Stunden"""
    try:
        if os.path.exists(EPG_CACHE):
            age = (time.time() - os.path.getmtime(EPG_CACHE)) / 3600
            if age < EPG_MAX_AGE_HOURS:
                xbmc.log(f"EPG Cache aktuell ({age:.1f}h alt)", xbmc.LOGINFO)
                return EPG_CACHE

        xbmc.log("EPG wird neu geladen...", xbmc.LOGINFO)
        r = requests.get(EPG_URL, timeout=30)
        r.raise_for_status()

        with open(EPG_CACHE, "wb") as f:
            f.write(gzip.decompress(r.content))

        xbmc.log("EPG erfolgreich aktualisiert", xbmc.LOGINFO)
        return EPG_CACHE

    except Exception as e:
        xbmc.log(f"EPG-Fehler: {e}", xbmc.LOGERROR)
        return None


def get_now_playing(epg_file, channel_id):
    """Gibt aktuelles EPG-Programm für tvg-id zurück"""
    try:
        tree = ET.parse(epg_file)
        root = tree.getroot()

        now_time = time.strftime("%Y%m%d%H%M%S")
        for programme in root.findall("programme"):
            if programme.get("channel") == channel_id:
                start = programme.get("start", "")[:14]
                stop = programme.get("stop", "")[:14]
                if start <= now_time <= stop:
                    title = programme.findtext("title", default="Unbekannt")
                    desc = programme.findtext("desc", default="")
                    return f"{title} ({desc})"
        return None
    except Exception as e:
        xbmc.log(f"EPG-Lese-Fehler: {e}", xbmc.LOGERROR)
        return None
