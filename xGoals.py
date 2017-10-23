
import numpy as np
import plotly as py
import plotly.graph_objs as go
import espn_scraper
from datetime import datetime
import pickle
from numpy import random
import operator
from collections import deque, defaultdict
import csv



def is_goal(event):
    if event[0] == "Goal":
        return 1
    return 0



class average_goals_calc:

	def __init__(self):
		self.parse = espn_scraper.Parser()
		self.db = self.parse.recorded_games
		self.view = self.parse.recorded_games.view('games/teams')
		self.locations = {"free kick":(0,0), "outside the box":(0,0), "right side":(0,0), "centre of the box":(0,0),
             "left side":(0,0), "long range":(0,0), "left side of the six yard box":(0,0), 
             "right side of the six yard box":(0,0), "six yard box":(0,0), "very close range":(0,0),
             "penalty":(0,0)}
		self.attmp = {"left footed shot":(0,0), "right footed shot":(0,0), "header":(0,0)}
		self.assist = {"headed pass":(0,0), "through ball":(0,0), "cross":(0,0), "corner":(0,0), "fast break":(0,0),
			"direct free kick":(0,0)}
		self.compound_events = {"date":datetime.today().strftime("%Y%m%d")}

	#function for calculating expected goals when passed in a series of events
	# events should only be for one team or one player 
	def calc_xG(self, events):
	    for event in events:
	        condition_prob = ''
	        if event[1]:
	            condition_prob = event[1]
	            cnt = self.locations[event[1]]
	            if is_goal(event):
	                self.locations[event[1]] = (cnt[0]+1, cnt[1]+1)
	            else:
	                self.locations[event[1]] = (cnt[0], cnt[1]+1)
	        if event[2]:
	            condition_prob += '-' + event[2]
	            cnt = self.attmp[event[2]]
	            if is_goal(event):
	                self.attmp[event[2]] = (cnt[0]+1, cnt[1]+1)
	            else:
	                self.attmp[event[2]] = (cnt[0], cnt[1]+1)
	        if event[3]:
	            condition_prob += '-' + event[3]
	            cnt = self.assist[event[3]]
	            if is_goal(event):
	                self.assist[event[3]] = (cnt[0]+1, cnt[1]+1)
	            else:
	                self.assist[event[3]] = (cnt[0], cnt[1]+1)
	        condition_prob = '-'.join(  item for item in event[1:] if item  )
	        if condition_prob in self.compound_events:
	            cnt = self.compound_events[condition_prob]
	            if is_goal(event):
	                self.compound_events[condition_prob] = (cnt[0]+1, cnt[1]+1)
	            else:
	                self.compound_events[condition_prob] = (cnt[0], cnt[1]+1)
	        else:
	            if is_goal(event):
	                self.compound_events[condition_prob] = (1, 1)
	            else:
	                self.compound_events[condition_prob] = (0, 1)
	    return


	def build_model(self, _reset=None):
		latest_date = ''
		
		try:
			# try and grab from current directory
			self.compound_events = pickle.load( open( "save.p", "rb" ) )
			print "loading model"
			if _reset:
				self.compound_events["date"] = ""
			# model has not been updated for today
			if self.compound_events["date"] < datetime.today().strftime("%Y%m%d"):
				latest_date = self.compound_events["date"]
				print "Updating model to today"
				raise Exception
		except:
			scoring_events = []
			cnt = 0
			print "building model"
			# build model from games in time frame
			for game in self.view:
			    if 'home' in game['value'] and game["key"] > latest_date:
			    	print game["key"]
			        self.calc_xG(game["value"]['home']['scoring events'])
			        cnt += len(game["value"]['home']['scoring events'])
			        self.calc_xG(game["value"]['away']['scoring events'])
			self.compound_events["date"] = datetime.today().strftime("%Y%m%d")
			_out = open("shot_data.txt", "w")
			_out.write("Compound Events")
			for key in self.compound_events:
			    _out.write(key)
			    _out.write(str(self.compound_events[key]))
			    _out.write('\n\n')
			_out.write(str(len(self.compound_events)))
			pickle.dump( self.compound_events, open("save.p", "wb") )


	def get_xG(self, events, b_dates, b_goals, b_probs, date):
		_cur = 0
		for thing in events["scoring events"]:
			key = '-'.join(  item for item in thing[1:] if item  )
			cur = self.compound_events[key]
			_cur += float(cur[0]/float(cur[1]))
		b_dates.append(datetime.strptime(str(date), "%Y%m%d"))
		b_goals.append(events["score"])
		b_probs.append(_cur)

	# if opp is false, then calculate expected goals for team, else calc for defence
	def calc_for_team(self, team, from_date, to_date, opp=False):
		b_probs = []
		b_goals = []
		b_dates = []
		for r in self.view:
			if r["value"]["date"] > from_date and r["value"]["date"] < to_date:
				if r["value"]["home"]["team name"] in team:
					if not opp:
						self.get_xG(r["value"]["home"], 
							b_dates, b_goals, b_probs, r["value"]["date"])
					else:
						self.get_xG(r["value"]["away"], 
							b_dates, b_goals, b_probs, r["value"]["date"])
				if r["value"]["away"]["team name"] in team:
					if not opp:
						self.get_xG( r["value"]["away"], 
							b_dates, b_goals, b_probs, r["value"]["date"])
					else:
						self.get_xG( r["value"]["home"], 
							b_dates, b_goals, b_probs, r["value"]["date"])

		return b_dates, np.array(b_goals), np.array(b_probs)


	def graph_Xg_one_team(self, b_dates, b_goals, xG, team, _def=False):
		averages = [np.mean(xG[:i]) for i in range(0,len(xG))]
		trace1 = go.Bar(
	    x=b_dates,
	    y=xG,
	    name='Expected Goals'
		)
		trace2 = go.Bar(
		    x=b_dates,
		    y=b_goals,
		    name='Actual Goals'
		)
		trace3 = go.Scatter(
		    x = b_dates,
		    y = averages,
		    mode = 'lines+markers',
		    name = 'Running average of error (actual goals-expected goals)'
		)
		if isinstance(_def, np.ndarray):
			trace4 = go.Scatter(
		    x = b_dates,
		    y = _def,
		    mode = 'lines+markers',
		    name = 'Defensive Expected goals'
			)
			data = [trace1, trace2, trace3, trace4]
			print "Defensive values included"
		else:	
			data = [trace1, trace2, trace3]
		layout = go.Layout(
		    barmode='group',
		    bargap=0.15,
		    bargroupgap=0.1,
		    title="Expected Goals vs. Actual Goals "+ team + " Past " + str(len(xG)) +" Games",
		    xaxis={"title":"Past game dates"},
		    yaxis={"title":"Goals scored"}
		)
		fig = go.Figure(data=data, layout=layout)
		py.offline.plot(fig, filename='stacked-bar')

	def get_running_xG(self, prob_goals):
		return [np.nanmean(prob_goals[:i]) for i in range(0,len(prob_goals))]

	def graph_compare_one_stat_mult_team(self, dates, list_stat, teams, title):

		team_graphs = []
		for i in xrange(0, len(teams)):
			team_graphs.append(
				go.Scatter(
					x=dates[i],
					y=list_stat[i],
					name=teams[i],
					mode = 'lines+markers',
					)
				)

		data = team_graphs
		layout = go.Layout(
		    title=title,
		    xaxis={"title":"Past game dates"},
		    yaxis={"title":"Goals scored"}
		)
		fig = go.Figure(data=data, layout=layout)
		py.offline.plot(fig, filename='_'.join(title.split(" ")))

	# num_sim: number of simulations to perform
	# starting_stats: starting array of expected goals for each team (array of numpy arrays)
	# 	 in general should be same size as game_depth
	# team_names: team name for index in starting_stats
	# schedule: Array of arrays, each internal array contains tuples of matching. each internal 
	# 	 array represents a matchday pairing two teams in the league together
	# game_depth: how many games back you want to consider. Each team's strength is represented by
	# 	 a queue of the past <game_depth> games, over which the average is taken. with each new 
	#	 simulated match day, the oldest game is replaced with the current game
	def simulate_league(self, num_sim, starting_stats, team_names, schedule, game_depth):
		team_stats = { }
		for i in xrange(len(team_names)):
			team_stats[team_names[i]] = deque(starting_stats[i], maxlen=game_depth)

		sims = [  ]
		
		for i in xrange(num_sim):
			table = defaultdict(int)
			for game in schedule:
				idx1 = random.poisson( np.mean(team_stats[game[0]] ) )
				idx2 = random.poisson( np.mean(team_stats[game[1]] ) )
				team_stats[game[0]].append(idx1)
				team_stats[game[1]].append(idx2)

				if round(idx1, 1) == round(idx2, 1):
					table[game[0]] +=1
					table[game[1]] +=1
				if round(idx1, 1) > round(idx2, 1):
					table[game[0]] +=3
				else:
					table[game[1]] +=3
			sims.append( table )


		for sim in sims:
			print sim
			print '\n\n'





xG_calculator = average_goals_calc()
xG_calculator.build_model()


teams = set(["Tottenham Hotspur", "Manchester City", "Manchester United"])
schedule_file = open("00082_UK_Football_Fixtures_2016-17_DedicatedExcel.csv", "r")
schedule = []
sch = csv.reader(schedule_file, delimiter=',')
next(sch)

for game in sch:
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

	if game[4] == "Hull":
		game[4] = "Hull City"
	if game[5] == "Hull":
		game[5] = "Hull City"

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
	if game[4] == '':
			break
	
	schedule.append((game[4], game[5]))
	teams.add(game[4])
	teams.add(game[5])




print schedule
teams = list(teams)

xg_pleague = []
_team=[]
for t in teams:
	print "xG for team::  ", t
	d, g, xG = xG_calculator.calc_for_team( set([t]), "20160101", "20160930" )
	if len(xG) == 0 or len(g) == 0:
		continue
	xg_pleague.append( (g+xG)/2.0 )
	_team.append(t)


print _team
xG_calculator.simulate_league(20, xg_pleague, _team, schedule, 10)

"""



#b_dates, b_goals, b_xG = xG_calculator.calc_for_team(set(["FC Bayern Mnchen", "Bayern Munich"]), "20160901", "20170730", False)

#bd_dates, bd_goals, bd_xG = xG_calculator.calc_for_team(set(["Borussia Dortmund"]), "20160901", "20170730", True)
c_dates, c_goals, c_xG = xG_calculator.calc_for_team(set(["Chelsea"]), "20150901", "20160701")
m_dates, m_goals, m_xG = xG_calculator.calc_for_team(set(["Manchester United"]), "20150901", "20160701")
nc_dates, nc_goals, nc_xG = xG_calculator.calc_for_team(set(["Arsenal"]), "20150901", "20160701")
lc_dates, lc_goals, lc_xG = xG_calculator.calc_for_team(set(["Manchester City"]), "20150901", "20160710")
t_dates, t_goals, t_xG = xG_calculator.calc_for_team(set(["Tottenham", "Tottenham Hotspur"]), "20150901", "20160710")
l_dates, l_goals, l_xG = xG_calculator.calc_for_team(set(["Liverpool"]), "20150901", "20160710")

#o_dates, o_goals, b_o_xG = xG_calculator.calc_for_team(set(["FC Bayern Mnchen", "Bayern Munich"]), "20160901", 
#	"20170730", True)




#b_r_xG = xG_calculator.get_running_xG(b_xG)

#bd_r_xG = xG_calculator.get_running_xG(bd_xG)
c_r_xG = xG_calculator.get_running_xG(c_xG)
m_r_xG = xG_calculator.get_running_xG(m_xG)
nc_r_xG = xG_calculator.get_running_xG(nc_xG)
lc_r_xG = xG_calculator.get_running_xG(lc_xG)
t_r_xG = xG_calculator.get_running_xG(t_xG)
l_r_xG = xG_calculator.get_running_xG(l_xG)

#xG_calculator.graph_Xg_one_team(b_dates, b_goals, b_xG, "Bayern Munich", b_o_xG )

print nc_xG
print lc_xG
print nc_r_xG
print lc_r_xG

xG_calculator.graph_compare_one_stat_mult_team( [m_dates, nc_dates, c_dates, lc_dates, t_dates, l_dates],
	[m_r_xG, nc_r_xG, c_r_xG, lc_r_xG, t_r_xG, l_r_xG], ["Manchester United","Arsenal", "Chelsea", "Manchester City",
	"Tottenham Hotspur", "Liverpool"],
	"2016 - 2017 Comparison of Premier League teams" )



#xG_calculator.graph_Xg_one_team(b_dates, b_goals, b_xG, "Bayern Munich")
#xG_calculator.graph_Xg_one_team(bd_dates, bd_goals, bd_xG, "Dortmund")
#xG_calculator.graph_Xg_one_team(c_dates, c_goals, c_xG, "Chelsea")
#xG_calculator.graph_Xg_one_team(m_dates, m_goals, m_xG, "Manchester United")

"""















