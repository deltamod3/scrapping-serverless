import json
from base64 import b64decode
from Crypto import Random
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from OpenSSL.crypto import load_publickey, FILETYPE_PEM, verify, X509
from response_lib.helper import api_response, unauthorized_error, internal_server_error, bad_request_error
from response_lib.mock_data import demo_search_result_json, demo_food_tracking_json

private_key = '''-----BEGIN RSA PRIVATE KEY-----
MIICdgIBADANBgkqhkiG9w0BAQEFAASCAmAwggJcAgEAAoGBALku1MCT5Fq0AKYQ
hLOW6GqvJZ7/FTuGFjJjEVI3VMMBzjhgM/UNPQlCSgEFT5yyQC3+Lp9xgx4i1gN2
9DkC9SZI1aG7H4SCTiRYgdgDsF0jUPRtuM6gR44Uwt28Jr6aAlD3raQDMOzO2gAd
SUe5G+ZNVFpcr7i4iYZBdQmoKMAbAgMBAAECgYAFuM24GZm/t7ohZ3dCOVJ7IWhP
LmCQk0cSTX9WhAEpeV/O3CIe20bch2DUAT8Bf3x+L1FveclsX/Uu7DkFnfLHK5jC
gGeeuwxUOZH1NoNwGXQbY5Ek7QgxFoAG20dhLKnYoqO3rdD5MF3xWsMYTk6rCGUa
56HEEgjqgtycAEJ+uQJBAOCHgfcwUT77bOIkK0zISREGs1Jm+Ei0SM/5Co8VeilO
039/BozpLpKePysxgsLiOI9zVJg692IaiC3/c4bZjF8CQQDTI4IZYPX9yOJ1NH0/
W4xv0IgyIl4YOV74ivL+xJmD6hDQQIbD8igBbnu0eDgUUQX5iByOY9pEe9F6WYni
SiXFAkEAucLC3wzlmxMPAYXlIRBvixudDubMMfKebxpfBwRA3p4t00T32WsusfUk
1AqRYcUiAGTtr0jR1SOYWV4IaZ/hRwJATflgE5VOY3Irx9MhqiNaIvUlRzaP/2w4
mZtfEB11AFWR7gbWfkjQ4250+vom48HkbfoJacCQnBgKDaBBnrN5bQJAKkA8FY87
731B9M60UN+UhJSqNYWAG++KwinguDDFKj/0rO+8K86+5at+sIPNEjN8Uoe/nkCg
UgTsJuaV0hmfcg==
-----END RSA PRIVATE KEY-----'''

joomla_public_key = '''-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1bezLmO1qhNSGiVlkc+s
WssiLb6HgY9Cmlno3AsXjMl9TO/SvTkm3uTvDQgM7o0mGLAm2XejDZNsU5kXri94
Ea9F5NpU+cGPktqcwjkd4iJf61czAfNcts2wMgAij2r+5btIYIGB1ftkTlg0rZCX
nYXcTs/UlJSalnqxCzRstyMzgAj9/ms/0OqYXRCewr9GoodmTe81vBqKdxMbC4AE
BXOu32pRA0zyi9Migux7to/kK6mVxLVWxuI2EBGJCpTSTEEPK8SvYpr3ipXDd0yp
pw6Kc6cIpm6SrSJtLCKKr407y0v4h05dM3zyAoXwCtkzKcUb+c7tOuydwxhkdGH6
4wIDAQAB
-----END PUBLIC KEY-----'''


def handler(event, context):
    print('Event: ', event)
    event_body = event.get('body', None)
    if not event_body:
        return bad_request_error("Missing body")
    request_body = json.loads(event_body)
    # search = request_body["search"]
    # ref_text = request_body["ref_text"]
    # technology = request_body["technology"]
    # purpose = request_body["purpose"]
    joomla_signature = request_body.get("signature", None)  # Joomla signature
    public_token = request_body.get("public_token", None)
    if not joomla_signature or not public_token:
        return unauthorized_error(dict(message='Invalid tokens'))
    try:
        public_token_encoded = bytes(public_token, 'utf-8')
        server_token_decoded = b64decode(public_token_encoded)
        print('server_token_decoded: ', server_token_decoded)
        cipher_obj_server = PKCS1_v1_5.new(RSA.importKey(private_key))
        token_data = cipher_obj_server.decrypt(server_token_decoded, Random.new().read)
        decrypted_data = token_data.decode()
        print('decrypted_data: ', decrypted_data)

        pub_key = load_publickey(FILETYPE_PEM, bytes(joomla_public_key, 'utf-8'))
        x509 = X509()
        x509.set_pubkey(pub_key)
        print('bytes(token_data): ', token_data)
        decoded_signature = b64decode(bytes(joomla_signature, 'utf-8'))
        print('decoded_signature: ', decoded_signature)
        try:
            verify(x509, decoded_signature, decrypted_data, 'sha1')
            return api_response(get_response())
        except Exception as e:
            return unauthorized_error(e)
    except Exception as e:
        return internal_server_error(e)


def get_response():
    return {
        "search": demo_search_result_json,
        "result": demo_food_tracking_json
    }
