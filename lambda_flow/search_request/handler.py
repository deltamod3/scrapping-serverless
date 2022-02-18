import json
import time
from distlib import logger
from libs.helper import api_response, internal_server_error, bad_request_error, verify_user
from models import get_dynamodb_table, tbl_tmp_searches, tmp_searches_keyword, tmp_searches_search_id, \
    tmp_searches_description, tmp_searches_technology, tmp_searches_created_at, tmp_searches_updated_at, \
    tmp_searches_total_crawled_result, tmp_searches_purpose, tmp_searches_user_id, tmp_searches_search_engine


def handler(event, context):
    print(event)
    email = verify_user(event)
    print('User email', email)
    event_body = event.get('body', None)
    if not event_body:
        return bad_request_error("Missing body")
    request_body = json.loads(event_body)

    keyword = request_body.get('keyword', None)  # Required
    description = request_body.get('description', None)  # Required
    technology = request_body.get('technology', None)  # Optional
    total_crawled_result = request_body.get('total_crawled_result', None)  # Optional
    purpose = request_body.get('purpose', None)  # Optional
    user_id = 1  # TODO Static for now
    search_engine = request_body.get('search_engine', None)  # Required
    if not keyword or not description or not search_engine:
        return bad_request_error("Invalid parameter")
    if search_engine != 'bing' and search_engine != 'google':
        return bad_request_error("Invalid search_engine")

    try:
        ts = int(time.time() * 1000)
        logger.info('New result_id: ', ts)
        if technology and type(technology) != list:
            return bad_request_error("Invalid technology. technology should be array list of strings or undefined")
        if total_crawled_result and type(total_crawled_result) != int:
            return bad_request_error("Invalid total_crawled_result. technology should be integer or undefined")
        if purpose and type(purpose) != str:
            return bad_request_error("Invalid purpose. purpose should be string or undefined")
        tmp_searches = get_dynamodb_table(tbl_tmp_searches)
        new_item = {
            tmp_searches_search_id: ts,
            tmp_searches_keyword: keyword,
            tmp_searches_description: description,
            tmp_searches_technology: technology,
            tmp_searches_created_at: ts,
            tmp_searches_updated_at: ts,
            tmp_searches_total_crawled_result: total_crawled_result,
            tmp_searches_purpose: purpose,
            tmp_searches_user_id: user_id,
            tmp_searches_search_engine: search_engine,
        }
        tmp_searches.put_item(Item=new_item)
        return api_response(new_item)
    except Exception as e:
        return internal_server_error(e)
