import time
from multiprocessing import Process, Pipe
import requests
import pandas as pd
from models import tmp_searches_keyword, tmp_searches_search_id, get_dynamodb_table, \
    tbl_tmp_results_step1, tmp_results_result_id, tmp_results_search_id, tmp_results_url, tmp_results_title, \
    tmp_results_description, tmp_results_date, tmp_searches_search_engine


def handler(event, context):
    print(event)
    print('Records length:', len(event.get('Records')))

    for record in event.get('Records'):
        if record.get('eventName') == 'INSERT':
            search_id = int(record['dynamodb']['NewImage'][tmp_searches_search_id]['N'])
            keyword = record['dynamodb']['NewImage'][tmp_searches_keyword]['S']
            search_engine = record['dynamodb']['NewImage'].get(tmp_searches_search_engine, None)
            if not search_engine:
                search_engine = 'bing'
            else:
                search_engine = search_engine['S']
            num_pages = 100  # TODO

            print('Indexed search Id: ', search_id)
            if not keyword:
                print('Invalid parameters: ',
                      {
                          "keyword": keyword,
                          "num_pages": num_pages,
                          "search_engine": search_engine,
                      })
                continue
            try:
                crawled_data = search_keyword(keyword, num_pages, search_engine)
                print('search result: ', crawled_data)
                for crawled_item in crawled_data:
                    # create a pipe for communication
                    parent_conn, child_conn = Pipe()
                    # create the process, pass instance and connection
                    process = Process(target=process_event_record, args=(search_id, crawled_item, child_conn))
                    process.start()
                    child_conn.close()  # <-- Close the child_conn end in the main process too.
                    try:
                        result_id = parent_conn.recv()
                        print('Processed this event: result_id: ', result_id)
                    except EOFError as err:
                        print('Got error here: ', err)
                    process.join()
            except Exception as e:
                print('Searching error: ', e)
        elif record.get('eventName') == 'MODIFY':
            search_id = record['dynamodb']['Keys'][tmp_searches_search_id]['N']
            print('Modified search_id {} from tmp_searches', search_id)
        elif record.get('eventName') == 'DELETE':
            search_id = record['dynamodb']['Keys'][tmp_searches_search_id]['N']
            print('Removed search_id {} from tmp_searches', search_id)


def process_event_record(search_id, crawled_item, conn):
    tmp_results_step1 = get_dynamodb_table(tbl_tmp_results_step1)
    ts = int(time.time() * 1000)
    print('result_id: ', ts)
    new_item = {
        tmp_results_result_id: ts,
        tmp_results_search_id: search_id,
        tmp_results_url: crawled_item['link'],
        tmp_results_title: crawled_item['title'],
        tmp_results_description: crawled_item['snippet'],
        tmp_results_date: ts,
    }
    tmp_results_step1.put_item(Item=new_item)
    conn.send(ts)
    conn.close()


def search_keyword(keyword, num_pages, search_engine):
    google_sc_scraper_api = 'http://54.193.187.177:7070/web_scraper/'
    if not keyword or not num_pages or not search_engine:
        raise Exception(
            'Invalid parameters for search: keywork: {}, num_pages: {}, search_engine: {}'.format(keyword, num_pages,
                                                                                                  search_engine))
    scrap_info = {
        'keyword': keyword,
        'num_pages': num_pages,
        'search_engine': search_engine
    }
    crawled_data = None
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
    return crawled_data
