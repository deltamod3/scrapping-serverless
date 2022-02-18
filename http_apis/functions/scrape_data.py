import json
import requests
import pandas as pd
from response_lib.helper import bad_request_error, api_response, internal_server_error


def handler(event, context):
    event_body = event.get('body', None)
    if not event_body:
        return bad_request_error("Missing body")
    google_sc_scraper_api = 'http://54.193.187.177:7070/web_scraper/'
    request_body = json.loads(event_body)

    keyword = request_body.get('keyword', None)
    num_pages = request_body.get('num_pages', None)
    search_engine = request_body.get('search_engine', None)
    if not keyword or not num_pages or not search_engine:
        return bad_request_error("Invalid parameter")
    file_type = str(search_engine)
    scrap_info = {
        'keyword': keyword,
        'num_pages': num_pages,
        'search_engine': file_type
    }
    crawled_data = None
    try:
        resp = requests.post(google_sc_scraper_api, json=scrap_info)
        data = resp.json()
        for key, urls in data['scraper_result'].items():
            if not urls['no_results']:
                if not crawled_data:
                    crawled_data = urls['results']
                else:
                    crawled_data += urls['results']
        crawled_data1 = pd.DataFrame(crawled_data).drop_duplicates("link").to_dict('records')

        seen = set()
        crawled_data = []
        for value in crawled_data1:
            links = tuple(value.items())
            if links[0] not in seen:
                seen.add(links[0])
                crawled_data.append(value)
        print(crawled_data)
        return api_response(crawled_data)
    except Exception as e:
        return internal_server_error(e)
