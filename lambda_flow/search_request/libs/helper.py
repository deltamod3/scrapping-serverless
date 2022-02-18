import json


def api_response(data):
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Request-Headers': '*',
            'Access-Control-Request-Method': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Methods': '*',
            'Access-Control-Allow-Credentials': True,
        },
        'body': json.dumps(data)
    }


def bad_request_error(message):
    print(message)
    return {
        'statusCode': 400,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Credentials': True,
        },
        'body': json.dumps(dict(message=message))
    }


def internal_server_error(e):
    print(e)
    return {
        'statusCode': 500,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Credentials': True,
        },
        'body': json.dumps(e)
    }


def unauthorized_error(e):
    print(e)
    return {
        'statusCode': 401,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Credentials': True,
        },
        'body': json.dumps(e)
    }


def verify_user(event):
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
    return principal_id
