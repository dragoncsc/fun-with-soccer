import redis
import couchdb
from couchdb.design import ViewDefinition
from collections import defaultdict, Counter
import json
from datetime import datetime, timedelta
from xGoals import average_goals_calc


class playerXgoals(object):
	# start up redis connection
	def __init__(self):
		self.r = redis.StrictRedis(host='localhost', port=6379, db=0)
		print "building model"
		xgoals = average_goals_calc()
		xgoals.build_model()
		all_players_m = xgoals.compound_events
		print "Build model"

		db = couchdb.Server()
		self.recorded_games = db["recordedgames"]

		players = defaultdict(list)
		print "Getting players"


		if not self.r.get("Last Update") or datetime.strptime(self.r.get("Last Update"), 
			"%d%m%Y") - datetime.today() > timedelta(days=5):
			for game in self.recorded_games.view('games/teams'):
				for event in game['value']['home']['scoring events']:
					players[event[-1]].append(event[:-1])
				for event in game['value']['away']['scoring events']:
					players[event[-1]].append(event[:-1])

			for player in players:
				self.r.set(player, json.dumps(players[player]))
			self.r.set("Last Update", datetime.today().strftime("%d%m%Y"))
			self.r.set("Date Format", "%d%m%Y")

		print "Done with grabbing player names"
		self.ex = redis.StrictRedis(host='localhost', port=6379, db=1)
		self.pages = redis.StrictRedis(host='localhost', port=6379, db=3)

	
	def update_x_goals_model(self):
		if not self.ex.get("Last Update") or datetime.strptime(self.ex.get("Last Update"), 
			"%d%m%Y") - datetime.today() > timedelta(days=5):
			print "Created ex goals db"
			for key in self.r.scan_iter():
				print "Curr person", key
				attempt_type = []
				successes = []
				ex_goals = defaultdict(int)
				if key == "Last Update" or key == "Date Format" or "resque" in key:
					continue
				for event in json.loads(self.r.get(key)):
					attempt_type.append( '-'.join([x for x in event[1:] if x is not None]) )
					if event[0] == "Goal":
						successes.append( '-'.join([ x for x in event[1:] if x is not None]) )
				att_counter = Counter(attempt_type)
				success_counter = Counter(successes)
				for goal in success_counter:
					tries = float( att_counter[ goal ] )
					count = float( success_counter[ goal ] )
					ex_goals[ goal ] = (count / tries, tries)
				self.ex.set(key+"ex_goals", json.dumps(ex_goals))

			self.ex.set("Last Update", datetime.today().strftime("%d%m%Y"))
			self.ex.set("Date Format", "%d%m%Y")


	def gen_player_page(self):
		print "in gen_player:"
		page_start = """<section class="mdl-shadow--4dp mdl-color--white section--center story">
		<div class="container-fliud">
		<div class="row">
		<div class="col-xs-20">
		<div id="today=table" class="padded">
		<table class="table table-bordered table-dark">
		<thead>
		<tr>
		<th scope="col">Type of Attempt</th>
		<th scope="col">Successes</th>
		<th scope="col">Number of Attempts</th>
		<th scope="col">Percent Successes</th>
		</tr>
		</thead>
		<tbody>
		""" 
		page_end = """ </tbody>
		</table>
		</div>
		</div>
		</div>
		</div>
		</section><br><br> """
		avoid = set(["Last Update", "Date Format", "Players xGoals", "Players xGoals Date"])
		for key in self.ex.scan_iter():
			if key in avoid:
				print "Avoiding: ", key
				continue
			print key
			model = json.loads(self.ex.get(key))
			table = ""
			for attempt in model:
				table = "\n".join([ table,
					"<tr>", "<td>"+attempt+"</td>",
					"<td>"+str(model[attempt][0]*model[attempt][1])+"</td>", 
					"<td>"+str(model[attempt][1])+"</td>", "<td>"+str(model[attempt][0])+"</td>",
					"</tr>"
					])
			self.pages.set(key[:-len("ex_goals")], page_start + table + page_end)
			print "Key for db 3:: |" + key[:-len("ex_goals")] + "|"
			print "Key in db1:: ", key
			#print page_start + table + page_end
			#print "Page done\n\n\n\n"


	# calculates player x goals per game, unfortunately stores entire model in one entry
	# as opposed to storing individual expected goal models
	def get_player_x_pergame(self):
		print "done updating ex goals player db"

		if not self.ex.get("Players xGoals Date") or datetime.strptime(self.ex.get("Players xGoals Date"),
		 "%d%m%Y") - datetime.today() > timedelta(days=5):
			pergame_exgoals = defaultdict(int)
			print "Building ex goals model"
			for game in recorded_games.view('games/teams'):
				cur_player = ''
				game_players = defaultdict(int)
				players = defaultdict(None)
				for event in game['value']['home']['scoring events']:
					cur_player = event[-1]
					if cur_player and cur_player not in game_players:
						players[cur_player] = json.loads(ex.get(cur_player+'ex_goals'))
					try:
						attempt = '-'.join([ x for x in event[1:-1] if x is not None])
						if attempt in players[cur_player] and players[cur_player][attempt][1] > 2:
							game_players[cur_player] += players[cur_player][attempt][0]
						else:
							game_players[cur_player] += float(all_players_m[attempt][0])/all_players_m[attempt][1]
					except:
						continue
				for event in game['value']['away']['scoring events']:
					cur_player = event[-1]
					#print cur_player
					if cur_player and cur_player not in game_players:
						players[cur_player] = json.loads(ex.get(cur_player+'ex_goals'))
					try:
						attempt = '-'.join([ x for x in event[1:-1] if x is not None])
						if attempt in players[cur_player] and players[cur_player][attempt][1] > 2:
							game_players[cur_player] += players[cur_player][attempt][0]
						else:
							game_players[cur_player] += float(all_players_m[attempt][0])/all_players_m[attempt][1]
						
					except:
						continue
				for person in game_players:
					if pergame_exgoals[person] == 0:
						pergame_exgoals[person] = (game_players[person], 1)
					else:
						prev_ex = pergame_exgoals[person]
						cur = prev_ex[0]*prev_ex[1] + game_players[person]
						pergame_exgoals[person] = (float(cur)/(prev_ex[1]+1), prev_ex[1]+1)
				# start here
			ex.set("Players xGoals", json.dumps(pergame_exgoals))
			ex.set("Players xGoals Date", datetime.today().strftime("%d%m%Y"))

	def calc_pergame_xgoals(self):
		pergame_exgoals = json.loads(self.ex.get("Players xGoals"))

		print "Done"

		games_won = 0
		games_seen = 0
		for game in self.recorded_games.view('games/teams'):
			if game['value']['league'] != 'English Premier League Table' or game['key'] < '20150101' or game['key'] > '20160101':
				continue
			away_ex = 0.0
			home_ex = 0.0
			if 'lineup' not in game['value']['home']:
				continue
			for person in game['value']['home']['lineup']:
				if person in pergame_exgoals:
					home_ex += pergame_exgoals[person][0]

			if 'lineup' not in game['value']['away']:
				continue

			for person in game['value']['away']['lineup']:
				if person in pergame_exgoals:
					away_ex += pergame_exgoals[person][0]
			print "Home team:: ", game['value']['home']['team name'], " : ", game['value']['home']['score']
			print "Home Ex goals: ", home_ex
			print "Away team:: ", game['value']['away']['team name'], " : ", game['value']['away']['score']
			print "Away Ex goals: ", away_ex
			print "Date:: ", game['key']
			
			if game['value']['home']['score'] == game['value']['away']['score']:
				print "Total games seen:: ", games_seen
				print "Total games predicted correctly:: ", games_won
				print '\n\n\n\n'
				continue
			
			if home_ex > away_ex:
				if game['value']['home']['score'] > game['value']['away']['score']:
					games_won += 1
					games_seen += 1
				else:
					games_seen += 1
			else:
				if game['value']['home']['score'] < game['value']['away']['score']:
					games_won += 1
					games_seen += 1
				else:
					games_seen += 1
			print "Total games seen:: ", games_seen
			print "Total games predicted correctly:: ", games_won

			print '\n\n\n\n'




temp = playerXgoals()
temp.update_x_goals_model()
temp.gen_player_page()
#temp.get_player_x_pergame()
#temp.calc_pergame_xgoals()




