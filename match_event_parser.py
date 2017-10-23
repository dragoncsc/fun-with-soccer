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