import os
import requests
from urllib.parse import quote_plus
from difflib import SequenceMatcher, get_close_matches

TMDB_API_KEY = os.getenv('TMDB_API_KEY')
if not TMDB_API_KEY:
    TMDB_API_KEY = "d67317159cbc25bdad2a79e81f06265d"  # replace or set env var

API_BASE = 'https://api.themoviedb.org/3'
POSTER_BASE = 'https://image.tmdb.org/t/p/w500'


def _get(path, params=None):
    if params is None:
        params = {}
    params['api_key'] = TMDB_API_KEY
    resp = requests.get(f"{API_BASE}{path}", params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def normalize_movie(m):
    return {
        'type': 'movie',
        'id': m.get('id'),
        'title': m.get('title') or m.get('original_title'),
        'overview': m.get('overview') or 'No overview available',
        'rating': m.get('vote_average') or 0,
        'release': m.get('release_date') or m.get('first_air_date') or 'Unknown',
        'poster': POSTER_BASE + m['poster_path'] if m.get('poster_path') else None,
        'raw': m,
    }


def normalize_tv(t):
    return {
        'type': 'tv',
        'id': t.get('id'),
        'title': t.get('name') or t.get('original_name'),
        'overview': t.get('overview') or 'No overview available',
        'rating': t.get('vote_average') or 0,
        'release': t.get('first_air_date') or t.get('first_air_date') or 'Unknown',
        'poster': POSTER_BASE + t['poster_path'] if t.get('poster_path') else None,
        'raw': t,
    }


def search_multi(query, page=1):
    """Search both movies and TV. Returns dict with lists: movies, tv, total_results."""
    q = quote_plus(query)
    # Use multi search endpoint
    data = _get(f"/search/multi", params={'query': query, 'page': page})

    movies = []
    tvs = []
    for item in data.get('results', [])[:50]:
        if item.get('media_type') == 'movie':
            movies.append(normalize_movie(item))
        elif item.get('media_type') == 'tv':
            tvs.append(normalize_tv(item))
        else:
            # sometimes person or other types show up; skip
            continue

    return {
        'movies': movies,
        'tv': tvs,
        'total_results': data.get('total_results', 0),
        'page': data.get('page', 1),
        'total_pages': data.get('total_pages', 1),
    }


def search_movies(query, page=1):
    data = _get('/search/movie', params={'query': query, 'page': page})
    return {'results': [normalize_movie(m) for m in data.get('results', [])], 'page': data.get('page', 1), 'total_pages': data.get('total_pages', 1)}


def search_tvs(query, page=1):
    data = _get('/search/tv', params={'query': query, 'page': page})
    return {'results': [normalize_tv(t) for t in data.get('results', [])], 'page': data.get('page', 1), 'total_pages': data.get('total_pages', 1)}


def get_movie_details(movie_id):
    data = _get(f'/movie/{movie_id}', params={'append_to_response': 'credits,images,release_dates'})
    details = {
        'type': 'movie',
        'id': data.get('id'),
        'title': data.get('title'),
        'overview': data.get('overview'),
        'rating': data.get('vote_average'),
        'release': data.get('release_date'),
        'runtime': data.get('runtime'),
        'genres': [g['name'] for g in data.get('genres', [])],
        'poster': POSTER_BASE + data['poster_path'] if data.get('poster_path') else None,
        'backdrop': POSTER_BASE + data['backdrop_path'] if data.get('backdrop_path') else None,
        'raw': data,
    }
    return details


def get_tv_details(tv_id):
    data = _get(f'/tv/{tv_id}', params={'append_to_response': 'credits,images'})
    details = {
        'type': 'tv',
        'id': data.get('id'),
        'title': data.get('name'),
        'overview': data.get('overview'),
        'rating': data.get('vote_average'),
        'first_air_date': data.get('first_air_date'),
        'seasons': data.get('seasons', []),
        'number_of_seasons': data.get('number_of_seasons'),
        'number_of_episodes': data.get('number_of_episodes'),
        'genres': [g['name'] for g in data.get('genres', [])],
        'poster': POSTER_BASE + data['poster_path'] if data.get('poster_path') else None,
        'backdrop': POSTER_BASE + data['backdrop_path'] if data.get('backdrop_path') else None,
        'raw': data,
    }
    return details


def get_tv_season(tv_id, season_number):
    data = _get(f'/tv/{tv_id}/season/{season_number}')
    return data


def get_recommendations(item_id, item_type='movie', page=1):
    path = f'/{item_type}/{item_id}/recommendations'
    data = _get(path, params={'page': page})
    results = data.get('results', [])
    return [normalize_movie(r) if item_type == 'movie' else normalize_tv(r) for r in results]


def suggest_title(query, max_suggestions=1):
    """Return a close match suggestion for the query using TMDb first-page results."""
    merged = []
    try:
        multi = search_multi(query, page=1)
        for m in multi.get('movies', [])[:10]:
            merged.append(m['title'])
        for t in multi.get('tv', [])[:10]:
            merged.append(t['title'])
    except Exception:
        pass

    if not merged:
        return None

    # use get_close_matches from difflib
    matches = get_close_matches(query, merged, n=max_suggestions, cutoff=0.6)
    return matches[0] if matches else None


def pretty_card(details):
    """Return a text card that mimics a sleek movie card."""
    if not details:
        return "No details available"

    if details['type'] == 'movie':
        lines = [f"🎬 {details.get('title')}", f"⭐ {details.get('rating')}", f"⏱ {details.get('runtime') or 'N/A'} mins", f"📅 {details.get('release')}"]
    else:
        lines = [f"📺 {details.get('title')}", f"⭐ {details.get('rating')}", f"Seasons: {details.get('number_of_seasons')}", f"Episodes: {details.get('number_of_episodes')}"]

    if details.get('genres'):
        lines.append('🎭 ' + ', '.join(details.get('genres')))

    lines.append('\n' + (details.get('overview') or 'No overview available'))
    return '\n'.join(lines)
