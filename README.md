# Mega Hilarious URL Shrinker <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f4a5/512.gif" alt="💥" width="32" height="32">

Welcome to the Mega Hilarious URL Shrinker project! Get ready for a laughter-filled experience like no other with the one and only ZLY (Zany Link Yanker) - the ultimate URL shortener that adds a dash of hilarity to every link!

## About <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f4a1/512.gif" alt="💡" width="32" height="32">

Prepare yourself for non-stop laughter with the Mega Hilarious URL Shrinker, affectionately known as ZLY. This open-source project, developed by the comedic masterminds at PythonPlumber, is here to revolutionize the world of link shortening. Built with <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f40d/512.gif" alt="🐍" width="15" height="15"> Python, HTML, CSS, and MongoDB, ZLY aims to bring a smile to your face while making your URLs shorter than a stand-up comedian's punchline.

Our mission is simple: to provide you with the funniest, easiest-to-use, and most customizable URL shortening service imaginable. Say goodbye to boring, long links and say hello to side-splittingly hilarious short URLs!

Contributions to this project are highly encouraged! If you have any jokes, puns, or comedic ideas to enhance the hilarity of ZLY, we'd love to hear them. Check out our contributing guidelines for more information on how you can join the laughter brigade.

## Getting Started <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f31f/512.gif" alt="🌟" width="32" height="32">

1. Set up a MongoDB database:
   - Create a MongoDB Atlas account and prepare for some seriously funny data storage.
   - Create a new project and cluster that will serve as the comedic hub for ZLY.
   - Add a new user to the database, ensuring they have the read and write permissions necessary to unleash the laughter.
   - Don't forget to whitelist the IP address of the server where you'll be running the Python code. Laughter has no boundaries, after all!
   - Replace `your_mongodb` in `app.py` with the connection URL to your MongoDB database:
     ```python
     app = Flask(__name__)
     client = MongoClient("your_mongodb")
     db = client.url_shortener
     ```

2. Set up the backend using Python:
   - Grab your funniest Python hat and install Flask, the jester of Python web frameworks, along with the pymongo library, which will help us interact with MongoDB.
   - Create a new Flask app and define two routes: one for the home page and one for the form submission. Get ready to unleash your comedic genius!
   - In the form submission route, generate a unique short URL and store it, along with the submitted long URL, in the MongoDB database. This is where the magic happens!
   - Return the short URL to the user in the form of a clickable link. Prepare for laughter-induced tears of joy!

## Deploy Your Side-Splitting Site

Get ready to share the laughter with the world by deploying your Mega Hilarious URL Shrinker. Choose your hosting method and let the hilarity ensue!

1. **Deploy on Render**:
   - Sign up for a Render account and get ready to unleash the comedy.
   - Create a new web service and select "From Repo" as the deployment method.
   - Choose the Git repository where your Flask app is located and let Render do the rest.
   - Select the branch you want to deploy, ensuring it's the funniest branch of all.
   - Configure your app by selecting the appropriate language, build command, and start command.
     - Start Command:
       ```
       gunicorn app:app
       ```
   - Click "Create Service" and let the laughter flow as Render builds and deploys your app.
   - Once the build is complete, open the URL provided by Render and get ready for non-stop hilarity!

2. **Deploy on Heroku**:
   - Create a Heroku account if you haven't already and prepare for some seriously funny deployment.
   - Install the Heroku CLI on your local machine and make sure it's equipped with the funniest jokes.
   - Navigate to your project directory in the terminal and create a new Heroku app:
     ```
     heroku create <app-name>
     ```
     Replace `<app-name>` with a name that will tickle everyone's funny bone.
   - Install the necessary dependencies for your Flask app by generating a requirements.txt file:
     ```
     pip freeze > requirements.txt
     ```
   - Commit all your humorous changes to your Git repository and push the code to Heroku:
     ```
     git push heroku master
     ```
   - Once the deployment is complete, open your app using the command:
     ```
     heroku open
     ```
     Get ready to laugh out loud as your hilarious app takes center stage!

3. **Deploy on a VPS**:
   - Select a VPS provider that appreciates good comedy. Look for providers known for their love of laughter, such as DigitalComic, Jokeode, or Vulthaha.

 -  Set up a server: After choosing a provider, create a server instance with your preferred operating system (Ubuntu, CentOS, etc.).

 -  Install dependencies: Install the necessary dependencies like Python, MongoDB, Nginx, and Gunicorn.

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
   

## License <img src="https://fonts.gstatic.com/s/e/notoemoji/latest/1f600/512.gif" alt="😀" width="30" height="30">

This project is licensed under the MIT License.
