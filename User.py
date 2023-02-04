import functools

class User:
    def __init__(self):
        self.j_Status = False
        self.j_Tag = None
        self.j_Nickname = None
        self.j_Text = None
        self.i_Status = False
        
    def loadProfile(self, tag, nickname, timeZoneDifference, team):
        self.tag = tag
        self.nickname = nickname
        self.timeZone = timeZoneDifference
        self.team = team

        self.t_SelectedTimes = set()
        self.t_GameByInvitation = False
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
            self.userDict[id].loadProfile(self.stats["Tag"], self.stats["Nickname"], self.stats["TimeZoneDifference"], self.stats["Team"])
        return self
    def get(self, id):
        if id in self.userDict:
            return self.userDict[id]
        else:
            self.userDict[id] = User()
            return self.userDict[id]
