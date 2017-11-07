import re
from match_event_parser import *
import nltk
from nltk.tokenize import sent_tokenize




class ESPNMatchEventParser(MatchEventParser):
   
    # Goal!  Azerbaijan 1, Czech Republic 2. Antonin Barak (Czech Republic)
    # header from the centre of the box to the top right corner. Assisted by
    # Vladimir Darida with a cross following a corner.
    @staticmethod
    def goal_event(time, event, curMatch):
        #try:
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
        '''
        except Exception as e:
            print "In goal"
            print e
            print event, '\n\n\n'
        '''

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

    @staticmethod
    def get_event( mess):
        team = get_regex_matches("\(([A-Za-z0-9 ]+)\)", mess)
        mess = sent_tokenize(mess.decode("utf-8", "ignore"))
        stuff = ["Own Goal", "Goal", "Attempt missed", "Attempt blocked", "Attempt saved", "Penalty saved"]
        poss = ["right side of the six yard box", "left side of the six yard box", 
                "outside the box", "right side", "centre of the box", "left side", "long range", 
               "six yard box", "very close range", "penalty"]
        attmp = ["left footed shot", "right footed shot", "header"]
        assist = ["headed pass", "through ball", "cross", "corner", "fast break", "direct free kick"]
        final = [None, None, None, None, team]
        cntr = 0
        for s in stuff:
            if s in mess[cntr]:
                final[0] = s
                break
        if final[0] == "Goal":
            cntr += 1
        cntr+=1
        if len(mess) < (1+cntr):
            return final
        for p in poss:
            if p in mess[cntr]:
                final[1] = p
                break
        if final[0] == "Penalty saved":
            final[1] = "penalty"
        for a in attmp:
            if a in mess[cntr]:
                final[2] = a
                break
        cntr+=1
        if len(mess) < (1+cntr):
            return final
        for a in assist:
            if a in mess[cntr]:
                final[3] = a
                return final
        return final







