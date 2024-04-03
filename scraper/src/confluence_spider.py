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
    headers = { }
    base_url = None
    confluence_base_urls = []
    confluence_space_key = None
    confluence_page_limit = None

    def __init__(self, config, typesense_helper, strategy):
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
        for confluence_base_url in self.confluence_base_urls:
            base_url = confluence_base_url['url']
            yield Request(self.get_content_url(base_url), headers = self.headers, callback = self.parse, cb_kwargs={'base_url': base_url})

    def parse(self, response, base_url):
        response_json = response.json()
        for result in response_json['results']:

            ancestors_len = len(result['ancestors'])
            ancestors_take =  ancestors_len if ancestors_len < 3 else 3 
            html = f"""
            <!DOCTYPE html>
            <html lang="en-US" >
                <body id="com-atlassian-confluence">
                    <main role="main" id="main">
                        <div id="main-header">
                            <nav aria-label="Breadcrumbs">
                                <ol id="breadcrumbs">
                                    { ''.join(map(lambda ancestor: '<li>' + ancestor['title'] + '</li>', list(result['ancestors'])[:ancestors_take])) }
                                </ol>
                            </nav>
                            <h1 id="title-text" class="with-breadcrumbs">
                                <a href="/confluence{result['_links']['webui']}">{result['title']}</a>
                            </h1>
                        </div>
                        <div id="main-content" class="wiki-content">
                            {result['body']['view']['value']}
                        </div>
                    </main>
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
            yield Request(f'{self.get_content_url(base_url)}&start={next_start}', headers = self.headers, callback = self.parse, cb_kwargs={'base_url': base_url})
