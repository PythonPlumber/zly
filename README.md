# Short URL Website

This is a simple web application that allows you to create short URLs. It's built using Python and PostgreSQL.

## About

Welcome to the PythonPlumber URL Shortener project! This is an open source project developed by PythonPlumber to create a simple and efficient URL shortening service using Python, HTML, CSS, and PostgreSQL.

The main goal of this project is to provide an easy-to-use and customizable URL shortening solution for users. By using this service, users can easily create short and memorable URLs for their long links.

This project is completely open source and contributions are always welcome. If you're interested in contributing to the project, please read our contributing guidelines for more information.

## Getting Started

1. Set up a PostgreSQL database:
   - Install PostgreSQL on your machine.
   - Create a new database and a table to store the shortened URLs.
   - and fill your database details in .env file

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
   
 -  Choose a VPS provider: You can choose any VPS provider like DigitalOcean, Linode, Vultr, or Amazon AWS, depending on your requirements.

 -  Set up a server: After choosing a provider, create a server instance with your preferred operating system (Ubuntu, CentOS, etc.).

 -  Install dependencies: Install the necessary dependencies like Python, PostgreSQL, Nginx, and Gunicorn.

 -  Clone the repository: Clone the repository that contains your URL shortener code to the server.

 -  Set up the environment: Create an environment file (.env) and set up your PostgreSQL database details and other necessary environment variables.

 -  Install Python dependencies: Install the required Python packages using pip or pipenv.

 -  Set up the database: Create the required tables and indexes in your PostgreSQL database using the provided migration scripts.

 -  Test the application: Run the application locally and test its functionality.

 -  Configure Nginx: Configure Nginx to act as a reverse proxy and serve the application.

 -  Start the application: Use Gunicorn to start the application and make it available on the specified port.

 -  Configure firewall: Open the necessary ports on the server firewall (usually 80 and 443 for HTTPS).
   

## License

This project is licensed under the MIT License.
