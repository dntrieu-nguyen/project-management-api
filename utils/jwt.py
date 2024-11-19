import datetime
import uuid
import jwt
from core.settings import JWT_ACCESS_TOKEN_EXP, JWT_REFRESH_TOKEN_EXP, JWT_SECRET


def generate_access_token(id, role):
    current_time = datetime.datetime.utcnow()
    expiration_time = current_time + datetime.timedelta(minutes=10)
    return jwt.encode(
        payload={
            'id': str(id),  
            'role': role,
            'iat': current_time.timestamp(),
            'nbf': current_time.timestamp(), 
            'exp': expiration_time.timestamp(),  
        },
        key=JWT_SECRET,
        algorithm="HS256",
    )

def generate_refresh_token(id):
    current_time = datetime.datetime.utcnow()
    expiration_time = current_time + datetime.timedelta(days=30)
    return jwt.encode(
        payload={
            'id': str(id), 
            'iat': current_time.timestamp(),
            'nbf': current_time.timestamp(),  
            'exp': expiration_time.timestamp(),  
        },
        key=JWT_SECRET,
        algorithm="HS256",
    )


def decode_token(token):
    try:
        return jwt.decode(token, key=JWT_SECRET, algorithms=["HS256"], leeway=10)  
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")
