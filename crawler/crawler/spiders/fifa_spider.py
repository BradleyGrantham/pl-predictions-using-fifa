import scrapy
from slugify import slugify


class FifaSpider(scrapy.Spider):
    name = "fifastats"

    # TODO - run this for extended period of time to get all players

    def start_requests(self):
        urls = [
            # 'https://www.fifaindex.com/players/',
            'https://www.fifaindex.com/players/fifa17_173/',
            'https://www.fifaindex.com/players/fifa16_73/',
            'https://www.fifaindex.com/players/fifa15_14/',
            'https://www.fifaindex.com/players/fifa14_13/',
            'https://www.fifaindex.com/players/fifa13_10/',

        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        for row in response.css('tr td'):
            link = row.css('a::attr(href)').extract()
            # print(name, link)
            if link: 
                if '/player/' in link[0]:
                    url = response.urljoin(link[0])
                    yield scrapy.Request(url, callback=self.parse_player)

        next_page = response.css('li.next a::attr(href)').extract_first()
        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.parse)

    def parse_player(self, response):
        name = response.css('div.media-body').css('h2.media-heading::text').extract()[0]

        try:
            team = response.css('div.col-lg-4').css('div.panel-heading').css('a::attr(title)')[2].extract()
        except IndexError:
            team = response.css('div.col-lg-4').css('div.panel-heading').css('a::attr(title)')[0].extract()

        number = response.css('div.col-lg-4').css('div.panel-body').css('span.pull-right')[3].css(
                'span::text').extract()[0]

        if len(number) == 4:
            number = response.css('div.col-lg-4').css('div.panel-body').css('span.pull-right')[1].css(
                'span::text').extract()[0]

        position = response.css('div.col-lg-5').css('div.panel-body').css('span.label::text').extract_first()

        rating = response.css('div.col-lg-5').css('div.panel-heading').css('span.label')[0].css('span.label::text').extract()[0]

        nationality = slugify(response.css('h2.subtitle a::text').extract()[0])

        yield {
            'name': slugify(name),
            'info': {
                'raw team': team,
                'team': slugify(team),
                'position': position,
                'raw name': name,
                'rating': int(rating),
                'kit number': number,
                'nationality': nationality,
                'url': response.request.url,
            }
        }


class MatchSpider(scrapy.Spider):
    name = "matchlineups"

    # TODO - want the other names - not full names

    def start_requests(self):
        urls = [
            'http://www.betstudy.com/soccer-stats/c/england/premier-league/d/results/2017-2018/',
            'http://www.betstudy.com/soccer-stats/c/england/premier-league/d/results/2016-2017/',
            'http://www.betstudy.com/soccer-stats/c/england/premier-league/d/results/2015-2016/',
            'http://www.betstudy.com/soccer-stats/c/england/premier-league/d/results/2014-2015/',
            'http://www.betstudy.com/soccer-stats/c/england/premier-league/d/results/2013-2014/',

        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_fixtures_page)

    def parse_fixtures_page(self, response):
        for info_button in response.css('ul.action-list').css('a::attr(href)'):
            url = response.urljoin(info_button.extract())
            yield scrapy.Request(url, callback=self.parse_match_page)

    def parse_match_page(self, response):
        
        home_team, away_team = response.css('div.player h2 a::text').extract()

        date = response.css('em.date').css('span.timestamp::text').extract_first()

        url = response.request.url

        match_number = response.request.url.split('-')[-1].split('/')[0]

        home_goals, away_goals = response.css('div.info strong.score::text').extract_first().split('-')
        
        for table in response.css('div.table-holder'):
            if table.css('h2::text').extract_first() == 'Lineups and subsitutes':
                lineups = table
        
        home_lineup_css = lineups.css('table.info-table')[0]
        away_lineup_css = lineups.css('table.info-table')[1]

        home_lineup_raw = [slugify(x) for x in home_lineup_css.css('tr td.left-align').css('a::attr(title)').extract()]
        away_lineup_raw = [slugify(x) for x in away_lineup_css.css('tr td.left-align').css('a::attr(title)').extract()]

        home_lineup = [slugify(x) for x in home_lineup_css.css('tr td.left-align').css('a::text').extract()]
        away_lineup = [slugify(x) for x in away_lineup_css.css('tr td.left-align').css('a::text').extract()]

        home_lineup_number = [int(x) for x in home_lineup_css.css('tr td.size23 strong::text').extract()]
        away_lineup_number = [int(x) for x in away_lineup_css.css('tr td.size23 strong::text').extract()]

        home_lineup_nationality = [int(x) for x in home_lineup_css.css('tr td.left-align::attr(alt)').extract()]
        away_lineup_nationality = [int(x) for x in away_lineup_css.css('tr td.left-align::attr(alt)').extract()]

        home_lineup_nationality = [slugify(x) for x in
                                   home_lineup_css.css('tr td.left-align').css('img.flag-ico::attr(alt)').extract()]
        away_lineup_nationality = [slugify(x) for x in
                                   away_lineup_css.css('tr td.left-align').css('img.flag-ico::attr(alt)').extract()]

        yield {
            'match number': int(match_number),
            'info': {
                'date': date,
                'home team': slugify(home_team),
                'away team': slugify(away_team),
                'home goals': int(home_goals),
                'away goals': int(away_goals),
                'home lineup raw names': home_lineup_raw,
                'away lineup raw names': away_lineup_raw,
                'home lineup names': home_lineup,
                'away lineup names': away_lineup,
                'home lineup numbers': home_lineup_number,
                'away lineup numbers': away_lineup_number,
                'home lineup nationalities': home_lineup_nationality,
                'away lineup nationalities': away_lineup_nationality,
                'url': url,
            }
        }


class FifaIndexTeamScraper(scrapy.Spider):
    name = "fifa-index-team"

    # TODO - run this for extended period of time to get all players

    def start_requests(self):
        urls = [
            'https://www.fifaindex.com/teams/',
            'https://www.fifaindex.com/teams/fifa17_173/',
            'https://www.fifaindex.com/teams/fifa16_73/',
            'https://www.fifaindex.com/teams/fifa15_14/',
            'https://www.fifaindex.com/teams/fifa14_13/',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        links = [a.extract() for a in response.css('td a::attr(href)')]
        for link in links:
            if '/team/' in link:
                url = response.urljoin(link)
                yield scrapy.Request(url, callback=self.parse_team)

        next_page = response.css('li.next a::attr(href)').extract_first()
        if next_page is not None and int(next_page.split('/')[-2]) < 10:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.parse)

    def parse_team(self, response):
        team = slugify(response.css('.media-heading::text').extract_first())

        for i in range(1, len(response.css('tr'))):
            name = slugify(response.css('.table > tbody:nth-child(2) > tr:nth-child({}) > td:nth-child(6) > a:nth-child(1)::attr(title)'.format(i)).extract_first())
            number = int(response.css('.table > tbody:nth-child(2) > tr:nth-child({}) > td:nth-child(1)::text'.format(i)).extract_first())
            nationality = slugify(response.css('.table > tbody:nth-child(2) > tr:nth-child({}) > td:nth-child(4) > a:nth-child(1) > img:nth-child(1)::attr(title)'.format(i)).extract_first())
            position = response.css('.table > tbody:nth-child(2) > tr:nth-child({}) > td:nth-child(7) > a:nth-child(1) > span:nth-child(1)::text'.format(i)).extract_first()
            rating = response.css('table > tbody:nth-child(2) > tr:nth-child({}) > td:nth-child(5) > span:nth-child(1)::text'.format(i)).extract_first()


            yield {
                'name': slugify(name),
                'team': team,
                'position': position,
                'rating': int(rating),
                'number': number,
                'nationality': nationality,
                'url': response.request.url
            }
