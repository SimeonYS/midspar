import re
import scrapy
from scrapy.loader import ItemLoader
from ..items import MidsparItem
from itemloaders.processors import TakeFirst
import requests
import json
from scrapy import Selector

pattern = r'(\xa0)?'
url = "https://midspar.dk/wp-admin/admin-ajax.php"

payload = "action=loadmorepost&page={}&department=0&more=true&termid=9&hovedkontor=false"
headers = {
    'authority': 'midspar.dk',
    'pragma': 'no-cache',
    'cache-control': 'no-cache',
    'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'x-requested-with': 'XMLHttpRequest',
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://midspar.dk',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://midspar.dk/category/nyheder/',
    'accept-language': 'en-US,en;q=0.9',
    'cookie': 'nmstat=f1c418cd-5c05-589c-9e22-0a0a2f52eeac; CookieConsent={stamp:%27e98aHKJpBGxwmrzOejAnJPlefBy5AnuACz9BftjhJOx2aaxDeCFUEQ==%27%2Cnecessary:true%2Cpreferences:true%2Cstatistics:true%2Cmarketing:true%2Cver:1%2Cutc:1615214322795%2Cregion:%27bg%27}; _ga=GA1.2.2051422233.1615214325; _hjid=b5a6b371-eee3-42c4-b3fb-282d0ba1474e; _fbp=fb.1.1615214325215.716538884; _gid=GA1.2.1222786949.1616414013; _dc_gtm_UA-1284915-1=1; _hjIncludedInPageviewSample=1; _hjAbsoluteSessionInProgress=0; _hjIncludedInSessionSample=0; _sn_m={"r":{"n":0,"r":"midspar"},"cs":{"5981":{"u":1},"1d2b":{"u":1}}}; SNS=1; _sn_a={"a":{"s":1616414023150,"e":1616414023148},"v":"908ded8d-4389-4834-8ecd-9b70c9fb62c7","g":{"sc":{"5981776d-2128-437c-8507-a45579ddaf9d":1}}}; _sn_n={"a":{"i":"9beddcee-f888-48b4-a7d9-4d6288b1e74e"},"cs":{"4645":{"t":{"i":1,"c":"5981776d-2128-437c-8507-a45579ddaf9d"}},"5981":{"i":[1647950034305,1],"c":1}},"ssc":1}'
}


class MidsparSpider(scrapy.Spider):
    name = 'midspar'
    page = 1
    start_urls = ['https://midspar.dk/category/nyheder/']

    def parse(self, response):
        data = requests.request("POST", url, headers=headers, data=payload.format(self.page))
        data = json.loads(data.text)
        container = data['html']
        for post in Selector(text=container).xpath('//a'):
            link = post.xpath('.//@href').get()
            date = post.xpath('.//p[@class="indledente-title"]/text()').get().strip()
            yield response.follow(link, self.parse_post, cb_kwargs=dict(date=date))

        if not container == "":
            self.page += 1
            yield response.follow(response.url, self.parse, dont_filter=True)

    def parse_post(self, response, date):
        title = response.xpath('//h1/text()').get()
        if not title:
            title = ''.join(response.xpath('//div[@class="message-block-title"]//text()').getall()).strip()
        content = response.xpath('//section[contains(@class,"container")]//text()[not (ancestor::h1 or ancestor::p[@class="date cdm-speech-text"] or ancestor::div[@id="breadcrumbs"] or ancestor::section[@id="buttons"] or ancestor::div[@class="image-with-text-left full"])]').getall()
        content = [p.strip() for p in content if p.strip()]
        content = re.sub(pattern, "",' '.join(content))

        item = ItemLoader(item=MidsparItem(), response=response)
        item.default_output_processor = TakeFirst()

        item.add_value('title', title)
        item.add_value('link', response.url)
        item.add_value('content', content)
        item.add_value('date', date)

        yield item.load_item()
