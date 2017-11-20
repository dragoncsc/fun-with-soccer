import re
from match_event_parser import *
import nltk
from difflib import SequenceMatcher




class ESPNMatchEventParser(MatchEventParser):

    def __init__(self):
        self.stuff = ["Own Goal", "Goal", "Attempt missed", "Attempt blocked", "Attempt saved", "Penalty saved"]
        self.poss = ["right side of the six yard box", "left side of the six yard box", 
                "outside the box", "right side", "centre of the box", "left side", "long range", 
               "six yard box", "very close range", "penalty"]
        self.attmp = ["left footed shot", "right footed shot", "header"]
        self.assist = ["headed pass", "through ball", "cross", "corner", "fast break", "direct free kick"]        
   
    # Goal!  Azerbaijan 1, Czech Republic 2. Antonin Barak (Czech Republic)
    # header from the centre of the box to the top right corner. Assisted by
    # Vladimir Darida with a cross following a corner.
    @staticmethod
    def goal_event(time, event, curMatch):
        minute = ESPNMatchEventParser.get_game_minute(time)
        if "Own Goal by" in event:
            scorer = "Own Goal"
            if curMatch.home[0] in event.split(",")[1].split(".")[0]:
                country = curMatch.away
            else:
                country = curMatch.home
            assist = get_regex_matches("by [A-Za-z0-9 ]+,", event)[3:-1]
            return ("goal", (country, minute, (scorer, assist)))
        country = get_regex_matches("\(.+\)", event)[1:-1]
        scorer = get_regex_matches("\. [A-Za-z- ]+ \(", event)[2:-2]
        if "Assisted by" in event:
            assist = get_regex_matches("Assisted by ([A-Za-z ]+) with", event)
            if not assist:
                assist = get_regex_matches("Assisted by ([A-Za-z ]+)\.", event)
            return ("goal",[country, minute, [scorer, assist]])
        return ("goal",[country, minute, [scorer, None]])


    # Marek Suchy (Czech Republic) is shown the yellow card for a bad foul.
    # Josef Husbauer (Czech Republic) is shown the yellow card.
    @staticmethod
    def ycard_event(time, line, curMatch):
        try:
            minute = ESPNMatchEventParser.get_game_minute(time)
            country = get_regex_matches("\(.+\)", line)[1:-1]
            scorer = get_regex_matches("^.+ \(", line)[:-2]
            return ("yellow card",[country, minute, [scorer, None]])
        except Exception as e:
            print "In yellow card"
            print e
            print line, '\n\n\n'


    # Second yellow card to Robert Mak (Slovakia).
    # Alexandru Gatcan (Moldova) is shown the red card for violent conduct.
    @staticmethod
    def rcard_event(time, line, curMatch):
        try:
            minute = ESPNMatchEventParser.get_game_minute(time)
            country = get_regex_matches("\(.+\)", line)[1:-1]
            if get_regex_matches("Second yellow card", line):
                scorer = get_regex_matches("to .+ \(", line)[2:-2]
                return ("red card",(country, minute, (scorer, None)))
            scorer = get_regex_matches("^.+ \(", line)[:-2]
            return ("red card",[country, minute, [scorer, None]])
        except Exception as e:
            print "in red card"
            print e
            print line, '\n\n\n'

    #Substitution, Czech Republic. Jan Kliment replaces Michal Krmencik.
    @staticmethod
    def sub_event(time, line, curMatch):
        try:
            minute = ESPNMatchEventParser.get_game_minute(time)
            country = get_regex_matches(", [A-Za-z0-9- ]+\.", line)[2:-1]
            scorer = get_regex_matches("\. .+ re", line)[2:-3]
            replaced = get_regex_matches("replaces .+\.$", line)[9:-1]
            return ("sub",[country, minute, [scorer, replaced]])
        except Exception as e:
            print "In Sub"
            print e
            print line, '\n\n\n'

    # Map event found in commentary to event parser function
    @staticmethod
    def get_type( line ):
        events = {"Goal!":ESPNMatchEventParser.goal_event, 
                  "Substitution,":ESPNMatchEventParser.sub_event, 
                  "shown the yellow card":ESPNMatchEventParser.ycard_event, 
                  "shown the red card":ESPNMatchEventParser.rcard_event,
                  "Second yellow card":ESPNMatchEventParser.rcard_event,
                  "Own Goal by":ESPNMatchEventParser.goal_event }
        for event in events.keys():
            _e = get_regex_matches(event, line)
            if _e:
                return events[_e]
        return None
    
    @staticmethod
    def grab_match_events( time, event ):

            event_t = get_type(event)(time, event)
            _events[event_t[0]] = event_t[1]

    def clean_teams(self, lineups, curMatch):
        teams = lineups.keys()
        if SequenceMatcher(curMatch.home[0], teams[0]).ratio() \
            > SequenceMatcher(curMatch.home[0], teams[1]).ratio():
            lineups[curMatch.home[0]] = lineups[teams[0]]
            lineups[curMatch.away[0]] = lineups[teams[1]]
        else:
            lineups[curMatch.home[0]] = lineups[teams[1]]
            lineups[curMatch.away[0]] = lineups[teams[0]]

    
    def get_event(self, mess):
        team = get_regex_matches("\(([A-Za-z0-9 .]+)\)", mess)
        if type(team)!= str:
            # some games' commentaries are just really messed up and there's nothing to do. 
            # for example, november 3rd 2011 CSK Moscow game
            return [None]
        player = get_regex_matches( "\. ([a-zA-Z0-9 ]+) \(", mess)
        final = [None, None, None, None, player, team]
        cntr = 0
        for s in self.stuff:
            if s in mess:
                final[0] = s
                break
        for p in self.poss:
            if p in mess:
                final[1] = p
                break
        if final[0] == "Penalty saved":
            final[1] = "penalty"
        for a in self.attmp:
            if a in mess:
                final[2] = a
                break
        for a in self.assist:
            if a in mess:
                final[3] = a
                return final
        return final







