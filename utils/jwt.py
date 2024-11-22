import datetime
import jwt
from core.settings import JWT_SECRET


def generate_access_token(id, role):
    current_time = datetime.datetime.now(datetime.timezone.utc)
    expiration_time = current_time + datetime.timedelta(minutes=30)
    payload = {
        'id': str(id),
        'role': role,
        'iat': current_time,
        'nbf': current_time,
        'exp': expiration_time,
    }
    return jwt.encode(payload=payload, key=JWT_SECRET, algorithm="HS256")


def generate_refresh_token(id):
    current_time = datetime.datetime.now(datetime.timezone.utc)
    expiration_time = current_time + datetime.timedelta(days=30)

    return jwt.encode(
        payload={
            'id': str(id),
            'iat': current_time,
            'nbf': current_time,
            'exp': expiration_time,
        },
        key=JWT_SECRET,
        algorithm="HS256",
    )


def decode_token(token):

    return jwt.decode(
        token,
        key=JWT_SECRET,
        algorithms=["HS256"],
        options={"verify_exp": True},
    )
