import json
from response_lib.mock_data import demo_search_result_json, demo_food_tracking_json
from response_lib.helper import api_response, unauthorized_error, internal_server_error, bad_request_error

from graphene import ObjectType, String, Schema

class Query(ObjectType):
    # this defines a Field `hello` in our Schema with a single Argument `name`
    hello = String(name=String(default_value="stranger"))
    goodbye = String()

    # our Resolver method takes the GraphQL context (root, info) as well as
    # Argument (name) for the Field and returns data for the query Response
    @staticmethod
    def resolve_hello(name):
        return f'Hello {name}!'

    @staticmethod
    def resolve_goodbye(info):
        return 'See ya!'

schema = Schema(query=Query)

def handler(event, context):
    request_context = event.get('requestContext', None)
    if not request_context:
        return unauthorized_error(dict(message='Invalid request context'))
    authorizer = request_context.get('authorizer', None)
    if not authorizer:
        return unauthorized_error(dict(message='Invalid authorizer'))
    principal_id = authorizer.get('principalId', None)
    if not principal_id:
        return unauthorized_error(dict(message='Invalid principal id'))
    print('Event: ', event)
    print('Client Email Address: ', principal_id)
    event_body = event.get('body', None)
    if not event_body:
        return bad_request_error("Missing body")
    request_body = json.loads(event_body)
    print('Request body: ', request_body)
    try:
        return api_response(get_response())
    except Exception as e:
        return internal_server_error(e)


def get_response():
    return {
        "search": demo_search_result_json,
        "result": demo_food_tracking_json
    }
