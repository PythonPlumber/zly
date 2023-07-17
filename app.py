from flask import Flask, render_template, request, redirect
from pymongo import MongoClient
import string
import random
import validators
import os
import schedule
import time
from datetime import datetime, timedelta

app = Flask(__name__)
mongo_url = os.getenv("MONGODB_URL")
client = MongoClient(mongo_url)
db = client.url_shortener

# Generate a random short code
def generate_short_code():
    length = 10
    chars = string.printable.strip()
    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        if not db.urls.find_one({"code": code}):
            return code

# Delete URLs that are 110 days old
def delete_expired_urls():
    expiration_date = datetime.now() - timedelta(days=110)
    db.urls.delete_many({"created_at": {"$lt": expiration_date}})


def schedule_deletion():
    # Schedule deletion of expired URLs
    schedule.every().day.at("00:00").do(delete_expired_urls)

    # Run the scheduled jobs
    while True:
        schedule.run_pending()
        time.sleep(1)
        
# Home page
@app.route('/')
def home():
    url_count = db.urls.count_documents({})
    # Increase visitor counter
    db.stats.update_one({}, {"$inc": {"visitors": 1}}, upsert=True)
    stats = db.stats.find_one()
    visitors = stats['visitors']
    return render_template('index.html', url_count=url_count, visitors=visitors)

# Create a new shortened URL
@app.route('/shorten', methods=['POST'])
def shorten():
    robot_confirmation = request.form.get('robot_confirmation')
    if not robot_confirmation:
        return render_template('error.html', message='Please confirm you are not a robot.')

    # Rest of your code for URL shortening
    original_url = request.form['url']
    if not validators.url(original_url):
        return render_template('error.html', message='Invalid URL')
    existing_url = db.urls.find_one({"original": original_url})
    if existing_url:
        return render_template('result.html', code=existing_url['code'])
    else:
        code = generate_short_code()
        db.urls.insert_one({"original": original_url, "code": code, "created_at": datetime.now()})
        return render_template('result.html', code=code)

# Redirect to original URL
@app.route('/<code>')
def redirect_to_url(code):
    url = db.urls.find_one({"code": code})
    if url:
        return redirect(url['original'])
    else:
        return render_template('error.html', message='URL not found')

# 404 page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    # Schedule deletion of expired URLs every day at midnight
    delete_expired_urls()  # Delete expired URLs when the application starts
    app.run(debug=True)
