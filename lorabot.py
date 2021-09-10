#!/usr/bin/python3
import locale, logging, os, subprocess, json, routeros_api
from telegram import (
    ParseMode,
    Update,
    Bot,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)

locale.setlocale(locale.LC_ALL, 'es_AR.utf8')
bot_id=os.getenv("LORA_BOT_ID")
host_pasarela=os.getenv("HOST_PASARELA")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
autorizados=json.loads(os.environ['LORA_BOT_AUTORIZADOS'])

def start(update: Update, context: CallbackContext):
    #print(update.message.from_user.id)
    if update.message.from_user.id not in autorizados:
        context.bot.send_message(chat_id=update.message.chat_id, text="No estás autorizado. \n Hasta luego!")
    else:
        nombre=update.message.from_user.first_name +" "+update.message.from_user.last_name
        # kb = [["ip"],["ssh"],["sshkill"]]
        # kb_markup = ReplyKeyboardMarkup(kb)
        context.bot.send_message(update.message.chat.id, text="Bienvenido "+ nombre + " a la pasarela Lora", reply_markup=ReplyKeyboardRemove())

def iipp(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.message.chat_id, text=subprocess.check_output(['hostname', '--all-ip-addresses'])[:-2].decode())

def reboot(update: Update, context: CallbackContext):
    print("chau")
    os.system("sudo reboot")

def rebootgw(update: Update, context: CallbackContext):
    connection = routeros_api.RouterOsApiPool(
        os.getenv("GW_LORA_IP"),
        username=os.getenv("GW_LORA_USR"),
        password=os.getenv("GW_LORA_PASS"),
        use_ssl=True,
        ssl_verify=False,
        ssl_verify_hostname=False,
        plaintext_login=True)
    api = connection.get_api()
    api.get_binary_resource('/').call('system/reboot')
    connection.disconnect()


def buscarssh(puerto,usuario):
    # puerto='22223'
    buscar= "ssh -f -N -T -R"+puerto+":localhost:22 "+usuario+"@"+host_pasarela
    p = subprocess.Popen(['ps', '-aux'], stdout=subprocess.PIPE)
    out, err = p.communicate()
    for line in out.splitlines():
        # print(line)
        if buscar in line.decode():
            pid = (line.split(None, 2)[1]).decode()
            return pid
    return 0

def ssh(update: Update, context: CallbackContext):
    if(update.message.from_user.id==autorizados[0]):
        pid=buscarssh('22223','pi')
        if(int(pid)>0):
            mensaje="ya existe un tunel "+pid 
        else:
            p = subprocess.Popen(["/usr/bin/sshpass", "-e", "/usr/bin/ssh", "-f", "-N", "-T", "-R22223:localhost:22", "pi@"+host_pasarela], stdout=subprocess.PIPE)
            out, err = p.communicate()
            pid=buscarssh('22223', 'pi')
            if(int(pid)>0):
                mensaje="se creó el tunel con id: "+pid+"\n"
            else:
                # print(out)
                print(err)
                mensaje="NO se creó el tunel"+"\n"+err

    elif(update.message.from_user.id==autorizados[1]):
        pid=buscarssh('22222','milton')
        if(int(pid)>0):
            mensaje="ya existe un tunel "+pid 
        else:
            p = subprocess.Popen(["/usr/bin/sshpass", "-e", "/usr/bin/ssh", "-f", "-N", "-T", "-R22222:localhost:22", "milton@"+host_pasarela], stdout=subprocess.PIPE)
            out, err = p.communicate()
            pid=buscarssh('22222','milton')
            if(int(pid)>0):
                mensaje="se creó el tunel con id: "+pid+"\n"
            else:
                # print(out)
                print(err)
                mensaje="NO se creó el tunel"+"\n"+err

    context.bot.send_message(chat_id=update.message.chat_id, text=mensaje)
    # print(subprocess.check_output)

def sshkill(update: Update, context: CallbackContext):
    p = subprocess.Popen(['ps', '-aux'], stdout=subprocess.PIPE)
    out, err = p.communicate()
    if(update.message.from_user.id==autorizados[0]):
        buscar= "ssh -f -N -T -R22223:localhost:22 pi@"+host_pasarela
    elif(update.message.from_user.id==autorizados[1]):
        buscar= "ssh -f -N -T -R22222:localhost:22 milton@"+host_pasarela
    for line in out.splitlines():
        if buscar in line.decode():
            print("encontrado")
            pid = (line.split(None, 2)[1]).decode()
            print(pid)
            p=subprocess.Popen(["kill", pid])
            out, err = p.communicate()
            print(out)
            print(err)
            if err:
                mensaje="ERROR: "+err
            else:
                mensaje= "se eliminó el pid: "+pid
            context.bot.send_message(chat_id=update.message.chat_id, text=mensaje)
            return

def main() -> None:
    # Create the Updater and pass it your bot's token.
    updater = Updater(bot_id)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start, Filters.user(user_id=autorizados)))
    dispatcher.add_handler(CommandHandler('ip', iipp))
    dispatcher.add_handler(CommandHandler('ssh', ssh))
    dispatcher.add_handler(CommandHandler('sshkill', sshkill))
    dispatcher.add_handler(CommandHandler('reboot', reboot))
    dispatcher.add_handler(CommandHandler('rebootgw', rebootgw))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
