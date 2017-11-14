


res = open('premier_league_2014_2015_results.csv', 'r')
out = open('epl_2014_2015_results.csv', 'w')
out.write("l,l,l,l,l,l\n")
games = []
for line in res:
	if line == '\n':
		continue
	print line.split(' v ')
	team2 = line.split(' v ')[1]
	team1 = []
	for i  in line.split(' ')[2:]:
		if i == 'v':
			team1 = ' '.join(team1)
			break
		team1.append(i)
	out.write("l,l,l,l,"+team1+","+ team2.strip()+"\n")
	games.append((team1,team2.strip()))

for i in games:
	print i
