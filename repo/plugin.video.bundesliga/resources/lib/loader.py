# loader.py
import requests

MASTER_URL = "https://raw.githubusercontent.com/EliasTX09/json/refs/heads/main/IPTV/IPTV_LINK.json"

def get_all_channels():
    """Lädt live alle Sender aus den Quellen"""
    data = requests.get(MASTER_URL).json()
    channels = []
    for src in data.get("sources", []):
        sub_data = requests.get(src).json()
        channels.extend(sub_data)
    return channels
