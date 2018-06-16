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

        team = response.css('div.col-lg-4').css('div.panel-heading').css('a::attr(title)')[0].extract()

        position = response.css('div.col-lg-4').css('div.panel-body').css('p')[0].css('a::attr(title)').extract()[0]

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
