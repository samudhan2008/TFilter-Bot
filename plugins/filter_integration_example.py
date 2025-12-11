from utils.tmdb import search_multi


def build_result_card(query):
    res = search_multi(query, page=1)
    combined = res.get('movies', []) + res.get('tv', [])
    if not combined:
        return {'title': query, 'desc': 'No metadata found'}

    primary = combined[0]
    card = {
        'title': primary['title'],
        'thumb': primary['poster'],
        'rating': primary['rating'],
        'release': primary['release'],
        'overview': primary['overview'][:300]
    }
    return card