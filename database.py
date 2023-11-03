import psycopg2
from decouple import config

conn = psycopg2.connect(
    host=config("host"),
    port=int(config("port")),
    user=config('user'),
    password=config('password'),
    database=config('database')
)

conn.autocommit = True
cursor = conn.cursor()