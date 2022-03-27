"""
AzeWhisperBot, Telegramda gizli mesaj göndərmək üçün bot
Copyright (C) 2021  Dash Eclipse

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from typing import Optional

from pyrogram import Client, filters, emoji
from pyrogram.errors.exceptions.bad_request_400 import (
    MessageIdInvalid, MessageNotModified
)
from pyrogram.types import (
    User,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery,
    ChosenInlineResult
)

from data import whispers

# https://core.telegram.org/bots/api#answercallbackquery
# https://core.telegram.org/bots/api#callbackquery
ANSWER_CALLBACK_QUERY_MAX_LENGTH = 200

# https://www.freeiconspng.com/downloadimg/37535
WHISPER_ICON_URL = "https://www.freeiconspng.com/uploads/whisper-icon-0.png"


@Client.on_inline_query()
async def answer_iq(_, iq: InlineQuery):
    query = iq.query
    split = query.split(' ', 1)
    if query == '' or len(query) > ANSWER_CALLBACK_QUERY_MAX_LENGTH \
            or (query.startswith('@') and len(split) == 1):
        title = f"{emoji.FIRE} Gizli mesaj yaz"
        content = ("**Daxili rejim vasitəsilə gizli mesajları göndərin**\n\n"
                   "İstifadəsi: `@AzeWhisperBot [@username|@] mesaj`")
        description = "İstifadəsi: @AzeWhisperBot [@username|@] mesaj"
        button = InlineKeyboardButton(
            "Daha Ətraflı...",
            url="https://t.me/AzeWhisperBot?start=learn"
        )
    elif not query.startswith('@'):
        title = f"{emoji.EYE} Mesajı ilk açana pıçılda"
        content = (
            f"{emoji.EYE} İlk açan pıçıltını oxuya bilər"
        )
        description = f"{emoji.SHUSHING_FACE} {query}"
        button = InlineKeyboardButton(
            f"{emoji.EYE} show message",
            callback_data="show_whisper"
        )
    else:
        # Python 3.8+
        u_target = 'anyone' if (x := split[0]) == '@' else x
        title = f"{emoji.LOCKED} {u_target} üçün gizli mesaj"
        content = f"{emoji.LOCKED} {u_target} üçün gizli mesaj"
        description = f"{emoji.SHUSHING_FACE} {split[1]}"
        button = InlineKeyboardButton(
            f"{emoji.LOCKED_WITH_KEY} show message",
            callback_data="show_whisper"
        )
    switch_pm_text = f"{emoji.INFORMATION} Gizli mesaj göndərməyi öyrən"
    switch_pm_parameter = "öyrən"
    await iq.answer(
        results=[
            InlineQueryResultArticle(
                title=title,
                input_message_content=InputTextMessageContent(content),
                description=description,
                thumb_url=WHISPER_ICON_URL,
                reply_markup=InlineKeyboardMarkup([[button]])
            )
        ],
        switch_pm_text=switch_pm_text,
        switch_pm_parameter=switch_pm_parameter
    )


@Client.on_chosen_inline_result()
async def chosen_inline_result(_, cir: ChosenInlineResult):
    query = cir.query
    split = query.split(' ', 1)
    len_split = len(split)
    if len_split == 0 or len(query) > ANSWER_CALLBACK_QUERY_MAX_LENGTH \
            or (query.startswith('@') and len(split) == 1):
        return
    if len_split == 2 and query.startswith('@'):
        # Python 3.9+
        # receiver_uname, text = split[0].removeprefix('@'), split[1]
        receiver_uname, text = split[0][1:] or '@', split[1]
    else:
        receiver_uname, text = None, query
    sender_uid = cir.from_user.id
    inline_message_id = cir.inline_message_id
    whispers[inline_message_id] = {
        'sender_uid': sender_uid,
        'receiver_uname': receiver_uname,
        'text': text
    }


@Client.on_callback_query(filters.regex("^show_whisper$"))
async def answer_cq(_, cq: CallbackQuery):
    inline_message_id = cq.inline_message_id
    if not inline_message_id or inline_message_id not in whispers:
        try:
            await cq.answer("Gizli mesaj tapılmadı", show_alert=True)
            await cq.edit_message_text(f"{emoji.NO_ENTRY} səhv pıçıltı")
        except (MessageIdInvalid, MessageNotModified):
            pass
        return
    else:
        whisper = whispers[inline_message_id]
        sender_uid = whisper['sender_uid']
        receiver_uname: Optional[str] = whisper['receiver_uname']
        whisper_text = whisper['text']
        from_user: User = cq.from_user
        if receiver_uname and from_user.username \
                and from_user.username.lower() == receiver_uname.lower():
            await read_the_whisper(cq)
            return
        if from_user.id == sender_uid or receiver_uname == '@':
            await cq.answer(whisper_text, show_alert=True)
            return
        if not receiver_uname:
            await read_the_whisper(cq)
            return
        await cq.answer("Bu sənin üçün deyil", show_alert=True)


async def read_the_whisper(cq: CallbackQuery):
    inline_message_id = cq.inline_message_id
    whisper = whispers[inline_message_id]
    whispers.pop(inline_message_id, None)
    whisper_text = whisper['text']
    await cq.answer(whisper_text, show_alert=True)
    receiver_uname: Optional[str] = whisper['receiver_uname']
    from_user: User = cq.from_user
    user_mention = (
        f"{from_user.first_name} (@{from_user.username})"
        if from_user.username
        else from_user.mention
    )
    try:
        t_emoji = emoji.UNLOCKED if receiver_uname else emoji.EYES
        await cq.edit_message_text(
            f"{t_emoji} {user_mention} mesajı oxudu"
        )
    except (MessageIdInvalid, MessageNotModified):
        pass
