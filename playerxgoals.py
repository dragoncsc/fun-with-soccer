import redis
import couchdb
from couchdb.design import ViewDefinition
from collections import defaultdict, Counter
import json

r = redis.StrictRedis(host='localhost', port=6379, db=0)
#r.flushdb()


db = couchdb.Server()
recorded_games = db["recordedgames"]

players = defaultdict(list)

for game in recorded_games.view('games/teams'):
	for event in game['value']['home']['scoring events']:
		print event[-1]
		players[event[-1]].append(event[:-1])
	for event in game['value']['away']['scoring events']:
		print event[-1]
		players[event[-1]].append(event[:-1])



for player in players:
	r.set(player, json.dumps(players[player]))


ex = redis.StrictRedis(host='localhost', port=6379, db=1)
#ex.flushdb()
print "Created ex goals db"
for key in r.scan_iter():
	print key, " :: "
	attempt_type = []
	successes = []
	ex_goals = {}
	for event in json.loads(r.get(key)):
		attempt_type.append( '-'.join([x for x in event[1:] if x is not None]) )
		if event[0] == "Goal":
			successes.append( '-'.join([ x for x in event[1:] if x is not None]) )
	att_counter = Counter(attempt_type)
	success_counter = Counter(successes)
	for goal in success_counter:
		tries = float( att_counter[ goal ] )
		count = float( success_counter[ goal ] )
		ex_goals[ goal ] = count / tries
	print "Total attempts:: ", len(attempt_type)
	print ex_goals
	ex.set(key+"ex_goals", json.dumps(ex_goals))
	print '\n\n\n'



print "Done"