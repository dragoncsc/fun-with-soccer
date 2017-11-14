import re



# make sure your string only matches one group in your regex
# or maybe come up with a new regex_matcher...
def get_regex_matches(regex, source_text):
    assert(isinstance(regex, (str, unicode)) and isinstance(source_text, (str, unicode)))
    rg = re.compile(regex, re.UNICODE)
    matches = rg.findall(source_text)
    tmp = []
    for i in matches:
        if isinstance(i, tuple):
            # remove annoying tuples and empty strings
            # this methods depends on there only being one match in the regex output
            tup = ''
            for j in i:
                if j != '':
                    tup = j
            tmp.append(tup)
        else:
            tmp.append(i)
    matches = tmp
    if len(matches) == 1:
        return matches[0]
    elif len(matches) == 0:
        return None
    else:
        return matches

#print get_regex_matches("(shown the red card)|(Second yellow card)", "Second yellow card to Robert Mak (Slovakia).")
#print get_regex_matches("^.+ \(", "Alexandru Gatcan (Moldova) is shown the red card for violent conduct.")

def sub_text(to_sub, replace, text):
    regex = re.compile(to_sub, re.IGNORECASE)
    return re.sub(regex, replace, text)


def get_schedule(schedule_file, schedule, teams):
    
    for game in schedule_file:
        if game[4] == "Man City":
            game[4] = "Manchester City"
        if game[5] == "Man City":
            game[5] = "Manchester City"

        if game[4] == "Man Utd":
            game[4] = "Manchester United"
        if game[5] == "Man Utd":
            game[5] = "Manchester United"

        if game[4] == "Swansea":
            game[4] = "Swansea City"
        if game[5] == "Swansea":
            game[5] = "Swansea City"

        if game[4] == "West Ham":
            game[4] = "West Ham United"
        if game[5] == "West Ham":
            game[5] = "West Ham United"

        if game[4] == "West Brom":
            game[4] = "West Bromwich Albion"
        if game[5] == "West Brom":
            game[5] = "West Bromwich Albion"

        if game[4] == "Newcastle":
            game[4] = "Newcastle United"
        if game[5] == "Newcastle":
            game[5] = "Newcastle United"

        if game[4] == "Norwich":
            game[4] = "Norwich City"
        if game[5] == "Norwich":
            game[5] = "Norwich City"

        if game[4] == "QPR":
            game[4] = "Queens Park Rangers"
        if game[5] == "QPR":
            game[5] = "Queens Park Rangers"
        if game[4] == "Man United":
            game[4] = "Manchester United"
        if game[5] == "Man United":
            game[5] = "Manchester United"

        if game[4] == "Man City":
            game[4] = "Manchester City"
        if game[5] == "Man City":
            game[5] = "Manchester City"
        
        if game[4] == "Spurs":
            game[4] = "Tottenham Hotspur"
        if game[5] == "Spurs":
            game[5] = "Tottenham Hotspur"
        
        if game[4] == "Hull":
            game[4] = u"Hull City"
        if game[5] == "Hull":
            game[5] = u"Hull City"
        if game[4] == "Leicester":
            game[4] = "Leicester City"
        if game[5] == "Leicester":
            game[5] = "Leicester City"
        if game[4] == "Stoke":
            game[4] = "Stoke City"
        if game[5] == "Stoke":
            game[5] = "Stoke City"
        if game[4] == "Tottenham":
            game[4] = "Tottenham Hotspur"
        if game[5] == "Tottenham":
            game[5] = "Tottenham Hotspur"
        if game[4] == u'Brighton & Hove Albion':
            game[4] = u'Brighton and Hove Albion'
        if game[5] == u'Brighton & Hove Albion':
            game[5] = u'Brighton and Hove Albion'
        if game[0] == 'EC' or game[4] == '':
                break
        schedule.append((game[4], game[5]))
        teams.add(game[4])
        teams.add(game[5])






class MatchEventParser():

    @staticmethod
    def get_game_minute(time):
        if isinstance(get_regex_matches('\+', time), (str, unicode)):
            times = get_regex_matches( "\d+", time )
            return int(times[0]) + int(times[1])
        return int(get_regex_matches( "\d+", time ))
    # Goal!  Azerbaijan 1, Czech Republic 2. Antonin Barak (Czech Republic)
    # header from the centre of the box to the top right corner. Assisted by
    # Vladimir Darida with a cross following a corner.
    @staticmethod
    def goal_event(time, event):
        raise NotImplemented
    
    # Marek Suchy (Czech Republic) is shown the yellow card for a bad foul.
    # Josef Husbauer (Czech Republic) is shown the yellow card.
    @staticmethod
    def ycard_event(time, line):
        raise NotImplemented
    
    @staticmethod
    def rcard_event(time, line):
        raise NotImplemented

    #Substitution, Czech Republic. Jan Kliment replaces Michal Krmencik.
    @staticmethod
    def sub_event(time, line):
        raise NotImplemented

    @staticmethod
    def get_type( line ):
        raise NotImplemented
    
    @staticmethod
    def grab_match_events( time, event ):
        raise NotImplemented