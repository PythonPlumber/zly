# Short URL Website

This is a simple web application that allows you to create short URLs. It's built using Python and MongoDB.

## About

Welcome to the PythonPlumber URL Shortener project! This is an open source project developed by PythonPlumber to create a simple and efficient URL shortening service using Python, HTML, CSS, and MongoDB.

The main goal of this project is to provide an easy-to-use and customizable URL shortening solution for users. By using this service, users can easily create short and memorable URLs for their long links.

This project is completely open source and contributions are always welcome. If you're interested in contributing to the project, please read our contributing guidelines for more information.

## Getting Started

1. Set up a mongoDB database:
- Create a MongoDB Atlas account and log in to the dashboard.
- Create a new project and cluster.
- Add a new user to the database with appropriate read and write permissions.
- Whitelist the IP address of the server where you will run the Python code and add 0.0.0.0 ip address to it.
- after replace your MongoDB url With `your_mongodb` ( in app.py )
```
app = Flask(__name__)
client = MongoClient("your_mongodb")
db = client.url_shortener
```
2. Set up the backend using Python:
   - Install Flask, a Python web framework, and the pymongo library, which allows you to interact with MongoDB from Python.
   - Create a new Flask app and define two routes: one for the home page and one for the form submission.
   - In the form submission route, generate a unique short URL and store it along with the submitted long URL in the MongoDB database.
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

 -  Set up the environment

 -  Install Python dependencies: Install the required Python packages using pip or pipenv.

 -  Set up the database: Create the required Mongo DB

 -  Test the application: Run the application locally and test its functionality.
```
$ python3 app.py
```
 -  Configure Nginx: Configure Nginx to act as a reverse proxy and serve the application.

 -  Start the application: Use Gunicorn to start the application and make it available on the specified port.

 -  Configure firewall: Open the necessary ports on the server firewall (usually 80 and 443 for HTTPS).
   

## License

This project is licensed under the MIT License.
