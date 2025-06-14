from jetextractors.extractors.daddylive import Daddylive
from jetextractors.models import JetLink

def extract_stream_url(page_url: str) -> str:
    """
    Extrahiert den vollständigen Stream-Link inklusive korrekt formatierter Header.

    :param page_url: Die URL zur HTML-Stream-Seite (z. B. https://daddylive.dad/stream/stream-558.php)
    :return: Ein string im Format: https://.../mono.m3u8|Referer=...&Origin=...&User-Agent=...
    """
    extractor = Daddylive()
    link_obj = JetLink(page_url)
    result = extractor.get_link(link_obj)

    if not result or not result.address:
        raise ValueError("Kein gültiger Stream-Link gefunden.")

    return result.address
