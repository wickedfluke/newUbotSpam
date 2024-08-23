import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import PeerUser, PeerChat, PeerChannel
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
import re

API_ID = 25765102 
API_HASH = "ea1f34752c0860fa799b4153da5c5554"

groups = []
spamEnabled = False
Time = 1
Message = None
auto_reply_message = None
approved_chats = set()

client = TelegramClient('opentelegramfiles', API_ID, API_HASH)

# Fissare il messaggio di auto-reply
@client.on(events.NewMessage(outgoing=True, pattern=r"\.reply"))
async def set_auto_reply_message(event):
    global auto_reply_message
    if event.is_reply:
        auto_reply_message = await event.get_reply_message()
        await event.reply("Messaggio di auto-reply fissato!")
    else:
        await event.reply("Rispondi a un messaggio per impostarlo come auto-reply!")

# Comando .approve per disabilitare l'auto-reply in una chat privata specifica
@client.on(events.NewMessage(outgoing=True, pattern=r"\.approve"))
async def approve_chat(event):
    global approved_chats
    if isinstance(event.peer_id, PeerUser):  # Verifica se la chat è una chat privata
        approved_chats.add(event.peer_id.user_id)  # Aggiungi la chat alla lista delle chat approvate
        await event.reply("Auto-reply disabilitato per questa chat.")
    else:
        await event.reply("Questo comando può essere usato solo nelle chat private!")

# Funzione per eseguire l'auto-reply
@client.on(events.NewMessage(incoming=True))
async def auto_reply(event):
    global auto_reply_message, approved_chats
    
    if isinstance(event.peer_id, PeerUser) and event.peer_id.user_id not in approved_chats:
        # Verifica se il messaggio arriva da una chat privata e che non sia stata approvata
        if not event.out and auto_reply_message:
            try:
                await event.reply(auto_reply_message)
            except Exception as e:
                print(f"Errore durante l'auto-reply: {str(e)}")

# Funzione per ottenere tutti i gruppi
async def get_all_groups(client):
    all_dialogs = await client.get_dialogs()
    return [dialog.id for dialog in all_dialogs if dialog.is_group]

# Funzione per gestire lo spam nei gruppi
async def do_spam(client, msg):
    try:
        all_groups = await get_all_groups(client)
        for group in all_groups:
            try:
                await client.forward_messages(group, msg)
                await asyncio.sleep(0.2)  
            except Exception as e:
                print(f"Errore durante l'inoltro al gruppo {group}: {str(e)}")
    except Exception as e:
        print(f"Errore generale nel ciclo di spam: {str(e)}")

# Funzione per fissare il messaggio di spam
@client.on(events.NewMessage(outgoing=True, pattern=r"\.mex"))
async def set_message(event):
    global Message
    if event.is_reply:
        Message = await event.get_reply_message()
        await event.reply("Messaggio fissato per lo spam.")
    else:
        await event.reply("Rispondi a un messaggio per fissarlo per lo spam!")

# Funzione per unire ai gruppi tramite link o @mention
@client.on(events.NewMessage(outgoing=True, pattern=r"\.join"))
async def join_groups(event):
    if event.is_reply:
        reply_msg = await event.get_reply_message()
        links = re.findall(r"(https?://t\.me/joinchat/[^\s]+|@[^\s]+)", reply_msg.text)
        
        for link in links:
            try:
                if link.startswith("http"):
                    await client(ImportChatInviteRequest(link.split('/')[-1]))
                elif link.startswith("@"):
                    await client(JoinChannelRequest(link[1:]))
                await event.reply(f"Joined successfully: {link}")
            except Exception as e:
                await event.reply(f"Failed to join: {link}\nError: {str(e)}")
    else:
        await event.reply("Rispondi a un messaggio contenente link di gruppo o @mention!")

@client.on(events.NewMessage(outgoing=True, pattern=r"\.help"))
async def send_help_link(event):
    help_link = "https://telegra.ph/Comandi-Spam-Userbot--Dev-DebiruDansei-08-23"
    await event.reply(f"Ecco la lista dei comandi: [Comandi Spam Userbot]({help_link})")


# Funzione per gestire i comandi di spam
@client.on(events.NewMessage(outgoing=True))
async def handle_commands(event):
    global groups, Message, spamEnabled, Time
    
    if event.text == ".start":
        if not spamEnabled:
            if Message is None:
                await event.reply("Errore: nessun messaggio fissato per lo spam.")
                return

            await event.edit("Spam avviato!")
            spamEnabled = True

            try:
                while spamEnabled:
                    await asyncio.wait([asyncio.create_task(do_spam(event.client, Message))])
                    for i in range(Time * 60):  
                        if spamEnabled:
                            await asyncio.sleep(1)
                        else:
                            break
            except Exception as e:
                await event.reply(f"Errore durante lo spam: {str(e)}")

    elif event.text == ".stop":
        await event.edit("Spam stoppato!")
        spamEnabled = False

    elif event.text == ".addgroup":
        if isinstance(event.peer_id, PeerUser):
            await event.edit("Stai parlando con un utente! Questo non è un gruppo!")
        else:
            try:
                if isinstance(event.peer_id, PeerChat):
                    groups.append(event.peer_id.chat_id)
                elif isinstance(event.peer_id, PeerChannel):
                    groups.append(event.peer_id.channel_id)
                await event.edit("Gruppo aggiunto per lo spam correttamente!")
            except Exception as e:
                await event.edit(f"Errore nell'aggiunta del gruppo: {str(e)}")

    elif event.text == ".addchannelforspam":
        if isinstance(event.peer_id, PeerChannel):
            groups.append(event.peer_id.channel_id)
            await event.edit("Canale aggiunto per lo spam correttamente!")

    elif event.text == ".remove_this_forspam":
        # Logica per rimuovere il gruppo corrente per lo spam
        try:
            if isinstance(event.peer_id, PeerChat) or isinstance(event.peer_id, PeerChannel):
                if event.peer_id.chat_id in groups:
                    groups.remove(event.peer_id.chat_id)
                elif event.peer_id.channel_id in groups:
                    groups.remove(event.peer_id.channel_id)
                await event.edit("Gruppo rimosso dallo spam correttamente!")
        except Exception as e:
            await event.edit(f"Errore durante la rimozione del gruppo per lo spam: {str(e)}")

    elif event.text == ".messaggio":
        if event.is_reply:
            new = await event.get_reply_message()
            media = new.media if new.media and type(new.media).__name__ not in ["MessageMediaWebPage", "MessageMediaUnsupported"] else None
            lp = bool(new.web_preview)
            Message = [new.text, media, lp]
            await event.edit("Messaggio fissato per lo spam.")
        else:
            await event.edit("Nessun messaggio fissato per lo spam! Rispondi a un messaggio per fissarlo.")

    elif event.text == ".time":
        if event.is_reply:
            new = await event.get_reply_message()
            try:
                selected_time = int(new.text)
                if 1 <= selected_time <= 60:
                    Time = selected_time
                    await event.edit(f"Tempo selezionato: {Time} minuti.")
                else:
                    await event.edit("Tempo non valido, inserire un valore tra 1 e 60.")
            except ValueError:
                await event.edit("Errore: inserire un numero valido.")

client.start()
client.run_until_disconnected()
