from base64 import b64decode
from Crypto import Random
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from OpenSSL.crypto import load_publickey, FILETYPE_PEM, verify, X509

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
    event_headers = event.get('headers', None)
    if not event_headers:
        policy = generate_policy(
            'unauthorized_error',
            "Deny",
            event['methodArn']
        )
        print('Missing Headers Policy: ', policy)
        return policy
    print('Headers: ', event_headers)
    auth_token = event_headers.get("authorization", None)
    if not auth_token:
        policy = generate_policy(
            'invalid_auth_header',
            "Deny",
            event['methodArn']
        )
        print('Invalid Auth header: ', policy)
        return policy

    joomla_signature = auth_token.split('@')[0]  # Joomla signature
    public_token = auth_token.split('@')[1]  # Public token
    if not joomla_signature or not public_token:
        policy = generate_policy(
            'unauthorized_error',
            "Deny",
            event['methodArn']
        )
        print('Invalid Token Policy: ', policy)
        return policy

    try:
        public_token_encoded = bytes(public_token, 'utf-8')
        server_token_decoded = b64decode(public_token_encoded)
        cipher_obj_server = PKCS1_v1_5.new(RSA.importKey(private_key))
        token_data = cipher_obj_server.decrypt(server_token_decoded, Random.new().read)
        decrypted_data = token_data.decode()
        print('decrypted_data: ', decrypted_data)

        pub_key = load_publickey(FILETYPE_PEM, bytes(joomla_public_key, 'utf-8'))
        x509 = X509()
        x509.set_pubkey(pub_key)
        decoded_signature = b64decode(bytes(joomla_signature, 'utf-8'))
        try:
            verify(x509, decoded_signature, decrypted_data, 'sha1')
            policy = generate_policy(
                decrypted_data,
                'Allow',
                event['methodArn']
            )
            print('Successful Policy: ', policy)
            return policy
        except Exception as e:
            print(e)
            policy = generate_policy(
                decrypted_data,
                "Deny",
                event['methodArn']
            )
            print('Verification Error Policy: ', policy)
            return policy
    except Exception as e:
        policy = generate_policy(
            str(e),
            "Deny",
            event['methodArn']
        )
        print('Token Verification Policy: ', policy)
        return policy


def generate_policy(principal_id, effect, resource, scopes=None):
    policy = {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    "Resource": resource
                }
            ]
        }
    }
    if scopes:
        policy['context'] = {'scopes': scopes}
    return policy
