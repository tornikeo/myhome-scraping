from urllib import response
import scrapy
from scrapy import Spider
from scrapy.http import TextResponse
from scrapy.selector import Selector
from scrapy.exceptions import CloseSpider
import re
import requests
from tqdm.auto import tqdm

MAX_PAGES = 12327
page_num_pat = re.compile(r'\d+')
class MyHomeSpider(Spider):
    name = 'myhome'

    def start_requests(self):
        start_urls = [f'https://www.myhome.ge/en/s/?Page={n}' for n in range(1, MAX_PAGES)]
        for url in tqdm(start_urls):
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response: TextResponse):
        statement_cards = response.css('#main_block > div.d-flex.justify-content-between.p-relative.search-content.has-map > div.search-wrap > div.search-contents.ml-0 > div > div > a')

        if len(statement_cards) == 0:
            raise CloseSpider(reason='done scraping')
        
        for statement_card in statement_cards:
            yield response.follow(
                url=statement_card, 
                callback=self.parse_statement, 
                # cb_kwargs=dict(statement_card=statement_card),
            )

        # pagination_links = response.css('li.next a')
        # next_url = page_num_pat.findall(response.url)[0]
        # yield from response.follow_all(pagination_links, self.parse)

    def parse_statement(self, statement_page: TextResponse, statement_card: Selector = None):

        image_url_format = ''
        # Also add images

        num = page_num_pat.findall(statement_page.url)[0]
        img_path = "/".join(list(num[::-1][:5]))

        selectors = dict(
            title='#main_block > div.detail-page > div.statement-header > div.statement-title *:not(svg)::text',
            stats='#main_block > div.detail-page > div.statement-header > div.info.d-flex.flex-wrap span::text',
            author='#main_block > div.detail-page > div.statement-author.align-items-center.flex-wrap > div:nth-child(2) *:not(svg)::text',
            main_features='#main_block > div.detail-page > div.main-features.row.no-gutters span::text ',
            text_desc='#main_block > div.detail-page > div.description > div:nth-child(2) > div *:not(svg)::text',
            amenities='#main_block > div.detail-page > div.amenities span *::text',
            price_gel='#main div.price-toggler-wrapper span::attr(data-price-gel)',
            price_usd='#main div.price-toggler-wrapper span::attr(data-price-usd)',
            guest_num='#main_block > div.detail-page > aside > div.price-box > div._asd > div.persons > span:not(.no) *::text',
            lat='#map ::attr(data-lat)',
            lng='#map ::attr(data-lng)',
            cadastral_code='#main_block > div.detail-page > div.statement-header > div.cadastral.d-flex.flex-wrap.mb-2 > span *::text',
            hr24_views_alert='#main_block > div.detail-page > aside > div.alert.alert-success.see-alert *::text'
        )

        meta_data = dict(
            url=statement_page.url,
            prod_link_tree=statement_page.css('div.product-link-tree a::text').getall(),
            image_dir=f'{num}', # added in the future!
        )

        # img_resp = requests.get(
        #     url=f"https://static.my.ge/myhome/photos/{img_path}/thumbs/{num}_{n}.jpg",
        #     headers={
        #     "sec-ch-ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"",
        #     "sec-ch-ua-mobile": "?0",
        #     "sec-ch-ua-platform": "\"Linux\"",
        #     "Referer": "https://www.myhome.ge/",
        #     "Referrer-Policy": "strict-origin-when-cross-origin"
        #     },
        # )
        # img_data = img_resp.content
        # with open('image_name.jpg', 'wb') as handler:
        #     handler.write(img_data)
        # for key in data.keys():
        #     vals = []
        #     for v in vals: statement_page.css(data[key]).getall()

        def str_prep(s):
            s = s.strip()
            s = re.sub(r'\t+',' ',s)
            return s
        data = {k: tuple(str_prep(s) for s in statement_page.css(v).getall()) for k,v in selectors.items()}
        data = {**data, **meta_data}
        yield  data 