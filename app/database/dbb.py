# import psycopg2

# def db():
#     conn = psycopg2.connect(
#         dbname="outfitly",
#         user="postgres",
#         password="shani123@#",
#         host="localhost",
#         port="5432"
#     )
#     return conn
import psycopg2
def db():
    conn = psycopg2.connect(
        "postgresql://postgres:gSxsdOJUmQZXzPvrRzUflElyxdprEESf@turntable.proxy.rlwy.net:38402/railway",
        sslmode='require'  # Railway requires SSL
    )
    return conn
