import requests
import yaml
import json
import telebot
from datetime import datetime
import threading
import random
from telebot import types

bot = telebot.TeleBot('5691240434:AAFOPOmDXh0VUt7gWmMCnpYKGJA8fylYM5c')
tasks = {}
adminchat = -881222268
chat = -881222268
AuthKey = 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6ImMzZGNhMDI0LTE1OWItNDQzNy1hYzgxLWJkYjJmYWFmMzQzMyIsImlhdCI6MTY2NTIwMzQ3Niwic3ViIjoiZGV2ZWxvcGVyLzI1ZDlkYWJjLTk4ZmItOGE2NS1mNDNhLWYxMzdmOTU4MjRmNCIsInNjb3BlcyI6WyJicmF3bHN0YXJzIl0sImxpbWl0cyI6W3sidGllciI6ImRldmVsb3Blci9zaWx2ZXIiLCJ0eXBlIjoidGhyb3R0bGluZyJ9LHsiY2lkcnMiOlsiOTUuMTY1LjEwLjIxMCJdLCJ0eXBlIjoiY2xpZW50In1dfQ.66RoyIwYFhIYTrhWQ7YUWQxei0jRVB4djJ0MlE1s7rImpOKWLS-9P9euTi3RBtPlFA0wKsrDhuJ-yBrHx8rPpA'

with open('lang.yaml', 'r', encoding='utf-8') as file:
    brawlers = yaml.safe_load(file)
with open('config.yaml', 'r', encoding='utf-8') as file:
    settings = yaml.safe_load(file)
with open('teams.yaml', 'r', encoding='utf-8') as file:
    teams = yaml.safe_load(file)
#print(settings)

def Check():
    #threading.Timer(60, Check).start()
    date = datetime.now()
    if date.strftime('%a/%H:%M') == 'Wed/11:00' and int(date.strftime('%W')) % 2 == 1:
        for id in settings['userlist']:
            tasks[id] = ['SetTime', {'17': ['17:00', '17:20', '17:40'], '18': ['18:00', '18:20', '18:40'], '19': ['19:00', '19:20', '19:40'], '20': ['20:00', '20:20', '20:40'], '21': ['21:00', '21:20', '21:40'], '22': ['22:00', '22:20', '22:40'], '23': ['23:00', '23:20', '23:40'], '08': ['08:00', '08:20', '08:40'], '09': ['09:00', '09:20', '09:40'], '10': ['10:00', '10:20', '10:40'], '11': ['11:00', '11:20', '11:40'], '12': ['12:00', '12:20', '12:40'], '13': ['13:00', '13:20', '13:40'], '14': ['14:00', '14:20', '14:40'], '15': ['15:00', '15:20', '15:40'], '16': ['16:00', '16:20', '16:40']}] 
            markup = types.InlineKeyboardMarkup(row_width=3)
            for i in tasks[id][1].keys():
                markup.add(types.InlineKeyboardButton(tasks[id][1][str(i)][0], callback_data='4' + str(i)+':00'), types.InlineKeyboardButton(tasks[id][1][str(i)][1], callback_data='4' + str(i)+':20'), types.InlineKeyboardButton(tasks[id][1][str(i)][2], callback_data='4' + str(i)+':40'))
    print(bot.send_message(-881222268, 'День 1 начнётся уже через 6 часов! Пожалуйста выберите ВСЕ времена, в которые вы будете свободны для клановой лиги.'))
    if date.strftime('%a/%H:%M') == 'Thu/17:00' and int(date.strftime('%W')) % 2 == 1:
        print("День 1 закончился")
    if date.strftime('%a/%H:%M') == 'Fri/11:00' and int(date.strftime('%W')) % 2 == 1:  
        print('День 2')
    elif date.strftime('%a/%H:%M') == 'Sun/11:00' and int(date.strftime('%W')) % 2 == 1: 
        print('День 3') 
Check()

def CheckMessage(message):
    id = message.chat.id
    if id != adminchat and id != chat:
        if not message.from_user.username:
            bot.send_message(id, 'Вы отвязали публичное имя! Ожидайте, скоро за вами придёт смерть')
            bot.send_message(adminchat, 'Пользователь ' + message.from_user.first_name + ' отвязал публичное имя! Необходим срочный расстрел.')
            return 0
        else:
            return 1
    else:
        bot.send_message(id, 'В этом чате команды запрещены.')
        return 0

def FindCommonTime(team, id):
    times = []
    players = []
    for id in teams[team]["users"]:
        if id != "Не назначено":
            if not settings["user"][id]["TimeForCL"]:

                return 'Спасибо что выбрали времена. Теперь ожидайте пока ваши тимейты также ответят на этот вопрос.'
            else:
                players.append(settings["user"][id]["TimeForCL"])
    if len(players) == 2:
        times = list(set(players[0]) & set(players[1]))
    else:
        times = list(set(players[0]) & set(players[1]) & set(players[2]))
    times = random.choice(times)
    return "Общее время это: " + times
@bot.message_handler(commands=['start'])
def start(message):
    id = message.chat.id
    if id != adminchat and id != chat:
        if message.from_user.username:
            if id not in settings['userlist']:
                tasks[id] = ['JoiningTheClub']
                bot.send_message(id, 'Привет, ' + message.from_user.first_name + '! Для вступления в наш прекрасный клуб, пожалуйста отправь свой ID из игры.')
            else:
                bot.send_message(id, 'Вы уже есть в клубе!')
        else:
            bot.send_message(id, 'Привет, ' + message.from_user.first_name + '! Перед вступлением в клуб пожалуйста создайте публичное имя пользователя (Настройки --> Изменить профиль --> @Выбрать имя пользователя).')
    else:
        bot.send_message(id, 'В данном чате команды недоступны')

@bot.message_handler(commands=['playerinfo'])
def PlayerInfo(message):
    id = message.chat.id
    if CheckMessage(message) == 1:
        bot.send_message(id, 'Отправьте ID игрока, которого вы хотите проверить.')
        tasks[id] = ['GetPlayerInfo']
        
def GetUserStats(text):
    if text[0] == '#':
        text = text[1:]
    url = 'https://api.brawlstars.com/v1/players/%23' + text
    r = requests.get(url, headers={'Authorization': AuthKey})
    if r.status_code != 200:
        text = 'Игрок под данным ID не найден. Проверьте правильность написания и повторите попытку.'
    else:
        data = json.loads(r.text)
        text = '🔸 Ник: *' + data['name'] + '*\n🔸 ID: `' + data['tag'] + '`\n🔸 Трофеи: *' + str(data['trophies']) + '*\n🔸 Уровень опыта: *' + str(data['expLevel'])
        if data['club']:
            text += '*\n🔸 Клуб: *' + data['club']['name']
        else:
            text += '*\n🔸 Клуб: *Отсутсвует'
        text += '*\n🔸 Побед в трио: *' + str(data['3vs3Victories']) + '*\n🔸 Побед в соло: *' + str(data['soloVictories']) + '*\n🔸 Побед в дуо: *' + str(data['duoVictories']) + '*\n🔸 Бойцы на 11 силе: '
        BrawlersAt11Lvl = 0
        BrawlersAt10Lvl = 0
        for i in range(len(data['brawlers'])):
            if data['brawlers'][i]['power'] == 11:
                text += '*' + brawlers[data['brawlers'][i]['name']] + '* | '
                BrawlersAt11Lvl += 1
            elif data['brawlers'][i]['power'] == 10:
                BrawlersAt10Lvl += 1
        text = text[:len(text)-2] + '\n🔸 Всего 11-ых уровней: *' + str(BrawlersAt11Lvl) + '*\n🔸 Всего 10-ых уровней: *' + str(BrawlersAt10Lvl) + '*'
    return text

@bot.message_handler(commands=['editteams'])
def EditTeams(message):
    id = message.chat.id
    print(id)
    if id != adminchat:
        tasks[id] = ['EditTeams']
        markup = types.InlineKeyboardMarkup(row_width=2)
        text = '*Какую команду вы хотите изменить?*\n\n*Текущие команды:*'
        for i in range(1, 11):
            text += '\n*Команда ' + str(i) + ':* ' + ("Не назначено" if str(teams['Team' + str(i)]['users'][0]) == "Не назначено" else settings["user"][teams['Team' + str(i)]['users'][0]]["Name"]) + ', ' + ("Не назначено" if str(teams['Team' + str(i)]['users'][1]) == "Не назначено" else settings["user"][teams['Team' + str(i)]['users'][1]]["Name"]) + ', ' + ("Не назначено" if str(teams['Team' + str(i)]['users'][2]) == "Не назначено" else settings["user"][teams['Team' + str(i)]['users'][2]]["Name"]) + '. '
        for i in range(1, 11, 2):
            markup.add(types.InlineKeyboardButton('Команда ' + str(i), callback_data='1' + 'Team' + str(i)), types.InlineKeyboardButton('Команда ' + str(i+1), callback_data='1' + 'Team' + str(i)))
        bot.send_message(id, text, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['settime'])
def SetTime(message):
    id = message.chat.id
    tasks[id] = ['SetTime', {'17': ['17:00', '17:20', '17:40'], '18': ['18:00', '18:20', '18:40'], '19': ['19:00', '19:20', '19:40'], '20': ['20:00', '20:20', '20:40'], '21': ['21:00', '21:20', '21:40'], '22': ['22:00', '22:20', '22:40'], '23': ['23:00', '23:20', '23:40'], '08': ['08:00', '08:20', '08:40'], '09': ['09:00', '09:20', '09:40'], '10': ['10:00', '10:20', '10:40'], '11': ['11:00', '11:20', '11:40'], '12': ['12:00', '12:20', '12:40'], '13': ['13:00', '13:20', '13:40'], '14': ['14:00', '14:20', '14:40'], '15': ['15:00', '15:20', '15:40'], '16': ['16:00', '16:20', '16:40']}] 
    markup = types.InlineKeyboardMarkup(row_width=3)
    for i in tasks[id][1].keys():
        markup.add(types.InlineKeyboardButton(tasks[id][1][str(i)][0], callback_data='4' + str(i)+':00'), types.InlineKeyboardButton(tasks[id][1][str(i)][1], callback_data='4' + str(i)+':20'), types.InlineKeyboardButton(tasks[id][1][str(i)][2], callback_data='4' + str(i)+':40'))
    bot.send_message(id, 'Пожалуйста выбери времена, когда ты сможешь отыграть клановую лигу?', reply_markup=markup)

@bot.message_handler(content_types=['text'])
def HandleText(message):
    id = message.chat.id
    tag = message.text.upper()
    if CheckMessage(message) == 1:
        if id in tasks:
            if tasks[id][0] == 'JoiningTheClub':
                text = GetUserStats(tag)
                if text[0] != 'И':
                    tasks[id] = ['WaitingForResults', message.from_user.first_name, message.from_user.username, tag, text]
                    markup = types.InlineKeyboardMarkup(row_width=2)
                    btn1 = types.InlineKeyboardButton(' ПРИНЯТЬ ', callback_data='+' + str(id))
                    btn2 = types.InlineKeyboardButton(' ОТКЛОНИТЬ ', callback_data='-' + str(id))
                    markup.add(btn1, btn2)
                    bot.send_message(id, 'Ваша заявка была отправлена на рассмотрение. Ожидайте результатов')
                    bot.send_message(adminchat, '*Заявка на вступление:*\n🔸 Пользователь: @' + message.from_user.username + '\n' + text, parse_mode='Markdown', reply_markup=markup)
                else:
                    bot.send_message(id, text)
            elif message.chat.id != adminchat and tasks[id][0] == 'GetPlayerInfo':
                text = GetUserStats(text)
                if text[0] != 'И':
                    bot.send_message(id, '*Инфомация об этом игроке:*\n' + text, parse_mode='Markdown')
                    del tasks[id]
                else:
                    bot.send_message(id, text)
            else:
                bot.send_message(id, 'Простите, но я вас не понимаю☹️')

@bot.callback_query_handler(func=lambda callback: callback.data[0] == '+' or callback.data[0] == '-')
def callback1(call): #Кнопки Принять и Отклонить
    id = int(call.data[1:])
    if call.data[0] == '+':
        bot.answer_callback_query(call.id, text='Заявка принята')
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='*Заявка на вступление:*\n' + str(tasks[id][4]) +'\n*Принято пользователем ' + call.from_user.first_name + '*', parse_mode='Markdown')
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton(' Клуб ', url='https://link.brawlstars.com/invite/band/ru?tag=28U82UGGV&token=2rfhzttd')
        btn2 = types.InlineKeyboardButton(' Беседа клуба ', url='https://t.me/+89YGgnypEvRhZWFi')
        markup.add(btn1, btn2)
        bot.send_message(id, 'Ваша заявка была *принята*! Добро пожаловать в наш уютный клуб.\n', reply_markup=markup, parse_mode='Markdown')
        settings['userlist'].append(id)
        settings['user'][id] = {'Name': tasks[id][1], 'Username':  tasks[id][2], 'Tag': tasks[id][3], 'TimeForCL': [], 'ClubTrophies': 0, 'Team': 1}
        with open('config.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(settings, f, sort_keys=False, allow_unicode=True)
        del tasks[id]
    elif call.data[0] == '-':
        bot.answer_callback_query(call.id, text='Заявка отклонена')
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='*Заявка на вступление:*\n' + str(tasks[id][4]) +'\n*Отклонено пользователем ' + call.from_user.first_name + '*', parse_mode='Markdown')
        bot.send_message(id, 'Ваша заявка была *отклонена*.', parse_mode='Markdown')
        del tasks[id]
        
@bot.callback_query_handler(func=lambda callback: callback.data[0] == '1')
def callback2(call): #Выбор игрока команды
    id = call.message.chat.id
    team = call.data[1:]
    tasks[id].append(team)
    markup = types.InlineKeyboardMarkup(row_width=3)
    for i in range(3):
        if teams[team]['users'][i] != "Не назначено":
            markup.add(types.InlineKeyboardButton(settings["user"][teams[team]['users'][i]]["Name"], callback_data='2' + str(i)))
        else:
            markup.add(types.InlineKeyboardButton("Не назначено", callback_data='2' + str(i)))
    bot.edit_message_text(chat_id=id, message_id=call.message.message_id, text='Кого из пользователей вы хотите изменить?', reply_markup=markup)
    
@bot.callback_query_handler(func=lambda callback: callback.data[0] == '2')
def callback3(call): #замена игрока
    id = call.message.chat.id
    team = tasks[id][1]
    player = int(call.data[1:])
    n = len(settings['userlist'])
    tasks[id] = ['ChangeUser', team, player]
    markup = types.InlineKeyboardMarkup(row_width=3)
    if n >= 3:
        for i in range(0, (n - n % 3), 3):
            markup.add(types.InlineKeyboardButton(settings["user"][settings['userlist'][i]]["Name"], callback_data='3' + str(settings['userlist'][i])), types.InlineKeyboardButton(settings["user"][settings['userlist'][i+1]]["Name"], callback_data='3' + str(settings['userlist'][i+1])), types.InlineKeyboardButton(settings["user"][settings['userlist'][i+2]]["Name"], callback_data='3' + str(settings['userlist'][i+2])))
    if n % 3 == 2:
        markup.add(types.InlineKeyboardButton(settings["user"][settings['userlist'][n-2]]["Name"], callback_data='3' + str(settings['userlist'][n-2])), types.InlineKeyboardButton(settings["user"][settings['userlist'][n-1]]["Name"], callback_data='3' + str(settings['userlist'][n-1])), types.InlineKeyboardButton('Не назначено', callback_data='3' + 'Не назначено'))
    elif n % 3 == 1:
        markup.add(types.InlineKeyboardButton(settings['user'][settings['userlist'][n-1]]['Name'], callback_data='3' + str(settings['userlist'][n-1])), types.InlineKeyboardButton('Не назначено', callback_data='3' + 'Не назначено'))    
    bot.edit_message_text(chat_id=id, message_id=call.message.message_id, text='На кого вы хотите заменить пользователя ' + str(teams[team]['users'][player]) + '?', reply_markup=markup)

@bot.callback_query_handler(func=lambda callback: callback.data[0] == '3')
def callback4(call): #результат замены
    id = call.message.chat.id
    replacement = int(call.data[1:])
    print(teams[tasks[id][1]]['users'][tasks[id][2]])
    print(settings["user"][replacement]["Name"])
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Пользователь ' + str(teams[tasks[id][1]]['users'][tasks[id][2]])  + ' заменен на ' + settings["user"][replacement]["Name"])
    teams[tasks[id][1]]['users'][tasks[id][2]] = replacement
    with open('teams.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(teams, f, sort_keys=False, allow_unicode=True)
    del tasks[id]
@bot.callback_query_handler(func=lambda callback: callback.data[0] == '4')
def callback5(call): 
    id = call.message.chat.id
    markup = types.InlineKeyboardMarkup(row_width=3)
    time = call.data[1:]
    if time[3:] == '00': 
        if tasks[id][1][time[:2]][0][0] != '✅':
            tasks[id][1][time[:2]][0] = '✅' + tasks[id][1][time[:2]][0]
        else:
            tasks[id][1][time[:2]][0] = tasks[id][1][time[:2]][0][1:]
    elif time[3:] == '20': 
        if tasks[id][1][time[:2]][1][0] != '✅':
            tasks[id][1][time[:2]][1] = '✅' + tasks[id][1][time[:2]][1]
        else:
            tasks[id][1][time[:2]][1] = tasks[id][1][time[:2]][1][1:]
    else: 
        if tasks[id][1][time[:2]][2][0] != '✅':
            tasks[id][1][time[:2]][2] = '✅' + tasks[id][1][time[:2]][2]
        else:
            tasks[id][1][time[:2]][2] = tasks[id][1][time[:2]][2][1:]
    for i in tasks[id][1].keys():
        markup.add(types.InlineKeyboardButton(tasks[id][1][str(i)][0], callback_data='4' + str(i)+':00'), types.InlineKeyboardButton(tasks[id][1][str(i)][1], callback_data='4' + str(i)+':20'), types.InlineKeyboardButton(tasks[id][1][str(i)][2], callback_data='4' + str(i)+':40'))
    markup.add(types.InlineKeyboardButton('СОХРАНИТЬ', callback_data='5'))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Пожалуйста выбери времена, когда ты сможешь отыграть клановую лигу?', reply_markup=markup)
@bot.callback_query_handler(func=lambda callback: callback.data[0] == '5')
def callback6(call): 
    for i in tasks[call.message.chat.id][1].keys():
        for j in range(3):
            if tasks[call.message.chat.id][1][str(i)][j][0] == '✅':
                settings["user"][call.message.chat.id]["TimeForCL"].append(str(tasks[call.message.chat.id][1][str(i)][j][1:]))
    if len(settings["user"][call.message.chat.id]["TimeForCL"]) == 5:
        bot.answer_callback_query(call.id, text='Вы должны выбрать как минимум 5 времен!')
    with open('config.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(settings, f, sort_keys=False, allow_unicode=True)
    text = FindCommonTime("Team" + str(settings["user"][call.message.chat.id]["Team"]), call.message.chat.id)
    if text[0] == "С":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text)
    else:
        for i in teams["Team" + str(settings["user"][call.message.chat.id]["Team"])]["users"]:
            if i != "Не назначено":
                bot.send_message(i, "Все пользователи выбрали времена. " + text)
bot.infinity_polling()