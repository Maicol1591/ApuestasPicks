import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd 

# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)

# Find a workbook by name and open the first sheet
# Make sure you use the right name here.
sheet = client.open("Peruvian Picks - Datos membresias (1)").sheet1

# Extract and print all of the values
nombre = sheet.col_values(1)
nombre.pop(1)
id_usuario = sheet.col_values(2)
id_usuario.pop(1)
estado = sheet.col_values(3)
estado.pop(1)
grupo = sheet.col_values(4)
grupo.pop(1)
duracion_membresia = sheet.col_values(5)
duracion_membresia.pop(1)
fecha_ingreso = sheet.col_values(6)
fecha_ingreso.pop(1)
tiempo_grupo = sheet.col_values(7)
tiempo_grupo.pop(1)
membresia_restante = sheet.col_values(10)
membresia_restante.pop(0)


# d = {'Nombre': nombre, 'Usuario': usuario, 'Fecha de ingreso': fecha_ingreso, 'Paquete': paquete, 'Receptor de deposito': receptor_deposito, 
# 'Tiempo de membresia': tiempo_membresia, 'Duracion del plan': duracion_plan, 
# 'Tiempo en el grupo': tiempo_grupo, 'Membresaia restante': membresia_restante, 'Estado': estado}

# df = pd.DataFrame(d)


"""
Pasos: 

#1 Crear Grupo de Telegram donde se mandarán los mensajes: https://t.me/+JSlgqm-UOE01NzIx
#2 Crear BOT
#3 Extraer API del Bot: 5272787789:AAFjGkkp_gkl_ZvIRoy_3fzenNZmafu_oUY
#4 Chat ID: (-1001660062839) http://api.telegram.org/bot5272787789:AAFjGkkp_gkl_ZvIRoy_3fzenNZmafu_oUY/getUpdates
#5 Mandar mensaje de prueba
http://api.telegram.org/bot5272787789:AAFjGkkp_gkl_ZvIRoy_3fzenNZmafu_oUY/sendMessage?chat_id=-435015478&text="Mensaje de prueba"

#6 Identificar a los nuevos integrantes del grupo
#7 Subir a los nuevos miembros a un Google Sheets (Añadir el ID del usuario)
#7 Identificar a todos los integrantes del grupo
#8 Mandar un mensaje a cada ID en función del tiempo restante de su membresía 
"""
import requests
import logging
from typing import Tuple, Optional

from telegram import Update, Chat, ChatMember, ParseMode, ChatMemberUpdated
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    ChatMemberHandler,
    MessageHandler,
    Filters
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


def extract_status_change(
    chat_member_update: ChatMemberUpdated,
) -> Optional[Tuple[bool, bool]]:
    """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
    of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
    the status didn't change.
    """
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = (
        old_status
        in [
            ChatMember.MEMBER,
            ChatMember.CREATOR,
            ChatMember.ADMINISTRATOR,
        ]
        or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    )
    is_member = (
        new_status
        in [
            ChatMember.MEMBER,
            ChatMember.CREATOR,
            ChatMember.ADMINISTRATOR,
        ]
        or (new_status == ChatMember.RESTRICTED and new_is_member is True)
    )

    return was_member, is_member


def track_chats(update: Update, context: CallbackContext) -> None:
    """Tracks the chats the bot is in."""
    result = extract_status_change(update.my_chat_member)
    if result is None:
        return
    was_member, is_member = result

    # Let's check who is responsible for the change
    cause_name = update.effective_user.full_name

    # Handle chat types differently:
    chat = update.effective_chat
    if chat.type == Chat.PRIVATE:
        if not was_member and is_member:
            logger.info("%s started the bot", cause_name)
            context.bot_data.setdefault("user_ids", set()).add(chat.id)
        elif was_member and not is_member:
            logger.info("%s blocked the bot", cause_name)
            context.bot_data.setdefault("user_ids", set()).discard(chat.id)
    elif chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        if not was_member and is_member:
            logger.info("%s added the bot to the group %s", cause_name, chat.title)
            context.bot_data.setdefault("group_ids", set()).add(chat.id)
        elif was_member and not is_member:
            logger.info("%s removed the bot from the group %s", cause_name, chat.title)
            context.bot_data.setdefault("group_ids", set()).discard(chat.id)
    else:
        if not was_member and is_member:
            logger.info("%s added the bot to the channel %s", cause_name, chat.title)
            context.bot_data.setdefault("channel_ids", set()).add(chat.id)
        elif was_member and not is_member:
            logger.info("%s removed the bot from the channel %s", cause_name, chat.title)
            context.bot_data.setdefault("channel_ids", set()).discard(chat.id)


def show_chats(update: Update, context: CallbackContext) -> None:
    """Shows which chats the bot is in"""
    user_ids = ", ".join(str(uid) for uid in context.bot_data.setdefault("user_ids", set()))
    group_ids = ", ".join(str(gid) for gid in context.bot_data.setdefault("group_ids", set()))
    channel_ids = ", ".join(str(cid) for cid in context.bot_data.setdefault("channel_ids", set()))
    text = (
        f"@{context.bot.username} is currently in a conversation with the user IDs {user_ids}."
        f" Moreover it is a member of the groups with IDs {group_ids} "
        f"and administrator in the channels with IDs {channel_ids}."
    )
    update.effective_message.reply_text(text)


def greet_chat_members(update: Update, context: CallbackContext) -> None:
    """Greets new users in chats and announces when someone leaves"""
    bot = context.bot
    result = extract_status_change(update.chat_member)
    if result is None:
        return

    was_member, is_member = result
    cause_name = update.chat_member.from_user.mention_html()
    member_name = update.chat_member.new_chat_member.user.mention_html()
    username = update.chat_member.new_chat_member.user.first_name
    chatId = update.chat_member.new_chat_member.user.id
    chatTittle = update._effective_chat.title

    if not was_member and is_member:
        update.effective_chat.send_message(
            f"{member_name} fue añadido por {cause_name}. ¡Bienvenido!",
            parse_mode=ParseMode.HTML,
        )
        sheet.update('B2', username)
        sheet.update('C2', chatId)
        sheet.update('D2', 'Activo')
        sheet.update('E2', chatTittle)
    
        


    elif was_member and not is_member:
        update.effective_chat.send_message(
            f"{member_name} ya no está con nosotros. Fue explusado por {cause_name} ...",
            parse_mode=ParseMode.HTML,
        )
        duracion = update.effective_user['until_date']
        sheet.update('D2', 'Retirado')
        sheet.update('F', duracion)


def start(update: Update, context: CallbackContext):
    tipo=update.effective_chat['type']

    if tipo == "supergroup":
        pass

    primer_nombre = update.effective_user['first_name']

    update.message.reply_text(f"Hola, {primer_nombre}, te recordamos que te quedan {membresia_restante} dias en tu membresia.")


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater("5272787789:AAFjGkkp_gkl_ZvIRoy_3fzenNZmafu_oUY")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Keep track of which chats the bot is in
    dispatcher.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER))
    dispatcher.add_handler(CommandHandler("show_chats", show_chats))

    # Handle members joining/leaving chats.
    dispatcher.add_handler(ChatMemberHandler(greet_chat_members, ChatMemberHandler.CHAT_MEMBER))
    dispatcher.add_handler(CommandHandler("start",start))


    # Start the Bot
    # We pass 'allowed_updates' handle *all* updates including `chat_member` updates
    # To reset this, simply pass `allowed_updates=[]`
    updater.start_polling(allowed_updates=Update.ALL_TYPES)
    

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    print("BOT LISTO")
    updater.idle()


if __name__ == "__main__":
    main()
