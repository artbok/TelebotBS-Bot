from aiogram import Bot, Dispatcher, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio, os, yaml
from dataRepository import *
from datetime import datetime, timedelta
from client import replaceHTML, calculateTime, makeRequest, log, setKeyboard, genMarkup, PlayerStats, calculateDayCL


folder = (os.getenv("mode") if os.getenv("mode") else "mainMode") + "//"
with open(folder + "tokens.yaml", encoding = "utf-8") as file:
    token = yaml.safe_load(file)
with open("lang.yaml", encoding = "utf-8") as file:
    lang = yaml.safe_load(file)


bot = Bot(token["botToken"])
loggerBot = Bot(token["loggerBotToken"])
dp = Dispatcher(bot)


async def sendTableToTeam(day, n, teamListsMessageId, team: Team):
    members = getTeamMembers(team.n)
    if len(members) == 3: team.t_MinAmount = 6
    elif len(members) == 2: team.t_MinAmount = 2
    else: team.t_MinAmount = 1
    team.t_TimeToPlay = None
    team.save()
    for user in members:
        tUser = getTrackedUser(user.id)
        tUser.n = n; tUser.save()
        createTDict(user.id)
        user.t_Counter = 0; user.save()
        user.t_MessageId = (await bot.send_message(user.id, lang["table"]["send1"].format(day, team.n, teamListsMessageId), "HTML", reply_markup = genMarkup(user))).message_id
        user.save()

async def dayStart():
    await loadGames()
    day = calculateDayCL()
    if day != "третий": n = 2
    else: n = 3
    setValue("dayStatus", "Preparing")
    teamLists = ""
    TDict.truncate_table()
    for team in Team.select():
        members = getTeamMembers(team.n)
        if len(members) != 0:
            teamLists += lang["table"]["team"].format(team.n)
            for user in members:
                teamLists += lang["table"]["teamMember"].format(user.id, user.nickname)
    teamListsMessageId = (await bot.send_message(token["chat"], lang["table"]["teamListsToTheChat"].format(day, teamLists), "HTML")).message_id
    await bot.pin_chat_message(token["chat"], teamListsMessageId)
    setValue("teamListsMessageId", teamListsMessageId)
    for team in Team.select():
        await sendTableToTeam(day, n, teamListsMessageId, team)
    await log("DayStart_Func", "club members")



async def updateTable():
    teamListsMessageId = getValue("teamListsMessageId")
    day = calculateDayCL()
    for user in User.select().where(User.rightsLevel >= 3, User.t_MessageId, User.t_Counter == 0):
        team = getTeam(user.team)
        if team.t_MinAmount == 1:
            user.t_MessageId = (await bot.send_message(user.id, lang["table"]["send2"].format(day, team.n, teamListsMessageId), "HTML", reply_markup = genMarkup(user))).message_id
        else:
            user.t_MessageId = (await bot.send_message(user.id, lang["table"]["send1"].format(day, team.n, teamListsMessageId), "HTML", reply_markup = genMarkup(user))).message_id
        user.t_Counter = 0; user.save()
    await log("Update table", "members")

async def intermediateResult():
    setValue("dayStatus", "CL")
    report = []
    for user in User.select().where(User.rightsLevel >= 3, User.t_MessageId != None):
        report.append(lang["mention"].format(user.id, user.nickname))
    if len(report) != 0:
        await bot.send_message(token["chat"], ", ".join(report) + "\nНа таблицу отвечаем активнее!", "HTML")
        #await botLogging("Chat", "intermediateResult")


async def checkTable():
    setValue("dayStatus", "CL")
    report = ""
    for team in Team.select():
        notAnswered = []
        members = getTeamMembers(team.n)
        for user in members:
            if user.t_MessageId:
                notAnswered.append(user)
                report += lang["table"]["teamMember"].format(user.id, user.nickname)
                await bot.delete_message(user.id, user.t_MessageId)
                await bot.send_message(user.id, lang["table"]["delete"], "HTML")
                user.t_Counter, user.t_MessageId = 0, None; user.save()
                (TDict.delete().where(TDict.userId == user.id)).execute()
        for user in members:
            if user not in notAnswered:
                if len(notAnswered) == 1:
                    await bot.send_message(user.id, lang["table"]["notAnsweredToTeammates1"].format(notAnswered[0].nickname), "HTML", reply_markup = setKeyboard(user))
                elif len(notAnswered) == 2:
                    await bot.send_message(user.id, lang["table"]["notAnsweredToTeammates2"].format(notAnswered[0].nickname, notAnswered[1].nickname), "HTML", reply_markup = setKeyboard(user))

    if report == "": 
        report = lang["table"]["allMembersAnswered"]
    else: 
        report = lang["table"]["listOfNotAnswered"].format(report)
    await bot.send_message(token["adminChat"], report, "HTML")
    await bot.send_message(token["chat"], report, "HTML")
    #await botLogging("Chat & AdminChat", "checkTable_func")


async def remindAboutCL():
    haveNotPlayed = []
    for tUser in TrackedUser.select().where(TrackedUser.n != 0):
        user = getUser(tUser.id)
        haveNotPlayed.append(lang["mention"].format(user.id, user.nickname))
    await bot.send_message(token["chat"], lang["remindAboutCL"].format(", ".join(haveNotPlayed)), "HTML")

async def endOfTheDay():
    setValue("dayStatus", None)

async def offerCancellation(team):
    offer: Offer = getOffer(team)
    members = getTeamMembers(team)
    for user in members:
        if user.o_MessageId:
            await bot.edit_message_text(lang["offerToPlay"]["ignored"].format(user.o_Text), user.id, user.o_MessageId, parse_mode = "HTML")
            user.o_MessageId, user.o_Text = None, None; user.save()
        await bot.send_message(user.id, lang["offerToPlay"]["autoCanceled"], "HTML")
    offer.delete_instance()
    #await botLogging(f"Team №{team}", "offerCancellation")


async def gameReminder(team):
    offer = getOffer(team)
    if offer:
        await offerCancellation(team)
    offer: Offer = Offer.create(type = "Reminder", data = team) 
    time = calculateTime(datetime.now().strftime("%H:%M"), 15)
    addTask(time, "offerCancellation", team)
    markup = InlineKeyboardMarkup(row_width = 2)
    markup.add(InlineKeyboardButton(lang["btn"]["canPlay"], callback_data = "acceptOffer|"), InlineKeyboardButton(lang["btn"]["can'tPlay"], callback_data = "declineOffer|"))
    for user in getTeamMembers(team): 
        user.o_Text = lang["offerToPlay"]["reminder"]["send"]
        user.o_MessageId = (await bot.send_message(user.id, user.o_Text, "HTML", reply_markup = markup)).message_id
        user.save()
    #await botLogging(f"Team №{team}", "gameReminder")

#Главная цикличная функция

async def check():
    time, day, week = datetime.now().strftime("%H:%M"), int(datetime.now().strftime("%w")), bool(int(datetime.now().strftime("%W")) % 2)
    dayStatus = getValue("dayStatus")
    if time == "07:36" and day in [3, 5, 0] and week: await dayStart()        
    elif time == "15:00" and day in [3, 5, 0] and week: await intermediateResult()
    elif time == "16:50" and day in [3, 5, 0] and week: await checkTable()
    elif time[3:] == "00" and dayStatus == "Preparing" and day in [3, 5, 0] and week: await updateTable()
    elif time == "15:00" and ((day in [4, 6] and week) or (day == 1 and not week)): await remindAboutCL()
    elif time == "17:02" and (day in [4, 6] and week) or (day == 1 and not week): await endOfTheDay()  
    for t in getTasks(time):
        match t.action:
            case "advanceReminder":
                if dayStatus == "CL":
                    for user in getTeamMembers(int(t.data)):
                        await bot.send_message(user.id, lang["advanceReminder"], "HTML")
                    #await botLogging(user.id, "Team " + t.data + ": AdvanceReminder") 
                    t.delete_instance()
            case "gameReminder":
                if dayStatus == "CL": 
                    await gameReminder(int(t.data))
                    t.delete_instance()
            case "undoTeamEditing":
                e_Id = getValue("e_Id")
                await bot.edit_message_text(lang["editTeams"]["error3"], e_Id, getValue("e_MessageId"))
                #await botLogging(getUser(e_Id), "undoTeamEditing")
                setValue("e_Id", None); setValue("e_MessageId", None), setValue("e_SelectedTeam", None), setValue("e_SelectedUser", None)
                t.delete_instance()
            case "offerCancellation": 
                await offerCancellation(int(t.data))
                t.delete_instance()
    await trackBattles(dayStatus)
    await asyncio.sleep(60 - datetime.now().second)

#Обработка матчей

async def trackBattles(dayStatus):
    if dayStatus == "CL":
        for tUser in getTrackedUsers():
            url = f"https://api.brawlstars.com/v1/players/%23{tUser.tag}/battlelog"
            data = await makeRequest(url)
            if isinstance(data, dict):
                for game in data["items"]:
                    if game["battleTime"] == tUser.lastGame or tUser.n == 0: 
                        break
                    if "type" in game["battle"] and game["battle"]["type"] == "teamRanked" and "trophyChange" in game["battle"]:
                        clubTrophies = getValue("clubTrophies"); setValue("clubTrophies", clubTrophies + game["battle"]["trophyChange"]) 
                        tUser.n -= 1; tUser.save()
                        if not isItInGameIds(game["battleTime"]):
                            users = set()
                            n = 1
                            for _ in range(2):
                                if len(users) == 0:
                                    n = abs(n-1)
                                    for a in game["battle"]["teams"][n]:
                                        member = User.get_or_none(User.tag == a["tag"][1:], User.rightsLevel >= 2)
                                        if member: 
                                            users.add(member)
                                            tUser2 = getTrackedUser(member.id)
                                            tUser2.dailyTrophies += game["battle"]["trophyChange"]
                                            tUser2.weeklyTrophies += game["battle"]["trophyChange"]
                                            tUser2.totalTrophies += game["battle"]["trophyChange"]
                                            tUser2.save()
                            (GameIds.create(game = game["battleTime"])).save()
                            teamsStructure = ""
                            for j in range(0, 3): 
                                tag = game["battle"]["teams"][n][j]["tag"][1:]
                                tempData = await makeRequest(f"https://api.brawlstars.com/v1/players/%23{tag}")
                                stats = PlayerStats(tempData, "")
                                member = User.get_or_none(User.tag == tag, User.rightsLevel >= 2)
                                if member: 
                                    teamsStructure += lang["matchInfo"]["playerStats"].format("🟦", lang["mention"].format(member.id, replaceHTML(game["battle"]["teams"][n][j]["name"])), lang["brawler"][game["battle"]["teams"][n][j]["brawler"]["name"]], game["battle"]["teams"][n][j]["brawler"]["power"], game["battle"]["teams"][n][j]["tag"], round(stats.trophies/1000, 1), stats.rate)
                                else:
                                    teamsStructure += lang["matchInfo"]["playerStats"].format("🟦", replaceHTML(game["battle"]["teams"][n][j]["name"]), lang["brawler"][game["battle"]["teams"][n][j]["brawler"]["name"]], game["battle"]["teams"][n][j]["brawler"]["power"], game["battle"]["teams"][n][j]["tag"], round(stats.trophies/1000, 1), stats.rate)
                            n = abs(n-1)
                            for j in range(0, 3):
                                tag = game["battle"]["teams"][n][j]["tag"][1:]
                                tempData = await makeRequest(f"https://api.brawlstars.com/v1/players/%23{tag}")
                                stats = PlayerStats(tempData, "")
                                teamsStructure += lang["matchInfo"]["playerStats"].format("🟥", replaceHTML(game["battle"]["teams"][n][j]["name"]), lang["brawler"][game["battle"]["teams"][n][j]["brawler"]["name"]], game["battle"]["teams"][n][j]["brawler"]["power"], game["battle"]["teams"][n][j]["tag"], round(stats.trophies/1000, 1), stats.rate)
                            member = User.get_or_none(User.tag == game["battle"]["starPlayer"]["tag"][1:], User.rightsLevel >= 2)
                            if member:
                                starPlayer = lang["mention"].format(member.id, replaceHTML(game["battle"]["starPlayer"]["name"]))
                            else:
                                starPlayer = replaceHTML(game["battle"]["starPlayer"]["name"])
                            text = lang["matchInfo"]["stats"].format(lang["gameMode"][game["battle"]["result"]], game["battle"]["trophyChange"] * len(users), lang["gameMode"][game["event"]["mode"]], game["event"]["map"], starPlayer, teamsStructure)
                            await bot.send_photo(token["chat"], f"https://cdn-old.brawlify.com/map/{game['event']['id']}.png", text, parse_mode="HTML")
                            #await botLogging(f"Team {getUser(tUser.id).team}", "MatchInfo")
                
                if tUser.lastGame != data["items"][0]["battleTime"]:
                    tUser.lastGame = data["items"][0]["battleTime"]; tUser.save()

async def loadGames():
    for tUser in TrackedUser.select():
        url = f"https://api.brawlstars.com/v1/players/%23{tUser.tag}/battlelog"
        data = await makeRequest(url)
        tUser.lastGame = data["items"][0]["battleTime"]; tUser.save()

if __name__ == "__main__":
    print(f"Successfully launched in {folder[:-2]}")
    while True:
        asyncio.run(check())
