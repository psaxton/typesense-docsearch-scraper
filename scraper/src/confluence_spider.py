"""
ConfluenceSpider
"""
from scrapy.spiders import Spider
from scrapy.http import Request
from .strategies.default_strategy import DefaultStrategy
from .typesense_helper import TypesenseHelper
import os

class ConfluenceSpider(Spider):
    """
    ConfluenceSpider
    """
    typesense_helper: TypesenseHelper = None
    strategy: DefaultStrategy = None
    get_content_url = ""
    headers = { }
    base_url = ""

    def __init__(self, typesense_helper, strategy):
        # Scrapy config
        self.name = 'confluence'
        self.js_render = False
        self.remove_get_params = False
        self.typesense_helper = typesense_helper
        self.strategy = strategy
        self.base_url = os.environ.get("CONFLUENCE_BASE_URL", None)
        space_key = os.environ.get("CONFLUENCE_SPACE_KEY", None)
        page_limit = os.environ.get("CONFLUENCE_PAGE_LIMIT", "100")
        api_key = os.environ.get("CONFLUENCE_API_KEY", None)
        self.get_content_url = f'{self.base_url}/rest/api/content?type=page&spaceKey={space_key}&expand=body.storage&limit={page_limit}'
        self.headers = {'Authorization' : f'Bearer {api_key}' }

    def start_requests(self):
        yield Request(self.get_content_url, headers = self.headers, callback = self.parse)

    def parse(self, response):
        response_json = response.json()
        for result in response_json['results']:
            html = f"""
            <!DOCTYPE html>
            <html lang="en-US" >
                <body id="com-atlassian-confluence" class="theme-default aui-layout aui-theme-default">
                    <h1 id="title-text" class="with-breadcrumbs">
                        <a href="/confluence{result['_links']['webui']}">{result['title']}</a>
                    </h1>
                    <div id="main-content" class="wiki-content">
                        {result['body']['storage']['value']}
                    </div>
                </body>
            </html>
            """

            page_relative_url = result["_links"]["webui"]
            current_page_url = f'{self.base_url}{page_relative_url}'
            records = self.strategy.get_records_from_response(html, current_page_url, is_confluence=True)
            self.typesense_helper.add_records(records, response.url, False)
            ConfluenceSpider.NB_INDEXED += len(records)
        if response_json['size'] == response_json['limit']:
            next_start = response_json['start'] + response_json['limit']
            yield Request(f'{self.get_content_url}&start={next_start}', headers = self.headers, callback = self.parse)
