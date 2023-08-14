from peewee import *
from datetime import datetime
import os
from playhouse import sqliteq

folder = (os.getenv("mode") if os.getenv("mode") else "mainMode") + "//"
db = SqliteDatabase(folder + 'data.db', timeout = 20)


class User(Model):
    id = PrimaryKeyField()
    rightsLevel = IntegerField(default = 0)
    status = CharField(null = True)
    nickname = CharField(null = True)
    tag = CharField(null = True)
    team = IntegerField(default = 0)
    hourDifference = IntegerField(default = 0)
    chatСhannel = AnyField(null = True)
    rep = FloatField(default = 0)
    j_Text = CharField(null = True)
    o_Text = CharField(null = True)
    o_MessageId = IntegerField(null = True)
    t_MessageId = IntegerField(null = True)
    t_Counter = IntegerField(default = 0)
    class Meta:
        database = db
        only_save_dirty = True
Model.save
if not User.table_exists():
    User.create_table()
    print("Table 'User' created")

def getUser(id) -> User:
    user = User.get_or_none(User.id == id)
    if not user: 
        return id
    return user

def getMembers() -> list[User]:
    return list(User.select().where(User.rightsLevel >= 2, User.team > 0))

def getTeamMembers(n) -> list[User]:
    return list(User.select().where(User.team == n))

def getInterlocutors(n) -> list[User]:
    return list(User.select().where((User.chatСhannel == n) | (User.team == n)))

class Team(Model):
    n = PrimaryKeyField()
    t_TimeToPlay = CharField(null = True)
    t_MinAmount = IntegerField(null = True)
    class Meta:
        database = db
        only_save_dirty = True

if not Team.table_exists():
    Team.create_table()
    for i in range(1, 11):
        (Team.create(n = i, t_TimeToPlay = None)).save()
    print("Table 'Team' created")

def getTeam(n) -> Team:
    if n == 0:
        return None
    return Team.get(Team.n == n)


class TDict(Model):
    id = AutoField()
    userId = IntegerField()
    h = IntegerField()
    m = IntegerField()
    selected = BooleanField(default = False)
    class Meta:
        database = db
        only_save_dirty = True

if not TDict.table_exists():
    TDict.create_table()
    print("Table 'TDict' created")

def createTDict(id):
    n = 16
    for h in range(17, 24):
        n += 1
        for m in ["00", "20", "40"]:
            (TDict.create(userId = id, count = n, h = h, m = m)).save()
    n += 7
    for h in range(7, 17):
        n += 1
        for m in ["00", "20", "40"]:
            (TDict.create(userId = id, count = n, h = h, m = m)).save()


class TrackedUser(Model):
    id = PrimaryKeyField()
    tag = CharField()
    lastGame = CharField(null = True)
#    trophies = 
    n = IntegerField(default = 0)
    dailyTrophies = IntegerField(default = 0)
    weeklyTrophies = IntegerField(default = 0)
    totalTrophies = IntegerField(default = 0)
    class Meta:
        database = db
        only_save_dirty = True

if not TrackedUser.table_exists():
    TrackedUser.create_table()
    for user in User.select():
        TrackedUser.create(id = user.id, tag = user.tag)
    print("Table 'TrackedUser' created")

def getTrackedUser(id) -> TrackedUser:
    return TrackedUser.get(TrackedUser.id == id)

def getTrackedUsers() -> list[TrackedUser]:
    return list(TrackedUser.select().where(TrackedUser.n > 0))

def getTrackedMembers(n) -> list[TrackedUser]:
    trackedMembers = []
    for user in getTeamMembers(n):
        trackedMembers.append(getTrackedUser(user.id))
    return trackedMembers

class GameIds(Model):
    id = AutoField()
    game = CharField()
    class Meta:
        database = db
        only_save_dirty = True

if not GameIds.table_exists():
    GameIds.create_table()
    print("Table 'GameIds' created")

def isItInGameIds(game) -> bool:
    return bool(GameIds.get_or_none(GameIds.game == game))


class Tasks(Model):
    id = AutoField()
    time = CharField()
    action = CharField()
    data = CharField(null = True)
    class Meta:
        database = db
        only_save_dirty = True

if not Tasks.table_exists():
    Tasks.create_table()
    print("Table 'Tasks' created")

def getTasks(time) -> list[Tasks]:
    return list(Tasks.select().where(Tasks.time == time))

def addTask(time, action, data):
    task = Tasks.create(time = time, action = action, data=data)
    task.save()


class Variable(Model):
    id = AutoField()
    key = CharField()
    value = AnyField(null = True)
    class Meta:
        database = db
        only_save_dirty = True

if not Variable.table_exists():
    Variable.create_table()
    (Variable.create(key = "dayStatus")).save()
    (Variable.create(key = "e_Id"))
    (Variable.create(key = "e_MessageId")).save()
    (Variable.create(key = "e_SelectedTeam")).save()
    (Variable.create(key = "e_SelectedUser")).save()
    (Variable.create(key = "clubTrophies", value = 0)).save()
    (Variable.create(key = "teamListsMessageId")).save()
    print("Table 'Variable' created")

def getValue(key) -> str:
    return Variable.get(Variable.key == key).value

def setValue(key, value):
    v = Variable.get(Variable.key == key)
    v.value = value
    v.save()


class Blacklist(Model):
    id = PrimaryKeyField()
    date = DateTimeField()
    class Meta:
        database = db
        only_save_dirty = True

if not Blacklist.table_exists():
    Blacklist.create_table()
    print("Table 'Blacklist' created")

def addToBlacklist(id):
    Blacklist.create(id = id, date = datetime.now()).save()

def isItBlacklisted(id) -> bool:
    return bool(Blacklist.get_or_none(Blacklist.id == id))


class Offer(Model):
    id = AutoField()
    type = CharField()
    time = CharField(null = True)
    data = AnyField()
    ownerId = IntegerField(null = True)
    ownerNickname = CharField(null = True)
    class Meta:
        database = db
        only_save_dirty = True

if not Offer.table_exists():
    Offer.create_table()
    print("Table 'Offer' created")

def getOffer(data) -> Offer:
    return Offer.get_or_none(data = data)
    

class Chat(Model):
    id = AutoField()
    type = CharField()
    time = CharField(null = True)
    data = AnyField()
    ownerId = IntegerField(null = True)
    ownerNickname = CharField(null = True)
    class Meta:
        database = db
        only_save_dirty = True

class BanList(Model):
    id = PrimaryKeyField()
    date = DateTimeField()
    reason = CharField()
    class Meta:
        database = db   
        only_save_dirty = True

if not BanList.table_exists():
    BanList.create_table()
    print("Table 'BanList' created")



#Script for updating User DB
#a = {468960807: [1, 'I_KUK', 'LYCR28Q0Q', 0, 0], 503614907: [3, 'tuysia', '9V8VP990L', 5, 0], 518309668: [3, 'adskijdrochila', '2GUJYGU0Y', 3, 0], 587262745: [4, '🔪MESSERN🔪', 'PG28CU9QR', 1, 0], 658551070: [1, 'Bad Boy', 'J9LRJU28', 0, 0], 782053987: [3, '_ĶøŢŁęŤkĄ_', 'GP8P9R08', 4, -1], 824210278: [1, 'MVP | LITVEN', '99VLVC2JG', 0, 3], 885241590: [4, 'Вадим Курседов', '9JYYULPYG', 2, 0], 922572148: [3, 'Tilays�🌆', '9J0L0RRQG', 6, 0], 944737635: [1, '.thaise♡✌🏿|BS', '89RV0LUG0', 0, 0], 950221051: [1, 'Bard & Мусор', 'GR02V0LV', 0, 0], 965991778: [3, 'ʳᵘˢĐø₲₲ɏ♡', 'CR89LJQC', 7, 0], 972222297: [3, 'Ordiks', '28R9PULUC', 8, 0], 980860780: [1, 'KilMiX', '20VVLYQ0U', 0, 0], 1008065939: [1, 'LesМиров', '28G09YRL9', 0, 3], 1064058134: [3, '}{отт@бь)ч', '9LQG00VL0', 2, -1], 1092114234: [1, 'zedest', '2CY00QP9G', 0, 3], 1146720942: [1, 'DarKat', '202V8JP00', 0, 0], 1193654237: [5, 'ㄒ乇爪ﾌ丨Ҝ', 'QQGPVJRP', 1, 0], 1218269633: [1, '[ММА]АКМЕРК', 'P2VP9CGJ0', 0, 0], 1230083523: [3, 'ꜰᴇʟᴅʏ🎺', '880VJ9QR9', 7, 0], 1301076069: [1, 'your..teyzon🦋', 'CGCL2Y02', 0, 0], 1336774916: [1, 'Fishyon', 'PCYC0JRJ0', 0, 0], 1349357882: [4, 'MrGloss15', 'Y998R89UV', 6, 0], 1351862795: [3, '⛈️Đ₳Ɽ₭ ₲ⱧØ₴₮🥀', 'VV8UY09R', 2, 2], 1445041950: [3, 'ʟᴀʟᴀ♡ᴘᴏᴘ', '2JCCJUPL2', 3, 2], 1446851981: [1, 'NEVER MIND', 'PVYU0CCGL', 0, 0], 1510718006: [1, 'NaVi | Legend ©', 'LVVVG0U9J', 0, 0], 1576478898: [1, 'QK|Kenleety최고', 'YJVGGJYYP', 0, 0], 1623274967: [1, '☄GG|Xfire🔥', 'YVGP8RP', 0, 0], 1627845759: [4, '_Prosto_Angel_', '80928892L2', 6, 0], 1642493961: [3, 'Maria', 'PQQG9C88', 4, 0], 1692914062: [4, 'snyusoed', 'PQQ28YRYC', 1, 0], 1723223576: [1, '_]LP[mr макс06_', '28PRV8UVY', 0, 0], 1738752390: [1, '🖤GX|Карась♂️', 'P2CQUP28', 0, 0], 17768398554: [1, '▪️♧@[$niper]♧▪️', '8UYGUUJVG', 0, 0], 1785790315: [1, 'L1e', '899CGVYGV', 0, 3], 1984049160: [1, 'gg', 'PQL028UQY', 0, 0], 2105650611: [3, 'читер777', 'P8GUGQCJ0', 7, 0], 2146490422: [3, '💲₥Ɽ. Ӿ🕶💲', 'YYUP9RVQJ', 3, 1], 5032866463: [1, 'HWA|ze®o🤞', '282JP99YQ', 0, 0], 5126831360: [1, "ʟᴜxᴜʀʏ'ss🧸", 'YV2LU0JCQ', 0, 0], 5133646963: [1, 'Рокдок', '8J8JUQ8GC', 0, 0], 5202556843: [1, 'DOШIK|YT', '9PJUR2QQP', 0, 0], 5215019520: [3, '⛩(Art64)⛩', '2LP28290G', 0, 0], 5244595406: [1, 'Ko6en 2', '89PL9889P', 0, 0], 5246056344: [3, 'BossKryt', 'P0LPP0L92', 8, 2], 5282701558: [1, 'ЧИТЕР777', 'Q0R0UQUJ', 0, -1], 5288907126: [1, 'TT🥀shark🥀', '80VGC0RY9', 0, 0], 5289217805: [1, 'NikAlroy', '2L980GQG8', 0, 0], 5305368469: [3, 'MakarGO21', '20L0PCJUG', 5, 0], 5320642593: [1, '$¥₽€® $T€₽k@', 'YQJ8LGG20', 0, 0], 5339762358: [1, '👉👉Андрей👈👈', 'PGVGJ9V0J', 0, 4], 5378472882: [1, 'Мочкун', 'Q2LCQU0LQ', 0, 3], 5398258926: [3, 'леон', '2JVR0G2QJ', 9, 2], 5470107567: [3, 'Volt Aloy', '2PL98VPLL', 9, -1], 5493796318: [3, '✨scromnik🌙', 'PRVC9R9UR', 5, 5], 5636142368: [1, '🍀[UU]ULUKASHI', 'LC9LJ0R2L', 0, 0], 5752626964: [3, 'Jle4eHbKaAa205', '8QULQ9PUR', 8, 0], 6048854567: [1, 'Netiko', 'P99ULYU82', 0, 0], 6055712750: [3, '👑Ķinğ Ĺèòñ👑™️', '9J0JGG9UGR', 4, 0], 6371303450: [1, 'blaffix🧸', 'P2VQ9QQJL', 0, 2]}
# for user in User.select():
#     user: User = user
#     a[user.id] = [user.rightsLevel, user.nickname, user.tag, user.team, user.hourDifference]
# print(a)
# exit()

# User.create_table()
# for id in a.keys():
#     user = User.create(id=id, rightsLevel = a[id][0], nickname=a[id][1], tag=a[id][2], team=a[id][3], hourDifference=a[id][4])
#     user.save()
