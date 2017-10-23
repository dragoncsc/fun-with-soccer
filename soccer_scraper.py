
# coding: utf-8

# In[2]:


import praw
import re
import itertools, collections

# Helper functions
def get_date(submission):
    time = submission.created
    return datetime.datetime.fromtimestamp(time)
def consume(iterator, n):
    collections.deque(itertools.islice(iterator, n))

class Team():
    def __init__(self, name):
        self.name = name
        self.scorers = None
        self.bench = None
        self.startingPlayers = None
        self.substitutions = None
        
class Match():
    def __init__(self, name, league):
        self.name = name
        self.home = None
        self.away = None
        self.league = league
        self.score = None

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class InputError(Error):
    """Exception raised for errors in the input.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """

    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


# start up reddit api        
reddit = praw.Reddit(client_id='BRLTrt5qDT0jyg',
                     client_secret='XzaAHKen1Jww91jR3nBGwg-G4Mo',
                     user_agent='my user agent')

tmp = reddit.subreddit('soccer')


# In[62]:


def get_regex_matches(regex, source_text):
    assert(isinstance(regex, (str, unicode)) and isinstance(source_text, (str, unicode)))
    rg = re.compile(regex, re.UNICODE)
    matches = rg.findall(source_text)
    if len(matches) == 1:
        return matches[0]
    elif len(matches) == 0:
        return None
    else:
        return matches

def sub_text(to_sub, replace, text):
    regex = re.compile(to_sub, re.IGNORECASE)
    return re.sub(regex, replace, text)



def clean_league(raw_league):
    if "Europa" in raw_league:
        return "Europa League"
    if "UCL" in raw_league or ("Champions" in raw_league and "League" in raw_league):
        return "Champions League"
    return raw_league



def get_game_minute(time):
    if isinstance(get_regex_matches('\+', time), (str, unicode)):
        times = get_regex_matches( "\d+", time )
        print times
        return int(times[0]) + int(times[1])
    return int(get_regex_matches( "\d+", time ))

def get_scorers(line, team):
    line = line.encode('ascii', errors='ignore')
    line = line.split(':')[1]
    _raw = line.split("),")
    scorers ={}
    for goal in _raw:
        player = goal.split("(")[0].strip()
        times = get_regex_matches("(\d+'(\+\d+')?)", goal)
        goal_time = []
        if isinstance(times, list):
            for i in times:
                goal_time.append(get_game_minute(i[0]))
        else:
            goal_time.append(get_game_minute(times[0]))
        scorers[player] = goal_time
    team.scorers = scorers
    
def scorers(threadIter, curMatch, team):
    _l = threadIter.next()
    while team.name not in _l: _l = threadIter.next()
    isHome = get_regex_matches(team.name, _l)
    if not isinstance(isHome, (str, unicode)):
        raise InputError(_l, "This was not the home team")
    get_scorers(_l, team)


# In[84]:


def get_venue(lines, curMatch):
    for i in lines:
        if "venue" in i.lower():
            curMatch.venue= i.split("**")[2].strip()

def parse_lineup(threadIter, team):
    lineUp = threadIter.next()
    lineUp = sub_text("(\(\[\]\(#(\w)+-(\w|\d)+\)(\w+ ?)+\))", "", lineUp)
    lineUp = [player.strip() for player in lineUp.split(",")]
    team.startingPlayers = lineUp
    team.startingPlayers[-1] = team.startingPlayers[-1][:-1]
    for _l in threadIter:
        if "Subs" in _l:
            _l = _l.split("**")[2][:-1]
            team.substitutions = [player.strip() for player in _l.split(",")]
            break

def get_lineups(threadIter, curMatch, homeTeam, awayTeam):
    scraped = False
    for line in threadIter:
        if "line-ups" in line.lower() or "line ups" in line.lower():
            for _l in threadIter:
                if homeTeam.name.lower() in _l.lower():
                    parse_lineup(threadIter, homeTeam)
                if awayTeam.name.lower() in _l.lower():
                    parse_lineup(threadIter, awayTeam)
                if isinstance(awayTeam.startingPlayers, list) and isinstance(awayTeam.startingPlayers, list):
                    scraped = True
                    break
        if scraped:
            break


def goal_event(line):
    minute = int(get_regex_matches("\d+", get_regex_matches("\*\*\d+'\*\*", line)))
    country = get_regex_matches("\(\w+\)", line)[1:-1]
    scorer = get_regex_matches(". \(", line)[2:-2]
    if "Assisted by" in line:
        assist = re.search("Assisted by(.*)\.\*\*", line).group(1).strip()
        return ("goal", (country, minute, (scorer, assist)))
    return ("goal", (country, minute, (scorer, None)))


def ycard_event(line):
    minute = int(get_regex_matches("\d+", get_regex_matches("\*\*\d+'\*\*", line)))
    country = get_regex_matches("\(\w+\)", line)[1:-1]
    scorer = get_regex_matches("\) \w+ \(", line)[2:-2]]
    return ("yellow card", (country, minute, (scorer, None)))


def rcard_event(line):
    minute = int(get_regex_matches("\d+", get_regex_matches("\*\*\d+'\*\*", line)))
    country = get_regex_matches("\(\w+\)", line)[1:-1]
    scorer = get_regex_matches("\) \w+ \(", line)[2:-2]
    return ("red card", (country, minute, (scorer, None)))

    
def sub_event(line):
    pass

def get_type(line):
    events = {"#icon-ball":goal_event, "#icon-yellow":ycard_event, 
              "#icon-red":rcard_event, "#icon-sub":sub_event}
    for event in events:
        _e = get_regex_matches(event, line)
        if _e:
            return events[_e]

def grab_match_events(threadIter, curMatch):
    _events = { "goal":[], "yellow card":[], "red card":[], "sub":[] }
    for _l in threadIter:
        event = get_regex_matches("\d+'")
        if event:
            event_t = get_type(_l)(_l)
            _events[event_t[0]] = event_t[1]


# In[88]:


for i in tmp.search(('flair:match+thread AND NOT ' 
                     'flair:post AND NOT flair:pre'),
                   sort="new", time_filter="week", 
                   limit=20):

    if i.author.name == "MatchThreadder":
        #print i.selftext.encode('ascii', errors='ignore')
        lines = i.selftext.encode('ascii', errors='ignore').split('\n')
        for j in lines:
            print j
        threadIter = iter(lines)
        firstLine = threadIter.next()
        teams = get_regex_matches(": .+ \[", i.title)
        teams = [team.encode('ascii', errors='ignore').strip() 
                 for team in (teams[2:-2].split("vs"))]
        homeTeam = Team(teams[0])
        awayTeam = Team(teams[1])
        league = clean_league(get_regex_matches("\[.+\]",
                                                i.title)[1:-1])
        curMatch = Match(i.title, league)
        team_icons = get_regex_matches("\[\]\(#sprite\d+-p\d+\)",
                                       firstLine)
        curMatch.score = get_regex_matches("\[\d+-\d+\]", firstLine)[1:-1]
        print curMatch.score
        if curMatch.score.split("-")[0] != "0":
            scorers(threadIter, curMatch, homeTeam)
        if curMatch.score.split("-")[1] != "0":
            scorers(threadIter, curMatch, awayTeam)
        get_venue(threadIter, curMatch)
        get_lineups(threadIter, curMatch, homeTeam, awayTeam)
        #grab_match_events(threadIter, curMatch)
        print "Hi!"
        break


# In[237]:


# test cases:
get_lineups(iter(("[](#icon-notes-big) **LINE-UPS**"+"\n"+"**[](#sprite2-p229) Tigre**"+"\n"+
           "Federico Crivelli, Gastn Bojanich, Alexis Niz, Mathias Abero, Maximiliano Caire, Renzo Spinacci, Lucas Menossi, Jacobo Mansilla ([](#icon-sub)Javier Iritier), Daniel Imperiale ([](#icon-sub)Carlos Luna), Lucas Janson ([](#icon-sub)Esteban Giambuzzi), Denis Stracqualursi."+
          "\n**Subs:** Hamilton Pereira, Julio Cesar Chiarini, Matas Prez Garca, Ivo Hongn."+"\n"+"____________________________"+'\n'+
          "**[](#sprite1-p110) River Plate**"+"\n"+"Germn Lux, Javier Pinola, Jonatan Maidana, Milton Casco ([](#icon-sub)Marcelo Saracchi), Jorge Moreira, Ignacio Fernndez ([](#icon-sub)Nicols De La Cruz), Enzo Prez, Leonardo Ponzio, Ignacio Scocco, Gonzalo Martinez, Carlos Auzqui ([](#icon-sub)Ariel Rojas)."+
          "\n"+"**Subs:** Augusto Batalla, Rafael Santos Borr, Ivn Rossi, Gonzalo Montiel.").split('\n')), 
            Match('asd', 'asd'), Team('Tigre'), Team('River Plate')) 




