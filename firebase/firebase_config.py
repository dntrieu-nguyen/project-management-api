import firebase_admin
from firebase_admin import credentials, db

from core.settings import FIREBASE, FIREBASE_DB_URL

cred = credentials.Certificate(FIREBASE)

firebase_admin.initialize_app(cred, {
    'databaseURL': FIREBASE_DB_URL
})