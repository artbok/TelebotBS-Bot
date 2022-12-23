import telebot
from telebot import types
from User import UserRepository, User
from datetime import datetime
from threading import Timer 
import yaml 
import requests
import json
import random

#ФУНКЦИИ, ОТВЕЧАЮЩИЕ ЗА ЧТЕНИЕ/СОХРАНЕНИЕ ФАЙЛОВ

def openFile(path):
    with open(path, encoding="utf-8") as file:
        return yaml.safe_load(file)

def saveFile(path, data):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True)

#ПЕРЕМЕННЫЕ

lang = openFile("storage\\lang.yaml") 
settings = openFile("storage\\settings.yaml")
teams = openFile("storage\\teams.yaml")
blacklist = openFile("storage\\blacklist.yaml")
adminlist = openFile("storage\\adminlist.yaml")
token = openFile("storage\\tokens.yaml")

LoggerBot = telebot.TeleBot(settings["LoggerBotToken"], skip_pending=True)
bot = telebot.TeleBot(settings["BotToken"], skip_pending=True)

adminchat = settings["adminchat"]
chat = settings["chat"]
CheckList = []
GameIDs = set()
timeTasks = {}

userRepository = UserRepository().load(settings)

#ЛОГИРОВАНИЕ

def userLogging(ChatID, first_name, text):
    log = "👤 | " + datetime.now().strftime("%H:%M:%S") + " | " + first_name + "(" + str(ChatID) + ") | " + text
    LoggerBot.send_message(1193654237, log)

def botLogging(ChatID, action):
    log = "🤖 | " + datetime.now().strftime("%H:%M:%S") + " | BOT to " + str(ChatID) + " | " + action
    LoggerBot.send_message(1193654237, log)

#ОТДЕЛЬНЫЕ ФУНКЦИИ

def checkChatID(id):
    if id != adminchat and id != chat:
        return True
    botLogging(id, "InvalidChatID")
    bot.send_message(id, "Использовать команды можно только в ЛС с ботом(@AboBS_bot)")
    return False


def getUserStats(tag, id):
    user: User = userRepository.get(id)
    url = "https://api.brawlstars.com/v1/players/%23" + tag
    r = requests.get(url, headers={"Authorization": settings["AuthKey"]})
    if r.status_code != 200:
        text = "Игрок под данным ID не найден. Проверьте правильность написания и повторите команду."
    else:
        data = json.loads(r.text)
        if user.j_Status is True:
            user.j_Nickname = data["name"]
            text = "👤 Ник: <a href='tg://user?id=" + str(id) + "'>" + data["name"] + "</a>\n"
        else:
            text = "👤 Ник: <b>" + data["name"] + "</b>\n"    
        text += "🎮 ID: <code>" + data["tag"] + "</code>\n🏆 Трофеи: <b>" + str(data["trophies"]) + "</b>\n🏅 Макс. трофеев: <b>" + str(data["highestTrophies"]) + "</b>\n" + "⭐️ Уровень опыта: <b>" + str(data["expLevel"])
        if data["club"]:
            text += "</b>\n👥 Клуб: <b>" + data["club"]["name"]
        else:
            text += "</b>\n👥 Клуб: <b>Отсутсвует"
        text +=  "</b>\n🥇 Побед в соло: <b>" + str(data["soloVictories"]) + "</b>\n🥈 Побед в дуо: <b>" + str(data["duoVictories"]) + "</b>\n🥉 Побед в трио: <b>" + str(data["3vs3Victories"]) + "</b>\n🏋🏿 Бойцы на 11 силе: "
        brawlersAt11Lvl = 0
        brawlersAt10Lvl = 0
        brawlersAt26Rank = 0
        brawlersAt30Rank = 0
        stack = 0
        for i in range(len(data["brawlers"])):
            if data["brawlers"][i]["rank"] >= 30:
                brawlersAt30Rank += 1
            elif data["brawlers"][i]["rank"] > 25:
                brawlersAt26Rank += 1
            if data["brawlers"][i]["power"] == 11:
                if stack % 3 == 0:
                    text += "\n        "
                text += "<b>" + lang[data["brawlers"][i]["name"]] + "</b>, "
                brawlersAt11Lvl += 1
                stack += 1
            elif data["brawlers"][i]["power"] == 10:
                brawlersAt10Lvl += 1
        text = text[:len(text)-2] + "\n🔹 Всего 11-ых уровней: <b>" + str(brawlersAt11Lvl) + "</b>\n🔹 Всего 10-ых уровней: <b>" + str(brawlersAt10Lvl) + "</b>\n🔸 Бойцов на 26-29 ранге: <b>" + str(brawlersAt26Rank) + "</b>\n🔸 Бойцов на 30-35 ранге: <b>" + str(brawlersAt30Rank) + "</b>"
    return text


def DayStart(day):
    text = "Всех приветвую, через 7 часов начнётся " + day + " день лиги клубов. Команды на первый день:"
    for i in teams.keys():
        text += "\nКоманда №" + str(i) + ": "
        teams[i]["time"] = "Не назначено"
        for id in teams[i]["users"]:
            if id != "Не назначено":
                user: User = userRepository.get(id)
                user.t_Dict = {'17': [['', '00'], ['', '20'], ['', '40']], '18': [['', '00'], ['', '20'], ['', '40']], '19': [['', '00'], ['', '20'], ['', '40']], '20': [['', '00'], ['', '20'], ['', '40']], '21': [['', '00'], ['', '20'], ['', '40']], '22': [['', '00'], ['', '20'], ['', '40']], '23': [['', '00'], ['', '20'], ['', '40']], '08': [['', '00'], ['', '20'], ['', '40']], '09': [['', '00'], ['', '20'], ['', '40']], '10': [['', '00'], ['', '20'], ['', '40']], '11': [['', '00'], ['', '20'], ['', '40']], '12': [['', '00'], ['', '20'], ['', '40']], '13': [['', '00'], ['', '20'], ['', '40']], '14': [['', '00'], ['', '20'], ['', '40']], '15': [['', '00'], ['', '20'], ['', '40']], '16': [['', '00'], ['', '20'], ['', '40']]}
                markup = types.InlineKeyboardMarkup(row_width=4)
                for h in user.t_Dict.keys():
                    vHour = visualTime(int(h), user.timeZone)
                    markup.add(types.InlineKeyboardButton(vHour, callback_data='4' + str(h)), types.InlineKeyboardButton(('✅' if user.t_Dict[h][0][0] != '' else '') + vHour + ":" + user.t_Dict[h][0][1], callback_data='4' + str(h) + '0'), types.InlineKeyboardButton(('✅' if user.t_Dict[h][1][0] != '' else '') + vHour + ":" + user.t_Dict[h][1][1], callback_data='4' + str(h) + '1'), types.InlineKeyboardButton(('✅' if user.t_Dict[h][2][0] != '' else '') + vHour + ":" + user.t_Dict[h][2][1], callback_data='4' + str(h) + '2'))
                markup.add(types.InlineKeyboardButton(text='Выберите еще минимум 8 времён', callback_data="None"))
                user.t_MessageID = bot.send_message(id, "Скоро начнётся " + day + " день клубной лиги! Обязательно выберите времена, когда вы будете свободны для игры. После выбора не забудьте нажать на кнопку сохранить! (Для этого необходимо выбрать как минимум 8 времен)", reply_markup=markup).message_id
                text += "\n   - <a href='tg://user?id=" + str(id) + "'>" + user.nickname + "</a>"
    text += """
\n\nКаждому из вас я отправил в личные сообщения таблицу с выбором времени, которую необходимо заполнить. После того как каждый игрок вашей команды выберет времена, я пришлю вам общее время игры. Лучше выбирать <b>как можно больше времён</b>, 
ведь если не найдётся ни одного общего времени, то вам придётся решать этот вопрос самостоятельно.  
Я отправлю вам напоминание за 20 минут до назначенного времени и в назначенное время. <b>При выборе времён просьба тыкать на кнопки не быстро, чтобы телеграм успел все обработать.</b> Желаю всем удачи!
"""
    botLogging("chat", "DayStart")
    bot.send_message(chat, text, parse_mode="HTML")
    saveFile("storage\\settings.yaml", settings)
    saveFile("storage\\teams.yaml", teams)

def CheckTable(day):
    text = "Через 10 минут начнётся " + day + " день клубной лиги! Рассписание игр на этот день: "
    for i in range(1, 11):
        text += "\nКоманда " + str(i) + " ("
        for id in teams[i]["users"]:
            if id != "Не назначено":
                user: User = userRepository.get(id)
                user.t_Dict = {}
                if day == "третий":
                    CheckList.append([id, 3])
                else:
                    CheckList.append([id, 2])
                text += user.nickname + ", "
                if teams[i]["time"] == "Не назначено":
                    bot.send_message(id, "Кто-то из ваших тимейтов так и не ответил на мой вопрос, поэтому теперь вы выбираете время самостоятельно)")
                    bot.delete_message(id, user.t_MessageID)
    
        text = text[:len(text)-2] + (") - <b>" + teams[i]["time"] + "</b>")
    botLogging("chat", "CheckTable")
    saveFile("storage\\settings.yaml", settings)    
    bot.send_message(chat, text + "\nЖелаю всем удачи!", parse_mode="HTML")

def EndOfTheDay(day):
    text = day + " день клубной лиги завершился! Наш клуб набрал: <b>" + str(settings["ClubTrophies"]) + " очков</b>. Рейтинг клуба по очкам: "
    leaderList = {}
    for i in range(1, 11):
        teams[i]['time'] = 'Не назначено'
        for id in teams[i]["users"]:
            if id != "Не назначено":
                settings['user'][id]["TimeForCL"] = []
                user: User = userRepository.get(id)
                user.times = []
                if settings['user'][id]['WeekTropheys'] not in leaderList:
                    leaderList[settings['user'][id]['WeekTropheys']] = [settings['user'][id]['Nickname']]
                else:
                    leaderList[settings['user'][id]['WeekTropheys']].append(settings['user'][id]['Nickname'])
    saveFile("storage\\settings.yaml", settings)   
    saveFile("storage\\teams.yaml", teams)   
    sorted(leaderList.keys(), reverse=True)
    position = 1
    for i in leaderList.keys():
        text += "\n<b>#" + str(position) + " " + str(i) + " очков</b>: "
        for j in leaderList[i]:
            text += j + ", "
        text = text[:len(text)-2]
        position += 1
    botLogging("chat", "EndOfTheDay")
    bot.send_message(chat, text, parse_mode="HTML")
def FindCommonTime(team, id):
    times = []
    players = []
    for id in teams[team]["users"]:
        if id != "Не назначено":
            user: User = userRepository.get(id)
            if not user.times:
                return 'Спасибо что выбрали времена. Теперь ожидайте пока ваши тимейты также ответят на этот вопрос.', "None"
            else:
                players.append(user.times)
    if len(players) == 3:
        times = list(set(players[0]) & set(players[1]) & set(players[2]))
    elif len(players) == 2:
        times = list(set(players[0]) & set(players[1]))
    else:
        times = players[0]
    if times:
        time = random.choice(times)
        teams[team]["time"] = time
        timeTasks[time].append([team, "Game"])
        h = time[:2]
        m = time[3:]
        if m == "00":
            m = "40"
            h = str(int(h)-1)
            if len(h) == 1:
                h = "0" + h
        elif m == "20":
            m = "00"
        else:
            m = "20"  
        timeTasks[h+":"+m].append([team, "Remind"])
        saveFile("storage\\teams.yaml", teams)
        return "Все пользователи выбрали свободные времена! Общим временем оказалось <b>", time
    else:
        #botLogging(id, "FCT team: " + str(team)) + " TimeNotFound"
        return "Все пользователи выбрали свободные времена! К сожалению общего времени не нашлось.", "NotFound"

def visualTime(hour, td):
    hour += td
    if hour > 23: hour -= 24 
    if hour < 0: hour += 24
    if len(str(hour)) == 1: return "0" + str(hour)
    return str(hour)

#ЦИКЛИЧНАЯ ГЛАВНАЯ ФУНКЦИЯ

def check():
    Timer(60, check).start()
    date = datetime.now().strftime('%a/%H:%M')
    week = int(datetime.now().strftime('%W')) % 2
    if date == 'Wed/08:00' and week == 1:
        DayStart("первый")
    elif date == 'Fri/08:00' and week == 1:
        DayStart("второй")
    elif date == 'Sun/13:22' and week == 1:
        DayStart("третий")
    if date == 'Wed/16:50' and week == 1:
         CheckTable("первый")
    elif date == 'Fri/16:50' and week == 1:
         CheckTable("второй")
    elif date == 'Sun/16:50' and week == 1:
         CheckTable("третий")
    if date == 'Thu/17:05' and week == 1:
        EndOfTheDay("Первый")
    elif date == 'Sat/17:05' and week == 1:
        EndOfTheDay("Второй")
    elif date == 'Mon/17:05' and week == 0:
        EndOfTheDay("Третий")      
    date = datetime.now().strftime('%H:%M')
    if date in timeTasks:
        for i in timeTasks[date]:
            if i[1] == "Remind":
                for id in teams[i[0]]["users"]:
                    if id != "Не назначено":
                        bot.send_message(id, "<b>Напоминаю, что через 20 минут вы собирались пойти в клубную лигу!</b>", parse_mode="HTML")
                        botLogging(id, "GameReminder1")
                timeTasks[date].remove(i)
            else:
                for id in teams[i[0]]["users"]:
                    if id != "Не назначено":
                        bot.send_message(id, "*Пожалуйста зайдите в игру и ожидайте своих тиммейтов.*", parse_mode="Markdown")
                        botLogging(id, "GameReminder2")
                timeTasks[date].remove(i)
            if len(timeTasks[date]) == 0:
                del timeTasks[date]
    for i in range(len(CheckList)):
        url = 'https://api.brawlstars.com/v1/players/%23' + settings["user"][CheckList[i][0]]["Tag"] + "/battlelog"
        r = requests.get(url, headers={'Authorization': settings["AuthKey"]})
        data = json.loads(r.text)
        if data["items"][0]["battle"]["type"] == "teamRanked" and "trophyChange" in data["items"][0]["battle"]:
            if CheckList[i][1] == 1:
                CheckList.pop(i)
            else:
                CheckList[i][1] -= 1
            settings['user'][CheckList[i][0]]['DayTropheys'] += data["items"][0]["battle"]["trophyChange"]
            settings['user'][CheckList[i][0]]['WeekTropheys'] += data["items"][0]["battle"]["trophyChange"]
            settings['user'][CheckList[i][0]]['TotalTropheys'] += data["items"][0]["battle"]["trophyChange"]
            settings['ClubTrophies'] += data["items"][0]["battle"]["trophyChange"]
            if data["items"][0]["event"]["id"] not in GameIDs:
                GameIDs.add(data["items"][0]["event"]["id"])
                if data["items"][0]["battle"]["result"] == "victory":
                    text = "*Результат матча* \nСтатус: *ПОБЕДА* \nРежим: *" + data["items"][0]["event"]["mode"] + "*\nКарта: *" + data["items"][0]["event"]["map"] + "*" + "\nЗвёздный игрок: *" + data["items"][0]["battle"]["starPlayer"]["name"] + "\nСоставы команд: *"
                for j in range(0, 3): 
                    text += "\n🟦 *" + data["items"][0]["battle"]["teams"][0][j]["name"] + "* (`" + data["items"][0]["battle"]["teams"][0][j]["tag"]  + "`), *" + lang[data["items"][0]["battle"]["teams"][0][j]["brawler"]["name"]] + "(" + str(data["items"][0]["battle"]["teams"][0][j]["brawler"]["power"]) + " ур.)*"
                for j in range(0, 3):
                    text += "\n🟥 *" + data["items"][0]["battle"]["teams"][1][j]["name"] + "* (`" + data["items"][0]["battle"]["teams"][1][j]["tag"]  + "`), *" + lang[data["items"][0]["battle"]["teams"][1][j]["brawler"]["name"]] + "(" + str(data["items"][0]["battle"]["teams"][1][j]["brawler"]["power"]) + " ур.)*"
                bot.send_message(chat, text, parse_mode="Markdown")
                botLogging(CheckList[i][0], "MatchInfo")

#ОТСЛЕЖИВАНИЕ ДЕЙСТВИЙ

@bot.message_handler(commands=["del"])
def dele(message):
    for id in settings["userlist"]:
        user: User = userRepository.get(id)
        bot.delete_message(id, user.t_MessageID)
@bot.message_handler(commands=["ds"])
def DS(message):
    DayStart("первый")
@bot.message_handler(commands=["ct"])
def CT(message):
    CheckTable("первый")
@bot.message_handler(commands=["ed"])
def ED(message):
    EndOfTheDay("Первый")
@bot.message_handler(commands=["start"])
def startCMD(message):
    id = message.chat.id
    userLogging(id, message.from_user.first_name, message.text)
    if checkChatID(id):
        botLogging(id, "WelcomeMessage")
        bot.send_message(id, "Привет," + message.from_user.first_name + """. Я управляющий бот клуба ABOBA. Я отвечаю за вступление в клуб, выбор общего времени для игры в клубную лигу с командой и отслеживанием клубных боев. 
Если ты хочешь вступить в наш прекрасный клуб, то пропиши команду /join""")


@bot.message_handler(commands=["join"])
def joinCMD(message):
    id = message.chat.id
    userLogging(id, message.from_user.first_name, message.text)
    if checkChatID(id):
            if id not in blacklist:
                user: User = userRepository.get(id)
                user.j_Status = True
                botLogging(id, "WaitingForTheTag")
                bot.send_message(id, "Для отправки заявки на вступление в наш клуб, необходимо отправить свой ID из игры. Будут оцениваться твои общие кубки, победы в трио, силовая лига, а также силы бойцов.")
            else:
                botLogging(id, "ApplicationHasBeenSentBefore")
                bot.send_message(id, "Вы уже отправляли заявку ранее!")

@bot.message_handler(commands=["settimezone"])
def setTimeZone(message):
    id = message.chat.id
    if id in settings['userlist'] or id == chat or id == adminchat:
        if checkChatID(id):
            markup = types.InlineKeyboardMarkup(row_width=6)
            differences = [['-14', '-13', '-12', '-11', '-10', '-9'], ['-8', '-7', '-6', '-5', '-4', '-3'], ['-2', '-1', '0', '+1', '+2', '+3'], ['+4', '+5', '+6', '+7', '+8', '+9']]
            for i in differences:
                markup.add(types.InlineKeyboardButton(i[0], callback_data="6"+i[0]), types.InlineKeyboardButton(i[1], callback_data="6"+i[1]), types.InlineKeyboardButton(i[2], callback_data="6"+i[2]), types.InlineKeyboardButton(i[3], callback_data="6"+i[3]), types.InlineKeyboardButton(i[4], callback_data="6"+i[4]), types.InlineKeyboardButton(i[5], callback_data="6"+i[5]))
            bot.send_message(id, "Выберите свою разницу во времени относительно московского(0).", reply_markup=markup)
    else:
        bot.send_message(id, "Данная команда доступна только участникам клуба ABOBA. Если вы хотите вступить к нам, пропишите команду /join")

@bot.message_handler(commands=["playerinfo"])
def PlayerInfo(message):
    id = message.chat.id
    userLogging(id, message.from_user.first_name, message.text)
    if checkChatID(id):
        user: User = userRepository.get(id)
        user.i_Status = True
        botLogging(id, "WaitingForTheTag")
        bot.send_message(id, "Отправьте ID игрока, которого вы хотите проверить.")
        

@bot.message_handler(commands=['editteams'])
def EditTeams(message):
    id = message.chat.id
    if id in adminlist:
        botLogging(id, "EditTeams: ChooseTeam")
        user: User = userRepository.get(id)
        user.editteams()
        markup = types.InlineKeyboardMarkup(row_width=2)
        text = '<b>Какую команду вы хотите изменить?\n\nТекущие команды:</b>'
        for i in range(1, 11):
            text += '\n<b>Команда ' + str(i) + ': </b>' + ("Не назначено" if teams[i]['users'][0] == "Не назначено" else settings["user"][teams[i]['users'][0]]["Nickname"]) + ', '
            text += ("Не назначено" if teams[i]['users'][1] == "Не назначено" else settings["user"][teams[i]['users'][1]]["Nickname"]) + ', ' + ("Не назначено" if teams[i]['users'][2] == "Не назначено" else settings["user"][teams[i]['users'][2]]["Nickname"])
        for i in range(1, 11, 2):
            markup.add(types.InlineKeyboardButton('Команда ' + str(i), callback_data='1' + str(i)), types.InlineKeyboardButton('Команда ' + str(i+1), callback_data='1' + str(i+1)))
        bot.send_message(id, text, reply_markup=markup, parse_mode='HTML')
    else:
        botLogging(id, "EditTeams: NotAdmin")


@bot.message_handler(content_types=["text"])
def handleText(message):
    id = message.chat.id
    tag = message.text.upper()
    if tag[0] == "#":
        tag = tag[1:]
    if id != adminchat and id != chat:
        userLogging(id, message.from_user.first_name, message.text)
        user: User = userRepository.get(id)
        if user:
            if user.j_Status:
                user.j_Tag = tag
                text = getUserStats(tag, id)
                if text[0] != "И":
                    blacklist.append(id)
                    saveFile("storage\\blacklist.yaml", blacklist)
                    user.j_Text = text 
                    markup = types.InlineKeyboardMarkup(row_width=2)
                    btn1 = types.InlineKeyboardButton(" ПРИНЯТЬ ", callback_data="+" + str(id))
                    btn2 = types.InlineKeyboardButton(" ОТКЛОНИТЬ ", callback_data="-" + str(id))
                    markup.add(btn1, btn2)
                    bot.send_message(id, "Твоя заявка на вступление была отправлена на рассмотрение. Я уведомлю тебя когда придёт результат!")
                    bot.send_message(adminchat, "<b>Заявка на вступление:</b>\n" + text, parse_mode="HTML", reply_markup=markup)
                    user.j_Status = False
                    botLogging(id, "Send Application to adminchat")
                else:
                    botLogging(id, "Invalid tag")
                    bot.send_message(id, text)
            elif user.i_Status:
                text = getUserStats(tag, user)
                if text[0] != "И":
                    botLogging(id, "Send info about player")
                    bot.send_message(id, "<b>Инфомация об этом игроке:</b> \n" + text, parse_mode="HTML")
                else:
                    bot.send_message(id, text)
                    botLogging(id, "Invalid tag")
                user.i_Status, user.i_Tag = False, None

#CALBACKS

@bot.callback_query_handler(func=lambda callback: callback.data[0] == "+" or callback.data[0] == "-")
def acceptOrDeny(call): #Кнопки Принять и Отклонить
    id = int(call.data[1:])
    user: User = userRepository.get(id)
    if call.data[0] == "+":
        bot.answer_callback_query(call.id, text="Заявка принята")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="<b>Заявка на вступление:</b> \n" + user.j_Text +"\n<b>Принято пользователем " + call.from_user.first_name + "</b>", parse_mode="HTML")
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton(" Клуб ", url="https://link.brawlstars.com/invite/band/ru?tag=28U82UGGV&token=2rfhzttd")
        btn2 = types.InlineKeyboardButton(" Беседа клуба ", url="https://t.me/+89YGgnypEvRhZWFi")
        markup.add(btn1, btn2)
        bot.send_message(id, "Ваша заявка была <b>принята</b>! Добро пожаловать в наш уютный клуб.\n", reply_markup=markup, parse_mode="HTML")
        settings["userlist"].append(id)
        settings["user"][id] = {"Tag": user.j_Tag, "Nickname": user.j_Nickname, "Team": 0, "TimeZoneDifference": 0, "TimeForCL": [], "WeekTropheys": 0, "TotalTropheys": 0}
        saveFile("storage\\settings.yaml", settings)
        botLogging(id, "Application has been accepted")
        userRepository.load(settings)
        user.loadProfile(user.j_Tag, user.j_Nickname, [], 0, 0, 0, 0)
    elif call.data[0] == "-":
        bot.answer_callback_query(call.id, text="Заявка отклонена")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="<b>Заявка на вступление:</b> \n" + user.j_Text +"\n<b>Отклонено пользователем " + call.from_user.first_name + "</b>", parse_mode="HTML")
        bot.send_message(id, "Ваша заявка была <b>отклонена</b>.", parse_mode="HTML")
        botLogging(id, "Application has been declined")

@bot.callback_query_handler(func=lambda callback: callback.data[0] == '4')
def timeTableClick(call): 
    id = call.message.chat.id
    user: User = userRepository.get(id)
    markup = types.InlineKeyboardMarkup(row_width=4)
    if len(call.data) == 4:
        h = call.data[1:3]
        m = int(call.data[3])
        if user.t_Dict[h][m][0] == '':
            user.t_Dict[h][m][0] = '✅'
            user.t_Counter += 1
        else:
            user.t_Dict[h][m][0] = ''
            user.t_Counter -= 1
    else:
        h = call.data[1:3]
        if user.t_Dict[h][0][0] == '✅' or user.t_Dict[h][1][0] == '✅' or user.t_Dict[h][2][0] == '✅':
            for i in range(3):
                if user.t_Dict[h][i][0] == '✅':
                    user.t_Dict[h][i][0] = ''
                    user.t_Counter -= 1
        else:
            for i in range(3):
                if user.t_Dict[h][i][0] == '':
                    user.t_Dict[h][i][0] = '✅' 
                    user.t_Counter += 1        

    for h in user.t_Dict.keys():
        vHour = visualTime(int(h), user.timeZone)
        markup.add(types.InlineKeyboardButton(vHour, callback_data='4' + str(h)), types.InlineKeyboardButton(('✅' if user.t_Dict[h][0][0] != '' else '') + vHour + ":" + user.t_Dict[h][0][1], callback_data='4' + str(h) + '0'), types.InlineKeyboardButton(('✅' if user.t_Dict[h][1][0] != '' else '') + vHour + ":" + user.t_Dict[h][1][1], callback_data='4' + str(h) + '1'), types.InlineKeyboardButton(('✅' if user.t_Dict[h][2][0] != '' else '') + vHour + ":" + user.t_Dict[h][2][1], callback_data='4' + str(h) + '2'))
    if user.t_Counter >= 8:
        markup.add(types.InlineKeyboardButton('СОХРАНИТЬ', callback_data='5'))
    else:
        markup.add(types.InlineKeyboardButton('Выберите еще минимум ' + str(8 - user.t_Counter) + ' времён', callback_data="0"))
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda callback: callback.data[0] == '1')
def callback2(call): #Выбор игрока команды
    id = call.message.chat.id
    user: User = userRepository.get(id)
    user.e_selectedTeam = int(call.data[1:]) 
    markup = types.InlineKeyboardMarkup(row_width=3)
    for i in range(3):
        if teams[user.e_selectedTeam]['users'][i] != "Не назначено":
            markup.add(types.InlineKeyboardButton(settings["user"][teams[user.e_selectedTeam]['users'][i]]["Nickname"], callback_data='2' + str(i)))
        else:
            markup.add(types.InlineKeyboardButton("Не назначено", callback_data='2' + str(i)))
    bot.edit_message_text(chat_id=id, message_id=call.message.message_id, text='Кого из пользователей вы хотите изменить?', reply_markup=markup)

@bot.callback_query_handler(func=lambda callback: callback.data[0] == '2')
def callback3(call): #замена игрока
    id = call.message.chat.id
    user: User = userRepository.get(id)
    user.e_selectedUser = int(call.data[1:])
    n = len(settings['userlist'])
    markup = types.InlineKeyboardMarkup(row_width=3)
    if n >= 3:
        for i in range(0, (n - n % 3), 3):
            markup.add(types.InlineKeyboardButton(settings["user"][settings['userlist'][i]]["Nickname"], callback_data='3' + str(settings['userlist'][i])), types.InlineKeyboardButton(settings["user"][settings['userlist'][i+1]]["Nickname"], callback_data='3' + str(settings['userlist'][i+1])), types.InlineKeyboardButton(settings["user"][settings['userlist'][i+2]]["Nickname"], callback_data='3' + str(settings['userlist'][i+2])))
    if n % 3 == 2:
        markup.add(types.InlineKeyboardButton(settings["user"][settings['userlist'][n-2]]["Nickname"], callback_data='3' + str(settings['userlist'][n-2])), types.InlineKeyboardButton(settings["user"][settings['userlist'][n-1]]["Nickname"], callback_data='3' + str(settings['userlist'][n-1])), types.InlineKeyboardButton('Не назначено', callback_data='3' + 'Не назначено'))
    elif n % 3 == 1:
        markup.add(types.InlineKeyboardButton(settings['user'][settings['userlist'][n-1]]['Nickname'], callback_data='3' + str(settings['userlist'][n-1])), types.InlineKeyboardButton('Не назначено', callback_data='3' + 'Не назначено'))    
    else:
        markup.add(types.InlineKeyboardButton('Не назначено', callback_data='3' + 'Не назначено'))
    bot.edit_message_text(chat_id=id, message_id=call.message.message_id, text='На кого вы хотите заменить пользователя ' + ("Не назначено" if teams[user.e_selectedTeam]["users"][user.e_selectedUser] == "Не назначено" else settings['user'][teams[user.e_selectedTeam]["users"][user.e_selectedUser]]['Nickname']) + '?', reply_markup=markup)

@bot.callback_query_handler(func=lambda callback: callback.data[0] == '3')
def changeResult(call): #результат замены
    id = call.message.chat.id
    user: User = userRepository.get(id)
    if call.data[1:] != "Не назначено":
        user.e_replacement = int(call.data[1:]) 
    else:
        user.e_replacement = call.data[1:]
    if teams[user.e_selectedTeam]['users'][user.e_selectedUser] == "Не назначено":
        if user.e_replacement == "Не назначено":
            text='Пользователь <b>Не назначено</b> заменен на <b>Не назначено\n \nТекущие команды:</b>'
        else:
            text = 'Пользователь <b>Не назначено</b> заменен на <b>' + settings['user'][user.e_replacement]["Nickname"] + '\n \nТекущие команды:</b>'
            user2: User = userRepository.get(user.e_replacement)
            if user2.team != 0: teams[user2.team]["users"][teams[user2.team]["users"].index(user.e_replacement)] = "Не назначено"
            user2.team = user.e_selectedTeam
            settings['user'][user.e_replacement]["Team"] = user.e_selectedTeam
            teams[user.e_selectedTeam]["users"][user.e_selectedUser] = user.e_replacement
    else:
        if user.e_replacement == "Не назначено":
            text = 'Пользователь <b>' + settings["user"][teams[user.e_selectedTeam]['users'][user.e_selectedUser]]["Nickname"] + '</b> заменен на <b>Не назначено\n \nТекущие команды:</b>'
            user1: User = userRepository.get(teams[user.e_selectedTeam]['users'][user.e_selectedUser])
            user1.team = 0
            settings["user"][teams[user.e_selectedTeam]['users'][user.e_selectedUser]]["Team"] = 0
            teams[user.e_selectedTeam]["users"][user.e_selectedUser] = "Не назначено"
        else:
            text = 'Пользователь <b>' + settings["user"][teams[user.e_selectedTeam]['users'][user.e_selectedUser]]["Nickname"] + '</b> заменен на <b>' + settings['user'][user.e_replacement]["Nickname"] + '\n \nТекущие команды:</b>'
            user1: User = userRepository.get(teams[user.e_selectedTeam]['users'][user.e_selectedUser])
            user1.team = 0
            settings["user"][teams[user.e_selectedTeam]['users'][user.e_selectedUser]]["Team"] = 0
            user2: User = userRepository.get(user.e_replacement)
            if user2.team != 0: teams[user2.team]["users"][teams[user2.team]["users"].index(user.e_replacement)] = "Не назначено"
            user2.team = user.e_selectedTeam
            settings['user'][user.e_replacement]["Team"] = user.e_selectedTeam
            teams[user.e_selectedTeam]["users"][user.e_selectedUser] = user.e_replacement
    saveFile("storage\\settings.yaml", settings)
    saveFile("storage\\teams.yaml", teams)
    for i in range(1, 11):
        text += '\n<b>Команда ' + str(i) + ': </b>' + ("Не назначено" if teams[i]['users'][0] == "Не назначено" else settings["user"][teams[i]['users'][0]]["Nickname"]) + ', ' + ("Не назначено" if teams[i]['users'][1] == "Не назначено" else settings["user"][teams[i]['users'][1]]["Nickname"]) + ', ' + ("Не назначено" if teams[i]['users'][2] == "Не назначено" else settings["user"][teams[i]['users'][2]]["Nickname"])
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML")
    user.editteams()
    user.e_Status = False

@bot.callback_query_handler(func=lambda callback: callback.data[0] == '5')
def saveButton(call): 
    id = call.message.chat.id
    user: User = userRepository.get(id)
    for h in user.t_Dict:
        for time in user.t_Dict[h]:
            if time[0] == '✅':
                settings["user"][id]["TimeForCL"].append(h + ":" + time[1])
                user.times.append(h + ":" + time[1])
    bot.send_message(chat, user.nickname + " - красавчик, потому что ответил боту на вопрос🔥")
    #userLogging(id, call.message.from_user.first_name,"SaveButton")
    saveFile("storage\\settings.yaml", settings)
    text, time = FindCommonTime(user.team, id)
    if time == "None":
        bot.edit_message_text(chat_id=id, message_id=user.t_MessageID, text=text)
    elif time == "NotFound":
        for i in teams[user.team]["users"]:
            if i != "Не назначено":
                user: User = userRepository.get(i)
                bot.edit_message_text(chat_id=i, message_id=user.t_MessageID, text=text)
        bot.send_message(chat, "Команда №" + str(user.team) + " не смогла найти единое время :(")
    else:
        for i in teams[user.team]["users"]:
            if i != "Не назначено":
                user: User = userRepository.get(i)
                
                bot.edit_message_text(chat_id=i, message_id=user.t_MessageID, text=text + visualTime(int(time[:2]), user.timeZone) + ":" + time[3:] + "</b>", parse_mode="HTML") 
        bot.send_message(chat, "Команда №" + str(user.team) + " играет в " + time)      
    
@bot.callback_query_handler(func=lambda callback: callback.data[0] == '6')
def SaveTimeZone(call):
    user: User = userRepository.get(call.message.chat.id)
    user.timeZone = int(call.data[1:])
    settings["user"][call.message.chat.id]["TimeZoneDifference"] = int(call.data[1:])
    saveFile("storage\\settings.yaml", settings)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Ваш часовой пояс успешно изменен!")
check()
botLogging("Program", "Bot successfully started")
bot.infinity_polling(skip_pending=True)

