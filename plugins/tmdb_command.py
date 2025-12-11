# Place under plugins/ so the bot auto-loads it.
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.tmdb import search_multi, get_movie_details, get_tv_details, suggest_title, pretty_card


@Client.on_message(filters.command('tmdb'))
async def tmdb_cmd(client, message):
    """Usage: /tmdb <query>  -- shows best match and an inline paginated list of results"""
    if len(message.command) == 1:
        return await message.reply('Send: /tmdb movie or series name')

    query = message.text.split(None, 1)[1]

    # Try suggestion first if user is likely misspelling
    suggestion = suggest_title(query)
    if suggestion and suggestion.lower() != query.lower():
        hint = f"Did you mean: {suggestion}? Use `/tmdb {suggestion}` to fetch it.\n\n"
    else:
        hint = ''

    results = search_multi(query, page=1)
    total = results.get('total_results', 0)
    movies = results.get('movies', [])
    tvs = results.get('tv', [])

    if total == 0:
        return await message.reply(hint + 'No results found on TMDb.')

    # Build a combined list (movies first, then tv)
    combined = movies + tvs

    # Take first item as primary
    primary = combined[0]
    # fetch full details for primary
    if primary['type'] == 'movie':
        details = get_movie_details(primary['id'])
    else:
        details = get_tv_details(primary['id'])

    caption = pretty_card(details)

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton('◀️ Prev', callback_data=f'tmdb_nav|{query}|1'),
          InlineKeyboardButton('Next ▶️', callback_data=f'tmdb_nav|{query}|2')],
         [InlineKeyboardButton('More info', callback_data=f'tmdb_info|{primary["type"]}|{primary["id"]}')]]
    )

    if details.get('poster'):
        await message.reply_photo(details['poster'], caption=caption, reply_markup=keyboard)
    else:
        await message.reply(caption, reply_markup=keyboard)