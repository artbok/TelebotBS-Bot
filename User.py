import functools

class User:
    def __init__(self):
        self.j_Status = False
        self.j_Tag = None
        self.j_Nickname = None
        self.j_Text = None

        self.i_Status = False
        self.i_Tag = None
        
    def loadProfile(self, tag, nickname, times, timeZone, team, weekTropheys, totalTropheys):
        self.tag = tag
        self.nickname = nickname
        self.times = times
        self.timeZone = timeZone
        self.team = team
        self.weekTropheys = weekTropheys
        self.totalTropheys = totalTropheys

        self.t_Status = False
        self.t_Dict = {}
        self.t_MessageID = None
        self.t_Counter = 0
    def editteams(self):
        self.e_Status = True
        self.e_selectedTeam = None
        self.e_selectedUser = None
        self.e_replacement = None
@functools.cache
class UserRepository:
    def __init__(self):
        self.userDict = {}
    def load(self, settings):
        for id in settings['userlist']:
            self.stats = settings['user'][id]
            self.userDict[id] = User()
            self.userDict[id].loadProfile(self.stats["Tag"], self.stats["Nickname"], self.stats["TimeForCL"], self.stats["TimeZoneDifference"], self.stats["Team"], self.stats["WeekTropheys"], self.stats["TotalTropheys"])
        return self
    def get(self, id):
        if id in self.userDict:
            return self.userDict[id]
        else:
            self.userDict[id] = User()
            return self.userDict[id]
