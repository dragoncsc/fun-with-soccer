# fun-with-soccer

Rough soccer simulator that scrapes ESPN soccer commentaries and builds and caches the entire web page in the 'data/' folder. Currently scrapes Jan. 1 2006-today, data quality significantly falls off by the end of 2009. Scrapes German, Spanish, Italian, French and English leagues, along with the champions league for the corresponding time. 

Once a particular game's web page is hit, the scraper will store the page on disk as a flat file, where each day scraped is a new directory, and each league is a different subdirectory within each day. Example:

data/ ->  20160203/   -> English_Premier_League_Table/   -> gameid=422425.txt

The individual game files are stored with the id given to them by ESPN. After the pages are cached, the scraper extracts information regarding shots on goal, yellow cards, red cards, substitutions. etc and stores this information as a document in a Couchdb instance. The purpose of caching the entire webpage is to allow the user to change the stored parameters/ modify analysis/extract different data down the line. 

The scraper is quite slow, and is meant to be run over night. Scraping 11 years takes about 230min on first run. Optimizations can be made by caching regexes and getting a better sense of the scraped data after 2011 to reduce the many try/catch sequences. No optimizations have been bothered to be implemented. Something on the order of 20,000 games are scraped and on the order of 500,000 attempts on goal are captured. The scraper does not currently scrape penalty shootouts, though they are assumed to be easy to scrape.

xGoal.py is used to build a model of attempts on goal, and is additionally used for visualization in conjunction with plotly. As a warning, xGoals uses the python module 'pickle' which is known to have security flaws as the target of an unpickling operation can execute automatically (this is a problem if the user doesn't know what they are unpickling). The pickle module is used to cache the last version of the model, so that the model does not have to be retrained on historical data at the start of every run. 

Currently, the expected goal model tries to capture the probability of a shot converting into a goal. The parameters that define the model include place of shot, body part used to take shot and assist type. Not all goals provide this data. These parameters account for penalties and roughly account for own goals, but further thought is needed for the latter. ESPN does not give very accurate data for shot location. Here are some examples: 

"Goal! Celtic 1, FC Bayern München 2. Javi Martínez (FC Bayern München) header from the centre of the box to the bottom left corner. Assisted by David Alaba with a cross."

"Goal! Roma 3, Chelsea 0. Diego Perotti (Roma) right footed shot from outside the box to the bottom left corner. Assisted by Aleksandar Kolarov."

"Goal! Paris Saint Germain 4, RSC Anderlecht 0. Layvin Kurzawa (Paris Saint Germain) header from the left side of the six yard box to the bottom left corner."

In place of precise locations, we are given approximate spaces inside of the box. This may actually be helpful as increased precision may add noise (think feet from the goal) while the discriptions are sufficiently detailed enough to draw a heat map of attempts in and around the 16 yard box. Currently, the model is too noisey to offer interesting 20 game simulations, in an effort to refine the accuracy of the model assist type may be removed. If a goal's commentary does not provide this data, then only the parameters given by the commentary will be accounted for in calculating the expected goal percentage. The sum total of all the expected goal calculations for a team during the game will represent the expected amount of goals for that team during the game, the sum of the opponent's calculations can be considered a measure of the first team's defensive strength.


Example of use:
Run espn_scraper.py, with the option of adjusting the dates on the bottom of the file, to scrape data.

The 'graph_Xg_one_team' function allows the user to graph the expected goals for one team. Example useage of the xGoals file(Paste this below the average_goals_calc() class definition):


xG_calculator = average_goals_calc()

xG_calculator.build_model()

c_dates, c_goals, c_xG = xG_calculator.calc_for_team(set(["Chelsea"]), "20150901", "20160701")

c_r_xG = xG_calculator.get_running_xG(c_xG)

xG_calculator.graph_Xg_one_team(c_dates, c_goals, c_xG, "Chelsea")


