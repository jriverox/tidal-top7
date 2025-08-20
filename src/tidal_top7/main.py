import argparse
import sys
import time
from typing import Iterable, List, Optional, Dict, Any

import tidalapi

# ----------------- Utils -----------------
import json

import json

def as_json(data):
    if isinstance(data, dict):
        return data
    if hasattr(data, "json"):
        try:
            return data.json()
        except Exception:
            txt = getattr(data, "text", None) or getattr(data, "content", b"").decode("utf-8", "ignore")
            return json.loads(txt) if txt else {}
    if isinstance(data, (str, bytes)):
        try:
            return json.loads(data if isinstance(data, str) else data.decode("utf-8", "ignore"))
        except Exception:
            return {}
    return {}

def api_request(session, method: str, path: str, *, params=None, data=None, headers=None):
    req_attr = getattr(session, "request", None)
    if callable(req_attr):
        resp = req_attr(method, path, params=params, data=data, headers=headers)
        return as_json(resp)
    if req_attr is not None and hasattr(req_attr, "request"):
        resp = req_attr.request(method, path, params=params, data=data, headers=headers)
        return as_json(resp)
    if hasattr(session, "_request"):
        resp = session._request(method, path, params=params, data=data, headers=headers)
        return as_json(resp)
    if method.upper() == "GET" and hasattr(session, "_get"):
        resp = session._get(path, params=params, headers=headers)
        return as_json(resp)
    raise RuntimeError("No pude encontrar un método HTTP compatible en tidalapi.Session")


def _get_user_id(session):
    # Intenta distintas propiedades comunes
    cand = []
    u = getattr(session, "user", None)
    if u is not None:
        cand += [getattr(u, "id", None), getattr(u, "user_id", None)]
    cand += [getattr(session, "user_id", None), getattr(session, "userid", None)]
    for c in cand:
        if c:
            return c
    raise RuntimeError("No pude determinar el user_id autenticado.")

def create_playlist_compat(session, title: str, description: str, public: bool = True, debug: bool = False):
    # 1) Métodos del wrapper (preferidos)
    u = getattr(session, "user", None)
    for attempt in (
        lambda: u.create_playlist(title, description),
        lambda: u.create_playlist(title, description, public),  # algunas versiones exigen el flag
    ):
        if u is None:
            break
        try:
            pl = attempt()
            if pl:
                if debug:
                    print(f"[DEBUG] Playlist creada via user.create_playlist: {getattr(pl,'name',title)}")
                return pl
        except Exception as e:
            if debug:
                print(f"[DEBUG] user.create_playlist error: {e}")

    # 2) API cruda
    uid = _get_user_id(session)
    data_variants = [
        {"title": title, "description": description, "public": public},
        {"title": title, "description": description, "public": str(public).lower()},
    ]
    path_variants = [f"users/{uid}/playlists", "playlists"]  # algunos forks exponen ambos
    last_err = None
    for path in path_variants:
        for payload in data_variants:
            try:
                # TIDAL suele esperar form-encoded; el wrapper maneja esto con data=dict
                created = api_request(session, "POST", path, data=payload)
                # Intenta parsear a objeto playlist del wrapper
                if hasattr(session, "parse_playlist"):
                    try:
                        pl = session.parse_playlist(created)
                        if pl:
                            if debug:
                                print(f"[DEBUG] Playlist creada via API+parse_playlist en {path}")
                            return pl
                    except Exception as e:
                        last_err = e
                # Fallback: construir Playlist con UUID
                uuid = created.get("uuid") or created.get("data", {}).get("uuid") or created.get("id")
                if uuid:
                    try:
                        from tidalapi.playlist import Playlist as PlaylistCls
                    except Exception:
                        PlaylistCls = getattr(tidalapi, "Playlist", None)
                    if PlaylistCls is None:
                        raise RuntimeError("No encontré clase Playlist en tidalapi.")
                    pl = PlaylistCls(session, uuid)
                    if debug:
                        print(f"[DEBUG] Playlist creada via API (uuid={uuid}) en {path}")
                    return pl
            except Exception as e:
                last_err = e
                if debug:
                    print(f"[DEBUG] create_playlist API error en {path} con {payload}: {e}")

    raise RuntimeError(f"No se pudo crear la playlist. Último error: {last_err}")

def add_tracks_compat(session, playlist, track_ids, debug: bool = False):
    # 1) Método del wrapper
    if hasattr(playlist, "add"):
        added = 0
        for batch in chunked(track_ids, 50):
            playlist.add(batch)
            added += len(batch)
        if debug:
            print(f"[DEBUG] Tracks agregados via playlist.add: {added}")
        return added

    # 2) API cruda
    uuid = getattr(playlist, "uuid", None) or getattr(playlist, "id", None)
    if not uuid:
        raise RuntimeError("No pude determinar UUID/ID de la playlist para agregar tracks.")

    added = 0
    path_variants = [f"playlists/{uuid}/items", f"v1/playlists/{uuid}/items"]
    for batch in chunked(track_ids, 50):
        payload_variants = [
            {"trackIds": ",".join(str(x) for x in batch)},                       # común
            {"trackIds": ",".join(str(x) for x in batch), "onDuplicate": "ADD"}  # por si exige política
        ]
        ok = False
        for path in path_variants:
            for payload in payload_variants:
                try:
                    api_request(session, "POST", path, data=payload)
                    ok = True
                    break
                except Exception as e:
                    if debug:
                        print(f"[DEBUG] add_tracks API error en {path} con {payload}: {e}")
            if ok:
                break
        if not ok:
            raise RuntimeError("No pude agregar pistas vía API cruda.")
        added += len(batch)
    if debug:
        print(f"[DEBUG] Tracks agregados via API cruda: {added}")
    return added

def safe_country_code(session: tidalapi.Session) -> str:
    cc = getattr(session, "country_code", None)
    if not cc or not isinstance(cc, str) or len(cc) != 2:
        return "US"  # fallback seguro para búsquedas
    return cc

def login_session(debug: bool = False):
    session = tidalapi.Session()
    session.login_oauth_simple()
    if not session.check_login():
        raise RuntimeError("Login no completado.")
    if debug:
        ra = getattr(session, "request", None)
        print(f"[DEBUG] country={getattr(session,'country_code','?')} request_attr={type(ra)} has(.request)={hasattr(ra,'request') if ra else False}")
    return session


def chunked(iterable: Iterable[int], size: int = 50) -> Iterable[List[int]]:
    bucket = []
    for x in iterable:
        bucket.append(x)
        if len(bucket) == size:
            yield bucket
            bucket = []
    if bucket:
        yield bucket

# ----------------- Search robusto -----------------

# Correcciones/notas de nombres comunes
NAME_FIXES = {
    "mathew good": "matthew good",
    "mathew good band": "matthew good band",
    "thronley": "thornley",
    "matchbox twenty": "matchbox 20",  # TIDAL suele listar como "Matchbox 20"
    "vast": "VAST",                    # a veces el case importa en heurísticas
    "pilot speed": "Pilate",           # nombre anterior de la banda
}

# Nombres alternativos extra a probar (además del fix)
ALT_VARIANTS = {
    "matchbox twenty": ["matchbox 20"],
    "matchbox 20": ["matchbox twenty"],
    "pilot speed": ["pilate"],
    "vast": ["VAST"],
}

def _name_variants(name: str) -> List[str]:
    q = name.strip().strip("\ufeff")
    base = q
    low = q.lower()

    variants = [base]

    # Fix directo
    if low in NAME_FIXES:
        variants.append(NAME_FIXES[low])

    # Alternativos
    if low in ALT_VARIANTS:
        variants.extend(ALT_VARIANTS[low])

    # Pequeñas normalizaciones
    if "&" in base and " and " not in base.lower():
        variants.append(base.replace("&", "and"))
    if " and " in base.lower() and "&" not in base:
        variants.append(base.replace(" and ", " & "))

    # Dedup conservando orden
    seen = set()
    uniq = []
    for v in variants:
        key = v.lower()
        if key not in seen:
            seen.add(key)
            uniq.append(v)
    return uniq

def _raw_search_artists(session, q: str, limit: int = 10, debug: bool = False):
    cc = safe_country_code(session)
    # Probamos distintas combinaciones que cambian entre builds del wrapper/endpoint
    param_trials = [
        {"query": q, "types": "artists", "limit": limit, "countryCode": cc},
        {"query": q, "type": "artists",  "limit": limit, "countryCode": cc},
        {"query": q, "types": "ARTISTS", "limit": limit, "countryCode": cc},
    ]
    path_trials = ["search", "v1/search"]  # algunos forks agregan el prefijo

    last_err = None
    for path in path_trials:
        for i, params in enumerate(param_trials, 1):
            try:
                raw = api_request(session, "GET", path, params=params)
                data = as_json(raw)
                artists_block = data.get("artists") or {}
                items = artists_block.get("items") or []
                if debug:
                    print(f"[DEBUG] {path} try#{i} '{q}' -> {len(items)} artistas")
                    for it in items[:3]:
                        print(f"        id={it.get('id')} name={it.get('name')}")
                if items:
                    return items
            except Exception as e:
                last_err = e
                if debug:
                    print(f"[DEBUG] _raw_search_artists {path} try#{i} error: {e}")

    if debug and last_err:
        print(f"[DEBUG] _raw_search_artists failed for '{q}': {last_err}")
    return []



def resolve_artist(session: tidalapi.Session, name: str, debug: bool = False):
    """
    Devuelve un objeto Artist usando varias rutas compatibles con distintas versiones del wrapper
    y un fallback crudo al endpoint /search.
    """
    for candidate in _name_variants(name):
        # 1) v0.6.x: session.search('artists', q)
        try:
            res = session.search("artists", candidate)  # returns SearchResult con .artists
            artists = getattr(res, "artists", []) or []
            if artists:
                # exacto insensitive primero
                for a in artists:
                    if getattr(a, "name", "").strip().lower() == candidate.lower():
                        return a
                return artists[0]
        except Exception:
            pass

        # 2) v0.7/0.8 forks: session.search(q, models=[tidalapi.artist.Artist])
        try:
            res2 = session.search(candidate, models=[tidalapi.artist.Artist])
            if res2:
                for a in res2:
                    if getattr(a, "name", "").strip().lower() == candidate.lower():
                        return a
                return res2[0]
        except Exception:
            pass

        # 3) Fallback crudo
        items = _raw_search_artists(session, candidate, limit=10, debug=debug)
        if items:
            # elegimos exacto insensitive si existe, si no el primero
            exact = None
            for it in items:
                nm = (it.get("name") or "").strip().lower()
                if nm == candidate.lower():
                    exact = it
                    break
            chosen = exact or items[0]
            try:
                return tidalapi.artist.Artist(session, chosen["id"])
            except Exception:
                # último recurso: devolver None y seguir con siguiente variante
                pass

    if debug:
        print(f"[DEBUG] resolve_artist falló para: {name}")
    return None

# ----------------- Top tracks -----------------

def get_top7_tracks(session: tidalapi.Session, artist_obj, debug: bool = False) -> List[int]:
    tracks = []

    # Preferimos métodos del objeto artista
    for attempt in (
        lambda: artist_obj.top_tracks(limit=7),
        lambda: artist_obj.get_top_tracks(limit=7),
    ):
        try:
            res = attempt()
            if res:
                tracks = res
                break
        except Exception:
            pass

    # Fallback v0.6.x: método del session
    if not tracks:
        try:
            tracks = session.get_artist_top_tracks(artist_obj.id)
        except Exception:
            tracks = []

    # Último recurso: ordenar por popularidad
    if not tracks:
        try:
            tracks = artist_obj.tracks(limit=50, order="POPULARITY")
        except Exception:
            tracks = []

    ids = []
    for t in tracks:
        tid = getattr(t, "id", None)
        if isinstance(t, int):
            tid = t
        if tid:
            ids.append(int(tid))
        if len(ids) >= 7:
            break

    if debug:
        print(f"[DEBUG] top7 {getattr(artist_obj,'name','?')} -> {len(ids)} tracks")
    return ids[:7]

# ----------------- Core -----------------

def build_tracks_from_artists(session: tidalapi.Session, artists: List[str], debug: bool = False) -> List[int]:
    all_ids: List[int] = []
    seen = set()
    for name in artists:
        artist = resolve_artist(session, name, debug=debug)
        if not artist:
            print(f"[WARN] No se encontró artista: {name}", file=sys.stderr)
            continue
        top_ids = get_top7_tracks(session, artist, debug=debug)
        if not top_ids:
            print(f"[WARN] Sin top tracks para: {name}", file=sys.stderr)
            continue
        for tid in top_ids:
            if tid not in seen:
                seen.add(tid)
                all_ids.append(tid)
        time.sleep(0.2)
    return all_ids

def create_playlist_and_add(session, title: str, description: str, track_ids: list[int], debug: bool = False):
    playlist = create_playlist_compat(session, title, description, public=True, debug=debug)
    added = add_tracks_compat(session, playlist, track_ids, debug=debug)
    return playlist, added

# ----------------- CLI -----------------

def cli():
    parser = argparse.ArgumentParser(
        prog="tidal-top7",
        description="Crea una playlist en TIDAL con el Top 7 de una lista de artistas."
    )
    parser.add_argument("--artists", default="", help='Lista separada por comas. Ej: "Radiohead, VAST, Fuel"')
    parser.add_argument("--artists-file", default="", help="Archivo de texto con un artista por línea.")
    parser.add_argument("--playlist-name", required=True, help='Nombre de la playlist.')
    parser.add_argument("--playlist-desc", default="Generada automáticamente con tidal-top7.", help="Descripción opcional.")
    parser.add_argument("--debug", action="store_true", help="Muestra logs de depuración.")
    args = parser.parse_args()

    # Reúne artistas
    names: List[str] = []
    if args.artists.strip():
        names += [n.strip() for n in args.artists.split(",") if n.strip()]
    if args.artists_file.strip():
        with open(args.artists_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    names.append(line)

    if not names:
        print("Debes especificar al menos un artista con --artists o --artists-file", file=sys.stderr)
        sys.exit(2)

    session = login_session(debug=args.debug)
    track_ids = build_tracks_from_artists(session, names, debug=args.debug)
    if not track_ids:
        print("No se encontraron tracks para los artistas indicados.", file=sys.stderr)
        sys.exit(1)

    playlist, added = create_playlist_and_add(session, args.playlist_name, args.playlist_desc, track_ids, debug=args.debug)

    print(f"✔ Playlist creada: {playlist.name} ({added} pistas)")
    print(f"URL: {getattr(playlist, 'share_url', '') or getattr(playlist, 'listen_url', '')}")

if __name__ == "__main__":
    cli()
