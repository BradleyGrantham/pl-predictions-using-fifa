import scrapy
from slugify import slugify


class FifaSpider(scrapy.Spider):
    name = "fifastats"

    def start_requests(self):
        urls = [
            'https://www.fifaindex.com/players/',
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
            # position = response.css('div.col-lg-4').css('div.panel-body').css('p')[2].css('a::attr(title)').extract()[0]
        except IndexError:
            team = response.css('div.col-lg-4').css('div.panel-heading').css('a::attr(title)')[0].extract()
            # position = response.css('div.col-lg-4').css('div.panel-body').css('p')[0].css('a::attr(title)').extract()[0]

        position = response.css('div.col-lg-5').css('div.panel-body').css('span.label::text').extract_first()

        rating = response.css('div.col-lg-5').css('div.panel-heading').css('span.label')[0].css('span.label::text').extract()[0]

        yield {
            'name': slugify(name),
            'info' : {
                'raw team' : team,
                'team': slugify(team),
                'position': position,
                'raw name': name,
                'rating': int(rating),
            }
        }


class MatchSpider(scrapy.Spider):
    name = "matchlineups"

    def start_requests(self):
        urls = [
            'http://www.betstudy.com/soccer-stats/c/england/premier-league/d/results/2017-2018/',
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
        
        home_lineup = lineups.css('table.info-table')[0]
        away_lineup = lineups.css('table.info-table')[1]

        home_lineup = [slugify(x) for x in home_lineup.css('tr td.left-align').css('a::attr(title)').extract()]
        away_lineup = [slugify(x) for x in away_lineup.css('tr td.left-align').css('a::attr(title)').extract()]

        yield {
            'match number': int(match_number),
            'info' : {
                'date' : date,
                'home team': slugify(home_team),
                'away team': slugify(away_team),
                'home goals': int(home_goals),
                'away goals': int(away_goals),
                'home lineup': ';'.join(home_lineup),
                'away lineup': ';'.join(away_lineup),
                'url': url,
            }
        }

