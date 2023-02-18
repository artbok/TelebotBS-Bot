import functools
from datetime import datetime

class Guest:
    def __init__(self):
        self.j_Status = False
        self.j_Tag = None
        self.j_Nickname = None
        self.j_Text = None
        self.i_Status = False
#    def updateLastActivity(self):
#        self.lastActivity = datetime.now()
class Member(Guest):
    def __init__(self, tag, nickname, timeZoneDifference, team):   
        super().__init__() 
        self.tag = tag
        self.nickname = nickname
        self.timeZone = timeZoneDifference
        self.team = team

        self.t_SelectedTimes = set()
        self.t_Dict = {}
        self.t_MessageID = None
        self.t_Counter = 0

class Admin(Member):
    def __init__(self, tag, nickname, timeZoneDifference, team):
        super().__init__(tag, nickname, timeZoneDifference, team)
        self.e_Status = True
        self.e_selectedTeam = None
        self.e_selectedUser = None
        self.e_replacement = None

@functools.cache
class UserRepository:
    def __init__(self):
        self.userDict = {}
    def loadProfiles(self, settings, adminlist):
        for id in settings['userlist']:
            self.stats = settings['user'][id]
            if id in adminlist:self.userDict[id] = Admin(self.stats["Tag"], self.stats["Nickname"], self.stats["TimeZoneDifference"], self.stats["Team"])
            else: self.userDict[id] = Member(self.stats["Tag"], self.stats["Nickname"], self.stats["TimeZoneDifference"], self.stats["Team"])
        return self
    def get(self, id):
        if id in self.userDict: return self.userDict[id]
        else:
            self.userDict[id] = Guest()
            return self.userDict[id]
