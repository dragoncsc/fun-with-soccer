<script src='https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.2/MathJax.js?config=TeX-MML-AM_CHTML'></script>
# Fun with Soccer

This project serves as my introduction to data science. Nothing in here is meant to be informative and my methodology may be flawed. If you find any issues in my process feel free to contact me with critiques.

Soccer simulator that scrapes ESPN commentaries, analyzes them, and then attempts to simulate a soccer season (starting from a point in time that you provide). This model attempts to impcorporate the idea of expected goals, where instead of simply using the number of goals scored as an indicator of team strength, the model takes into account the actual shots on goal, and the likelihood of these shots to go in. The expected goals model is built on 10 years worth of games and about 500,000 attempts on goal. The expected goals model is parametrized based on:
1) location of shot 
2) body part used to shoot 
3) assist type as given by the commentary. 

Starting from the **date** given by the user and the number of games in the past (**n**) the model should use to initialize team strengths, the model first calculates the expected goals for the **n** games in the past, and then finds the maximum likelihood parameter &#955; to be used in the team's generative model (which takes the form of a poisson process). Then, using the schedule for the season, the teams are simulated against eachother, where each game involves drawing from the team's generative model. The winner of the game is the model which outputted the higher expected goal value. The model can either be updated to incorporate the outputed value or can remain static. The winner of a game gets 3 points, a draw give both participants 1 point and a loss results in 0 points. The simulation can then be rerun as many times as desired.


### Data Collection
Finding detailed soccer data for free is very difficult. Some sites like [Opta](http://www.optasports.com/events/premier-league.aspx) collect play-by-play data on games but charge a high premium on accessing their data. I thought it would be interesting to look inot building an expected goals model in addition to a soccer simulater, so I neeed some level of granularity (position/type of shot) so I wanted to find an easily accessible and free source of data. [ESPN's soccer page](http://www.espnfc.us/scores?date=20111017) shows all the games that were played on a certain day across all leagues, each game has a lot of data associated with it, and all of which is freely accsible so I thought I'd start there. 

I scraped German, Spanish, Italian, French and English leagues, along with the Champions League from December 2017 to October 2006. Once a particular [game's web page](http://www.espn.com/soccer/commentary?gameId=323960) is hit, the scraper will store the page on disk as a flat file, where each day scraped is a new directory, and each league is a different subdirectory within each day. 

Example:
```data/ ->  20160203/   -> English_Premier_League_Table/   -> gameid=422425.txt, gameid=422425lineup.txt```

The individual game files are stored with the id given to them by ESPN. After the pages are cached, the scraper extracts information regarding shots on goal, yellow cards, red cards, substitutions. etc and stores this information as a document in a Couchdb instance. The purpose of caching the entire webpage is to allow the user to change the stored parameters/ modify analysis/extract different data down the line. 

This scraper was a fun opportunity to learn GoLang, which is a wonderful and straight-forward language.

### Getting expected goals

I parsed the commentaries (which are probably written in conjunction with a bot) for each game to determine the parameters of my expected goals model. Below are some examples of goals followed by a blocked attempt on goal:

```
Goal! Celtic 1, FC Bayern München 2. Javi Martínez (FC Bayern München) header from the centre of the box to the bottom left corner. Assisted by David Alaba with a cross.

Goal! Roma 3, Chelsea 0. Diego Perotti (Roma) right footed shot from outside the box to the bottom left corner. Assisted by Aleksandar Kolarov.

Goal! Paris Saint Germain 4, RSC Anderlecht 0. Layvin Kurzawa (Paris Saint Germain) header from the left side of the six yard box to the bottom left corner.

Attempt blocked. Fernando Llorente (Athletic de Bilbao) header from the centre of the box is blocked. Assisted by Andoni Iraola with a cross.
```

The match commentaries follow a specific order which makes them easier to scrape. For goals the order is:
```
Goal! <Home team><home team score>, <away team> <away team score>. <scorer> <Scorer team> [OPTIONAL] <body part> [OPTIONAL] <location on field> [OPTIONAL] <assist type> [OPTIONAL] <assister>.
```
The commentary order for missed or blocked attempts is similar. Since each attempt has at most three parameters, but can have only one is some cases, attempts with all three parameters as attempts with fewer parameters contribute to the percentages of attempts with few parameters as weel. This means if there are (goals)702/1312(attempts) for a `right footed shot from the left side of the 6 yard box with a throughball assist`, these attempts will also contribute to the success percentages for `right footed shot` and `shot from the left side of the 6 yard box`. Later, when trying to initialize a team's strength at the beginning of a simulation, the model tries to use as detailed a shot attempt as is given in the commentary to determine the overall number of expected goals.

I allowed the expected goal model to be generated across all leagues, as opposed to the league I'm trying to simulate, because during numerous tests (for the permier leagge), the constraining the model to just premier league attempts did not significantly affect the model in any way.

Here are some example tables of expected goal calculations from part of a premier league season:

#### For 2016, between 2016-08-05 and 2017-03-01 

| Team | Actual goal average | Expected goals average | Actual goals and Expected goals averaged |
| ----  |   ---   |   ---   |   --- |
| Swansea City  |   1.42285365588   |   1.23076923077   |   1.32681144333 |
| Southampton  |   1.7483768272   |   1.0625   |   1.4054384136 |
| Manchester United  |   2.10066063951   |   1.77777777778   |   1.93921920864 |
| Liverpool  |   2.24129513629   |   1.96551724138   |   2.10340618883 |
| Middlesbrough  |   0.893514382878   |   0.814814814815   |   0.854164598846 |
| Stoke City  |   1.417632479   |   1.12   |   1.2688162395 |
| Tottenham Hotspur  |   1.87715667843   |   1.81081081081   |   1.84398374462 |
| Burnley  |   1.25891822307   |   1.03703703704   |   1.14797763005 |
| West Ham United  |   1.56635504159   |   1.2962962963   |   1.43132566894 |
| Manchester City  |   2.37764553826   |   2.21621621622   |   2.29693087724 |
| Arsenal  |   2.21912888553   |   2.32352941176   |   2.27132914865 |
| Bournemouth  |   1.49211890521   |   1.32   |   1.4060594526 |
| Crystal Palace  |   1.44016665995   |   1.22222222222   |   1.33119444109 |
| West Bromwich Albion  |   1.36463229618   |   1.38461538462   |   1.3746238404 |
| Sunderland  |   1.26533900217   |   0.923076923077   |   1.09420796263 |
| Watford  |   1.14097579101   |   1.11111111111   |   1.12604345106 |
| Everton  |   1.62766468047   |   1.61538461538   |   1.62152464793 |
| Hull City  |   1.26060915744   |   0.923076923077   |   1.09184304026 |
| Chelsea  |   1.90300633612   |   2.24137931034   |   2.07219282323 |
| Leicester City  |   1.30612562134   |   1.05714285714   |   1.18163423924 |

The above data showes that generally, expected goal calculations are lower than the actual number of goals scored, with some notable exceptions being Chelsea, West Brom, and Arsenal. Chelsea ended up winning this season.


## Simulations
Every game being simulated is assumed to be played in 90 minutes, and goals are assumed to be independent events. Both assumptions are not true for all games (champions league knockout stages can go into extra time), and a team is (roughly) more likely to concede after just having conceded. [This slide deck/paper](http://www2.stat-athens.aueb.gr/~karlis/Bivariate%20Poisson%20Regression.pdf) suggests that **"Empirical evidence show small and not significant correlation (usually less than 0.05)"** so I thought this simplifying assumption was fair. Given these two assumptions I thought it was appropiate to use a Poision distribution. Since soccer is a low scoring game, and so the goal variance isn't so great (there's a reason why 7-1 was a big deal) I figured a possion distribution would work over a negative binomial distribution.

I considered using pymc3 so that I could use bayesian models to find relative team strengths, but in the end decided that a frequentist approach would be quicker (since its pretty easy to calculate the maximum likelihood parameter for a poisson distribution. In the future I plan to use a bayesian model to study team strengths.

The user of the model can specify when to start the simulation from, and the dates to use for initializing team strength. During my tests with the model, I would start part way through a season to get a sense of how strong a team is after thier summer signings. My scraper does not scrape friendlies, so the model does not have to account for teams playing non-competitive games. When initializing team strength, the scraper goes through all the cached commentaries and calculates the expected goal values based on the recorded attempts. When the expected goals are found for the previous **n** games, the model then tries to find the maximum likelihood estimator (the parameter that best describes the distribution that models the team's goals every game) of the observed data to define the team's poisson distribution for goals. Luckily, since we are working with simple poisson distributions, the process for finding the maximum likelihood estimator is nothing more than finding the average of the observed data! This estimator is consistent and unbaised which is good for the model. 

When two teams 'play' eachother in the simulator, the model is just sampling the team's respective distribution and compares  the output from both teams. This isn't such an effective technique when run just once, but when the model is run on 100 or 5000 simulations, the randomness from sampling from a teams distribution is somewhat reduced. A resonsble way of determining a ranking without going though a laborous game-by-game simulation process would be to just look at each teams' distribution and ranking by each team's &#955;parameter, but this isn't a very fun approach (nor does it capture any sense of randomness or uncertainty which is perhaps somewhere a bayesian model would be more effetive). The model was run in a setting where the model parameter was updated dynamically during a simulation (by using a running average to generate an MLE) and in a setting where the model parameter was kept constant during he simulation. The output did not differ significantly between these two sampling methods, which intuitively makes sense since we would be updating the distribution's parameter with an event that we genrated from the generative distribution. 

## Error function
To understand how accurate the model is, the model needs an interpretable error function. While testing, the error funtion used was: abs(true league position - average simulated league position). The maximum error using this model would be 200, which suggests that, on average, the 20 teams in the premier league are off by 10 positions as compared to the true final table.

## Some Output
Here's some output from simulating the past three premier league seasons, with each configuration run with 1000 simulations:

| Season | Type of goal model used | Error | Standard Deviation |
| --- | --- | --- | ---|
| 2016-2017 | Actual goals scored | 40.4 | 3.666|
| 2016-2017 | Expected goals scored | 39.6 | 3.980 |
| 2016-2017 | Average between Expected and Actual Goals | 39.0 | 3.715 |
| 2015-2016 | Actual goals scored | 61.0 | 4.219 |
| 2015-2016 | Expected goals scored | 62.8 | 3.487 |
| 2015-2016 | Average between Expected and Actual Goals | 62.8 | 3.487 |
| 2014-2015 | Actual goals scored | 47.6 | 2.653 |
| 2014-2015 | Expected goals scored | 50.2 | 3.736 |
| 2014-2015 | Average between Expected and Actual Goals | 52.0 | 4.195 |

Unfortunately the errors are quite close to eachother for all three types of goal counting methods  so I can't conclusively say that one method is better than another. This is probably due in part to the lack of granularity of information offered by the ESPN commentaries. The shot positions were quite vague ("Left side of the 16 yard box", "Outside of the box", "Far outside the box").

Interestingly, the errors aren't too large, for the 2016-2017 season, a team in my simulation was off its true position by around 1.9 places which is pretty cool.



