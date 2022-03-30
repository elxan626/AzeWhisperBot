"""
ezWhisperBot, Telegram Bot for sending whisper messages
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
from datetime import datetime

from pyrogram import Client, filters, emoji
from pyrogram.types import (Message,
                            InlineKeyboardMarkup, InlineKeyboardButton,
                            CallbackQuery)

from data import whispers

LEARN_TEXT = (
    "Bu bot yalnız daxili rejimdə işləyir, istifadə nümunəsi kimi olardı"
    "belə:\n\n"
    "- @username-ə mesaj yaz\n"
    "`@AzeWhisperBot @username hansısa mesaj`\n\n"
    "- Hər kəsin dəfələrlə oxuya biləcəyi bir pıçıltı yazın,\n"
    "`@AzeWhisperBot @username hansısa mesaj`\n\n"
    "- Onu ilk açana pıçıldayın\n"
    "`@AzeWhisperBot hansısa mesaj`"
)
LEARN_REPLY_MARKUP = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                "Növbəti",
                callback_data="learn_next"
            )
        ]
    ]
)

DEFAULT_TEXT = (
    "Bu bot sizə pıçıltı mesajları göndərməyə imkan verir, "
    "yalnız daxili rejimdə işləyir\n\n"
    "[Source Code](https://github.com/dashezup/ezWhisperBot)"
    " | [👨‍💻 Developer](https://t.me/muellime)"
    " | [📣 Support](https://t.me/muellime)"
)
DEFAULT_REPLY_MARKUP = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                "Yoxlamaq üçün qrup seçin",
                switch_inline_query=""
            ),
            InlineKeyboardButton(
                "Bu qrupda yoxla",
                switch_inline_query_current_chat=""
            )
        ],
        [
            InlineKeyboardButton(
                "Mənim pıçıltılarım",
                callback_data="list_whispers"
            )
        ]
    ]
)


@Client.on_message(filters.text
                   & filters.incoming
                   & ~filters.edited
                   & filters.command("start"))
async def command_start(_, m: Message):
    if len(m.command) == 2 and m.command[1] == "learn":
        text_start = LEARN_TEXT
        reply_markup = LEARN_REPLY_MARKUP
    else:
        text_start = DEFAULT_TEXT
        reply_markup = DEFAULT_REPLY_MARKUP
    await m.reply_text(
        text_start,
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )


@Client.on_callback_query(filters.regex("^(learn_next|start)$"))
async def show_main_page(_, cq: CallbackQuery):
    await cq.edit_message_text(
        text=DEFAULT_TEXT,
        disable_web_page_preview=True,
        reply_markup=DEFAULT_REPLY_MARKUP
    )
    await cq.answer(
        f"{emoji.ROBOT} İndi siz bunu daxili rejimdə yoxlayın"
        if cq.data == "learn_next"
        else None
    )


@Client.on_callback_query(filters.regex("^list_whispers$"))
async def list_whispers(_, cq: CallbackQuery):
    user_id = cq.from_user.id
    user_whispers = [
        i for i in whispers.values() if i['sender_uid'] == user_id
    ]
    if len(user_whispers) == 0:
        text = "Sənin heç bir pıçıltın yoxdur"
    else:
        text = f"Sizin **{len(user_whispers)}** pıçıltılarınız var"
    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    f"{emoji.WASTEBASKET}  Pıçıltılarımı sil",
                    callback_data="delete_my_whispers"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{emoji.BACK_ARROW}  Əsas səhifə",
                    callback_data="start"
                )
            ]
        ]
    )
    await cq.edit_message_text(
        text=text,
        reply_markup=reply_markup
    )
    await cq.answer()


@Client.on_callback_query(filters.regex("^delete_my_whispers$"))
async def delete_my_whispers(_, cq: CallbackQuery):
    user_id = cq.from_user.id
    deleted_whispers = [
        whispers.pop(k)
        for k, v in list(whispers.items())
        if v['sender_uid'] == user_id
    ]
    if len(deleted_whispers) == 0:
        await cq.answer("Sənin heç bir pıçıltın yoxdur")
    else:
        await cq.answer(f"Removed {len(deleted_whispers)} whispers")
        utcnow = datetime.utcnow().strftime('%F %T')
        await cq.edit_message_text(
            f"Your whispers has been removed at `{utcnow}`",
            reply_markup=cq.message.reply_markup
        )
