from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from meiduo_mall import settings

def generic_email_access_token(user_id,email):
    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=24 * 60 * 60)
    token = s.dumps({
        'id': user_id,
        'email': email
    })
    access_token = token.decode()
    return access_token

from itsdangerous import BadTimeSignature,SignatureExpired,BadData
def check_email_token(token):
    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=24 * 60 * 60)
    try:
        result = s.loads(token)
    except Exception:
        return None

    return result
