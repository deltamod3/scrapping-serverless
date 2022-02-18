from response_lib.mock_data import demo_search_result_json, demo_search_result_details_json
from response_lib.helper import verify_user, bad_request_error, api_response, internal_server_error


def handler(event, context):
    email = verify_user(event)
    print('User email: ', email)
    path_parameters = event.get('pathParameters', None)
    try:
        if not path_parameters:
            # New search and Get all
            event_qs = event.get('queryStringParameters', None)
            if not event_qs:
                # Get all
                data = get_all_search()
            else:
                # New search
                search_text = event_qs.get('search_text', None)
                if not search_text:
                    return bad_request_error("Missing search_text")
                data = start_new_search(search_text)
        else:
            # Get one
            search_id = path_parameters.get('search_id', None)
            if not search_id:
                return bad_request_error("Missing search_id")
            search_id = int(search_id)
            if not search_id:
                return bad_request_error("Invalid search id")
            data = get_search(search_id)
            if not data:
                return bad_request_error('Not found search data for the search id: ' + str(search_id))
        return api_response(data)
    except Exception as e:
        return internal_server_error(e)


def start_new_search(search_text):
    return demo_search_result_json


def get_all_search():
    return demo_search_result_json


def get_search(search_id):
    if search_id <= 0 or search_id > len(demo_search_result_details_json):
        return None
    return demo_search_result_details_json[int(search_id) - 1]
