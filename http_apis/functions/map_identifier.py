import requests
import json
from response_lib.helper import internal_server_error, bad_request_error, api_response


def handler(event, context):
    print(event)
    event_body = event.get('body', None)
    if not event_body:
        return bad_request_error("Missing body")
    request_body = json.loads(event_body)
    try:
        api_key = 'AIzaSyAMUU41zsgLEfd1hnuA0prdJwyLixbneeQ'

        # url variable store url
        api = "https://maps.googleapis.com/maps/api/place/textsearch/json?"

        if not 'urls' in request_body:
            return bad_request_error("Invalid parameter: urls")
        url_data = request_body.get('urls', [])
        print('request data', url_data)
        if type(url_data) is not list:
            return bad_request_error("Invalid urls type: Need array")
        results = []
        for item in url_data:
            url_data_no_protocol = item.split('://')

            domain = url_data_no_protocol[len(url_data_no_protocol) - 1].split('/')[0]
            url = api + 'query=https:\/\/' + domain + '&key=' + api_key
            print('url: ', url)
            r = requests.get(url)
            #  json format data into python format data
            x = r.json()
            print('Result: ', x)
            results.append({
                "url": 'https://' + domain,
                "results": x['results'],
            })
        return api_response(results)
    except Exception as e:
        return internal_server_error(e)
