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
