import os
from flask import Flask, render_template, request, redirect
import psycopg2
import string
import random

DATABASE_URL = os.environ['DATABASE_URL']
DB_USER = os.environ['DB_USER']
DB_PASSWORD = os.environ['DB_PASSWORD']
DB_HOST = os.environ['DB_HOST']
DB_PORT = os.environ['DB_PORT']

# Connect to PostgreSQL database
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)

app = Flask(__name__)

conn = psycopg2.connect(database="dbname", user="user", password="password", host="host", port="port")
cur = conn.cursor()

def generate_short_url():
    """Generate a random 5-character string for the short URL"""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(5))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def shorten_url():
    long_url = request.form['long_url']
    short_url = generate_short_url()

    cur.execute("INSERT INTO urls (short_url, long_url) VALUES (%s, %s)", (short_url, long_url))
    conn.commit()

    return render_template('index.html', short_url=short_url)

@app.route('/<short_url>')
def redirect_to_long_url(short_url):
    cur.execute("SELECT long_url FROM urls WHERE short_url = %s", (short_url,))
    long_url = cur.fetchone()[0]

    return redirect(long_url)

if __name__ == '__main__':
    app.run(debug=True)
