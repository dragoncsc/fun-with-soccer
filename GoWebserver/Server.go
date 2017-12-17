
package main

import (
	"fmt"
	"net/http"
	"regexp"
	"html/template"
	"errors"
	"github.com/go-redis/redis"
	"strings"
	"time"
	"os"
	"sync"
	"github.com/PuerkitoBio/goquery"
	"path/filepath"
	"io/ioutil"
	//"bytes"
	//"go/doc"
)

type Page struct {
	Title string
	HTML string
}

type pageScrape struct{
	wg sync.WaitGroup
	sem chan int
}

// Important global variables
var templates = template.Must(template.ParseFiles("edit.html", "view.html"))
var validPath = regexp.MustCompile("^/(edit|save|view|player)/([a-zA-Z0-9% ]+)$")
var client = redis.NewClient(&redis.Options{
						Addr:     "localhost:6379",
						Password: "", // no password set
						DB:       3,  // use DB
						})
var wantedLeages = map[string]bool{"Spanish Primera División": true, "World Cup Qualifying - UEFA":true,
"World Cup Qualifying - CONMEBOL":true,
"English Premier League":true, "German Bundesliga":true, "UEFA Europa League":true,
"Spanish Primera Division":true, "FIFA World Cup":true,
"Italian Serie A":true, "French Ligue 1":true,
"UEFA Champions League":true}

func getTitle(w http.ResponseWriter, r *http.Request) (string, error) {
	println(r.URL.Path)
	m := validPath.FindStringSubmatch(r.URL.Path)
	println(m)
	if m == nil {
		http.NotFound(w, r)
		return "", errors.New("Invalid Page Title")
	}
	return m[2], nil // The title is the second subexpression.
}

func handler(w http.ResponseWriter, r *http.Request){
	fmt.Fprintf(w, "Hi, I love %s!", r.URL.Path[1:])
}

func renderTemplate(w http.ResponseWriter, tmpl string, p *Page) {

	tpl := template.Must(template.ParseFiles(tmpl + ".html"))
	tplVars := map[string]interface{} {
		"Html": template.HTML(p.HTML),
		"Title": p.Title,
	}

	err := tpl.Execute(w, tplVars)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

func playerModel(w http.ResponseWriter, r *http.Request){
	player, err := getTitle(w, r)
	if err != nil{
		return
	}
	player = strings.Replace(player, "%20", " ", -1)
	playerModelTable := loadPlayer(player)
	renderTemplate(w, "edit", &Page{Title:player, HTML: playerModelTable})
}

func loadPlayer(player string) (string){
	playerPage, err := client.Get(player).Result()
	if err != nil{
		println("Error for player: " + player)
		println("Error:: " + err.Error())
		return "<h1 class='header' align='center' style='font-size: 64.1127px;'>"+
			"No model for " + player + "</h1>"
	}
	return playerPage
}


// Functions for scraping
// exists returns whether the given file or directory exists or not
func exists(path string) (bool, error) {
	_, err := os.Stat(path)
	if err == nil { return true, nil }
	if os.IsNotExist(err) { return false, nil }
	return true, err
}


func updateSoccerPages(){
	today:= time.Now().Local()

	til := time.Date(
		2017, 10, 10, 0, 0, 0, 0, time.UTC)
	println("Til:: " + til.Format("2006-01-02"))
	println("Today:: " + today.Format("2006-01-02"))
	scraperRun(today, til)

}


func scraperRun(from time.Time, to time.Time){
	cntr := 1
	var wg sync.WaitGroup
	// added later on to make sure we don't spawn too many go routines
	// since each go routine can make ~400 site hits
	const MAX = 37
	// used to make sure we don't exit without all other threads exiting
	// using both WaitGroup for fun/learning and so that main() will
	// keep running even after the last MAX go routines have spun off
	var trackPages = pageScrape{wg, make(chan int, MAX)}
	// initialize the incremented date with current date
	// have a counter running that is input into AddDate to
	// lower the date
	for tmp := time.Date(
		from.Year(), from.Month(), from.Day(),
		0, 0, 0, 0, time.UTC);
		to.Before(tmp); cntr += 1 {
			println("Starting run")
			// add an int to sem, if MAX ints have been added then this will block
			trackPages.sem <- 1
			// decrementing dates is strange in Golang
			tmp := from.AddDate(0, 0, -1*cntr)
			trackPages.wg.Add(1)
			go processDate(from.AddDate(0, 0, -1*cntr), &trackPages)
			if !to.Before(tmp) {
				break
			}
	}
	trackPages.wg.Wait()

}

func processDate( from time.Time , trackPages * pageScrape){

	resp, err := http.Get("http://www.espn.com/soccer/scoreboard/_/league/all/date/" +
		from.Format("20060102"))
	check(err, "get call")
	byte, err := ioutil.ReadAll(resp.Body)
	resp.Body.Close()
	if err != nil{
		println("Skipping: " + from.Format("2006-01-02"))
	}
	println("Closed, creating directory")
	if _, err := os.Stat("../data/"+from.Format("20060102")); err != nil {
		println("Made directory")
		os.MkdirAll(filepath.Join("../data/", from.Format("20060102")), 0755)
	}
	ioutil.WriteFile(filepath.Join("../data/", from.Format("20060102"),
		from.Format("20060102")+".txt"), byte, 0755)
	println("About to look for link")
	findGameFiles(fmt.Sprintf("%s", byte), from, trackPages)
	// decrement the counter again to signal that this thread is done
	trackPages.wg.Done()
	// remove int from sem so that we can load another page
	<- trackPages.sem
	}


func findGameFiles(pageText string, from time.Time, trackPages * pageScrape)	{

	var matchURL = regexp.MustCompile( `www\.espnfc\.us\/commentary\?gameId=\d+`)
	gameIDList := matchURL.FindAllString(pageText, -1)

	for i := 0; i < len(gameIDList); i ++{
		println("Found another page: " + gameIDList[i])
		trackPages.wg.Add(1)
		go grabPage(from.Format("20060102"), gameIDList[i], trackPages)

	}
}

func grabPage( date string, page string, trackPages * pageScrape){
		// build new goquery
		doc, err := goquery.NewDocument("http://" + page)
		check(err, "creating new document")
		// grab HTML from document so we have both HTML tree and a string for writing to file
		tmp, _ :=doc.Html()
		// use CSS selector found with the browser inspector
		// for each, use index and item
		doc.Find(".sub-module header").Each(func(index int, item *goquery.Selection) {
			linkTag := item
			linkText := linkTag.Text()
			if strings.Contains(linkText, "Standings") == true {
				str := strings.TrimSpace(linkText)
				league := str[:len(str)-10]
				fmt.Printf("Link #%d: '%s'\n", index, league + " Table")
				if wantedLeages[league]{
					// check if league directory already exists
					leagueDir := strings.Replace(league+" Table", " ", "_", -1)
					if _, err := os.Stat("../data/"+date + "/" + leagueDir); err != nil {
						println("Made directory")
						os.MkdirAll(filepath.Join("../data/",date,leagueDir), 0755)
					}
					// grab other pages from game
					var lineup = grabAdditionPages(strings.Replace(page, "commentary", "lineups", 1))
					var stats = grabAdditionPages(strings.Replace(page, "lineups", "matchstats", 1))

					gameName := strings.Split(page, "?")
					println("Writing file")
					ioutil.WriteFile(filepath.Join("../data/",date,
						leagueDir, gameName[1]+".txt"), []byte(tmp), 0755)
					ioutil.WriteFile(filepath.Join("../data/",date,
						leagueDir, gameName[1]+"lineup.txt"), []byte(lineup), 0755)
					ioutil.WriteFile(filepath.Join("../data/",date,
						leagueDir, gameName[1]+"stats.txt"), []byte(stats), 0755)
				}
			}
		})
		trackPages.wg.Done()
	}

func grabAdditionPages(pg string) string{
	goq, err := goquery.NewDocument("http://" + pg)
	check(err, "getting goquery for: "+pg)
	html, err := goq.Html()
	check(err, "converting to html: "+pg)
	return html
}

func check(e error, s string) {
	if e != nil {
		println("Panic in: " + s)
		panic(e)
	}
}


func main() {
	today:= time.Now().Local()
	prev := today.AddDate(0, 0, -1)
	println(prev.Format("20060102"))
	updateSoccerPages()

	http.HandleFunc("/", handler)
	http.HandleFunc("/player/", playerModel)
	//println(http.ListenAndServe(":8080", nil).Error())

}
