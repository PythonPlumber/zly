from flask import Flask, render_template, request, redirect, jsonify
from pymongo import MongoClient
import string
import random
import validators
import os
import schedule
import time
import requests
from datetime import datetime, timedelta
import psutil

app = Flask(__name__)
mongo_url = os.getenv("MONGODB_URL")
client = MongoClient(mongo_url)
db = client.url_shortener

# Generate a random short code
def generate_short_code():
    length = 4
    chars = string.printable.strip()
    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        if not db.urls.find_one({"code": code}):
            return code

# Delete URLs that are 110 days old
def delete_expired_urls():
    expiration_date = datetime.now() - timedelta(days=110)
    db.urls.delete_many({"created_at": {"$lt": expiration_date}})

# Your new cron job function
def cron_job_function():
    # Make an HTTP request to the cron job URL
    response = requests.get("http://zly.uk.to/")
    if response.status_code == 200:
        print("Cron job executed successfully")
    else:
        print("Cron job failed")

def schedule_deletion():
    # Schedule deletion of expired URLs
    schedule.every().day.at("00:00").do(delete_expired_urls)

    # Schedule your new cron job function every 10 minutes
    schedule.every(10).minutes.do(cron_job_function)

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

# Retrieve statistics in JSON format
@app.route('/stats')
def stats_json():
    stats = db.stats.find_one()
    if stats:
        # Calculate uptime
        uptime = int(time.time() - stats['start_time'])
        stats['uptime'] = uptime

        # Calculate database percentage
        total_urls = db.urls.count_documents({})
        database_percentage = 0
        if total_urls > 0:
            expired_urls = db.urls.count_documents({"created_at": {"$lt": datetime.now() - timedelta(days=110)}})
            database_percentage = (expired_urls / total_urls) * 100
        stats['database_percentage'] = database_percentage

        # Calculate system usage
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent
        stats['system_usage'] = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'disk_percent': disk_percent
        }

        return jsonify(stats)
    else:
        return jsonify({"message": "No statistics found"})

# 404 page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    delete_expired_urls()  # Delete expired URLs when the application starts
    schedule_deletion()  # Schedule deletion of expired URLs and your cron job function
    app.run(debug=True)
