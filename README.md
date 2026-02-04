# ZLY | URL Shortening Service

**ZLY** (Zany Link Yanker) is an open-source, full-stack URL shortening application. Built with a focus on simplicity and efficiency, it leverages Python and MongoDB to provide a reliable service for transforming long-form URLs into concise, shareable identifiers.

---

## Technical Overview

The application utilizes a Flask-based backend and a NoNoSQL database architecture to ensure rapid data retrieval and reliable persistence.

* **Backend:** Python 3.x, Flask
* **Database:** MongoDB Atlas
* **Infrastructure:** Gunicorn (WSGI), Nginx (Reverse Proxy)
* **Frontend:** HTML5, CSS3

## Features

* **Unique Slug Generation:** Automatically creates shortened identifiers for all submitted URLs.
* **Persistent Data Management:** Robust storage and retrieval via MongoDB integration.
* **Environment Security:** Configured to use `.env` files for sensitive database credentials and API keys.
* **Cross-Platform Deployment:** Optimized for PaaS (Render, Heroku) and self-hosted VPS environments.

---

## Installation & Setup

### 1. Database Configuration
1. Provision a MongoDB cluster via **MongoDB Atlas**.
2. Create a database user with `readWrite` permissions.
3. Configure Network Access (IP Whitelisting) for your deployment environment.
4. Retrieve your Connection String and define the `MONGO_URI` in your environment variables.

### 2. Local Development
Ensure you have Python 3.x and `pip` installed:

```bash
# Clone the repository
git clone [https://github.com/PythonPlumber/ZLY.git](https://github.com/PythonPlumber/ZLY.git)

# Install core dependencies
pip install Flask pymongo python-dotenv

# Execute the development server
python3 app.py

```

---

## Deployment Guide

### Render (PaaS)

1. Connect your repository to the **Render** dashboard.
2. Select **Web Service**.
3. Configure the **Start Command**:
```bash
gunicorn app:app

```


4. Define your `MONGO_URI` under the **Environment** tab.

### Heroku

1. Initialize the application via CLI:
```bash
heroku create [your-app-name]

```


2. Ensure a `requirements.txt` and `Procfile` exist in the root directory.
3. Deploy the source code:
```bash
git push heroku master

```



### VPS (Self-Hosted)

For production environments (Ubuntu/Debian recommended):

1. **System Dependencies:** Install `nginx`, `python3-pip`, and `mongodb`.
2. **Process Management:** Use **Gunicorn** managed by `systemd` to ensure high availability.
3. **Reverse Proxy:** Configure **Nginx** to forward traffic to the Gunicorn application socket.
4. **Security:** Configure your firewall (UFW) to allow traffic on ports `80` (HTTP) and `443` (HTTPS).

---

## License

This project is licensed under the **MIT License**.

---

**Maintained by [PythonPlumber**](https://github.com/PythonPlumber)**

```
**Would you like me to generate a `requirements.txt` file or a professional `Procfile` to complete this repository?**

```
