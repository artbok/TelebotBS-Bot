from aiogram import Bot, Dispatcher, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, Message, CallbackQuery, ContentType
import requests, json, os, emoji, yaml, asyncio
from math import ceil
import multiprocessing as mp
from datetime import datetime, timedelta
from dataRepository import *


def openFile(file):
    with open(file, encoding = "utf-8") as file:
        return yaml.safe_load(file)

folder = (os.getenv("mode") if os.getenv("mode") else "mainMode") + "//"


lang = openFile("lang.yaml") 
token = openFile(folder + "tokens.yaml")


bot = Bot(token["botToken"])
loggerBot = Bot(token["loggerBotToken"])
dp = Dispatcher(bot)

#Логирование

async def log(action, name, id, data, team, rep, fromBot):
    tags = []
    if fromBot:
        if id:
            log = f"💬 <b>ABOBUS → {name}</b>(<code>{id}</code>)\n"
            tags.append(f"User{id}")
        else:
            log = f"💬 <b>ABOBUS → {name}</b>\n"
            tags.append(name)
    else:
        if id:
            log = f"💬 <b>{name}(<code>{id}</code>) → ABOBUS</b>\n"
            tags.append(f"User{id}")
        else:
            log = f"💬 <b><code>{name}</code> → ABOBUS</b>\n"
            tags.append(f"User{name}")
    log += f"🕒 Time: <b>{datetime.now().strftime('%H:%M:%S')}</b>\n💭 Action: <b>{action}</b>\n"
    if data:
        log += f"💾 Data: <b>{data}</b>\n"
    if team:
        tags.append(f"Team{team}")
    if rep != None:
        log += f"👁‍🗨 Reputation: <b>{rep}</b>\n"
    log += f"#{' | #'.join(tags)}"
    await loggerBot.send_message(token["logChat"], log, "HTML")


async def userLog(action, name, id = None, data = None, team = None, rep = None):
    await log(action, name, id, data, team, rep, False)


async def botLog(action, name, id = None, data = None, team = None, rep = None):
    await log(action, name, id, data, team, rep, True)

#Отдельные функции

async def makeRequest(url) -> dict:
    flag = False
    while not flag:
        try:
            r = requests.get(url, headers = {"Authorization": token["authKey"]})
            flag = True
        except Exception as e:
            print(f"Error while request (makeRequest func)\nURL: {url}\n{e}")
            await asyncio.sleep(0.5)
    if r.status_code == 200: 
        return json.loads(r.text)
    return r.status_code


async def urlOfTheIcon(icon) -> str:
    flag = False
    url = "https://brawlace.com/assets/images/brawlstars/icons-players/{0}.png"
    while not flag:
        try:
            r = requests.get(url.format(icon))
            flag = True
        except Exception as e:
            print("Error while request (urlOfTheIcon func)", e)
            await asyncio.sleep(0.5)
    if r.status_code == 200:
        return url.format(icon)
    return url.format(28000000)


def isCorrectId(id):
    return bool(User.get_or_none(id))


def replaceHTML(text) -> str: 
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def tagProcessing(text: str) -> str:
    text = text.upper().replace("O", "0").replace("#", "")
    if text.find("HTTPS://") >= 0:
        if text.count("=") == 2 and text.count("&") == 1: 
            return text[(text.find("=") + 1):text.find("&")]
        return False
    return text


def formatedHourDifference(hourDifference):
    if hourDifference > 0: 
        return f"+{hourDifference}"
    else:
        return hourDifference
    

def calculateTime(time, dif) -> str:
    h, m = map(int, time.split(":"))
    t = str(timedelta(hours = h, minutes = m) + timedelta(minutes = dif))
    if len(t) == 7: 
        t = "0" + t
    i = t.find(":")
    return t[i-2:i+3].replace(" ", "0")


def visualHour(hour, td) -> str:
    hour += td
    if hour > 23: hour -= 24 
    if hour < 0: hour += 24
    return '{:02}'.format(hour)


def calculateDayCL() -> tuple[str, int]:
    match int(datetime.now().strftime("%w")):
        case 3: day = "первый"
        case 5: day = "второй"
        case 0: day = "третий"
        case _: day = "тестовый"
    return day


def canUseOfferToPlayCL(user: User) -> bool:
    tUser = getTrackedUser(user.id)
    daystatus = getValue("dayStatus")
    if tUser.n != 0 and user.team != 0 and daystatus:
        for member in getTeamMembers(user.team):
            if member.t_MessageId:
                return False
        return True
    return False


def setKeyboard(user: User) -> ReplyKeyboardMarkup:
    user.status = None; user.save()
    kb = ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True, row_width = 2, is_persistent = True, 
                             input_field_placeholder = lang["ph"]["selectCommand"])
    btns = []
    btns.append(KeyboardButton(lang["btn"]["playerInfo"]))
    if user.rightsLevel <= 3:
        btns.append(KeyboardButton(lang["btn"]["help"]))
    if not isItBlacklisted(user.id) and user.rightsLevel == 1:
        btns.append(KeyboardButton(lang["btn"]["joinTheClub"]))
    if user.rightsLevel >= 3:
        btns.append(KeyboardButton(lang["btn"]["setHourDifference"]))
        btns.append(KeyboardButton(lang["btn"]["teamChat"]))
        if canUseOfferToPlayCL(user):
            btns.append(KeyboardButton(lang["btn"]["offerToPlayCL"]))
        if user.chatСhannel:
            btns.append(KeyboardButton(lang["btn"]["privateChat"]))
    if user.rightsLevel >= 4:
        btns.append(KeyboardButton(lang["btn"]["makeAnAnnouncement"]))
        btns.append(KeyboardButton(lang["btn"]["enterChat"]))
        if not getValue("dayStatus"):
            btns.append(KeyboardButton(lang["btn"]["editTeams"]))
    if len(btns) % 2 == 1:
        kb.add(btns[0])
        btns.pop(0)
    for i in range(0, len(btns), 2):
        kb.add(btns[i], btns[i+1])
    return kb


class PlayerStats:
    def __init__(self, data, title):
        self.hisAccount, self.nickname, self.tag = True, replaceHTML(data["name"]), data["tag"]
        self.icon = data["icon"]["id"]
        self.club = lang["playerInfo"]["notInAClub"] if "name" not in data["club"] else replaceHTML(data["club"]["name"])
        self.trophies = data["trophies"]
        self.trophiesRate = round((self.trophies / (len(lang['brawler']) * 750)) * 50, 1)
        self.highestTrophies = data["highestTrophies"]
        self.soloVictories, self.duoVictories, self.trioVictories = data["soloVictories"], data["duoVictories"], data["3vs3Victories"]
        self.victoriesRate = round(data["3vs3Victories"] / 1800 + (data["soloVictories"] + data["duoVictories"]) / 500, 1)
        self.at35Rank, self.at30Rank, self.at25Rank = 0, 0, 0
        self.at11Lvl, self.at10Lvl = 0, 0
        self.gadgets, self.starPowers, self.gears = 0, 0, 0
        self.upTo300, self.upTo500, self.upTo650, self.upTo800, self.upTo1000, self.over1000 = 0, 0, 0, 0, 0, 0
        self.brawlerTrophies = []
        self.averageTrophies = self.trophies // len(lang["brawler"]) 
        for brawler in data["brawlers"]:
            rank, power, trophies = brawler["rank"], brawler["power"], brawler["trophies"]
            if rank == 35: self.at35Rank += 1
            elif rank >= 30: self.at30Rank += 1
            elif rank >= 25: self.at25Rank += 1

            if power == 11: self.at11Lvl += 1
            elif power == 10: self.at10Lvl += 1

            self.gadgets += len(brawler["gadgets"])
            self.starPowers += len(brawler["starPowers"])
            self.gears += len(brawler["gears"])
            if trophies >= 1000: self.over1000 += 1
            elif trophies >= 800: self.upTo1000 += 1
            elif trophies >= 650: self.upTo800 += 1
            elif trophies >= 500: self.upTo650 += 1
            elif trophies >= 300: self.upTo500 += 1
            else: self.upTo300 += 1
            self.brawlerTrophies.append(trophies)
        self.brawlerTrophies.sort(reverse = True)
        self.trophiesLost, self.reward = 0, 0
        self.ranksRate = round(self.at25Rank * 0.2 + self.at30Rank * 0.6 + self.at35Rank, 1)
        self.pumpingRate = round(self.at11Lvl * 0.15 + self.at10Lvl * 0.07 + self.gadgets * 0.015 + self.starPowers * 0.03 + self.gears * 0.02, 1)
        for i in range(10):
            t = self.brawlerTrophies[i]
            if i <= len(self.brawlerTrophies) and t > 500:
                if t < 525: 
                    self.trophiesLost += t - 500
                    self.reward += 4
                elif t < 1000:
                    self.trophiesLost += t % 25 + 1
                    self.reward += 2 + 2 * ceil((t - 499) / 25)
                elif t >= 1500:
                    self.trophiesLost = t - 1499
                    self.reward = 64
                else:
                    self.trophiesLost += t % 50 + 1
                    self.reward += 42 + 2 * ceil((t - 999) / 50)
            else: break
        self.hours = int(3 * (data["soloVictories"] * 4 + data["duoVictories"] * 3 + data["3vs3Victories"] * 2) // 60)
        self.rate = round(self.trophiesRate + self.victoriesRate + self.pumpingRate + self.ranksRate, 1)
        self.text = title + lang["playerStats"].format(
            self.nickname, self.tag, self.club, self.trophies, self.trophiesRate, self.highestTrophies, self.victoriesRate, self.soloVictories, self.duoVictories, self.trioVictories,
            len(self.brawlerTrophies), len(lang["brawler"]), self.pumpingRate, self.at11Lvl, self.at10Lvl, self.gadgets, len(lang["brawler"]) * 2, self.starPowers, self.gears,
            self.upTo300, self.upTo500, self.upTo650, self.upTo800, self.upTo1000, self.over1000, self.averageTrophies, self.ranksRate, self.at25Rank, self.at30Rank, self.at35Rank,
            self.trophies - self.trophiesLost, self.trophiesLost, self.reward, self.hours, self.rate
            )
        

async def guestRegistration(id, text, messageId):
    await bot.send_message(id, lang["lookingForATag"], "HTML", reply_to_message_id = messageId)
    await bot.send_chat_action(id, "typing")
    tag = tagProcessing(text)
    if tag:
        data = await makeRequest(f"https://api.brawlstars.com/v1/players/%23{tag}")
        if isinstance(data, dict):
            stats = PlayerStats(data, lang["playerInfo"]["result1"])
            user: User = User.create(id = id, rightsLevel = 1, nickname = replaceHTML(stats.nickname), tag = tag); user.save()
            (TrackedUser.create(id = id, tag = tag)).save()
            await bot.send_message(id, lang["guestRegistration"]["success"].format(stats.nickname), "HTML")
            url = await urlOfTheIcon(stats.icon)
            await bot.send_photo(user.id, url, stats.text, "HTML", reply_markup = setKeyboard(user))
            await userLog("guestRegistration: success", user.nickname, user.id, f"tag: {tag}")
        elif data == 503: 
            await bot.send_message(id, lang["guestRegistration"]["gameOnMaintenance"], "HTML")
            await userLog("guestRegistration: game on maintenance", id, data = text)
        else:
            await bot.send_message(id, lang["guestRegistration"]["playerNotFound"], "HTML")
            await userLog("guestRegistration: player not found", id, data = text)
    else: 
        await bot.send_message(id, lang["guestRegistration"]["incorrectURL"], "HTML")
        await userLog("guestRegistration: incorrect url", id, data = text)


async def playerInfo(user: User): 
    user.status = "playerInfo"; user.save()
    kb = ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True, row_width = 2, is_persistent = True, 
                                    input_field_placeholder = lang["ph"]["playerInfo"])
    kb.add(lang["btn"]["userTag"].format(user.tag), lang["btn"]["cancel"])
    await bot.send_message(user.id, lang["playerInfo"]["waitingForATag"], "HTML", reply_markup = kb)
    await userLog("player info", user.nickname, user.id) 


async def sendStats(user, text, messageId):
    user.status = None; user.save()
    await bot.send_message(user.id, lang["lookingForATag"], "HTML", reply_to_message_id = messageId)
    tag = tagProcessing(text)
    if tag:
        data = await makeRequest(f"https://api.brawlstars.com/v1/players/%23{tag}")
        if isinstance(data, dict):
            title = lang["playerInfo"]["result1"] if user.tag == tag else lang["playerInfo"]["result2"]
            stats = PlayerStats(data, title)
            url = await urlOfTheIcon(stats.icon)
            await bot.send_photo(user.id, url, stats.text, parse_mode = "HTML", reply_markup = setKeyboard(user))
            await botLog("sendStats: success", user.nickname, user.id, text)
        elif data == 503: 
            await bot.send_message(user.id, lang["playerInfo"]["gameOnMaintenance"], "HTML", reply_markup = setKeyboard(user))
            await botLog("sendStats: game on maintenance", user.nickname, user.id, text)
        else: 
            await bot.send_message(user.id, lang["playerInfo"]["playerNotFound"], "HTML", reply_markup = setKeyboard(user))
            await botLog("sendStats: invalid tag", user.nickname, user.id, text)
    else:
        await bot.send_message(user.id, lang["playerInfo"]["incorectURL"], "HTML", reply_markup = setKeyboard(user))
        await botLog("sendStats: incorrect url", user.nickname, user.id, text)


# async def clubInfoCMD(user: User): 
#     if isinstance(user, User):
#         user.status = "clubInfo"; user.save()
#         # kb = ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True, row_width = 2, is_persistent = True, 
#         #                              input_field_placeholder = lang["ph"]["playerInfo"])
#         # kb.add(lang["btn"]["userTag"].format(user.tag), lang["btn"]["cancel"])
#         await bot.send_message(user.id, lang["clubInfo"]["waitingForATag"], "HTML")
#         #await botLogging(user, "clubInfoCMD")


async def getClubStats(tag):
    url = "https://api.brawlstars.com/v1/clubs/%23" + tag
    data = await makeRequest(url)
    members = ""
    if isinstance(data, dict):
        for player in data["members"]:
            if player["role"] == "president": role = "(👑)"
            elif player["role"] == "vicePresident": role = "(🔱)"
            elif player["role"] == "senior": role = "(🎖)"
            else: role = "(🎗)"
            members += lang["membersStats"].format(role, stats.nickname, stats.tag, round(stats.trophies / 1000, 1), stats.rate)
        return lang["clubStats"].format(data["name"], data["tag"][1:], data["description"], data["trophies"], len(data["members"]), members)
    
#Команда join

async def joinTheClub(user: User):
    if isItBlacklisted(user.id) or user.rightsLevel != 1:
        await bot.send_message(user.id, lang["join"]["applicationWasSentBefore"], reply_markup = setKeyboard(user))
        await userLog("join the club", user.nickname, user.id, data = "application has been sent before")
        return
    user.status = "joinTheClub"; user.save()
    kb = ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True, row_width = 2, is_persistent = True, 
                             input_field_placeholder = lang["ph"]["selectCommand"])
    kb.add(KeyboardButton(lang["btn"]["continue"]), KeyboardButton(lang["btn"]["cancel"]))
    await bot.send_message(user.id, lang["join"]["rulesAgreement"], "HTML", reply_markup = kb)
    await userLog("join the club", user.nickname, user.id)
    
async def sendApplication(user: User):
    if user.status != "joinTheClub":
        await bot.send_message(user.id, lang["notUnderstood"], "HTML", reply_markup = setKeyboard(user))
        return
    user.status = None
    data = await makeRequest(f"https://api.brawlstars.com/v1/players/%23{user.tag}")
    if isinstance(data, dict):
        stats = PlayerStats(data, lang["join"]["application"])
        addToBlacklist(user.id)
        await bot.send_message(user.id, lang["join"]["applicationSent"], reply_markup = setKeyboard(user))
        user.j_Text = stats.text
        markup = InlineKeyboardMarkup(row_width = 2)
        markup.add(InlineKeyboardButton(lang["btn"]["accept"], callback_data = f"acceptApplication|{user}"), InlineKeyboardButton(lang["btn"]["reject"], callback_data = f"rejectApplication|{user}"))
        url = await urlOfTheIcon(stats.icon)
        await bot.send_photo(token["adminChat"], url, stats.text, "HTML", reply_markup = markup)
        await userLog("send application to the adminchat", user.nickname, user.id) 
    else:
        await bot.send_message(user.id, lang["join"]["gameOnMaintenance"], reply_markup = setKeyboard(user))
        await userLog("sendApplication: game on maintenance", user.nickname, user.id)
    user.save()


async def acceptApplication(user: User, callId, messageId, name): 
    await bot.edit_message_caption(token["adminChat"], messageId, caption = lang["join"]["acceptedApplication"].format(user.j_Text, name), parse_mode = "HTML")
    await bot.answer_callback_query(callId, text = lang["callback"]["acceptApplication"])
    inClubChat = (await bot.get_chat_member(token["chat"], user.id)).is_chat_member()
    if not inClubChat:
        user.rightsLevel, user.j_Text = 2, None; user.save()
        await bot.send_message(user.id, lang["join"]["applicationWasAccepted1"], "HTML", disable_web_page_preview = True, reply_markup = setKeyboard(user))
    else:
        user.rightsLevel, user.j_Text = 3, None; user.save()
        await bot.send_message(user.id, lang["join"]["applicationWasAccepted2"], "HTML", disable_web_page_preview = True, reply_markup = setKeyboard(user)) 
    await userLog("application was accepted", user.nickname, user.id, f"accepted by {name}")


async def rejectApplication(user: User, callId, messageId, name):
    await bot.edit_message_caption(token["adminChat"], messageId, caption = lang["join"]["rejectedApplication"].format(user.j_Text, name), parse_mode = "HTML")
    await bot.answer_callback_query(callId, text = lang["callback"]["rejectApplication"])
    await bot.send_message(user.id, lang["join"]["applicationWasRejected"], "HTML")
    user.j_Text = None; user.save()
    await userLog("application was rejected", user.nickname, user.id, f"rejected by {name}")

#Помощь

async def help(user: User):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(lang["btn"]["askForHelp"], callback_data = "help|"))
    await bot.send_message(user.id, lang["help"]["text"], "HTML", reply_markup = markup, disable_web_page_preview = True)
    await userLog("help", user.nickname, user.id, team = user.team)


async def enterQuestion(user: User, msgId):
    await bot.delete_message(user.id, msgId)
    kb = ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True, row_width = 2, is_persistent = True, 
                             input_field_placeholder = lang["ph"]["enterQuestion"])
    kb.add(KeyboardButton(lang["btn"]["skip"]), KeyboardButton(lang["btn"]["cancel"]))
    user.status = "enterQuestion"; user.save()
    await bot.send_message(user.id, lang["help"]["enterQuestion"], "HTML", reply_markup = kb)
    await userLog("enterQuestion", user.nickname, user.id)


async def sendQuestion(user: User, text):
    if text == lang["btn"]["skip"]:
        await bot.send_message(token["adminChat"], lang["help"]["question2"].format(user.nickname, user.team, user.id), "HTML")
    else:
        await bot.send_message(token["adminChat"], lang["help"]["question1"].format(user.nickname, text, user.team, user.id), "HTML")
    await bot.send_message(user.id, lang["help"]["questionSent"], "HTML", reply_markup = setKeyboard(user))
    await userLog("sendQuestion", user.nickname, user.id, text)
#Выбор часовой разницы

async def selectHourDifference(user: User):
    if user.rightsLevel >= 3:
        user.status = None; user.save()
        markup = InlineKeyboardMarkup(row_width = 6)
        differences = [['-14', '-13', '-12', '-11', '-10', '-9'], ['-8', '-7', '-6', '-5', '-4', '-3'], ['-2', '-1', '0', '+1', '+2', '+3'], ['+4', '+5', '+6', '+7', '+8', '+9']]
        for i in differences:
            markup.add(InlineKeyboardButton(i[0], callback_data = f"selectedHour|{i[0]}"), InlineKeyboardButton(i[1], callback_data = f"selectedHour|{i[1]}"), InlineKeyboardButton(i[2], callback_data = f"selectedHour|{i[2]}"), 
                    InlineKeyboardButton(i[3], callback_data = f"selectedHour|{i[3]}"), InlineKeyboardButton(i[4], callback_data = f"selectedHour|{i[4]}"), InlineKeyboardButton(i[5], callback_data = f"selectedHour|{i[5]}"))
        await bot.send_message(user, lang["hourDifference"]["select"].format(formatedHourDifference(user.hourDifference)), "HTML", reply_markup = markup)
        await userLog("select hour difference", user.nickname, user.id)
    else:
        await bot.send_message(user.id, lang["notUnderstood"], "HTML")


async def saveHourDifference(user: User, messageId, hourDifference):
    s = user.hourDifference != int(hourDifference)
    user.hourDifference = int(hourDifference); user.save()
    time = visualHour(int(datetime.now().strftime('%H')), user.hourDifference) + datetime.now().strftime(':%M')
    await bot.delete_message(user.id, messageId)
    await bot.send_message(user.id, lang["hourDifference"]["save"].format(formatedHourDifference(user.hourDifference), time), "HTML", reply_markup = setKeyboard(user))
    if s and user.t_MessageId:
        await bot.edit_message_reply_markup(user.id, user.t_MessageId, reply_markup = genMarkup(user))
    await userLog("save hour difference", user.nickname, user.id, formatedHourDifference(user.hourDifference))
    

async def selectTarget(user: User):
    if user.rightsLevel < 4:
        await bot.send_message(user.id, lang["notUnderstood"], "HTML")
        return
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(lang["btn"]["toEveryone"], callback_data = "makeAnAnnouncement|toEveryone"))
    markup.add(InlineKeyboardButton(lang["btn"]["toClubMembers"], callback_data = "makeAnAnnouncement|toClubMembers"))
    await bot.send_message(user.id, lang["makeAnAnnouncement"]["selectTarget"], "HTML", reply_markup = markup)


async def selectText(user: User, target, messageId):
    await bot.delete_message(user.id, messageId)
    if target == "toEveryone":
        user.status = "makeAnAnnouncementToEveryone"
    else:
        user.status = "makeAnAnnouncementToClubMembers"
    user.save()
    await bot.send_message(user.id, lang["makeAnAnnouncement"]["selectText"], "HTML")


async def sendAnAnnouncement(user: User, text):
    if user.status == "makeAnAnnouncementToEveryone":
        userList = list(User.select())
    else:
        userList = getMembers()
    text = lang["makeAnAnnouncement"]["format"].format(text, user.nickname)
    try:
        await userLog(user.status, user.nickname, user.id, text)
    except Exception as e:
        await bot.send_message(user.id, lang["makeAnAnnouncement"]["formatError"], "HTML")
        return
    await bot.send_message(user.id, lang["makeAnAnnouncement"]["success"], "HTML", reply_markup = setKeyboard(user))
    for receiver in userList:
        try:
            await bot.send_message(receiver.id, text, "HTML", reply_markup=setKeyboard(receiver))
        except Exception as e:
            print(e)
            print(receiver.id)


async def banUser(user: User, args):
    if user.rightsLevel != 5:
        await bot.send_message(user.id, lang["notUnderstood"], "HTML", reply_markup = setKeyboard(user))
        return
    args = list(args.split())
    if len(args) < 2:
        await bot.send_message(user.id, lang["ban"]["incorrectFormat"], "HTML", reply_markup = setKeyboard(user))
        return
    id = args[0]
    reason = " ".join(args[1:])
    user2 = getUser(id)
    if not user2:
        await bot.send_message(user.id, lang["ban"]["userNotFound"], "HTML", reply_markup = setKeyboard(user))
    await bot.send_message(user.id, lang["ban"]["forAdmin"].format(user2.nickname, id), "HTML", reply_markup = setKeyboard(user))
    user2.delete_instance()
    TrackedUser.delete_by_id(id)
    BanList.create(id = user2.id, date = datetime.now(), reason = reason)    
    await bot.send_message(id, lang["ban"]["forUser"].format(reason), "HTML", reply_markup = ReplyKeyboardRemove())
    
#Редактирование команд

def genTeamsList():
    markup = InlineKeyboardMarkup(row_width = 2)
    last = None
    listOfTeams = ""
    for team in Team.select():
        n = team.n
        if not last: 
            last = InlineKeyboardButton(lang["btn"]["team"].format(n), callback_data = f"selectedTeam|{n}")
        else: 
            markup.add(last, InlineKeyboardButton(lang["btn"]["team"].format(n), callback_data = f"selectedTeam|{n}"))
            last = None
        members = getTeamMembers(n)
        if len(members) != 0:
            nicknames = [user.nickname for user in members]
            listOfTeams += lang["editTeams"]["team"].format(n, ", ".join(nicknames))
        else: listOfTeams += lang["editTeams"]["team"].format(n, "❌")
    return markup, lang["editTeams"]["currentTeams"].format(listOfTeams)


async def editTeams(user: User):
    if user.rightsLevel >= 4:
        text = genTeamsList()[1]
        markup = InlineKeyboardMarkup(row_width = 1)
        markup.add(InlineKeyboardButton(lang["btn"]["edit"], callback_data = "editTeams|"))
        dayStatus = getValue("dayStatus")
        if dayStatus != "Preparing":
            await bot.send_message(user, text, "HTML", reply_markup = markup)
            await userLog("edit teams", user.nickname, user.id)
        else: 
            await bot.send_message(user, lang["editTeams"]["error2"].format(text), "HTML")
            await userLog("edit teams", user.nickname, user.id, "can not edit teams during battle day")
    else:
        await bot.send_message(user.id, lang["notUnderstood"], "HTML")


async def selectTeam(id, messageId):
    markup, currentTeams = genTeamsList()
    e_Id = getValue("e_Id")
    if e_Id is None: 
        setValue("e_Id", id)
        setValue("e_MessageId", messageId)
        time = calculateTime(datetime.now().strftime("%H:%M"), 5)
        addTask(time, "undoTeamEditing", None)
        await bot.edit_message_text(lang["editTeams"]["selectTeam"].format(currentTeams), id, messageId, parse_mode = "HTML", reply_markup = markup)
    else:
        await bot.delete_message(id, messageId) 
        await bot.send_message(lang["editTeams"]["error1"].format(currentTeams, getUser(e_Id).nickname), id, messageId, parse_mode = "HTML")


async def choosePlayer(id, messageId, selectedTeam): 
    setValue("e_SelectedTeam", selectedTeam)
    members = getTeamMembers(selectedTeam)
    markup = InlineKeyboardMarkup(row_width = 3)
    for user in members:
        markup.add(InlineKeyboardButton(user.nickname, callback_data = f"selectedUser|{user.nickname}"))
    if len(members) == 0: 
        markup.add(InlineKeyboardButton("➕", callback_data = "selectedUser|+"))
        await bot.edit_message_text(lang["editTeams"]["addPlayer"], id, messageId, reply_markup = markup)
    else:
        if len(members) < 3: markup.add(InlineKeyboardButton("➕", callback_data = "selectedUser|+"))
        await bot.edit_message_text(lang["editTeams"]["editPlayers"], id, messageId, reply_markup = markup)
    

async def userToChange(id, messageId, selectedUser): 
    setValue("e_SelectedUser", selectedUser)
    members = list(User.select().where(User.rightsLevel >= 3).order_by(User.team))
    n = len(members)
    markup = InlineKeyboardMarkup(row_width = 3)
    if n >= 3:
        for i in range(0, (n - n % 3), 3):
            markup.add(InlineKeyboardButton(members[i].nickname, callback_data = f"replacementUser|{members[i].nickname}"), 
                       InlineKeyboardButton(members[i+1].nickname, callback_data = f"replacementUser|{members[i+1].nickname}"), 
                       InlineKeyboardButton(members[i+2].nickname, callback_data = f"replacementUser|{members[i+2].nickname}"))
    if n % 3 == 2:
        markup.add(InlineKeyboardButton(members[n-2].nickname, callback_data = f"replacementUser|{members[n-2].nickname}"), 
                   InlineKeyboardButton(members[n-1].nickname, callback_data = f"replacementUser|{members[n-1].nickname}"), 
                   InlineKeyboardButton("❌", callback_data = "replacementUser|-"))
    elif n % 3 == 1:
        markup.add(InlineKeyboardButton(members[n-1].nickname, callback_data = f"replacementUser|{members[n-1].nickname}"), 
                   InlineKeyboardButton("❌", callback_data = "replacementUser|-"))    
    else:
        markup.add(InlineKeyboardButton("❌", callback_data = "replacementUser|-"))
    if selectedUser == "+": 
        await bot.edit_message_text(lang["editTeams"]["playerToAdd"].format(getValue("e_SelectedTeam")), id, messageId, parse_mode = "HTML", reply_markup = markup)
    else: 
        await bot.edit_message_text(lang["editTeams"]["playerToReplace"].format(selectedUser), id, messageId, parse_mode = "HTML", reply_markup = markup)


async def changeResult(id, messageId, replacement): 
    selectedTeam = getValue("e_SelectedTeam")
    selectedUser = getValue("e_SelectedUser")
    (Tasks.delete().where(Tasks.action == "undoTeamEditing")).execute()
    if selectedUser == "+":
        if replacement == "-":
            text = lang["editTeams"]["result1"]
        else:
            text = lang["editTeams"]["result2"].format(selectedTeam, replacement)
            user = User.get(User.nickname == replacement)
            user.team = selectedTeam; user.save()
    else:
        user = User.get(User.nickname == selectedUser)
        if replacement == "-":      
            user.team = 0; user.save()
            text = lang["editTeams"]["result3"].format(selectedTeam, selectedUser)
        else:
            if selectedUser == replacement: 
                text = lang["editTeams"]["result1"]
            else:
                user.team = 0; user.save()
                text = lang["editTeams"]["result4"].format(selectedTeam, selectedUser, replacement)
                user = User.get(User.nickname == replacement)
                user.team = selectedTeam; user.save()
    markup, teamLists = genTeamsList()
    markup = InlineKeyboardMarkup(row_width = 1)
    markup.add(InlineKeyboardButton(lang["btn"]["editAgain"], callback_data = "editTeams|"))
    await bot.edit_message_text(text + teamLists, id, messageId, parse_mode = "HTML", reply_markup = markup)
    setValue("e_Id", None); setValue("e_MessageId", None); setValue("e_SelectedTeam", None); setValue("e_SelectedUser", None)
    await userLog("edit teams result", getUser(id).nickname, id, text[:-2])

#Выбор времени для КЛ

def addRowToMarkup(markup, minAmount, vHour, hour, row):
    hour = '{:02}'.format(hour)
    if len(row) == 1: 
        markup.add(InlineKeyboardButton(row[0][0], callback_data = row[0][1]))
    elif len(row) == 2:
        if minAmount != 1:
            markup.add(InlineKeyboardButton(vHour, callback_data = "rowClick|" + hour), InlineKeyboardButton(row[0][0], callback_data = row[0][1]), 
                       InlineKeyboardButton(row[1][0], callback_data = row[1][1]))
        else: markup.add(InlineKeyboardButton(row[0][0], callback_data = row[0][1]), InlineKeyboardButton(row[1][0], callback_data = row[1][1]))
    elif len(row) == 3:
        if minAmount != 1: 
            markup.add(InlineKeyboardButton(vHour, callback_data = "rowClick|" + hour), InlineKeyboardButton(row[0][0], callback_data = row[0][1]), InlineKeyboardButton(row[1][0], callback_data = row[1][1]), InlineKeyboardButton(row[2][0], callback_data = row[2][1]))
        else: 
            markup.add(InlineKeyboardButton(row[0][0], callback_data = row[0][1]), InlineKeyboardButton(row[1][0], callback_data = row[1][1]), InlineKeyboardButton(row[2][0], callback_data = row[2][1]))
    return markup


def genMarkup(user: User):
    team: Team = getTeam(user.team)
    markup = InlineKeyboardMarkup(row_width = 4)   
    row = []
    hour = None
    for t in TDict.select().where(TDict.userId == user.id):
        if hour == None: vHour = visualHour(int(t.h), user.hourDifference); hour = t.h
        if hour != t.h: 
            markup = addRowToMarkup(markup, team.t_MinAmount, vHour, hour, row)
            row = []
            hour = t.h
            vHour = visualHour(int(t.h), user.hourDifference)
            row.append([f"{('✅' if t.selected is True else '')}{vHour}:{'{:02}'.format(t.m)}", f"timeClick|{'{:02}'.format(t.h)}:{'{:02}'.format(t.m)}"])
        else: 
            row.append([f"{('✅' if t.selected is True else '')}{vHour}:{'{:02}'.format(t.m)}", f"timeClick|{'{:02}'.format(t.h)}:{'{:02}'.format(t.m)}"])
    markup = addRowToMarkup(markup, team.t_MinAmount, vHour, hour, row)
    n = len(getTeamMembers(user.team))
    if (n == 3 and team.t_MinAmount != 6) or (n == 2 and team.t_MinAmount != 2):
        markup.add(InlineKeyboardButton(lang["btn"]["suggestAnotherTime"], callback_data = "chooseAnotherTime|"))
    if team.t_MinAmount != 1:
        if user.t_Counter >= team.t_MinAmount: 
            markup.add(InlineKeyboardButton(lang["btn"]["save"], callback_data = "saveButton|"))
        else: 
            markup.add(InlineKeyboardButton(lang["btn"]["chooseMore"].format(team.t_MinAmount - user.t_Counter), callback_data = "|"))
    return markup


async def timeClick(user: User, data, messageId): 
    if messageId != user.t_MessageId:
        await bot.edit_message_text(lang["messageIsOutdated"], user.id, messageId, parse_mode = "HTML")
        return
    h, m = map(int, data.split(":"))
    team: Team = getTeam(user.team)
    if team.t_MinAmount == 1: 
        await setCommonTime(user, data, messageId)
    else:
        t = TDict.get(TDict.userId == user.id, TDict.h == h, TDict.m == m)
        if t.selected is False:
            t.selected = True
            user.t_Counter += 1
        else:
            t.selected = False
            user.t_Counter -= 1
        t.save(); user.save()
        await bot.edit_message_reply_markup(user.id, messageId, reply_markup = genMarkup(user))
    

async def rowClick(user: User, h, messageId):
    if messageId != user.t_MessageId:
        await bot.edit_message_text(lang["messageIsOutdated"], user.id, messageId, parse_mode = "HTML")
        return
    flag = False
    times = list(TDict.select().where(TDict.userId == user.id, TDict.h == h))
    for t in times:
        if t.selected is True: 
            flag = True
            break
    if flag is True:
        for t in times:
            if t.selected is True:
                t.selected = False
                user.t_Counter -= 1
                t.save(); user.save()
    else:
        for t in times:
            if t.selected is False:
                t.selected = True
                user.t_Counter += 1
                t.save(); user.save()
    await bot.edit_message_reply_markup(user.id, messageId, reply_markup = genMarkup(user))     


async def saveButton(user: User, messageId): 
    if messageId != user.t_MessageId:
        await bot.edit_message_text(lang["messageIsOutdated"], user.id, messageId, parse_mode = "HTML")
        return
    user.t_MessageId, user.t_Counter = None, 0
    user.save()
    notAnswered = list(User.select().where(User.team == user.team, User.t_MessageId > -1))
    await bot.delete_message(user.id, messageId)
    if len(notAnswered) == 1:
        await bot.send_message(user.id, lang["table"]["save1"].format(notAnswered[0].nickname), "HTML", reply_markup = setKeyboard(user))
    else:
        await bot.send_message(user.id, lang["table"]["save2"].format(notAnswered[0].nickname, notAnswered[1].nickname), "HTML", reply_markup = setKeyboard(user))
    team: Team = getTeam(user.team)
    if team.t_MinAmount == 6: 
        team.t_MinAmount = 2
        msg = "send1"
    elif team.t_MinAmount == 2: 
        team.t_MinAmount = 1
        msg = "send2"
    user.save(); team.save()
    for user2 in notAnswered:
        (TDict.delete().where(TDict.userId == user2.id)).execute()
    for t in TDict.select().where(TDict.userId == user.id, TDict.selected == True):
        for user2 in notAnswered:
            (TDict.create(userId = user2.id, h = t.h, m = t.m)).save()
    (TDict.delete().where(TDict.userId == user.id)).execute()
    pinnedMsg = getValue("teamListsMessageId")
    day = calculateDayCL()

    for user2 in notAnswered:
        if user2.status != "choosesAnotherTime":
            if user2.t_Counter == 0:     
                await bot.delete_message(user2.id, user2.t_MessageId)   
                user2.t_MessageId = (await bot.send_message(user2.id, lang["table"][msg].format(day, user2.team, pinnedMsg), "HTML", reply_markup = genMarkup(user2))).message_id
            else:
                await bot.edit_message_text(lang["table"]["outOfDate"], user2.id, user2.t_MessageId, parse_mode = "HTML")
                user2.t_MessageId = (await bot.send_message(user2.id, lang["table"][msg].format(day, user2.team, pinnedMsg), "HTML", reply_markup = genMarkup(user2))).message_id
        user2.t_Counter = 0
        user2.save()
    await userLog("save button", user.nickname, user.id, f"remain: {' ,'.join(notAnswered)}", user.team, user.rep)


async def setCommonTime(user: User, time, messageId):
    if messageId != user.t_MessageId:
        await bot.edit_message_text(lang["messageIsOutdated"], user.id, messageId, parse_mode = "HTML")
        return
    await bot.delete_message(user.id, user.t_MessageId)
    (TDict.delete().where(TDict.userId == user.id)).execute()
    team: Team = getTeam(user.team)
    team.t_TimeToPlay = time; team.t_MinAmount = 0; team.save()
    addTask(time, "gameReminder", user.team)
    addTask(calculateTime(time, -15), "advanceReminder", user.team)
    user.t_MessageId, user.t_Counter = None, 0; user.save()
    for member in getTeamMembers(user.team):
        vTime = visualHour(int(time[:2]), member.hourDifference) + ":" + time[3:]
        await bot.send_message(member.id, lang["table"]["sendSelectedTime"].format(vTime), "HTML", reply_markup = setKeyboard(member))
    await userLog("select common time", user.nickname, user.id, f"selected time: {time}", user.team, user.rep)
    

async def backToTheTable(user: User):
    user.status = None; user.save()
    team = getTeam(user.team)
    if team.t_MinAmount == 1:
        text = "send2"
    else:
        text = "send1"
    day = calculateDayCL()
    teamListsMessageId = getValue("teamListsMessageId")
    await bot.edit_message_text(lang["table"][text].format(day, user.team, teamListsMessageId), user.id, user.t_MessageId, parse_mode = "HTML", reply_markup = genMarkup(user))


async def chooseAnotherTime(user: User, messageId):
    if messageId != user.t_MessageId:
        await bot.edit_message_text(lang["messageIsOutdated"], user.id, messageId, parse_mode = "HTML")
        return
    user.status = "choosesAnotherTime"; user.save()
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(lang["btn"]["backToTheTable"], callback_data = "backToTheTable|"))
    await bot.edit_message_text(lang["table"]["chooseAnotherTime"], user.id, user.t_MessageId, reply_markup = markup)


async def suggestAnotherTime(user: User, text):
    time = timeProcessing(user, text)
    if time == "incorrect format":
        await bot.send_message(user.id, lang["table"]["incorrectFormat"], "HTML")
        await userLog("suggestAnotherTime: incorrect format", user.nickname, user.id, text, user.team, user.rep)
    elif time == "incorrect time":
        await bot.send_message(user.id, lang["table"]["incorrectTime"], "HTML")
        await userLog("suggestAnotherTime: incorrect time", user.nickname, user.id, text, user.team, user.rep)
    else:
        await bot.delete_message(user.id, user.t_MessageId)
        members = getTeamMembers(user.team)
        for member in members:
            if member.id != user.id:
                if member.t_MessageId:
                    await bot.delete_message(member.id, member.t_MessageId)
                    member.t_MessageId, member.t_Counter = None, 0; member.save()
                await bot.send_message(member.id, lang["table"]["suggestAnotherTime"].format(user.nickname), "HTML", reply_markup = setKeyboard(user))
        await sendOffer(user, user.team, time, True)
        
async def getNotAnsweredUsers(user: User):
    if user.rightsLevel < 4:
        await bot.send_message(user.id, lang["notUnderstood"], "HTML", reply_markup = setKeyboard(user))
        return
    notAnswered = list(User.select().where(User.rightsLevel >= 3, User.t_MessageId, User.t_Counter == 0))
    text = ""
    for user2 in notAnswered:
        pass
#Приглашения

async def offerToPlay_Menu(user: User):
    if canUseOfferToPlayCL(user):
        team = getTeam(user.team)
        markup = InlineKeyboardMarkup(row_width = 1)
        markup.add(InlineKeyboardButton(lang["btn"]["now"], callback_data = "offerToPlayNow|"), InlineKeyboardButton(lang["btn"]["selectTime"], callback_data = "offerTimeToPlay|"))
        if not team.t_TimeToPlay: 
            await bot.send_message(user.id, lang["offerToPlay"]["menu1"], "HTML", reply_markup = markup)
        else: 
            await bot.send_message(user.id, lang["offerToPlay"]["menu2"].format(calculateTime(team.t_TimeToPlay, user.hourDifference * 60)), "HTML", reply_markup = markup)


async def cancelTimeToPlay(user: User, team: Team):
    if team.t_TimeToPlay:
        (Tasks.delete().where(Tasks.action == "advanceReminder", Tasks.data == str(team.n))).execute()
        (Tasks.delete().where(Tasks.action == "gameReminder", Tasks.data == str(team.n))).execute()
        for member in getTeamMembers(team.n):
            if member.id != user.id:
                await bot.send_message(member.id, lang["offerToPlay"]["cancelTimeToPlay1"].format(calculateTime(team.t_TimeToPlay, member.hourDifference * 60), user.nickname), "HTML")
            else:
                await bot.send_message(member.id, lang["offerToPlay"]["cancelTimeToPlay2"].format(calculateTime(team.t_TimeToPlay, member.hourDifference * 60)), "HTML")
        await userLog("cancel time to play", user.nickname, user.id, team.t_TimeToPlay, team.n)
        team.t_TimeToPlay = None; team.save()


async def offerToPlayNow(user: User, messageId):
    await bot.delete_message(user.id, messageId)
    dayStatus = getValue("dayStatus")
    if dayStatus != "CL":
        await bot.send_message(user.id, lang["offerToPlay"]["error1"], "HTML")
        return
    offer = getOffer(user.team)
    if offer:
        await bot.send_message(user.id, lang["offerToPlay"]["alreadyCreated"], "HTML")
        return
    team = getTeam(user.team)
    offer: Offer = Offer.create(type = "Now", data = user.team, ownerId = user.id, ownerNickname = user.nickname)
    time = calculateTime(datetime.now().strftime("%H:%M"), 15)
    addTask(time, "offerCancellation", team.n)
    markup = InlineKeyboardMarkup(row_width = 2)
    markup.add(InlineKeyboardButton(lang["btn"]["canPlay"], callback_data = "acceptOffer|"), InlineKeyboardButton(lang["btn"]["can'tPlay"], callback_data = "declineOffer|"))
    mrkp = InlineKeyboardMarkup(row_width = 2)
    mrkp.add(InlineKeyboardButton(lang["btn"]["cancelOffer"], callback_data = "cancelOffer|"))
    for member in getTeamMembers(user.team): 
        member.o_Text = lang["offerToPlay"]["now"]["toTeammates"].format(user.nickname)
        if member.id != user.id: 
            member.o_MessageId = (await bot.send_message(member.id, member.o_Text, "HTML", reply_markup = markup)).message_id
        else:
            await bot.send_message(user.id, lang["offerToPlay"]["now"]["toOwner"], "HTML", reply_markup = mrkp)
        member.save()
    await userLog("offer to play now", user.nickname, user.id, user.team, user.rep)


async def acceptOffer(user: User):
    offer: Offer = getOffer(user.team)
    await bot.edit_message_text(lang["offerToPlay"]["accepted"].format(user.o_Text), user.id, user.o_MessageId, parse_mode = "HTML")
    user.o_MessageId, user.o_Text = None, None; user.save()
    members = getTeamMembers(user.team)
    remain = len(members) - 1
    for user2 in members:
        if user2.id != user.id: 
            if not user2.o_MessageId: remain -= 1
            if offer.type == "AtTime":
                await bot.send_message(user2.id, lang["offerToPlay"]["atTime"]["canPlay"].format(user.nickname, offer.time), "HTML")
            else:
                await bot.send_message(user2.id, lang["offerToPlay"]["now"]["canPlay"].format(user.nickname), "HTML")
    await userLog("accept offer", user.nickname, user.id, f"remain: {remain}", user.team, user.rep)

    if remain == 0: 
        (Tasks.delete().where(Tasks.action == "offerCancellation", Tasks.data == user.team)).execute()
        for user2 in members:
            if offer.type == "AtTime":
                await bot.send_message(user2.id, lang["offerToPlay"]["atTime"]["everyoneCanPlay"].format(offer.time), "HTML", reply_markup = setKeyboard(user2))
            else:
                await bot.send_message(user2.id, lang["offerToPlay"]["now"]["everyoneCanPlay"], "HTML", reply_markup = setKeyboard(user2))
        if offer.type == "AtTime":
            addTask(calculateTime(offer.time, -15), "advanceReminder", user.team)
            addTask(offer.time, "gameReminder", user.team)
            team = getTeam(user.team)
            team.t_TimeToPlay = offer.time; team.save()
            await botLog(f"everyone can play at {offer.time}", f"Team{user.team}")
        else:
            await botLog("everyone can play now", f"Team{user.team}")
        offer.delete_instance()
    else: 
        await bot.send_message(user.id, lang["offerToPlay"]["waitForTeammates"])
    

async def declineOffer(user: User):
    offer: Offer = getOffer(user.team)
    await bot.edit_message_text(lang["offerToPlay"]["declined"].format(user.o_Text), user.id, user.o_MessageId, parse_mode = "HTML")
    await bot.send_message(user.id, lang["offerToPlay"]["offerTime"], "HTML")
    (Tasks.delete().where(Tasks.action == "offerCancellation", Tasks.data == user.team)).execute()
    user.o_MessageId, user.o_Text = None, None; user.save()
    members = getTeamMembers(user.team)
    for user2 in members:
        if user2.o_MessageId:
            await bot.edit_message_text(lang["offerToPlay"]["declined"].format(user2.o_Text), user2.id, user2.o_MessageId, parse_mode = "HTML")
            user2.o_MessageId = None; user2.save()
        if user2.id != user.id: 
            if offer.type == "AtTime":
                await bot.send_message(user2.id, lang["offerToPlay"]["atTime"]["can'tPlay"].format(user.nickname, offer.time), "HTML")
            else:
                await bot.send_message(user2.id, lang["offerToPlay"]["now"]["can'tPlay"].format(user.nickname), "HTML")
    offer.delete_instance()
    await userLog("decline offer", user.nickname, user.id, team = user.team, rep = user.rep)


async def offerToPlaySelectTime(user: User, messageId):
    team: Team = getTeam(user.team)
    await bot.delete_message(user.id, messageId)
    offer: Offer = getOffer(team.n)
    (Tasks.delete().where(Tasks.action == "offerCancellation", Tasks.data == user.team)).execute()
    if offer:
        await bot.send_message(user.id, lang["offerToPlay"]["alreadyCreated"])
    else:
        user.status = "selectingTime"; user.save()
        await bot.send_message(user.id, lang["offerToPlay"]["selectTime"])
    await userLog("selecting time to create an offer", user.nickname, user.id, team = user.team, rep = user.rep)


async def timeResponse(user: User, text):
    team = getTeam(user.team)
    user.status = None; user.save()
    time = timeProcessing(user, text)
    if time == "incorrect format":
        await bot.send_message(user.id, lang["offerToPlay"]["incorrectFormat"], "HTML")
        await userLog("OfferToPlayAtTime: incorrect format", user.nickname, user.id, text, user.team, user.rep)
    elif time == "incorrect time":
        await bot.send_message(user.id, lang["offerToPlay"]["incorrectTime"], "HTML")
        await userLog("OfferToPlayAtTime: incorrect time", user.nickname, user.id, text, user.team, user.rep)
    else:
        await sendOffer(user, team, time)


def timeProcessing(user: User, text):
    if text.count(":") == 1 and (len(text) >= 3 and len(text) <= 5):
        h1, m1 = text.split(":")
        try:
            h1 = int(h1)
            m1 = int(m1)
        except ValueError:
            return "incorrect format"
        if h1 >= 0 and h1 < 24 and m1 >= 0 and m1 < 60:
            dayStatus = getValue("dayStatus")
            time = calculateTime(text, -user.hourDifference * 60)
            h1, m1 = map(int, time.split(":"))
            if dayStatus == "Preparing": 
                return time
            else:
                h2, m2 = map(int, datetime.now().strftime("%H:%M").split(":"))
                if (h1 < 17 and h2 >= 17): 
                    return time
                if (h1 >= 17 and h2 >= 17) or (h1 < 17 and h2 < 17):
                    dif = (h1 * 60 + m1) - (h2 * 60 + m2)
                    if dif > 0: 
                        return time
                    return "incorrect time"
    return "incorrect format"


async def sendOffer(user: User, team, time, cancel=False):  
    if cancel:
        await cancelOffer(user)    
    offer: Offer = getOffer(user.team)                                                                                     
    if not offer:
        offer: Offer = Offer.create(type = "AtTime", time = time, data = user.team, ownerId = user.id, ownerNickname = user.nickname)
        await cancelTimeToPlay(user, getTeam(user.team))
        addTask(time, "offerCancellation", user.team)
        markup = InlineKeyboardMarkup(row_width = 2)
        markup.add(InlineKeyboardButton(lang["btn"]["canPlay"], callback_data = "acceptOffer|"), InlineKeyboardButton(lang["btn"]["can'tPlay"], callback_data = "declineOffer|"))
        members = getTeamMembers(team)
        mrkp = InlineKeyboardMarkup(row_width = 2)
        mrkp.add(InlineKeyboardButton(lang["btn"]["cancelOffer"], callback_data = "cancelOffer|"))
        await bot.send_message(user.id, lang["offerToPlay"]["atTime"]["toOwner"].format(calculateTime(time, user.hourDifference * 60)), "HTML", reply_markup = mrkp)
        for user2 in members:
            user2.o_Text = lang["offerToPlay"]["atTime"]["toTeammates"].format(offer.ownerNickname, calculateTime(offer.time, user2.hourDifference * 60))
            if user2.id != user.id:
                user2.o_MessageId = (await bot.send_message(user2.id, user2.o_Text, "HTML", reply_markup = markup)).message_id
                user2.save()
        await userLog(f"offer to play at {offer.time}", user.nickname, user.id, team = user.team, rep = user.rep)
    else: 
        await bot.send_message(user.id, lang["offerToPlay"]["alreadyCreated"], "HTML")
        await userLog("offer already created", user.nickname, user.id, team = user.team, rep = user.rep)
    

async def cancelOffer(user: User, msgId=None):
    if msgId:
        await bot.delete_message(user.id, msgId)
    offer: Offer = getOffer(user.team)
    if offer:
        members = getTeamMembers(user.team)
        for member in members:
            if member.o_MessageId:
                await bot.edit_message_text(lang["offerToPlay"]["canceled"].format(member.o_Text), member.id, member.o_MessageId, parse_mode = "HTML")
                member.o_MessageId, member.o_Text = None, None; member.save()
            if member.id != offer.ownerId:
                await bot.send_message(member.id, lang["offerToPlay"]["canceledToTeammates"].format(offer.ownerNickname), "HTML")
            else:
                await bot.send_message(member.id, lang["offerToPlay"]["canceledToOwner"], "HTML")
        offer.delete_instance()

#EnterChat

async def startChat(user: User):
    if user.rightsLevel < 4:
        await bot.send_message(user.id, lang["notUnderstood"], "HTML", reply_markup = setKeyboard(user))
        return
    user.status = "enterChat"; user.save()
    await bot.send_message(user.id, lang["chat"]["select"], "HTML")


async def enterChat(user: User, n):
    try:
        n = int(n)
    except Exception:
        await bot.send_message(user.id, lang["chat"]["incorrectId"], "HTML")
        return
    kb = ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True, row_width = 2, is_persistent = True,
                             input_field_placeholder = lang["ph"]["msgToTeammates"])
    kb.add(KeyboardButton(lang["btn"]["turnOffChatMode"]))
    if n in range(1, 11):
        await enterChatMode(user, n)
    else:
        if not isCorrectId(n) or n == user.id:
            await bot.send_message(user.id, lang["chat"]["incorrectId"], "HTML")
            return
        if len(getInterlocutors(n)) == 0:
            user2: User = getUser(n)
            user2.chatСhannel, user2.status = n, "chatWithUser"; user2.save()
            kb = ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True, row_width = 2, is_persistent = True,
                             input_field_placeholder = lang["ph"]["msgToTeammates"])
            kb.add(KeyboardButton(lang["btn"]["turnOffChatMode"]))
            await bot.send_message(user2.id, lang["chat"]["created"].format(user.nickname), "HTML", reply_markup = kb)
        await enterChatMode(user, n)
        

async def turnOffСhatMode(user: User):
    if user.status != "teamChat":
        await bot.send_message(user.id, lang["chat"]["turnOffChatMode1"], "HTML", reply_markup = setKeyboard(user))
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(lang["btn"]["leaveChat"], callback_data = f"leaveChat|{user.chatСhannel}"))
        await bot.send_message(user.id, lang["chat"]["turnOffChatMode2"], "HTML", reply_markup = markup)
    else:
        await bot.send_message(user.id, lang["chat"]["turnOffChatMode1"], "HTML", reply_markup = setKeyboard(user))
    await userLog("turn off chat mode", user.nickname, user.id, team = user.team)


async def leaveChat(user: User, msgId):
    await bot.delete_message(user.id, msgId)
    if not user.chatСhannel:
        await bot.send_message(user.id, lang["chat"]["error2"])
        return
    interlocutors = getInterlocutors(user.chatСhannel)
    if len(interlocutors) == 1 and user.chatСhannel > 10:
        user2 = interlocutors[0]
        if user2.status == "chatWithUser":
            await bot.send_message(user2.id, lang["chat"]["deletion"], "HTML", reply_markup = setKeyboard(user2))
            user2.status, user2.chatСhannel = None, None; user2.save()
    user.chatСhannel = None; user.save()
    await bot.send_message(user.id, lang["chat"]["leave"], "HTML", reply_markup=setKeyboard(user))

async def enterChatMode(user: User, n):
    interlocutors = getInterlocutors(n)
    if n <= 10 and (len(interlocutors) == 0 or interlocutors == [user]):
        await bot.send_message(user.id, lang["chat"]["error1"], "HTML", reply_markup = setKeyboard(user))
        await userLog("enterChatMode: alone in the chat", user.nickname, user.id, team = user.team)
        return
    listOfInterlocutors = []
    for user2 in interlocutors:
        if user2.id != user.id:
            listOfInterlocutors.append(f"<b>{user2.nickname}</b>")
    listOfInterlocutors = ", ".join(listOfInterlocutors)
    if n in range(1, 11): 
        if user.team == n:
            user.status = "teamChat"
        else:
            user.status = "chatWithTeam"
            user.chatСhannel = n
    else: 
        user.status = "chatWithUser"
        user.chatСhannel = n
    user.save()
    kb = ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True, row_width = 2, is_persistent = True, input_field_placeholder = lang["ph"]["msgToTeammates"])
    kb.add(KeyboardButton(lang["btn"]["turnOffChatMode"]))
    await bot.send_message(user.id, lang["chat"]["enter"].format(listOfInterlocutors), "HTML", reply_markup = kb)
    await userLog("enter chat mode", user.nickname, user.id, n, user.team)

async def msgToChat(user: User, prefix, n, text):
    interlocutors = getInterlocutors(n)
    for user2 in interlocutors:
        if user2.id != user.id:
            if (user2.chatСhannel == n and user2.status in {"chatWithTeam", "chatWithUser"}) or (user2.status == "teamChat" and user2.team == n):
                await bot.send_message(user2.id, lang["chat"]["msgFormat1"].format(prefix, user.nickname, text), "HTML")
            else:
                await bot.send_message(user2.id, lang["chat"]["msgFormat2"].format(prefix, user.nickname, text), "HTML")             
    await userLog("msg to the chat", user.nickname, user.id, text, user.team)


async def stickerToChat(user: User, prefix, n, stickerId, emoji):
    interlocutors = getInterlocutors(n)
    for user2 in interlocutors:
        if user2.id != user.id:
            msgId = (await bot.send_sticker(user2.id, stickerId)).message_id
            if (user2.chatСhannel == n and user2.status in {"chatWithTeam", "chatWithUser"}) or (user2.status == "teamChat" and user2.team == n):
                await bot.send_message(user2.id, lang["chat"]["stickerFormat1"].format(prefix, user.nickname, emoji), "HTML", reply_to_message_id = msgId)
            else:
                await bot.send_message(user2.id, lang["chat"]["stickerFormat2"].format(prefix, user.nickname, emoji), "HTML", reply_to_message_id = msgId)             
    await loggerBot.send_sticker(token["logChat"], stickerId)
    await userLog("sticker to the chat", user.nickname, user.id, emoji, user.team)

async def savePlayerTrophies():
    trophies = {}
    for user in getMembers():
        data = await makeRequest(f"https://api.brawlstars.com/v1/players/%23{user.tag}")
        stats = PlayerStats(data, "")
        trophies[user.id] = stats.trophies
    print(trophies)

async def calculateTropheyDifference():
    a = {518309668: 48676, 587262745: 45494, 782053987: 46121, 885241590: 46521, 922572148: 47478, 972222297: 50292, 1108068259: 46643, 1193654237: 50740, 1349357882: 50619, 1351862795: 48648, 1445041950: 49008, 1627845759: 44646, 1642493961: 46004, 1646626302: 46365, 1692914062: 45652, 1817035234: 46993, 1904720832: 48583, 2146490422: 48376, 5191199723: 47971, 5231780417: 48172, 5261847682: 53179, 5305368469: 50155, 5398258926: 47801, 5493796318: 49542, 5752626964: 44025, 6055712750: 48233, 6199304130: 46321}
    b = {468960807: 50668, 503614907: 44713, 518309668: 48435, 587262745: 45148, 658551070: 42251, 782053987: 46104, 885241590: 46521, 922572148: 47655, 944737635: 40492, 950221051: 50794, 965991778: 41417, 972222297: 50213, 980860780: 35392, 1064058134: 44499, 1146720942: 50334, 1193654237: 50589, 1218269633: 53358, 1230083523: 43424, 1301076069: 45902, 1336774916: 56959, 1349357882: 50430, 1351862795: 48623, 1445041950: 49015, 1446851981: 46547, 1510718006: 35505, 1576478898: 50106, 1627845759: 44646, 1642493961: 45636, 1692914062: 45072, 1723223576: 43654, 1738752390: 37081, 1768635078: 44456, 1785790315: 49668, 1817035234: 46967, 1904720832: 48573, 1984049160: 42629, 2105650611: 46895, 2146490422: 48362, 5126831360: 47156, 5133646963: 42521, 5202556843: 43265, 5231780417: 47335, 5246056344: 49375, 5282701558: 48372, 5288907126: 52920, 5289217805: 48240, 5305368469: 50251, 5339762358: 49296, 5378472882: 46259, 5398258926: 47461, 5482685819: 50589, 5493796318: 49333, 5561942434: 48616, 5752626964: 44105, 6055712750: 47922, 6199304130: 46360, 6371303450: 53837}
    text = "Изменения в трофеях у игроков клуба за прошедшую неделю:"
    for id in a.keys():
        user = getUser(id)
        if id in b:
            text += f"\n{user.nickname} - {a[id]}🏆 ({formatedHourDifference(a[id] - b[id])})"
    await bot.send_message(token["chat"], f"<b>{text}</b>", "HTML")
@dp.message_handler(content_types = [ContentType.NEW_CHAT_MEMBERS])
async def newChatMembers(msg: Message):
    if msg.chat.id == token["chat"]:
        user = getUser(msg["new_chat_participant"]["id"])
        if user and user.rightsLevel == 2:
            await bot.promote_chat_member(token["chat"], user.id, can_manage_video_chats = True)
            await bot.set_chat_administrator_custom_title(token["chat"], user.id, emoji.replace_emoji(user.nickname, replace = '').lstrip().rstrip())
            await bot.send_message(token["chat"], lang["join"]["welcomeToTheChat"].format(user.nickname, user.tag), "HTML", reply_to_message_id = msg.message_id)
            user.rightsLevel = 3; user.save()
            await bot.send_message(user, lang["join"]["welcomeText"], "HTML", reply_markup = setKeyboard(user), disable_web_page_preview = True)


@dp.message_handler(content_types=[ContentType.TEXT, ContentType.STICKER])
async def handleMessages(msg: Message):
    if msg.chat.type == "private":
        id = msg.chat.id
        user: User = getUser(id)
        if msg.content_type == "text":
            text = replaceHTML(msg.text)
            if isinstance(user, User): 
                match text:
                    case "/start": 
                        await bot.send_message(user.id, lang["start"]["user"], "HTML", reply_markup = setKeyboard(user))
                        await userLog("start", user.nickname, user.id)
                    case "Отмена❌": 
                        await bot.delete_message(user.id, msg.message_id)
                        user.status = None; user.save() 
                        await bot.send_message(id, lang["commandCanceled"], "HTML", reply_markup = setKeyboard(user))
                        await userLog("cancel command", user.nickname, user.id)
                    case "Вступить в клуб✉️": 
                        await joinTheClub(user)
                    case "Продолжить":
                        await sendApplication(user)
                    case "Информация об игроке👤":
                        await playerInfo(user)
                    case "Редактировать команды✏️": 
                        await editTeams(user)
                    case "Установить часовую разницу🌍":
                        await selectHourDifference(user)
                    case "Предложить сыграть КЛ⚔️":
                        await offerToPlay_Menu(user)
                    case "Командный чат💬":
                        await enterChatMode(user, user.team)
                    case "Завершить разговор🚪":
                        await turnOffСhatMode(user)
                    case "Помощь❓":
                        await help(user)
                    case "Войти в чат👁‍🗨":
                        await startChat(user)
                    case "Сделать объявление📣":
                        await selectTarget(user)
                    case "Частный чат🔐":
                        await enterChatMode(user, user.chatСhannel)
                    case _:
                        if user.status == "playerInfo": 
                            await sendStats(user, text, msg.message_id)
                        elif user.status == "enterQuestion":
                            await sendQuestion(user, text)
                        elif user.status == "selectingTime": 
                            await timeResponse(user, text)
                        elif user.status == "enterChat":
                            await enterChat(user, text)
                        elif user.status == "choosesAnotherTime":
                            await suggestAnotherTime(user, text)
                        elif user.status and user.status[:12] == "announcement":
                            await sendAnAnnouncement(user, msg.text)
                        elif user.status == "teamChat":
                            await msgToChat(user, lang["chat"]["teamChatPrefix"], user.team, text)
                        elif user.status == "chatWithTeam":
                            await msgToChat(user, lang["chat"]["chatWithTeamPrefix"], user.chatСhannel, text)
                        elif user.status == "chatWithUser":
                            await msgToChat(user, lang["chat"]["chatWithUserPrefix"], user.chatСhannel, text)
                        elif text[:4] == "/ban":
                            await banUser(user, text[:4])
                        else:
                            await bot.send_message(user.id, lang["notUnderstood"], "HTML")
                            await userLog("unrecognized text", user.nickname, user.id, data = text)
            else:
                if not BanList.get_or_none(id):
                    if text == "/start": 
                        with open("insruction.png", 'rb') as photo:
                            await bot.send_photo(user, photo, lang["start"]["guest"].format(msg.from_user.first_name), "HTML", reply_markup = ReplyKeyboardRemove())
                        await userLog("start", id)
                    else: 
                        await guestRegistration(user, text, msg.message_id)
                        await userLog("tag", id, data = text)
                else:
                    await bot.send_message(id, lang["ban"]["banned"], "HTML")
        elif msg.content_type == "sticker":
            if isinstance(user, User):
                if user.status == "teamChat": 
                    await stickerToChat(user, lang["chat"]["teamChatPrefix"], user.team, msg.sticker.file_id, msg.sticker.emoji)
                elif user.status == "chatWithTeam":
                    await stickerToChat(user, lang["chat"]["chatWithTeamPrefix"], user.chatСhannel, msg.sticker.file_id, msg.sticker.emoji)
                elif user.status == "chatWithUser":
                    await stickerToChat(user, lang["chat"]["chatWithUserPrefix"], user.chatСhannel, msg.sticker.file_id, msg.sticker.emoji)

@dp.callback_query_handler()
async def handleCallbacks(call: CallbackQuery):
    if (datetime.now() - call.message.date).days <= 1:
        sep = call.data.find("|")
        calltype, data = call.data[:sep], call.data[sep+1:]
        user: User = getUser(call.message.chat.id)
        match calltype:
            case "acceptApplication": await acceptApplication(getUser(int(data)), call.id, call.message.message_id, call.from_user.first_name)
            case "rejectApplication": await rejectApplication(getUser(int(data)), call.id, call.message.message_id, call.from_user.first_name)
            case "help": await enterQuestion(user, call.message.message_id)
            case "selectedHour": await saveHourDifference(user, call.message.message_id, data)
            case "editTeams": await selectTeam(call.message.chat.id, call.message.message_id)
            case "selectedTeam": await choosePlayer(call.message.chat.id, call.message.message_id, int(data))
            case "selectedUser": await userToChange(call.message.chat.id, call.message.message_id, data)
            case "replacementUser": await changeResult(call.message.chat.id, call.message.message_id, data)
            case "timeClick": await timeClick(user, data, call.message.message_id)
            case "rowClick": await rowClick(user, data, call.message.message_id)
            case "saveButton": await saveButton(user, call.message.message_id)
            case "chooseAnotherTime": await chooseAnotherTime(user, call.message.message_id)
            case "backToTheTable": await backToTheTable(user)
            case "offerToPlayNow": await offerToPlayNow(user, call.message.message_id)
            case "acceptOffer": await acceptOffer(user) 
            case "declineOffer": await declineOffer(user)
            case "cancelOffer": await cancelOffer(user, call.message.message_id)
            case "offerTimeToPlay": await offerToPlaySelectTime(user, call.message.message_id)
            case "leaveChat": await leaveChat(user, call.message.message_id)
            case "makeAnAnnouncement": await selectText(user, data, call.message.message_id)
    else:
        await bot.answer_callback_query(call.id, lang["messageIsOutdated"], "HTML")
        await bot.edit_message_text(lang["messageIsOutdated"], call.message.chat.id, call.message.message_id, parse_mode = "HTML")

if __name__ == "__main__":
    print(f"Successfully launched in {folder[:-2]}")
    executor.start_polling(dp, skip_updates = True)