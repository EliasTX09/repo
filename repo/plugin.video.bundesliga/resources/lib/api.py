# -*- coding: utf-8 -*-
import os
import json
import gzip
import requests
import xml.etree.ElementTree as ET
import xbmc
import xbmcaddon
from xbmcvfs import translatePath  # ✅ Richtig für Kodi 21+

ADDON = xbmcaddon.Addon()
ADDON_PATH = translatePath(ADDON.getAddonInfo("path"))
EPG_FILE = os.path.join(ADDON_PATH, "epg_cache.json")

# Hauptquelle mit Verweis auf SPORT.json etc.
MAIN_SOURCE_URL = "https://raw.githack.com/EliasTX09/json/main/IPTV/IPTV_LINK.json"
EPG_URL = "https://epgshare01.online/epgshare01/epg_ripper_DE1.xml.gz"


# ==============================
# JSON / API
# ==============================
def load_json(url):
    """Lädt JSON-Datei von URL"""
    try:
        xbmc.log(f"api.load_json: Lade JSON von {url}", xbmc.LOGINFO)
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        xbmc.log(f"api.load_json Fehler: {e}", xbmc.LOGERROR)
        return None


def get_main_source():
    """Holt erste JSON-Quelle aus MAIN_SOURCE_URL"""
    data = load_json(MAIN_SOURCE_URL)
    if not data or "sources" not in data:
        xbmc.log("api.get_main_source: Keine Quellen gefunden!", xbmc.LOGERROR)
        return None
    return data["sources"][0]


def get_items(source_url):
    """Lädt Senderliste aus JSON"""
    xbmc.log(f"api.get_items() wurde aufgerufen mit source={source_url}", xbmc.LOGINFO)
    data = load_json(source_url)
    if not data:
        xbmc.log("api.get_items: Keine Daten erhalten!", xbmc.LOGERROR)
        return []

    items = []
    for i, item in enumerate(data):
        streams = []
        for k, v in item.items():
            if k.startswith("link("):
                num = k.split("(")[1].split(")")[0]
                name_key = f"name({num})"
                streams.append({
                    "title": item.get(name_key, f"Stream {num}"),
                    "url": v,
                    "thumbnail": item.get("thumbnail", "")
                })

        items.append({
            "id": i,
            "epg_id": item.get("id", ""),  # EPG-ID (z. B. "Das.Erste.de")
            "title": item.get("title", f"Sender {i}"),
            "thumbnail": item.get("thumbnail", ""),
            "multi": streams
        })

    xbmc.log(f"api.get_items: {len(items)} Sender geladen", xbmc.LOGINFO)
    return items


# ==============================
# EPG Handling
# ==============================
def download_epg():
    """Lädt und cached die EPG-Daten als JSON."""
    xbmc.log("api.download_epg: Lade EPG-Daten herunter...", xbmc.LOGINFO)
    try:
        r = requests.get(EPG_URL, timeout=15)
        r.raise_for_status()
        xml_data = gzip.decompress(r.content)
        root = ET.fromstring(xml_data)

        epg = {}
        for prog in root.findall("programme"):
            chan = prog.attrib.get("channel")
            title = prog.findtext("title", default="").strip()
            start = prog.attrib.get("start", "")
            end = prog.attrib.get("stop", "")
            if chan not in epg:
                epg[chan] = []
            epg[chan].append({
                "title": title,
                "start": start,
                "end": end
            })

        with open(EPG_FILE, "w", encoding="utf-8") as f:
            json.dump(epg, f)
        xbmc.log(f"api.download_epg: {len(epg)} Kanäle gespeichert", xbmc.LOGINFO)
        return epg

    except Exception as e:
        xbmc.log(f"api.download_epg Fehler: {e}", xbmc.LOGERROR)
        return {}


def load_epg():
    """Lädt den lokalen EPG-Cache oder lädt neu herunter."""
    if not os.path.exists(EPG_FILE):
        xbmc.log("api.load_epg: Kein lokaler Cache gefunden, lade neu...", xbmc.LOGINFO)
        return download_epg()
    try:
        with open(EPG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return download_epg()


def get_epg_info(channel_id):
    """Gibt aktuelle und nächste Sendung zu einem Sender zurück."""
    try:
        epg = load_epg()
        if channel_id not in epg or not epg[channel_id]:
            return None

        now = xbmc.getInfoLabel("System.Time(hh:mm)")
        current = None
        next_show = None

        shows = epg[channel_id]
        if len(shows) >= 2:
            current, next_show = shows[0], shows[1]
        elif len(shows) == 1:
            current = shows[0]

        return {
            "title": current.get("title", "Keine Daten") if current else "Keine Daten",
            "start": current.get("start", "") if current else "",
            "end": current.get("end", "") if current else "",
            "next_title": next_show.get("title", "") if next_show else ""
        }

    except Exception as e:
        xbmc.log(f"api.get_epg_info Fehler: {e}", xbmc.LOGERROR)
        return None
