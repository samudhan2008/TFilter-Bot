from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.tmdb import *
from helper import temp


@Client.on_callback_query()
async def tmdb_callbacks(client, callback_query):
    data = callback_query.data or ''
    # Navigation callbacks: tmdb_nav|<query>|<action_page>
    # action_page: integer page requested (1 prev, 2 next) but we can pass page number too
    if data.startswith('tmdb_nav'):
        try:
            _, raw_query, page_str = data.split('|', 2)
            page = int(page_str)
        except Exception:
            return await callback_query.answer('Invalid navigation', show_alert=True)

        # determine desired page: if page==1 go to page-1 else page+1 -- but to keep stateless we treat page as desired page index
        # For simplicity we toggle between page 1 and 2 here. You can extend to include absolute pages.
        desired_page = 1 if page == 2 else 2
        results = search_multi(raw_query, page=desired_page)
        combined = results.get('movies', []) + results.get('tv', [])
        if not combined:
            return await callback_query.answer('No more results', show_alert=True)

        primary = combined[0]
        if primary['type'] == 'movie':
            details = get_movie_details(primary['id'])
        else:
            details = get_tv_details(primary['id'])

        caption = pretty_card(details)
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton('◀️ Prev', callback_data=f'tmdb_nav|{raw_query}|{desired_page}'),
              InlineKeyboardButton('Next ▶️', callback_data=f'tmdb_nav|{raw_query}|{desired_page+1}')],
             [InlineKeyboardButton('More info', callback_data=f'tmdb_info|{primary["type"]}|{primary["id"]}')]]
        )

        try:
            if details.get('poster'):
                await callback_query.message.edit_media(
                    media=await client.send_photo(callback_query.message.chat.id, details['poster']),
                    reply_markup=keyboard,
                )
                # Instead of editing media directly (which can be complex), we'll edit caption only
                await callback_query.message.edit_caption(caption, reply_markup=keyboard)
            else:
                await callback_query.message.edit_caption(caption, reply_markup=keyboard)
        except Exception:
            # fallback to editing text
            await callback_query.message.edit_caption(caption, reply_markup=keyboard)

        await callback_query.answer()
        return

    if data.startswith('tmdb_info'):
        try:
            _, item_type, item_id = data.split('|', 2)
            item_id = int(item_id)
        except Exception:
            return await callback_query.answer('Invalid', show_alert=True)

        if item_type == 'movie':
            details = get_movie_details(item_id)
        else:
            details = get_tv_details(item_id)

        caption = pretty_card(details)
        # add season buttons for TV
        buttons = []
        if item_type == 'tv':
            seasons = details.get('seasons') or []
            row = []
            for s in seasons[:6]:
                row.append(InlineKeyboardButton(f"S{s['season_number']}", callback_data=f'tmdb_season|{item_id}|{s['season_number']}'))
                if len(row) == 3:
                    buttons.append(row)
                    row = []
            if row:
                buttons.append(row)

        keyboard = InlineKeyboardMarkup(buttons) if buttons else None

        if details.get('poster'):
            await callback_query.message.edit_media(media=await client.send_photo(callback_query.message.chat.id, details['poster']))
            await callback_query.message.edit_caption(caption)
        else:
            await callback_query.message.edit_caption(caption)

        await callback_query.answer()
        return

    if data.startswith('tmdb_season'):
        try:
            _, tv_id, season_no = data.split('|', 2)
            tv_id = int(tv_id); season_no = int(season_no)
        except Exception:
            return await callback_query.answer('Invalid', show_alert=True)

        season = get_tv_season(tv_id, season_no)
        # Build season message
        eps = season.get('episodes', [])
        lines = [f"Season {season.get('season_number')} — {season.get('name', '')}"]
        for e in eps[:10]:
            lines.append(f"{e.get('episode_number')}. {e.get('name')} — {e.get('overview')[:120]}")
        text = '\n'.join(lines)
        await callback_query.message.edit_caption(text)
        await callback_query.answer()

        return
