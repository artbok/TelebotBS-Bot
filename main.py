import telebot
from telebot import types
from User import UserRepository, User
from datetime import datetime
from threading import Timer 
import yaml 
import requests
import json
import random
import math

#Выбор режима запуска

def selectModeOnLaunching():
    global folder
    mode = input("Select launch mode: \nTestMode - Enter | MainMode: MM\nMode: ")
    if mode == "": folder = "storage2\\"; print("You have selected TestMode")
    elif mode == "MM": folder = "storage\\"; print("You have selected MainMode")
    else: print("I don't understand you\n"); selectModeOnLaunching()
selectModeOnLaunching()

#Чтение/Сохранение файлов

def openFile(file):
    with open(folder + file, encoding="utf-8") as file:
        return yaml.safe_load(file)

def saveFile(file, data):
    with open(folder + file, "w", encoding="utf-8") as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True)

lang = openFile("lang.yaml") 
settings = openFile("settings.yaml")
teams = openFile("teams.yaml")
blacklist = openFile("blacklist.yaml")
adminlist = openFile("adminlist.yaml")
token = openFile("tokens.yaml")
message = openFile("messages.yaml")

#Боты

LoggerBot = telebot.TeleBot(token["LoggerBotToken"], skip_pending=True)
bot = telebot.TeleBot(token["BotToken"], skip_pending=True)

#Переменные

adminchat = token["adminchat"]
chat = token["chat"]
CheckList = []
GameIDs = set()
timeTasks = {}
suggestionsToPlay = {}
battleDay = False
userRepository = UserRepository().load(settings) #прогрузка профилей каждого члена клуба

#ФУНКЦИЯ ЛОГИРОВАНИЯ

def botLogging(id, action):
    if id is int and id > 0: 
        if id in settings['userlist']: log = "<b>" + datetime.now().strftime("%H:%M:%S") + " | 🤖 --> 👤 </b>(<code>"+ str(id) + "</code>) | " + action
        else: settings['userlist']: log = "<b>" + datetime.now().strftime("%H:%M:%S") + " | 🤖 --> 👤</b> <code>"+ str(id) + "</code> | " + action
    else: log = "<b>" + datetime.now().strftime("%H:%M:%S") + " | 🤖 --> 👤 </b> <code>" + str(id) + "</code> | " + action
    LoggerBot.send_message(1193654237, log, parse_mode="HTML")


#ФУНКЦИИ ЗАПУСКОВ ВРЕМЕННЫХ СОБЫТИЙ

def dayStart(day):
    loadGames(); teamlists = ""
    for i in teams.keys():
        if teams[i]["users"][0] != teams[i]["users"][1] and teams[i]["users"][0] != teams[i]["users"][2]: 
            teamlists += "\nКоманда №" + str(i) + ": "
            for id in teams[i]["users"]:
                if id != "Не назначено":
                    if day == "Wed" or day == "Fri": CheckList.append([id, 2])
                    else: CheckList.append([id, 3])
                    user: User = userRepository.get(id)
                    user.t_Dict = {**{str(i): [["", "00"], ["", "20"], ["", "40"]] for i in range(17, 24)}, **{str(j): [["", "00"], ["", "20"], ["", "40"]] for j in range(8, 17)}}
                    user.t_MessageID = bot.send_message(id, message['DayStartPersonal'], reply_markup=genMarkup(id)).message_id
                    print(user.t_MessageID)
                    teamlists += "\n   - <a href='tg://user?id=" + str(id) + "'>" + user.nickname + "</a>"
    bot.send_message(chat, message['DayStartChat'].format(teams=teamlists), parse_mode="HTML")
    botLogging("chat", "DayStart_func"); saveFile("settings.yaml", settings); saveFile("teams.yaml", teams)


def checkTable():
    global battleDay
    battleDay = True
    for i in teams.keys():
        for id in teams[i]["users"]:
            if id != "Не назначено":
                user: User = userRepository.get(id)
                user.t_Dict = {}
                if teams[i]["time"] == "Не назначено" and user.t_GameByInvitation is False:
                    user.t_GameByInvitation = True
                    bot.send_message(adminchat, message["NotAnsweredReport"].format(id=id, nickname=user.nickname), parse_mode="HTML")
                    bot.send_message(id, message["NotAnswered"], reply_markup=setKeyboard(id))
                    bot.edit_message_text(chat_id=id, message_id=user.t_MessageID, text=message["DelTable"])
    botLogging("chat", "CheckTable_func"); saveFile("settings.yaml", settings)    


def endOfTheDay():
    global battleDay
    battleDay = False
    raiting = ""
    leaderList = {}
    for i in range(1, 11):
        teams[i]['time'] = 'Не назначено'
        for id in teams[i]["users"]:
            if id != "Не назначено":
                user: User = userRepository.get(id)
                user.times = []
                if settings['user'][id]['WeeklyTrophies'] not in leaderList:
                    leaderList[settings['user'][id]['WeeklyTrophies']] = [settings['user'][id]['Nickname']]
                else:
                    leaderList[settings['user'][id]['WeeklyTrophies']].append(settings['user'][id]['Nickname'])
    saveFile("settings.yaml", settings)   
    saveFile("teams.yaml", teams)   
    sorted(leaderList.keys(), reverse=True)
    position = 1
    for i in sorted(leaderList.keys(), reverse=True):
        raiting += "\n<b>" + str(position) + " место (" + str(i) + " очков)</b>: "
        for j in leaderList[i]:
            raiting += j + ", "
        raiting = raiting[:len(raiting)-2]; position += 1
    botLogging("chat", "EndOfTheDay_func")
    bot.send_message(chat, message["EndOfTheDayChat"].format(points=settings["ClubTrophies"], leaderList=raiting), parse_mode="HTML")

#ОТСЛЕЖИВАНИЕ БОЁВ

def MatchTracking():
    global CheckList
    CheckList2 = []
    for i in CheckList:
        id = i[0]
        url = 'https://api.brawlstars.com/v1/players/%23' + settings["user"][id]["Tag"] + "/battlelog"
        r = requests.get(url, headers={'Authorization': token["AuthKey"]})
        data = json.loads(r.text)
        for game in data["items"]:
            if game["battleTime"] == settings['user'][id]["LastCheckedGame"]: break
            if "type" in game["battle"] and game["battle"]["type"] == "teamRanked" and "trophyChange" in game["battle"]:
                settings['user'][id]['DailyTrophies'] += game["battle"]["trophyChange"]
                settings['user'][id]['WeeklyTrophies'] += game["battle"]["trophyChange"]
                settings['user'][id]['TotalTrophies'] += game["battle"]["trophyChange"]
                settings['ClubTrophies'] += game["battle"]["trophyChange"]
                if game["battleTime"] not in GameIDs:
                    GameIDs.add(game["battleTime"])
                    if game["battle"]["result"] == "victory": text = "<b>Информация об матче</b> \nРезультат: <b>ПОБЕДА (+" + str(game["battle"]["trophyChange"]) + "🏆)</b> \nРежим: <b>" + game["event"]["mode"] + "</b>\nКарта: <b>" + game["event"]["map"] + "</b>" + "\nЗвёздный игрок: <b>" + delHTML(game["battle"]["starPlayer"]["name"]) + "\nСоставы команд: </b>"
                    else: text = "<b>Информация об матче</b> \nРезультат: <b>ПОРАЖЕНИЕ (+" + str(game["battle"]["trophyChange"]) + "🏆)</b> \nРежим: <b>" + game["event"]["mode"] + "</b>\nКарта: <b>" + game["event"]["map"] + "</b>" + "\nЗвёздный игрок: <b>" + delHTML(game["battle"]["starPlayer"]["name"]) + "\nСоставы команд: </b>"
                    for j in range(0, 3): 
                        text += "\n🟦 <b>" + delHTML(game["battle"]["teams"][0][j]["name"]) + "</b> (<code>" + game["battle"]["teams"][0][j]["tag"]  + "</code>), <b>" + lang[game["battle"]["teams"][0][j]["brawler"]["name"]] + "(" + str(game["battle"]["teams"][0][j]["brawler"]["power"]) + " ур.)</b>"
                    for j in range(0, 3):
                        text += "\n🟥 <b>" + delHTML(game["battle"]["teams"][1][j]["name"]) + "</b> (<code>" + game["battle"]["teams"][1][j]["tag"]  + "</code>), <b>" + lang[game["battle"]["teams"][1][j]["brawler"]["name"]] + "(" + str(game["battle"]["teams"][1][j]["brawler"]["power"]) + " ур.)</b>"
                    bot.send_message(chat, text, parse_mode="HTML")
                    botLogging(id, "MatchInfo")
                if i[1] != 1: i[1] -= 1
                else: i = None
        if i != None: CheckList2.append(i)
        settings['user'][id]["LastCheckedGame"] = data["items"][0]["battleTime"]    
        saveFile("settings.yaml", settings)
    CheckList = CheckList2

def loadGames():
    for i in teams.keys():
        for id in teams[i]["users"]:
            if id != "Не назначено":
                url = 'https://api.brawlstars.com/v1/players/%23' + settings["user"][id]["Tag"] + "/battlelog"
                r = requests.get(url, headers={'Authorization': token["AuthKey"]})
                data = json.loads(r.text)
                settings['user'][id]["LastCheckedGame"] = data["items"][0]["battleTime"]    
    saveFile("settings.yaml", settings)

#ЦИКЛИЧНАЯ ГЛАВНАЯ ФУНКЦИЯ

def check():
    Timer(60, check).start()
    date = datetime.now().strftime('%a/%H:%M')
    week = int(datetime.now().strftime('%W')) % 2
    #if (date == 'Wed/08:00' or date == 'Fri/08:00' or date == 'Sun/08:00') and week == 1: dayStart(date[:3])
    if (date == 'Wed/16:50' or date == 'Fri/16:50' or date == 'Sun/16:50') and week == 1: checkTable()
    elif (date == 'Thu/17:05' and week == 1) or (date == 'Sat/17:05' and week == 1) or (date == 'Mon/17:05' and week == 0): endOfTheDay()    
    date = datetime.now().strftime('%H:%M')
    if date in timeTasks:
        for i in timeTasks[date]:
            if i[1] == "Remind":
                for id in teams[i[0]]["users"]:
                    if id != "Не назначено":
                        bot.send_message(id, "<b>Напоминаю, что через 20 минут вы собирались пойти в клубную лигу!</b>", parse_mode="HTML")
                        botLogging(id, "Team " + str(i[0]) + ": AdvanceReminder")
                timeTasks[date].remove(i)
            else:
                suggestToPlay(i[0], None)
                botLogging("Team " + str(i[0]), "GameReminder")
                timeTasks[date].remove(i)
            if len(timeTasks[date]) == 0: del timeTasks[date]
    MatchTracking()

#ПРОВЕРКА ПРАВ

def permission(id):
    if id == 1193654237: return "Owner"
    elif id in adminlist: return "Admin"
    elif id in settings['userlist']: return "Member"
    else: return "User"

#УСТАНОВКА КЛАВИАТУРЫ

def setKeyboard(id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
    role = permission(id)
    if role != "User" and userRepository.get(id).t_GameByInvitation is True: kb.add(types.KeyboardButton("Предложить сыграть КЛ⚔️"))
    if role == "Owner":
        kb.add(types.KeyboardButton("Информация об игроке👤"), types.KeyboardButton("Установить часовую разницу🌍"), types.KeyboardButton("Редактировать команды✏️"), types.KeyboardButton("DayStart_func"), types.KeyboardButton("CheckTable_func"), types.KeyboardButton("EndOfTheDay_func"))
    elif role == "Admin":
        kb.add(types.KeyboardButton("Информация об игроке👤"), types.KeyboardButton("Установить часовую разницу🌍"), types.KeyboardButton("Редактировать команды✏️"))
    elif role == "Member":
        kb.add(types.KeyboardButton("Информация об игроке👤"), types.KeyboardButton("Установить часовую разницу🌍"))
    else:
        if id not in blacklist: kb.add(types.KeyboardButton("Информация об игроке👤"), types.KeyboardButton("Вступить в клуб✉️"))
        else: kb.add(types.KeyboardButton("Информация об игроке👤"))
    return kb

#КОМАНДА ЗАПУСКА БОТА

@bot.message_handler(commands=["start"])
def startCMD(message):
    id = message.chat.id
    #userLogging(id, message.from_user.first_name, message.text)
    if id > 0:
        botLogging(id, "StartCMD")
        bot.send_message(id, "Привет, " + message.from_user.first_name + """. Я бот, помогающий в управлении клубом ABOBA. Я имею следующий функционал:\n - обрабатываю заявки на вступления \n - формирую команды для игры\n - выбираю общее время для игры в КЛ с командой
 - напоминаю о запланированных играх \n - отслеживаю клубные бои\n - веду статистику по клубу\n \nЕсли ты хочешь присоединиться к нам, то нажми на кнопку <b>Вступить в клуб✉️</b> в меню команд. """, parse_mode="HTML", reply_markup=setKeyboard(id))

#ПОЛУЧЕНИЕ ИНФОРМАЦИИ ОБ ИГРОКЕ

def delHTML(text):
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return text

def playerInfo(id):
    user: User = userRepository.get(id)
    user.i_Status = True
    botLogging(id, "WaitingForTheTag")
    bot.send_message(id, "Отправьте ID игрока, которого вы хотите проверить.")

def getUserStats(tag, id):
    user: User = userRepository.get(id)
    url = "https://api.brawlstars.com/v1/players/%23" + tag
    r = requests.get(url, headers={"Authorization": token["AuthKey"]})
    if r.status_code != 200: text = "Игрок под данным ID не найден. Проверьте правильность написания ID и "
    else:
        data = json.loads(r.text)
        if user.j_Status is True: user.j_Nickname = data["name"]
        text = "👤 Ник: <b>" + delHTML(data["name"]) + "</b>\n🎮 ID: <code>" + data["tag"] + "</code>\n🏆 Трофеи: <b>" + str(data["trophies"]) + "</b>\n🏅 Макс. трофеев: <b>" + str(data["highestTrophies"]) + "</b>\n" + "⭐️ Уровень опыта: <b>" + str(data["expLevel"])
        if data["club"]: text += "</b>\n👥 Клуб: <b>" + delHTML(data["club"]["name"])
        else: text += "</b>\n👥 Клуб: <b>Отсутствует"
        text +=  "</b>\n🥇 Побед в соло: <b>" + str(data["soloVictories"]) + "</b>\n🥈 Побед в дуо: <b>" + str(data["duoVictories"]) + "</b>\n🥉 Побед в трио: <b>" + str(data["3vs3Victories"]) + "</b>\n🏋🏿 Бойцы на 11 силе: "
        brawlersAt11Lvl = 0
        brawlersAt10Lvl = 0
        brawlersAt26Rank = 0
        brawlersAt30Rank = 0
        stack = 0
        for i in range(len(data["brawlers"])):
            if data["brawlers"][i]["rank"] >= 30: brawlersAt30Rank += 1
            elif data["brawlers"][i]["rank"] > 25: brawlersAt26Rank += 1
            if data["brawlers"][i]["power"] == 11:
                if stack % 3 == 0: text += "\n        "
                text += "<b>" + lang[data["brawlers"][i]["name"]] + "</b>, "
                brawlersAt11Lvl += 1
                stack += 1
            elif data["brawlers"][i]["power"] == 10: brawlersAt10Lvl += 1
        text = text[:len(text)-2] + "\n🔹 Всего 11-ых уровней: <b>" + str(brawlersAt11Lvl) + "</b>\n🔹 Всего 10-ых уровней: <b>" + str(brawlersAt10Lvl) + "</b>\n🔸 Бойцов на 26-29 ранге: <b>" + str(brawlersAt26Rank) + "</b>\n🔸 Бойцов на 30-35 ранге: <b>" + str(brawlersAt30Rank) + "</b>"
    return text

def sendTag(tag, id):
    user: User = userRepository.get(id)
    if user.j_Status is True:
        user.j_Tag = tag
        text = getUserStats(tag, id)
        if text[0] != "И":
            blacklist.append(id)
            saveFile("blacklist.yaml", blacklist)
            user.j_Text = text 
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(types.InlineKeyboardButton("НАПИСАТЬ " + user.j_Nickname, url="tg://user?id=" + str(id)))
            markup.add(types.InlineKeyboardButton(" ПРИНЯТЬ ", callback_data="+" + str(id)), types.InlineKeyboardButton(" ОТКЛОНИТЬ ", callback_data="-" + str(id)))
            bot.send_message(id, "Твоя заявка на вступление была отправлена на рассмотрение. Я уведомлю тебя когда придёт результат!", reply_markup=setKeyboard(id))
            bot.send_message(adminchat, "<b>Заявка на вступление:</b>\n" + text, parse_mode="HTML", reply_markup=markup)
            user.j_Status = False
            botLogging(id, "Send Application to adminchat")
        else:
            botLogging(id, "Invalid tag")
            bot.send_message(id, text + "отправьте его заново")
    elif user.i_Status is True:
        text = getUserStats(tag, user)
        user.i_Status = False
        if text[0] != "И":
            botLogging(id, "Send info about player")
            bot.send_message(id, "<b>Информация об этом игроке:</b> \n" + text, parse_mode="HTML", reply_markup=setKeyboard(id))
        else:
            bot.send_message(id, text + "повторите команду", reply_markup=setKeyboard(id))
            botLogging(id, "Invalid tag")


#ВСТУПЛЕНИЕ В КЛУБ

def join(id):
    user: User = userRepository.get(id)
    user.i_Status = False
    if id not in blacklist:
        user: User = userRepository.get(id)
        user.j_Status = True
        botLogging(id, "WaitingForTheTag")
        bot.send_message(id, "Для отправки заявки на вступление в наш клуб, необходимо отправить свой ID из игры. Будут оцениваться твои общие кубки, победы в трио, силовая лига, а также силы бойцов.")
    else:
        botLogging(id, "ApplicationHasBeenSentBefore")
        bot.send_message(id, "Вы уже отправляли заявку ранее!", reply_markup=setKeyboard(id))


def acceptApplication(callID, chatID, messageID, name, id): #Кнопки Принять и Отклонить
    user: User = userRepository.get(id)
    bot.answer_callback_query(callID, text="Заявка принята")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("НАПИСАТЬ " + user.j_Nickname, url="tg://user?id=" + str(id)))
    bot.edit_message_text(chat_id=chatID, message_id=messageID, text="<b>Заявка на вступление:</b> \n" + user.j_Text +"\n<b>Принято пользователем " + name + "</b>", parse_mode="HTML", reply_markup=markup)
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton(" Клуб ", url="https://link.brawlstars.com/invite/band/ru?tag=28U82UGGV&token=2rfhzttd")
    btn2 = types.InlineKeyboardButton(" Беседа клуба ", url="https://t.me/+vp-n9-uL01VhZmUy")
    markup.add(btn1, btn2)
    settings["userlist"].append(id)
    settings["user"][id] = {"Tag": user.j_Tag, "Nickname": user.j_Nickname, "Team": 0, "TimeZoneDifference": 0, "DailyTrophies": 0, "WeeklyTrophies": 0, "TotalTrophies": 0, "LastCheckedGame": "Netu"}
    saveFile("settings.yaml", settings)
    botLogging(id, "Application has been accepted")
    userRepository.load(settings)
    user.loadProfile(user.j_Tag, user.j_Nickname, 0, 0)
    bot.send_message(id, "Ваша заявка была <b>принята</b>!", reply_markup=setKeyboard(id), parse_mode="HTML")
    bot.send_message(id, "Добро пожаловать в наш уютный клуб. Для вступления в клуб и в группу клана нажми на кнопки ниже.\n", reply_markup=markup, parse_mode="HTML")
    user.j_Nickname, user.j_Tag, user.j_Text = None, None, None


def denyApplication(callID, chatID, messageID, name, id):
    user: User = userRepository.get(id)
    bot.answer_callback_query(callID, text="Заявка отклонена")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("НАПИСАТЬ " + user.j_Nickname, url="tg://user?id=" + str(id)))
    bot.edit_message_text(chat_id=chatID, message_id=messageID, text="<b>Заявка на вступление:</b> \n" + user.j_Text +"\n<b>Отклонено пользователем " + name + "</b>", parse_mode="HTML", reply_markup=markup)
    bot.send_message(id, "Ваша заявка была <b>отклонена</b>.", parse_mode="HTML")
    botLogging(id, "Application has been declined")

#СМЕНА ЧАСОВОЙ РАЗНИЦЫ

def selectHourDifference(id):
    userRepository.get(id).i_Status = False
    markup = types.InlineKeyboardMarkup(row_width=6)
    differences = [['-14', '-13', '-12', '-11', '-10', '-9'], ['-8', '-7', '-6', '-5', '-4', '-3'], ['-2', '-1', '0', '+1', '+2', '+3'], ['+4', '+5', '+6', '+7', '+8', '+9']]
    for i in differences:
        markup.add(types.InlineKeyboardButton(i[0], callback_data="1"+i[0]), types.InlineKeyboardButton(i[1], callback_data="1"+i[1]), types.InlineKeyboardButton(i[2], callback_data="1"+i[2]), types.InlineKeyboardButton(i[3], callback_data="1"+i[3]), types.InlineKeyboardButton(i[4], callback_data="1"+i[4]), types.InlineKeyboardButton(i[5], callback_data="1"+i[5]))
    bot.send_message(id, "Выберите часовую разницу относительно Москвы(0).", reply_markup=markup)


def saveHourDifference(id, hourDifference, messageID):
    user: User = userRepository.get(id)
    user.timeZone = int(hourDifference)
    settings["user"][id]["TimeZoneDifference"] = user.timeZone
    saveFile("settings.yaml", settings)
    botLogging(id, "SetHourDif: " + hourDifference)
    bot.delete_message(id, messageID)
    bot.send_message(id, "Ваша часовая разница успешно изменена на <b>" + hourDifference + "</b>. У тебя сейчас <b>" + visualTime(int(datetime.now().strftime('%H')), user.timeZone) + datetime.now().strftime(':%M') + "</b> верно?", parse_mode="HTML", reply_markup=setKeyboard(id))

#РЕДАКТИРОВАНИЕ КОМАНД 

def editTeams(id):
    user: User = userRepository.get(id)
    user.i_Status = False
    user.editteams()
    markup = types.InlineKeyboardMarkup(row_width=2)
    text = '<b>Какую команду вы хотите изменить?\n\nТекущие команды:</b>'
    for i in range(1, 11):
        text += '\n<b>Команда ' + str(i) + ': </b>' + ("Не назначено" if teams[i]['users'][0] == "Не назначено" else settings["user"][teams[i]['users'][0]]["Nickname"]) + ', '
        text += ("Не назначено" if teams[i]['users'][1] == "Не назначено" else settings["user"][teams[i]['users'][1]]["Nickname"]) + ', ' + ("Не назначено" if teams[i]['users'][2] == "Не назначено" else settings["user"][teams[i]['users'][2]]["Nickname"])
    for i in range(1, 11, 2):
        markup.add(types.InlineKeyboardButton('Команда ' + str(i), callback_data='5' + str(i)), types.InlineKeyboardButton('Команда ' + str(i+1), callback_data='5' + str(i+1)))
    botLogging(id, "EditTeamsCMD")
    bot.send_message(id, text, reply_markup=markup, parse_mode='HTML')

def choosePlayer(id, selTeam, messageID): #Выбор игрока команды
    user: User = userRepository.get(id)
    user.e_selectedTeam = selTeam
    markup = types.InlineKeyboardMarkup(row_width=3)
    for i in range(3):
        if teams[user.e_selectedTeam]['users'][i] != "Не назначено":
            markup.add(types.InlineKeyboardButton(settings["user"][teams[user.e_selectedTeam]['users'][i]]["Nickname"], callback_data='6' + str(i)))
        else:
            markup.add(types.InlineKeyboardButton("Не назначено", callback_data='6' + str(i)))
    bot.edit_message_text(chat_id=id, message_id=messageID, text='Кого из пользователей вы хотите изменить?', reply_markup=markup)


def userToChange(id, selUser, messageID): #замена игрока
    user: User = userRepository.get(id)
    user.e_selectedUser = selUser
    n = len(settings['userlist'])
    markup = types.InlineKeyboardMarkup(row_width=3)
    if n >= 3:
        for i in range(0, (n - n % 3), 3):
            markup.add(types.InlineKeyboardButton(settings["user"][settings['userlist'][i]]["Nickname"], callback_data='7' + str(settings['userlist'][i])), types.InlineKeyboardButton(settings["user"][settings['userlist'][i+1]]["Nickname"], callback_data='7' + str(settings['userlist'][i+1])), types.InlineKeyboardButton(settings["user"][settings['userlist'][i+2]]["Nickname"], callback_data='7' + str(settings['userlist'][i+2])))
    if n % 3 == 2:
        markup.add(types.InlineKeyboardButton(settings["user"][settings['userlist'][n-2]]["Nickname"], callback_data='7' + str(settings['userlist'][n-2])), types.InlineKeyboardButton(settings["user"][settings['userlist'][n-1]]["Nickname"], callback_data='7' + str(settings['userlist'][n-1])), types.InlineKeyboardButton('Не назначено', callback_data='7' + 'Не назначено'))
    elif n % 3 == 1:
        markup.add(types.InlineKeyboardButton(settings['user'][settings['userlist'][n-1]]['Nickname'], callback_data='7' + str(settings['userlist'][n-1])), types.InlineKeyboardButton('Не назначено', callback_data='7' + 'Не назначено'))    
    else:
        markup.add(types.InlineKeyboardButton('Не назначено', callback_data='7' + 'Не назначено'))
    bot.edit_message_text(chat_id=id, message_id=messageID, text='На кого вы хотите заменить пользователя ' + ("Не назначено" if teams[user.e_selectedTeam]["users"][user.e_selectedUser] == "Не назначено" else settings['user'][teams[user.e_selectedTeam]["users"][user.e_selectedUser]]['Nickname']) + '?', reply_markup=markup)


def changeResult(id, replacement, messageID): #результат замены
    user: User = userRepository.get(id)
    if replacement != "Не назначено": user.e_replacement = int(replacement) 
    else: user.e_replacement = replacement
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
    saveFile("settings.yaml", settings)
    saveFile("teams.yaml", teams)
    for i in range(1, 11):
        text += '\n<b>Команда ' + str(i) + ': </b>' + ("Не назначено" if teams[i]['users'][0] == "Не назначено" else settings["user"][teams[i]['users'][0]]["Nickname"]) + ', ' + ("Не назначено" if teams[i]['users'][1] == "Не назначено" else settings["user"][teams[i]['users'][1]]["Nickname"]) + ', ' + ("Не назначено" if teams[i]['users'][2] == "Не назначено" else settings["user"][teams[i]['users'][2]]["Nickname"])
    bot.edit_message_text(chat_id=id, message_id=messageID, text=text, parse_mode="HTML")
    botLogging(id, "EditTeams: Result: " + text)
    user.editteams()
    user.e_Status = False

#НАСТРОЙКИ ПРОФИЛЯ
# def userSettings(id):
#     markup = types.InlineKeyboardMarkup(row_width=4)
#     "<b>НАСТРОЙКА ВАШЕГО ПРОФИЛЯ:<b>"
#     markup.add(types.InlineKeyboardButton("КАЖДЫЙ МАТЧ" + "ВКЛ", callback_data='a')
#ВЫБОР ВРЕМЁН

def visualTime(hour, td):
    hour += td
    if hour > 23: hour -= 24 
    if hour < 0: hour += 24
    if len(str(hour)) == 1: return "0" + str(hour)
    return str(hour)


def genMarkup(id):
    user: User = userRepository.get(id)
    markup = types.InlineKeyboardMarkup(row_width=4)
    n = 0
    for h in user.t_Dict.keys():
        vHour = visualTime(int(h), user.timeZone)
        if len(user.t_Dict[h]) == 1: markup.add(types.InlineKeyboardButton(('✅' if user.t_Dict[h][0][0] != '' else '') + vHour + ":" + user.t_Dict[h][0][1], callback_data='3' + str(h) + "0"))
        elif len(user.t_Dict[h]) == 2: markup.add(types.InlineKeyboardButton(vHour, callback_data='2' + str(h)), types.InlineKeyboardButton(('✅' if user.t_Dict[h][0][0] != '' else '') + vHour + ":" + user.t_Dict[h][0][1], callback_data='3' + str(h) + "0"), types.InlineKeyboardButton(('✅' if user.t_Dict[h][1][0] != '' else '') + vHour + ":" + user.t_Dict[h][1][1], callback_data='3' + str(h) + "1"))
        else: markup.add(types.InlineKeyboardButton(vHour, callback_data='2' + str(h)), types.InlineKeyboardButton(('✅' if user.t_Dict[h][0][0] != '' else '') + vHour + ":" + user.t_Dict[h][0][1], callback_data='3' + str(h) + "0"), types.InlineKeyboardButton(('✅' if user.t_Dict[h][1][0] != '' else '') + vHour + ":" + user.t_Dict[h][1][1], callback_data='3' + str(h) + "1"), types.InlineKeyboardButton(('✅' if user.t_Dict[h][2][0] != '' else '') + vHour + ":" + user.t_Dict[h][2][1], callback_data='3' + str(h) + "2"))
        n += len(user.t_Dict[h])
    markup.add(types.InlineKeyboardButton('Нет свободных времён', callback_data='8'))
    # flag = True
    # for i in teams[user.team]["users"]:
    #     if i != "Не назначено" and i != id: 
    #         user2: User = userRepository.get(i)
    #         if user2.t_SelectedTimes == set(): flag = False 
    # if flag is False:
    if user.t_Counter >= math.ceil(n / 6): markup.add(types.InlineKeyboardButton('СОХРАНИТЬ', callback_data='4'))
    else: markup.add(types.InlineKeyboardButton('Выберите еще минимум ' + str(math.ceil(n / 6) - user.t_Counter), callback_data="0"))
    return markup


def selectRowClick(id, h, messageID):
    user: User = userRepository.get(id)
    flag = False
    for i in user.t_Dict[h]:
        if i[0] == '✅': 
            flag = True
            break
    if flag is True:
        for i in range(len(user.t_Dict[h])):
            if user.t_Dict[h][i][0] == '✅':
                user.t_Dict[h][i][0] = ''
                user.t_Counter -= 1
    else:
        for i in range(len(user.t_Dict[h])):
            if user.t_Dict[h][i][0] == '':
                user.t_Dict[h][i][0] = '✅' 
                user.t_Counter += 1   
    bot.edit_message_reply_markup(chat_id=id, message_id=messageID, reply_markup=genMarkup(id))       


def selectTimeClick(id, h, m, messageID): 
    user: User = userRepository.get(id)
    if user.t_Dict[h][m][0] == '':
        user.t_Dict[h][m][0] = '✅'
        user.t_Counter += 1
    else:
        user.t_Dict[h][m][0] = ''
        user.t_Counter -= 1    
    bot.edit_message_reply_markup(chat_id=id, message_id=messageID, reply_markup=genMarkup(id))


def findCommonTime(id, team):
    everyoneAnswered = True
    playersTimes = []
    for i in teams[team]["users"]:
        if i != "Не назначено":
            user: User = userRepository.get(i)
            if len(user.t_SelectedTimes) != 0: playersTimes.append(user.t_SelectedTimes)
            elif i != id: everyoneAnswered = False
    if len(playersTimes) == 1: time = sorted(list(playersTimes[0]))
    elif len(playersTimes) == 2: time = sorted(list(playersTimes[0] & playersTimes[1]))
    else: time = sorted(list(playersTimes[0] & playersTimes[1] & playersTimes[2]))
    if everyoneAnswered is False and time != []:
        table = {}
        for t in time:
            h, m = t[:2], t[3:]
            if int(h) > 16:
                if h not in table: table[h] = [["", m]]
                else: table[h].append(["", m])
        for t in time:
            h, m = t[:2], t[3:]
            if int(h) < 17:
                if h not in table: table[h] = [["", m]]
                else: table[h].append(["", m])
        for i in teams[team]["users"]:
            if i != "Не назначено":
                user: User = userRepository.get(i)
                print(i, user.t_Counter, user.t_Dict, table)
                if user.t_Counter == 0 and i != id and user.t_Dict != table:
                    user.t_Dict = table
                    bot.edit_message_text(chat_id=i, message_id=user.t_MessageID, text="Скоро начнётся день клубной лиги! Тебе нужно выбрать все свободные времена из представленных ниже. После выбора не забудь нажать на кнопку сохранить!", reply_markup=genMarkup(i))
        return
    if everyoneAnswered is False and time == []:
        for i in teams[team]["users"]:
            user: User = userRepository.get(i)
            if len(user.t_SelectedTimes) == 0: bot.edit_message_text(chat_id=i, message_id=user.t_MessageID, text="К сожалению твои тиммейты не смогли найти общего времени, а значит от твоего ответа ничего не зависит.")
    if time != []:
        time = random.choice(time)
        teams[team]["time"] = time
        if time not in timeTasks: timeTasks[time] = [[team, "Game"]]
        else: timeTasks[time].append([team, "Game"])
        h, m = time[:2], time[3:]
        if m == "00":
            m = "40"
            h = str(int(h)-1)
            if len(h) == 1: h = "0" + h
        elif m == "20": m = "00"
        else: m = "20"  
        if h+":"+m not in timeTasks: timeTasks[h+":"+m] = [[team, "Remind"]]
        else: timeTasks[h+":"+m].append([team, "Remind"])
        saveFile("teams.yaml", teams)
        for i in teams[team]["users"]:
            if i != "Не назначено":
                user = userRepository.get(i)
                bot.send_message(i, "Все пользователи выбрали свободные времена! Общим временем оказалось <b>" + visualTime(int(time[:2]), user.timeZone) + ":" + time[3:] + "</b>", parse_mode="HTML")
        botLogging(id, "FCT_func: Team" + str(team) + ": " + time)
    else:
        botLogging(id, "FCT_func: Team" + str(team) + ": TimeNotFound")
        for i in teams[team]["users"]:
            if i != "Не назначено":
                user: User = userRepository.get(i)
                user.t_GameByInvitation = True
                bot.send_message(i, "Все пользователи выбрали свободные времена, но к сожалению общего времени не нашлось.")
                bot.send_message(i, "Команда играет по приглашениям. Когда будешь свободен для игры в клановую лигу нажми на кнопку <b>Предложить сыграть КЛ⚔️</b>.", parse_mode="HTML", reply_markup=setKeyboard(i))


def saveButton(id): 
    user: User = userRepository.get(id)
    bot.edit_message_text(chat_id=id, message_id=user.t_MessageID, text='Спасибо что выбрали времена. Теперь ожидайте пока ваши тиммейты также ответят на этот вопрос.')
    for h in user.t_Dict:
        for t in range(len(user.t_Dict[h])):
            if user.t_Dict[h][t][0] == '✅': user.t_SelectedTimes.add(h+":"+user.t_Dict[h][t][1])
    botLogging(id, "SaveTable_Button: " + str(sorted(list(user.t_SelectedTimes))))
    saveFile("settings.yaml", settings)
    findCommonTime(id, user.team)


def noFreeTimeButton(id):
    user: User = userRepository.get(id)
    for i in teams[user.team]["users"]:
        if i != "Не назначено":
            user2: User = userRepository.get(i)
            user2.t_GameByInvitation = True
            if user2.t_SelectedTimes == set(): bot.delete_message(i, user2.t_MessageID)
            if i != id: bot.send_message(i, "<b>" + user.nickname + "</b> не нашёл свободных времён, поэтому твоя команда играет по приглашениям. Когда будешь свободен для игры в клановую лигу нажми на кнопку <b>Предложить сыграть КЛ⚔️</b>.", parse_mode="HTML", reply_markup=setKeyboard(i))
            else: bot.send_message(i, "Команда играет по приглашениям. Когда будешь свободен для игры в клановую лигу нажми на кнопку <b>Предложить сыграть КЛ⚔️</b>. ", parse_mode="HTML", reply_markup=setKeyboard(i))

def autoDelSuggestMessage(team):
    for i in suggestionsToPlay[team]["notAnswered"]:
        bot.edit_message_text(chat_id=i, message_id=suggestionsToPlay[team]["messageIDs"][i], text="<b>" + settings["user"][suggestionsToPlay[team]["owner"]]["Nickname"] + "</b> предлагал сыграть в клубную лигу.\n \n <b>Приглашение проигнорировано</b>", parse_mode="HTML")
    for i in teams[team]["users"]:
        if i != "Не назначено":
            if i in suggestionsToPlay[team]["notAnswered"]: bot.send_message(i, "Вы проигноривали приглашение, поэтому оно было автоматически отменено.")
            elif i != suggestionsToPlay[team]["owner"]: bot.send_message(i, "<b>" + settings["user"][suggestionsToPlay[team]["notAnswered"][0]]["Nickname"] + "</b> проигнорировал приглашение, поэтому оно было автоматически отменено.", parse_mode="HTML")
    if len(suggestionsToPlay[team]["notAnswered"]) == 1: bot.send_message(suggestionsToPlay[team]["owner"], "<b>" + settings["user"][suggestionsToPlay[team]["notAnswered"][0]]["Nickname"] + "</b> проигнорировал твоё приглашение, поэтому оно было автоматически отменено.", parse_mode="HTML")
    else: bot.send_message(suggestionsToPlay[team]["owner"], "<b>" + settings["user"][suggestionsToPlay[team]["notAnswered"][0]]["Nickname"] + "</b> и <b>" + settings["user"][suggestionsToPlay[team]["notAnswered"][1]]["Nickname"] + "</b> проигнорировали твоё приглашение, поэтому оно было автоматически отменено.", parse_mode="HTML")

def suggestToPlay(team, owner):
    if battleDay is True:
        if team not in suggestionsToPlay:
            suggestionsToPlay[team] = {"owner": owner, "messageIDs": {}, "notAnswered": [], "timer": Timer(900, autoDelSuggestMessage, [team])}
            suggestionsToPlay[team]["timer"].start()
            if owner is not None: bot.send_message(owner, "Приглашение отправлено твоим тиммейтам. Если через 15 минут, кто-то из них не ответит, приглашение будет автоматически отменено.")
        else:
            bot.send_message(owner, "Приглашение уже создано!")
            return
        if owner is None:
            for i in teams[team]["users"]:
                if i != "Не назначено": 
                    suggestionsToPlay[team]["messageIDs"][i] = bot.send_message(i, "Наступило время сыграть в клубную лигу! Как только все твои тиммейты будут готовы сыграть, заходи в игру и ожидай команду.", parse_mode="HTML", reply_markup=types.InlineKeyboardMarkup(row_width=2).add(types.InlineKeyboardButton("Могу сыграть", callback_data="9AcceptInvite"), types.InlineKeyboardButton("Не могу сыграть", callback_data="9DenyInvite"))).message_id
                    suggestionsToPlay[team]["notAnswered"].append(i)    
        else:
            user: User = userRepository.get(owner)
            for i in teams[team]["users"]:
                if i != "Не назначено" and i != owner: 
                    suggestionsToPlay[team]["messageIDs"][i] = bot.send_message(i, "<b>" + user.nickname + "</b> предлагает сейчас сыграть в клубную лигу.", parse_mode="HTML", reply_markup=types.InlineKeyboardMarkup(row_width=2).add(types.InlineKeyboardButton("Могу сыграть", callback_data="9AcceptInvite"), types.InlineKeyboardButton("Не могу сыграть", callback_data="9DenyInvite"))).message_id
                    suggestionsToPlay[user.team]["notAnswered"].append(i)
    else:
        bot.send_message(owner, "Приглашения можно отправлять только в течение игрового дня!")

def clickToSuggest(id, answer):
    user: User = userRepository.get(id)
    suggestionsToPlay[user.team]["notAnswered"].remove(id)
    if answer == "AcceptInvite":
        if suggestionsToPlay[user.team]["owner"] is not None: bot.edit_message_text(chat_id=id, message_id=suggestionsToPlay[user.team]["messageIDs"][id], text="<b>" + settings["user"][suggestionsToPlay[user.team]["owner"]]["Nickname"] + "</b> предлагает сейчас сыграть в клубную лигу.\n \n <b>Приглашение принято</b>", parse_mode="HTML")
        else: bot.edit_message_text(chat_id=id, message_id=suggestionsToPlay[user.team]["messageIDs"][id], text="Наступило время сыграть в клубную лигу! Как только все твои тиммейты будут готовы сыграть, заходи в игру и ожидай команду.\n \n <b>Приглашение принято</b>", parse_mode="HTML")
        bot.send_message(id, "Ожидай, пока твои тиммейты также ответят на этот вопрос.")
        for i in teams[user.team]["users"]:
            if i != "Не назначено":
                if i != id: 
                    bot.send_message(i, "<b>" + user.nickname + "</b> может сыграть", parse_mode="HTML")
        if suggestionsToPlay[user.team]["notAnswered"] == []: 
            for j in teams[user.team]["users"]:
                if j != "Не назначено":
                    user: User = userRepository.get(j)
                    user.t_GameByInvitation = False
                    bot.send_message(j, "Вся команда готова сыграть! Заходите в игру и уничтожайте своих противников🔥", reply_markup=setKeyboard(j))
            suggestionsToPlay[user.team]["timer"].cancel()
            del suggestionsToPlay[user.team]
    else:
        if suggestionsToPlay[user.team]["owner"] is not None: bot.edit_message_text(chat_id=id, message_id=suggestionsToPlay[user.team]["messageIDs"][id], text="<b>" + settings["user"][suggestionsToPlay[user.team]["owner"]]["Nickname"] + "</b> предлагает сейчас сыграть в клубную лигу.\n \n <b>Приглашение отклонено</b>", parse_mode="HTML")
        else: bot.edit_message_text(chat_id=id, message_id=suggestionsToPlay[user.team]["messageIDs"][id], text="Наступило время сыграть в клубную лигу! Как только все твои тиммейты будут готовы сыграть, заходи в игру и ожидай команду.\n \n <b>Приглашение отклонено</b>", parse_mode="HTML")
        for i in teams[user.team]["users"]:
            if i != "Не назначено":
                if i != id: bot.send_message(i, "<b>" + user.nickname + "</b> не может сыграть", parse_mode="HTML") 
                bot.send_message(i, "Приглашение отменено. Попробуйте предложить сыграть позже.", reply_markup=setKeyboard(i))
                if suggestionsToPlay[user.team]["owner"] is not None and i in suggestionsToPlay[user.team]["notAnswered"]: bot.edit_message_text(chat_id=i, message_id=suggestionsToPlay[user.team]["messageIDs"][i], text="<b>" + settings["user"][suggestionsToPlay[user.team]["owner"]]["Nickname"] + "</b> предлагал сыграть в клубную лигу.\n \n <b>Приглашение отменено</b>", parse_mode="HTML")
                else: bot.edit_message_text(chat_id=i, message_id=suggestionsToPlay[user.team]["messageIDs"][i], text="Наступило время сыграть в клубную лигу! Как только все твои тиммейты будут готовы сыграть, заходи в игру и ожидай команду.\n \n <b>Приглашение отменено</b>", parse_mode="HTML")
                suggestionsToPlay[user.team]["timer"].cancel()
        del suggestionsToPlay[user.team]

@bot.message_handler(commands=["deltable"])        
def delTable(message):
    for i in teams.keys():
        for j in teams[i]['users']:
            if j != "Не назначено": 
                user: User = userRepository.get(j)
                bot.delete_message(j, user.t_MessageID)   
                     
#ХЭНДЛЕРЫ сообщений и кликов

@bot.message_handler(content_types=["text"])
def handleText(message):
    id = message.chat.id
    role = permission(id)
    user: User = userRepository.get(id)
    text = message.text
    if id > 0:
        LoggerBot.send_message(1193654237,  "<a href='tg://user?id=" + str(id) + "'>👤 " + str(id) + "</a> | " + datetime.now().strftime("%H:%M:%S") + " | " +  text, parse_mode="HTML")
        if user.i_Status is False and text == "Информация об игроке👤": playerInfo(id) 
        elif user.j_Status is False and text == "Вступить в клуб✉️" and role == "User": join(id) 
        elif text == "Редактировать команды✏️" and (role == "Admin" or role == "Owner"): editTeams(id)
        elif text == "Установить часовую разницу🌍" and role != "User": selectHourDifference(id)
        elif text == "Предложить сыграть КЛ⚔️" and role != "User": suggestToPlay(user.team, id)
        elif text == "DayStart_func" and role == "Owner": dayStart("Wed")
        elif text == "CheckTable_func" and role == "Owner": checkTable()
        elif text == "EndOfTheDay_func" and role == "Owner": endOfTheDay()
        elif user.i_Status is True or user.j_Status is True: sendTag((text.upper()[1:] if text[0] == "#" else text.upper()), id)

@bot.callback_query_handler(func=lambda call: True)
def handleCallbacks(call):
    calltype = call.data[0]
    data = call.data[1:]
    if calltype == "+": acceptApplication(call.id, call.message.chat.id, call.message.message_id, call.from_user.first_name, int(data))
    elif calltype == "-": denyApplication(call.id, call.message.chat.id, call.message.message_id, call.from_user.first_name, int(data))
    elif calltype == "1": saveHourDifference(call.message.chat.id, data, call.message.message_id)
    elif calltype == "2": selectRowClick(call.message.chat.id, data, call.message.message_id)
    elif calltype == "3": selectTimeClick(call.message.chat.id, data[:2], int(data[2:]), call.message.message_id)
    elif calltype == "4": saveButton(call.message.chat.id)
    elif calltype == "5": choosePlayer(call.message.chat.id, int(data), call.message.message_id)
    elif calltype == "6": userToChange(call.message.chat.id, int(data), call.message.message_id)
    elif calltype == "7": changeResult(call.message.chat.id, data, call.message.message_id)
    elif calltype == "8": noFreeTimeButton(call.message.chat.id)
    elif calltype == "9": clickToSuggest(call.message.chat.id, data)
check()
botLogging("Program", "Bot launched in " + ("<b>TestMode</b>"if len(folder) == 9 else "<b>MainMode</b>"))
bot.infinity_polling(skip_pending=True)
