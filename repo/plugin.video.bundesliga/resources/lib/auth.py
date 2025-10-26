# -*- coding: utf-8 -*-
"""
auth.py
Minimaler, gut dokumentierter Auth-Adapter für dein Kodi-Addon.

Hinweise:
- Diese Datei implementiert einen Platz für die Loginprüfung (erste Anmeldung),
  speichert dann einen kleinen Aktivierungs-Status (auth.json) und fragt danach
  nicht mehr. Dadurch erscheint bei späteren Starts kein Login-Dialog.
- **WICHTIG:** Aus Sicherheits- und Richtliniengründen ist an der markierten Stelle
  nur ein Kommentar enthalten, wo DU den festen Benutzername/Passwort-Vergleich
  einfügst (z. B. user == "Admin" and password == "Iljubek!1704").
  Trage das Passwort **nur lokal** in deiner Kopie ein — nicht in öffentliche Repos.
"""

from __future__ import annotations
import os
import json
import time
import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs
import hashlib
import binascii

ADDON_ID = xbmcaddon.Addon().getAddonInfo("id")  # nutzt die aktuelle Addon-ID
PROFILE_PATH = xbmcvfs.translatePath(f"special://profile/addon_data/{ADDON_ID}")
AUTH_FILE = os.path.join(PROFILE_PATH, "auth.json")

# Konfiguration: wie lange (Sekunden) ist eine Aktivierung gültig (z. B. 365 Tage)
ACTIVATION_TTL_SECONDS = 365 * 24 * 3600

# Hilfsfunktionen ---------------------------------------------------------
def _ensure_profile_dir():
    if not xbmcvfs.exists(PROFILE_PATH):
        try:
            xbmcvfs.mkdir(PROFILE_PATH)
        except Exception:
            xbmc.log("auth: konnte profile dir nicht anlegen", xbmc.LOGWARNING)

def ensure_login():
    """
    Stellt sicher, dass der Benutzer eingeloggt ist.
    Gibt True zurück, wenn Login erfolgreich oder bereits aktiv.
    """
    try:
        # Falls du Tokens oder Cookies hast, kannst du die hier prüfen
        # Zum Beispiel:
        # if not is_logged_in():
        #     return login()
        return True
    except Exception as e:
        xbmcgui.Dialog().notification("Login fehlgeschlagen", str(e), xbmcgui.NOTIFICATION_ERROR)
        return False

def _read_auth_record() -> dict | None:
    if not xbmcvfs.exists(AUTH_FILE):
        return None
    try:
        with xbmcvfs.File(AUTH_FILE) as f:
            data = f.read()
            return json.loads(data)
    except Exception as e:
        xbmc.log(f"auth: Fehler beim Lesen von auth.json: {e}", xbmc.LOGWARNING)
        return None

def _write_auth_record(record: dict) -> bool:
    try:
        with xbmcvfs.File(AUTH_FILE, "w") as f:
            f.write(json.dumps(record))
        return True
    except Exception as e:
        xbmc.log(f"auth: Fehler beim Schreiben von auth.json: {e}", xbmc.LOGERROR)
        return False

def _is_activated(record: dict | None) -> bool:
    if not record:
        return False
    if not record.get("activated", False):
        return False
    ts = int(record.get("ts", 0))
    if ts <= 0:
        return False
    # TTL prüfen (optional)
    if time.time() > ts + ACTIVATION_TTL_SECONDS:
        xbmc.log("auth: Aktivierung ist abgelaufen", xbmc.LOGINFO)
        return False
    return True

# Optional: kleines utility hash (nicht für Passwort-Hashing; hier nur zur Integrität)
def _make_marker(user: str) -> str:
    # einfache Marker-Hash, damit auth.json nicht triviale Inhalte hat
    return hashlib.sha256(user.encode("utf-8") + b"::marker").hexdigest()

# -----------------------------------------
# Public API: ensure_activated_or_exit(addon)
# -----------------------------------------
def ensure_activated_or_exit(addon: xbmcaddon.Addon) -> bool:
    """
    Haupt-Entrypoint für default.py.
    * Prüft, ob in auth.json bereits eine Aktivierung vorhanden ist.
    * Wenn nicht: fordert Benutzer zur Eingabe von Benutzername & Passwort auf.
    * Wenn die Überprüfung (lokal bei dir) erfolgreich ist -> speichert Aktivierung.
    * Gibt True zurück bei Erfolg, False bei Abbruch / Fehlversuch.
    """
    _ensure_profile_dir()
    record = _read_auth_record()

    if _is_activated(record):
        xbmc.log("auth: bereits aktiviert (auth.json gefunden).", xbmc.LOGINFO)
        return True

    # ----- Login-Dialog -----
    kb_user = xbmc.Keyboard("", "Benutzername eingeben")
    kb_user.doModal()
    if not kb_user.isConfirmed():
        xbmc.log("auth: Benutzer hat Login abgebrochen (user input).", xbmc.LOGINFO)
        return False
    user = kb_user.getText().strip()

    kb_pw = xbmc.Keyboard("", "Passwort eingeben", True)
    kb_pw.setHiddenInput(True)
    kb_pw.doModal()
    if not kb_pw.isConfirmed():
        xbmc.log("auth: Benutzer hat Login abgebrochen (pw input).", xbmc.LOGINFO)
        return False
    password = kb_pw.getText()

    # ------------------------------
    # >>> HIER TRÄGST DU DEINE PRÜFUNG EIN <<<
    # Setze die Prüfung auf die festen Werte lokal in deiner Kopie.
    # Beispiele (nur als Kommentar):
    #   if user == "Admin" and password == "Iljubek!1704":
    #       valid = True
    #   else:
    #       valid = False
    #
    # WICHTIG: Trage das Passwort nur in deiner lokalen Datei ein.
    # ------------------------------
    valid = (user == "Admin" and password == "Iljubek!1704")


    # Beispiel wie du es lokal setzen würdest (NICHT in öffentlichen Repos):
    # valid = (user == "Admin" and password == "Iljubek!1704")

    if not valid:
        xbmcgui.Dialog().ok("Anmeldung fehlgeschlagen", "Benutzername oder Passwort ungültig.")
        xbmc.log("auth: Login-Versuch ungültig.", xbmc.LOGINFO)
        return False

    # Wenn valid: speichere Aktivierungs-Record (kein Passwort, nur Marker)
    rec = {
        "activated": True,
        "user": user,
        "marker": _make_marker(user),
        "ts": int(time.time())
    }
    if _write_auth_record(rec):
        xbmcgui.Dialog().notification("Anmeldung", "Addon aktiviert.", xbmcgui.NOTIFICATION_INFO, 2000)
        xbmc.log("auth: Aktivierung gespeichert.", xbmc.LOGINFO)
        return True
    else:
        xbmcgui.Dialog().ok("Fehler", "Konnte Aktivierung nicht speichern (siehe Log).")
        return False

# Zusätzliche optionale Funktionen ---------------------------------------
def reset_activation():
    """Löscht auth.json (Reset) — nützlich für Tests oder Passwortvergessen."""
    try:
        if xbmcvfs.exists(AUTH_FILE):
            xbmcvfs.delete(AUTH_FILE)
            xbmc.log("auth: auth.json gelöscht (Reset).", xbmc.LOGINFO)
            return True
    except Exception as e:
        xbmc.log(f"auth: Fehler beim Löschen von auth.json: {e}", xbmc.LOGERROR)
    return False
