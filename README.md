# Short URL Website

This is a simple web application that allows you to create short URLs. It's built using Python and PostgreSQL.


## Getting Started

1. Set up a PostgreSQL database:
   - Install PostgreSQL on your machine.
   - Create a new database and a table to store the shortened URLs.
   - In this example, we'll call the database "url_shortener" and the table "urls". The table will have three columns: "id" (integer, primary key), "short_url" (text), and "long_url" (text).

2. Set up the backend using Python:
   - Install Flask, a Python web framework, and the psycopg2 library, which allows you to interact with PostgreSQL from Python.
   - Create a new Flask app and define two routes: one for the home page and one for the form submission.
   - In the form submission route, generate a unique short URL and store it along with the submitted long URL in the PostgreSQL database.
   - Return the short URL to the user in the form of a clickable link.


### Deploy code on Heroku,

- Create a Heroku account if you don't already have one.
- Install the Heroku CLI on your local machine.
- Open your terminal and navigate to your project directory.
- Create a new Heroku app using the following command:
```
heroku create <app-name>
```
Replace <app-name> with the name you want to give your app.

- Add PostgreSQL add-on to your Heroku app using the following command:
   
```
heroku addons:create heroku-postgresql:hobby-dev
```
 
- Update the DATABASE_URL environment variable in your Heroku app settings with your PostgreSQL database URL, which can be found on the Heroku dashboard.
- Install the necessary dependencies for your Flask app using a requirements.txt file:
   
```
   pip freeze > requirements.txt
```

- Commit all changes to your Git repository and push the code to Heroku using the following command:
```
git push heroku master
```
 
- Once the deployment is complete, you can open your app using the following command:
```
heroku open
```

- This will open your app in the default browser.
   
   
   
### deploy your advance URL shortener code on a VPS,
