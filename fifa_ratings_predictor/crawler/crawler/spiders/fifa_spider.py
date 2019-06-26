import scrapy
from slugify import slugify


class FifaSpider(scrapy.Spider):
    name = "fifastats"
    latest_season = "fifa19"

    # TODO - run this for extended period of time to get all players
    def start_requests(self):
        urls = [
            "https://www.fifaindex.com/players/fifa19/",
            "https://www.fifaindex.com/players/fifa18/",
            "https://www.fifaindex.com/players/fifa17/",
            "https://www.fifaindex.com/players/fifa16/",
            "https://www.fifaindex.com/players/fifa15/",
            "https://www.fifaindex.com/players/fifa14/",
            "https://www.fifaindex.com/players/fifa13/",
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        for player_row in response.css("tr"):
            link = player_row.css("figure.player a::attr(href)").get()
            if link:
                if "/player/" in link:
                    # extract team
                    team = player_row.css("a.link-team")
                    if team:
                        # only add if player has a team
                        team_name = team.attrib["title"]
                        request = response.follow(link, callback=self.parse_player)
                        # pass additional parameter for the player
                        request.meta["team"] = team_name
                        yield request

        for page_link in response.css(".pagination a.page-link"):
            text = page_link.css("::text").get()
            next = page_link.attrib["href"]
            if "Next" in text:
                print("Next page:", next)
                yield response.follow(next, callback=self.parse)

    def parse_player(self, response):
        name = response.css("img.player").attrib["title"]
        
        team = response.meta["team"]
        if not team:
            # gives the title of the first occurence
            team = (
                response.css("div.team")
                .css("a.link-team")
                .attrib["title"]
            )

        number = (
            response.css("div.team")    # multiple results when multiple teams !
            .css("span.float-right::text")
            .get()
        )

        position = (
            response.css("div.team")    # multiple results when multiple teams !
            .css("a.link-position")
            .attrib["title"]
        )

        rating = response.css(".card-header span.rating::text").get() # first: total, second: potential

        nationality = response.css("a.link-nation").attrib["title"]

        url = response.request.url

        season = url.split("/")[-2]
        if "/fifa" not in url:
            season = self.latest_season

        yield {
            "name": slugify(name),
            "info": {
                "raw team": team,
                "team": slugify(team),
                "position": position,
                "raw name": name,
                "rating": int(rating),
                "kit number": number,
                "nationality": slugify(nationality),
                "season": season,
                "url": url,
            },
        }


class MatchSpider(scrapy.Spider):
    name = "matchlineups"

    # TODO - want the other names - not full names

    def start_requests(self):
        urls_france = [
            "http://www.betstudy.com/soccer-stats/c/france/ligue-1/d/results/2018-2019/",
            "http://www.betstudy.com/soccer-stats/c/france/ligue-1/d/results/2017-2018/",
            "http://www.betstudy.com/soccer-stats/c/france/ligue-1/d/results/2016-2017/",
            "http://www.betstudy.com/soccer-stats/c/france/ligue-1/d/results/2015-2016/",
            "http://www.betstudy.com/soccer-stats/c/france/ligue-1/d/results/2014-2015/",
            "http://www.betstudy.com/soccer-stats/c/france/ligue-1/d/results/2013-2014/",
            "http://www.betstudy.com/soccer-stats/c/france/ligue-1/d/results/2012-2013/"
        ]
        urls_england = [
            "http://www.betstudy.com/soccer-stats/c/england/premier-league/d/results/2018-2019/",
            "http://www.betstudy.com/soccer-stats/c/england/premier-league/d/results/2017-2018/",
            "http://www.betstudy.com/soccer-stats/c/england/premier-league/d/results/2016-2017/",
            "http://www.betstudy.com/soccer-stats/c/england/premier-league/d/results/2015-2016/",
            "http://www.betstudy.com/soccer-stats/c/england/premier-league/d/results/2014-2015/",
            "http://www.betstudy.com/soccer-stats/c/england/premier-league/d/results/2013-2014/",
            "http://www.betstudy.com/soccer-stats/c/england/premier-league/d/results/2012-2013/"
        ]
        urls_germany = [
            "http://www.betstudy.com/soccer-stats/c/england/premier-league/2018-2019/",
            "http://www.betstudy.com/soccer-stats/c/england/premier-league/2017-2018/",
            "http://www.betstudy.com/soccer-stats/c/england/premier-league/2016-2017/",
            "http://www.betstudy.com/soccer-stats/c/england/premier-league/2015-2016/",
            "http://www.betstudy.com/soccer-stats/c/england/premier-league/2014-2015/",
            "http://www.betstudy.com/soccer-stats/c/england/premier-league/2013-2014/",
            "http://www.betstudy.com/soccer-stats/c/england/premier-league/2012-2013/"
        ]
        urls = urls_england
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_fixtures_page)

    def parse_fixtures_page(self, response):
        for info_button in response.css("ul.action-list").css("a::attr(href)"):
            url = info_button.get()
            yield response.follow(url, self.parse_match_page)

    def parse_match_page(self, response):

        home_team, away_team = response.css("div.player h2 a::text").getall()

        date = response.css("em.date").css("span.timestamp::text").get()

        url = response.request.url

        match_number = response.request.url.split("-")[-1].split("/")[0]

        home_goals, away_goals = (
            response.css("div.info strong.score::text").get().split("-")
        )

        for table in response.css("div.table-holder"):
            if table.css("h2::text").get() == "Lineups and subsitutes":
                lineups = table

        home_lineup_css = lineups.css("table.info-table")[0]
        away_lineup_css = lineups.css("table.info-table")[1]

        home_lineup_raw = [
            slugify(x)
            for x in home_lineup_css.css("tr td.left-align")
            .css("a::attr(title)")
            .extract()
        ]
        away_lineup_raw = [
            slugify(x)
            for x in away_lineup_css.css("tr td.left-align")
            .css("a::attr(title)")
            .extract()
        ]

        home_lineup = [
            slugify(x)
            for x in home_lineup_css.css("tr td.left-align").css("a::text").getall()
        ]
        away_lineup = [
            slugify(x)
            for x in away_lineup_css.css("tr td.left-align").css("a::text").getall()
        ]

        home_lineup_number = [
            int(x) for x in home_lineup_css.css("tr td.size23 strong::text").getall()
        ]
        away_lineup_number = [
            int(x) for x in away_lineup_css.css("tr td.size23 strong::text").getall()
        ]

        home_lineup_nationality = [
            slugify(x)
            for x in home_lineup_css.css("tr td.left-align")
            .css("img.flag-ico::attr(alt)")
            .getall()
        ]
        away_lineup_nationality = [
            slugify(x)
            for x in away_lineup_css.css("tr td.left-align")
            .css("img.flag-ico::attr(alt)")
            .getall()
        ]

        yield {
            "match number": int(match_number),
            "info": {
                "date": date,
                "home team": slugify(home_team),
                "away team": slugify(away_team),
                "home goals": int(home_goals),
                "away goals": int(away_goals),
                "home lineup raw names": home_lineup_raw,
                "away lineup raw names": away_lineup_raw,
                "home lineup names": home_lineup,
                "away lineup names": away_lineup,
                "home lineup numbers": home_lineup_number,
                "away lineup numbers": away_lineup_number,
                "home lineup nationalities": home_lineup_nationality,
                "away lineup nationalities": away_lineup_nationality,
                "url": url,
            },
        }


class FifaIndexTeamScraper(scrapy.Spider):
    name = "fifa-index-team"
    latest_season = "fifa19"

    # TODO - run this for extended period of time to get all players

    def start_requests(self):
        urls = [
            "https://www.fifaindex.com/teams/fifa19/",
            "https://www.fifaindex.com/teams/fifa18/",
            "https://www.fifaindex.com/teams/fifa17/",
            "https://www.fifaindex.com/teams/fifa16/",
            "https://www.fifaindex.com/teams/fifa15/",
            "https://www.fifaindex.com/teams/fifa14/",
            "https://www.fifaindex.com/teams/fifa13/",
            "https://www.fifaindex.com/teams/fifa12/"
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        for team_row in response.css("table.table-teams tr"):
            link = team_row.css("td a.link-team::attr(href)").get()
            if link:
                if "/team/" in link:
                    yield response.follow(link, callback=self.parse_team)

        for page_link in response.css(".pagination a.btn"):
            text = page_link.css("::text").get()
            next = page_link.attrib["href"]
            if "Next" in text and int(next.split("/")[-2]) < 10:    # < 10 for 1. Bundesliga, < 15 for 2. Bundesliga
                print("Next page:", next)
                yield response.follow(next, callback=self.parse)

    def parse_team(self, response):
        team = slugify(response.css("div h1::text").get())
        print(team)

        players_table = response.css('table.table-players')[0]
        for player in players_table.css('tbody tr'):
            player_name_link = player.css("td:nth-child(6) a.link-player")

            name = player_name_link.attrib["title"]

            url = player_name_link.attrib["href"]

            season = url.split("/")[-2]
            if "/fifa" not in url:
                season = self.latest_season

            number = int(player.css("td:nth-child(1)::text").get())
            
            nationality = player.css("td:nth-child(4) a::attr(title)").get()

            for position_option in player.css("span.position::text").getall():
                if position_option not in ["Sub", "Res"]:
                    position = position_option
                    break

            rating = player.css("td:nth-child(5) span.rating::text").get()
            
            yield {
                "name": slugify(name),
                "team": team,
                "position": position,
                "rating": int(rating),
                "number": number,
                "nationality": slugify(nationality),
                "season": season,
                "url": url,
            }

class FixturesSpider(scrapy.Spider):
    name = "fixtures"

    # TODO - want the other names - not full names

    def start_requests(self):
        more_urls = [
            "https://www.betstudy.com/soccer-stats/c/germany/bundesliga/d/fixtures/",
            "http://www.betstudy.com/soccer-stats/c/england/premier-league/d/fixtures/"
        ]
        urls = [
            "https://www.betstudy.com/soccer-stats/c/france/ligue-1/d/fixtures/"
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_fixtures)

    @staticmethod
    def parse_fixtures(response):
        for fixture in response.css("tr")[1:]:
            home_team = fixture.css("td.right-align a::text").get()
            away_team = fixture.css("td.left-align a::text").get()
            date = fixture.css("td::text").get()
            yield {
                "date": date,
                "home team": slugify(home_team),
                "away team": slugify(away_team),
                "url": response.request.url,
            }
