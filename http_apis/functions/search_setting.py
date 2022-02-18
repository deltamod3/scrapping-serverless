import json
from response_lib.helper import verify_user, bad_request_error, api_response, internal_server_error


def handler(event, context):
    email = verify_user(event)
    print('User email: ', email)
    path_parameters = event.get('pathParameters', None)
    if not path_parameters:
        return bad_request_error('Missing path parameters')
    result_id = path_parameters.get('result_id', None)
    search_id = path_parameters.get('search_id', None)
    event_body = event.get('body', None)
    try:
        if result_id:
            result_id = int(result_id)
            if not result_id:
                return bad_request_error('Invalid result_id')
            http_method = event.get('httpMethod', None)
            if http_method == 'PATCH':
                if not event_body:
                    return bad_request_error("Missing body")
                request_body = json.loads(event_body)
                is_favourite = request_body.get('is_favourite', None)
                if not is_favourite:
                    return bad_request_error("Missing is_favourite")
                if not (is_favourite is False or is_favourite is True):
                    return bad_request_error("Invalid is_favourite")
                is_favourite = bool(is_favourite)
                # TODO CHANGE STATE with patch_result_id and isFavourite
            elif http_method == 'DELETE':
                print(result_id)
                # TODO DELETE with result_id
            else:
                return bad_request_error("Invalid http method" + http_method)
        elif search_id:
            search_id = int(search_id)
            if not search_id:
                return bad_request_error('Invalid search_id')
            # TODO DELETE with search_id
        else:
            return bad_request_error('Invalid path parameters')
        return api_response(dict(status=True))
    except Exception as e:
        return internal_server_error(e)
