import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import run_async, CommandHandler, Filters
from telegram.utils.helpers import mention_html
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, User, CallbackQuery

from tg_bot import dispatcher, BAN_STICKER, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat, is_bot_admin
from tg_bot.modules.helper_funcs.extraction import extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.helper_funcs.filters import CustomFilters

RBAN_ERRORS = {
    "Bir Yetkiliyi Banlayamam",
    "Sohbet Mevcut Değil",
    "Üyeyi Kısıtlamak/Kısıtlama Kaldırmak İçin Yeterli Yetkim Yok.",
    "User_not_participant",
    "Peer_id_invalid",
    "Sohbet Devre Dışı.",
    "Basit Bir Gruptan Atmak İçin Bir Kullanıcının Davetlisi Olması Gerekir",
    "Chat_admin_required",
    "Yalnızca Bir Grubu Oluşturan Kişi Grup Yöneticilerini Atabilir!",
    "Channel_private",
    "Bir Sohbet Değil!"
}

RUNBAN_ERRORS = {
    "Bir Yetkiliyi Banlayamam",
    "Sohbet Mevcut Değil",
    "Üyeyi Kısıtlamak/Kısıtlama Kaldırmak İçin Yeterli Yetkim Yok.",
    "User_not_participant",
    "Peer_id_invalid",
    "Sohbet Devre Dışı.",
    "Basit Bir Gruptan Atmak İçin Bir Kullanıcının Davetlisi Olması Gerekir",
    "Chat_admin_required",
    "Yalnızca Bir Grubu Oluşturan Kişi Grup Yöneticilerini Atabilir!",
    "Channel_private",
    "Bir Sohbet Değil!"
}



@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Lütfen Bir Kullanıcı Seçiniz")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Kullanıcı Bulunamadı!")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Gerçekten Sahibimi Banlamamı Mı İstiyorsun ??")
        return ""

    if user_id == bot.id:
        message.reply_text("Kendimi Banlayacağımı mı Düşündün? Çok Çılgınsın :)")
        return ""

    log = "<b>{}:</b>" \
          "\n#BAN" \
          "\n<b>Admin:</b> {}" \
          "\n<b>Kullanıcı:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name))
    if reason:
        log += "\n<b>Sebep:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        keyboard = []
        reply = """{} Yasaklandı!\nSebep: {}""".format(mention_html(member.user.id, member.user.first_name),reason)
        message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Banned!', quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Kahretsin, O Kullanıcıyı Yasaklayamam.")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Lütfen Bir Kullanıcı Seçiniz.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Kullanıcı Bulunamadı!")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Yetkilileri Banlamayı Çok İsterdim...")
        return ""

    if user_id == bot.id:
        message.reply_text("Kendimi Banlayacağımı mı Düşündün? Çok Çılgınsın :)")
        return ""

    if not reason:
        message.reply_text("Bu kullanıcıyı Yasaklamak İçin Bir Zaman Belirtmediniz!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    bantime = extract_time(message, time_val)

    if not bantime:
        return ""

    log = "<b>{}:</b>" \
          "\n#SÜRELİ BAN" \
          "\n<b>Admin:</b> {}" \
          "\n<b>Kullanıcı:</b> {}" \
          "\n<b>Süre:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name), time_val)
    if reason:
        log += "\n<b>Sebep:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("Banlandı! Kullanıcının Banı {} Süre Sonra Açılacak.".format(time_val))
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text("Banlandı! Kullanıcının Banı {} Süre Sonra Açılacak.".format(time_val), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Kahretsin, Bu Kullanıcıyı Yasaklayamam.")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def kick(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Kullanıcı Bulunamadı.")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id):
        message.reply_text("Gerçekten Sahibimi Banlamamı Mı İstiyorsun ??")
        return ""

    if user_id == bot.id:
        message.reply_text("Evvveeettt, Bunu Yapmayacağım.")
        return ""

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("Kicked!")
        log = "<b>{}:</b>" \
              "\n#KOVULDU" \
              "\n<b>Admin:</b> {}" \
              "\n<b>Kullanıcı:</b> {}".format(html.escape(chat.title),
                                         mention_html(user.id, user.first_name),
                                         mention_html(member.user.id, member.user.first_name))
        if reason:
            log += "\n<b>Sebep:</b> {}".format(reason)

        return log

    else:
        message.reply_text("Kahretsin, Bu Kullanıcıyı Yasaklayamam.")

    return ""


@run_async
@bot_admin
@can_restrict
def kickme(bot: Bot, update: Update):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("nE Adminler İstifa Edemez KARDEŞİM KENDİNE GEL!!")
        return

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text("Gerçekten Bunu Yapmak Mı İstedin\nPEKİ O ZAMAN GÖRÜŞÜRÜZ!")
    else:
        update.effective_message.reply_text("Huh? Bunu Yapamam :/")


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def unban(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Kullanıcı Bulunamadı")
            return ""
        else:
            raise

    if user_id == bot.id:
        message.reply_text("Kendi Banımı mı Açayım?")
        return ""

    if is_user_in_chat(chat, user_id):
        message.reply_text("Zaten Sohbette Olan Birinin Yasağını Neden Kaldırmaya Çalışıyorsunuz?")
        return ""

    chat.unban_member(user_id)
    message.reply_text("Evet, Kullanıcı Tekrar Katılabilir!")

    log = "<b>{}:</b>" \
          "\n#UNBANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {}".format(html.escape(chat.title),
                                     mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name))
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    return log


@run_async
@bot_admin
def rban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("Görünüşe göre bir sohbetten/kullanıcıdan bahsetmiyorsunuz.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Bu Bir Geçerli Kullanıcı Değil!")
        return
    elif not chat_id:
        message.reply_text("Bu Bir Geçerli Sohbet Değil!")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text("Sohbet Bulunamadı! Geçerli Bir Sohbet Kimliği Girdiğinizden Emin Olun Veya Beni Oraya Ekleyin")
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("Üzgünüm ama bu özel bir sohbet!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(bot.id).can_restrict_members:
        message.reply_text("Oradaki insanları kısıtlayamam! Yönetici olduğumdan ve kullanıcıları yasaklayabileceğimden emin olun.")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Kullanıcıyı Bulamadım!")
            return
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Gerçekten Sahibimi Banlayacağımı mı düşündün?")
        return

    if user_id == bot.id:
        message.reply_text("Hadi Ama Dostum Kendimi Neden Banlayayım?")
        return

    try:
        chat.kick_member(user_id)
        message.reply_text("[kullanıcı](tg://user?id={}) Yasaklandı".format(user_id), parse_mode='Markdown')
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Banned!', quote=False)
        elif excp.message in RBAN_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Well damn, I can't ban that user.")

@run_async
@bot_admin
def runban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("You don't seem to be referring to a chat/user.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return
    elif not chat_id:
        message.reply_text("You don't seem to be referring to a chat.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text("Chat not found! Make sure you entered a valid chat ID and I'm part of that chat.")
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("I'm sorry, but that's a private chat!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(bot.id).can_restrict_members:
        message.reply_text("I can't unrestrict people there! Make sure I'm admin and can unban users.")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user there")
            return
        else:
            raise
            
    if is_user_in_chat(chat, user_id):
        message.reply_text("Why are you trying to remotely unban someone that's already in that chat?")
        return

    if user_id == bot.id:
        message.reply_text("I'm not gonna UNBAN myself, I'm an admin there!")
        return

    try:
        chat.unban_member(user_id)
        message.reply_text("Yep, this user can join that chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Unbanned!', quote=False)
        elif excp.message in RUNBAN_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR unbanning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Well damn, I can't unban that user.")


__help__ = """
 - /kickme: Yazan Kişiyi Gruptan Atar

*Admin only:*
 - /ban <kullanıcı yada yanıt>: Yanıtlanan Kişiyi Veya Etiketlenen Kişiyi Yasaklar
 - /tban <kullanıcı yada yanıt> x(m/h/d): Kişiyi Süreli Olarak Yasaklar. m = Dakika, h = Saat, d = Gün.
 - /unban <kullanıcı yada yanıt>: Kullanıcının Yasağını Kaldırır.
 - /kick <kullanıcı yada yanıt>: Kullanıcıyı Gruptan Atar.
"""

__mod_name__ = "Bans"

BAN_HANDLER = CommandHandler("ban", ban, pass_args=True, filters=Filters.group)
TEMPBAN_HANDLER = CommandHandler(["tban", "tempban"], temp_ban, pass_args=True, filters=Filters.group)
KICK_HANDLER = CommandHandler("kick", kick, pass_args=True, filters=Filters.group)
UNBAN_HANDLER = CommandHandler("unban", unban, pass_args=True, filters=Filters.group)
KICKME_HANDLER = DisableAbleCommandHandler("kickme", kickme, filters=Filters.group)
RBAN_HANDLER = CommandHandler("rban", rban, pass_args=True, filters=CustomFilters.sudo_filter)
RUNBAN_HANDLER = CommandHandler("runban", runban, pass_args=True, filters=CustomFilters.sudo_filter)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
dispatcher.add_handler(RBAN_HANDLER)
dispatcher.add_handler(RUNBAN_HANDLER)
