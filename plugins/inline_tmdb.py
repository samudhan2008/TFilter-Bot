# Inline query handler so users can do: @YourBot query
from pyrogram import Client, filters
from pyrogram.types import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from utils.tmdb import search_multi
import html


@Client.on_inline_query()
async def inline_tmdb(client, inline_query):
    q = inline_query.query.strip()
    if not q:
        return await inline_query.answer([], cache_time=1)

    results = search_multi(q, page=1)
    combined = results.get('movies', []) + results.get('tv', [])
    answers = []
    for i, item in enumerate(combined[:8]):
        title = item['title']
        text = f"{title}\n⭐ {item['rating']} • {item['release']}\n\n{item['overview'][:200]}"
        thumb = item['poster']
        kb = InlineKeyboardMarkup([[InlineKeyboardButton('More Info', callback_data=f'tmdb_info|{item['type']}|{item['id']}')]])
        answers.append(InlineQueryResultArticle(
            id=str(item['id']) + '-' + item['type'],
            title=title,
            input_message_content=InputTextMessageContent(text),
            description=item['overview'][:64],
            reply_markup=kb
        ))

    await inline_query.answer(results=answers, cache_time=60)