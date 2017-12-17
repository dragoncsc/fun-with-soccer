# -*- coding: utf-8 -*-
import urllib2 
from espn_match_event_parser import ESPNMatchEventParser, get_regex_matches, sub_text
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import os, errno
from random import randint
from time import sleep
import couchdb
from couchdb.design import ViewDefinition
from collections import defaultdict


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


class Parser():
    
    def __init__(self, scrape_only=False):
        self.scrape_only = scrape_only
        self.num_failed_games = 0
        self.espnParser = ESPNMatchEventParser()
        user_agent = ("Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US;"
                              " rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7")
        self.headers = {'User-Agent': user_agent}
        self.db = couchdb.Server()
        try:
            self.recorded_games = self.db["recordedgames"]
        except:
            self.recorded_games = self.db.create("recordedgames")
        self.wantedLeagues = {"World Cup Qualifying - UEFA", "World Cup Qualifying - CONMEBOL", 
            "English Premier League", "German Bundesliga", "UEFA Europa League",
            "UEFA Champions League", "Spanish Primera Division", "FIFA World Cup", 
            "Italian Serie A", "French Ligue 1", u"Spanish Primera División",
            "UEFA Champions League"}
        self.seen_games = '''function(doc) { if (doc.date){emit(doc.date, doc);} }'''
        self.homeView = ViewDefinition( "games", "teams", self.seen_games )
        self.homeView.sync(self.recorded_games)

    def run(self, date):
        get_date_games( datetime.today(), datetime.strptime(date, "%Y%m     %d") )

    def get_date_games(self, startDate, endDate):
        user_agent = ("Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US;"
                              " rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7")
        headers = {'User-Agent': user_agent}
        _date = startDate
        endDate = endDate.strftime("%Y%m%d")
        curDate = _date.strftime("%Y%m%d")
        while curDate != endDate:
            curDate = _date.strftime("%Y%m%d")
            _date = _date - timedelta(days=1)
            print "CUr date: ", curDate, 'https://www.espnfc.com/scores?date='+curDate
            cntr = 0
            while cntr < 5:
                try:
                    req = urllib2.Request('https://www.espnfc.com/scores?date='+curDate, headers=headers)
                    url = urllib2.urlopen(req).read().decode('utf-8', 'ignore')
                    break
                except Exception as e:
                    print e
                    cntr +=1
                    sleep(randint(1,10))
            if cntr == 5:
                continue
            self.espn = BeautifulSoup(url, 'html.parser')
            leagues = self.espn.find_all("div", { "class" : "score-league" })
            f = self.espn.find_all("div", { "id" : "all-scores-leagues-dropdown" })[0].find_all("option")
            p = {}
            for k in f[1:]:
                p[int(k["value"])] = k.renderContents().decode("utf-8")

            for league in leagues:
                try:
                    if p[int(league["data-league-id"])] in self.wantedLeagues:
                        if "Table" not in p[int(league["data-league-id"])]:
                            curLeague = p[int(league["data-league-id"])] + " Table"
                        else:
                            curLeague = p[int(league["data-league-id"])]

                        print "Successfuly caught league: ", curLeague, '\n\n'
                        path = self.ensure_directories( curDate, curLeague)
                        links = []
                        for k in league.find_all( "a", { "class":"primary-link" } ):
                            if "match" in k['href']:
                                self.parse_game_events(sub_text("match", "commentary", k["href"]),
                                    path, curDate, curLeague)
                            else:
                                self.parse_game_events(sub_text("report", "commentary", k["href"]),
                                    path, curDate, curLeague)
                    curLeage = "NoLeagueCaught"
                except (urllib2.HTTPError) as e:
                    print str(e)
                    print "Internal server error or could not league keys"
                    continue


    def ensure_directories(self, date, league):
        print league
        league = sub_text( " ", "_", league )
        path = "data/"+date+"/"+league+"/"
        if not os.path.exists(path):
            os.makedirs(path)
            return path
        return path


    def pull_game_html(self, url, path, gameId ):
        try:
            _file = open(path+gameId+".txt", 'r')
            contents = _file.read()
            return contents
        except:
            cntr = 0
            while cntr < 5:
                try:
                    req = urllib2.Request(url, headers=self.headers)
                    contents = urllib2.urlopen(req).read().decode('ascii', 'ignore')
                    break
                except:
                    sleep(randint(1,10))
                    cntr+=1
                    continue
            if cntr == 5:
                self.num_failed_games+=1
                print "Game could not open: ", path+gameId
                return False
            _file = open(path+gameId+".txt", "w" )
            _file.write(contents)
            _file.close()
            return contents

    def get_line_ups(self, gameId, path):

        try:
            _file = open(''.join([path,gameId,"lineup.txt"]), 'r')
            contents = _file.read()
        except IOError:
            url = ''.join(['http://www.espnfc.us/lineups?',gameId])
            req = urllib2.Request(url, headers=self.headers)
            contents = urllib2.urlopen(req).read().decode('ascii', 'ignore')
            _file = open(''.join([path,gameId,"lineup.txt"]), "w" )
            _file.write(contents)
            _file.close()
        #finally:
        #    return None
        game = BeautifulSoup(contents, 'html.parser')
        lineups = {}
        for team in game.find_all("div", { "class" : "content-tab" }):
            cur_team = team.find("caption").find_all(text=True)[1].strip()
            lineups[cur_team] = []
            for player in team.find_all('div', {"class":"accordion-header lineup-player"}):
                cur = player.find_all('span', {'class':'name'})[1]
                if cur != None:
                    lineups[cur_team].append(cur.find_all(text=True)[1].encode("ascii", errors="ignore").strip())

        return lineups

    def parse_game_events(self, url, path, date, league):
        print "Current URL:: ", url
        _events = {"goal":defaultdict(list), "yellow card":defaultdict(list), 
            "red card":defaultdict(list), "sub":defaultdict(list)}
        _scoring_event = defaultdict(list)
        gameId = url.split("?")[1]
        contents = self.pull_game_html(url, path, gameId)
        lineups = self.get_line_ups(gameId, path)
        print lineups
        if not contents or (self.scrape_only and self.game_exists(gameId)) or not lineups:
            return
        self.espn = BeautifulSoup(contents, 'html.parser')
        curMatch = Match(date, league)
        try: 
            lines = self.espn.find_all('table')[2].find_all("tr")
            firstLine = lines[0].find_all("td")[2].renderContents().strip().split(",")
        except Exception as e:
            print "Failure to find second table! Cannot parse: ", url, " :: ", e
            return
        if "Match ends" not in firstLine and "Second Half ends" not in firstLine:
            return
        try:
            curMatch.score = ''.join([get_regex_matches("\d+$",
                firstLine[1])+"-"+get_regex_matches("\d+.$", firstLine[2])])
            curMatch.home = (get_regex_matches(".*[^\d+$]", firstLine[1]).strip(),
                int(get_regex_matches("\d+$", firstLine[1])))
            curMatch.away = (get_regex_matches(".*[^\d+.$]", firstLine[2]).strip(),
                int(get_regex_matches("\d+.$", firstLine[2])[:-1]))
        except:
            print "---------- failed parsing score, skipping --------\n\n"
            return
        print curMatch.home, "  ", curMatch.away, " TEAMS-------------------------\n\n"
        lineups = self.espnParser.clean_teams(lineups, curMatch)
        for events in lines:
            event = events.find_all('td')
            # if there was a goal attempt, get information for xG
            evt_res =  self.espnParser.get_event(event[2].renderContents())
            if evt_res[0] != None:
                _scoring_event[evt_res[-1]].append(evt_res[:-1])
            event_t = self.espnParser.get_type(event[2].renderContents().strip())
            if event_t:
                try:
                    # get the type of event and then call the appropiate espn function
                    # ("goal",[team, minute, [scorer, assist]])
                    event_t = event_t(
                        event[0].renderContents().strip(),
                        event[2].renderContents().strip(),
                        curMatch)
                    _events[event_t[0]][event_t[1][0]].append(event_t[1][1:])
                except Exception as e:
                    print e, "   error in: ", url, " Teams: ", curMatch.home, "   ", curMatch.away
        self.save_game(curMatch, _events, gameId, _scoring_event, lineups)

    def game_exists(self, gameId):
        if gameId in self.recorded_games:
            return True
        return False

    def save_game(self, match, _events, gameId, _scoring_event, lineups):
        if gameId in self.recorded_games:
            doc = self.recorded_games[gameId]
        else:
            doc = {}
        doc['home'] = {"team name": match.home[0], "score": match.home[1], "scoring events" :
                        _scoring_event[match.home[0]], "yellow card" : _events["yellow card"].get(match.home[0]),
                        "red card":_events["red card"].get(match.home[0]), "subs":_events["sub"].get(match.home[0]),
                        "goal" : _events["goal"].get(match.home[0]), "lineup":lineups[match.home[0]]}
        doc['away'] = {"team name": match.away[0], "score": match.away[1], "scoring events" :
                        _scoring_event[match.away[0]], 
                        "yellow card" : _events["yellow card"].get(match.away[0]),
                        "red card":_events["red card"].get(match.away[0]), 
                        "subs":_events["sub"].get(match.away[0]),
                        "goal" : _events["goal"].get(match.away[0]), 
                        "lineup":lineups[match.away[0]]}
        doc['score'] = match.score
        doc['date'] = match.name
        doc['league'] = match.league
        if gameId not in self.recorded_games:
            self.recorded_games[gameId] = doc
            print "wrote to db"
        else:
            _id, _rev = self.recorded_games.save(doc)
            print "wrote to db with: ", _id





if __name__ == "__main__":
    parse = Parser()
    parse.get_date_games( datetime(2017,11, 21), datetime(2005, 10, 9) )#datetime.today(),
#parse.get_date_games( datetime(2017, 10, 11), datetime(2017, 10, 9))









