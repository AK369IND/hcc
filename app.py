import sqlite3
from flask import Flask, flash, json, jsonify, redirect, render_template, request, session
from flask.helpers import url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from supplement import apology, login_required

from google.oauth2 import id_token
from google.auth.transport import requests

from datetime import datetime

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# The database connection function
def setup_connection():
    connection = sqlite3.connect("hcc.db", isolation_level=None)
    # isolation_level autocommits/saves the changes in the database after each connection

    connection.row_factory = sqlite3.Row 
    # when row_factory attribute is set to Row, 
    # it allows name based calls to table columns than just index based calls

    # return a cursor to the database
    return connection.cursor()


# About page
@app.route("/", methods=["GET"])
def about():
    return render_template("about.html")


# Sign Up User; NOT Google SignUp
@app.route("/signUp", methods=["GET", "POST"])
def signUp():
    c = setup_connection()

    # User submitted to register.html via POST request method
    if request.method == "POST":
        # Query for the entered username or email if already exists in db
        c.execute('''SELECT * FROM all_users WHERE username_or_name = ?''',
                                (request.form.get("username_or_sub"), ))
        check_user = c.fetchall()
        c.execute('''SELECT * FROM all_users WHERE email = ?''',
                                (request.form.get("email"), ))
        check_email = c.fetchall()
        if len(check_user) != 0:
            flash("Username already exists.", category="message")
            return redirect("/signUp")
        elif len(check_email) != 0:
            flash("Email already exists.", category="message")
            return redirect("/signUp")
        # Entered password field and confirmation field must match exactly
        elif request.form.get("hash_or_sub") != request.form.get("confirmation"):
            flash("Passwords don't match.", category="message")
            return redirect("/signUp")
        # If all good then add the user to db
        else:
            c.execute('''INSERT INTO all_users(username_or_name, hash_or_sub, email, 
                            google_login, home_admin)
                         VALUES(?, ?, ?, ?, ?)''',
                        (request.form.get("username_or_name"),
                        generate_password_hash(request.form.get("hash_or_sub")), 
                        request.form.get("email"), 
                        0, 
                        0))
            # New user created
            c.execute(''' SELECT email FROM all_users 
                            WHERE email = ? ''', (request.form.get('email'), ))
            new_user = c.fetchall()
            session["user_id"] = new_user[0]["id"]
            flash("Welcome to HCC..!", category="message")
            return render_template("hcc.html")

    else:
        return render_template("signUp.html")


# Login User; NOT Google Login
@app.route("/login", methods=["GET", "POST"])
def login():
    c = setup_connection()

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting the custom login form)
    if request.method == "POST":
        # Query database for username
        c.execute("SELECT * FROM all_users WHERE username_or_name = ?",
                    (request.form.get("username_or_name"), ))
        current_user = c.fetchall()
        # Ensure username exists and password is correct
        if len(current_user) != 1 or not check_password_hash(current_user[0]["hash_or_sub"], request.form.get("hash_or_sub")):
            flash("Invalid username and/or password.", category="message")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = current_user[0]["id"]

        flash("Log In successful.", category="message")
        # Redirect user to main page
        return redirect("/hcc")

    else:
        return render_template("login.html")
        

# Google authentication check for signUp/login; 
# passes the id_token from frontend to backend and returns acknowledgement
@app.route("/auth", methods=["POST"] )
def auth():
    token = request.form["idtoken"]
    try:
        # Specify the CLIENT_ID of the app that accesses the backend:
        # The verify_oauth2_token function verifies the JWT signature, the aud(audience i.e clientID) claim, and the exp claim. 
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), "377349762655-ohe5aed0ncqrjhh11jnp6helod04v231.apps.googleusercontent.com")

        # ID token is valid. 
        # Forget any user id/ session
        session.clear()

        # Get the user's Google Account ID from the decoded token and
        # check if it is already in our db
        c = setup_connection()
        c.execute('''SELECT * FROM all_users WHERE email = ?''',
                                (idinfo['email'], ))
        check_email = c.fetchall()
        if len(check_email) != 0:
            # its a login, set up a new session
            session["user_id"] = check_email[0]["id"]
        else:
            # its a signUp, set up the db info for new user
            c.execute('''INSERT INTO all_users(username_or_name, hash_or_sub, email, 
                            google_login, home_admin)
                         VALUES(?, ?, ?, ?, ?)''',
                        (idinfo['name'],
                        generate_password_hash(idinfo['sub']), 
                        idinfo['email'], 
                        1, 
                        0))
            c.execute('''SELECT id FROM all_users WHERE email = ?''',
                                (idinfo['email'], ))
            current_user_id = c.fetchall()
            # set up a new session
            session["user_id"] = current_user_id[0]["id"]

        flash("Log In successful.", category="message")
        return idinfo['name']
    except ValueError:
        # Invalid token
        flash("Failed to recieve token", category="message")
        return redirect("/login")


# Log user out
@app.route("/logout", methods=["GET"])
@login_required
def logout():
    # Forget any user_id/ session
    session.clear()

    # Redirect user to about
    return redirect("/")


# Main Control Center
@app.route("/hcc", methods=["GET", "POST"])
@login_required
def hcc():
    c = setup_connection()
    c.execute(''' SELECT username_or_name FROM all_users WHERE
                id = ? ''',
                (session["user_id"], ))
    current_user_name = c.fetchall()
    return render_template("hcc.html", current_user_name = current_user_name)


# showing device power consumptions
@app.route("/devicesData", methods=["GET", "POST"])
@login_required
def devicesData():
    c = setup_connection()
    if request.method == "GET":
        c.execute(''' SELECT device_consumption FROM all_devices ''')
        device_consumption = c.fetchall()
        c.execute(''' SELECT username_or_name FROM all_users 
                        WHERE id = ? ''', (session['user_id'], ))
        current_user_name = c.fetchall()
        return render_template("devicesData.html", device_consumption = device_consumption, current_user_name=current_user_name)
    else:
        # get the json data from post request from frontend hcc.html
        device_id_str = request.form.get('device')
        device_id = int(device_id_str) + 1 
        device_state_str = request.form.get('device_state')
        device_state = int(device_state_str)

        c.execute('''SELECT * FROM all_devices WHERE
                    device_id = ?''', (device_id, ))
        device = c.fetchall()
        if device_state == 1:
            # note down start time and update device state to 1 ie ON
            start_time  = datetime.now() 
            c.execute(''' UPDATE all_devices 
                            SET device_start_time = ?, 
                            device_state = ? WHERE 
                            device_id = ?''', (start_time, 1, device_id))
        elif device_state == 0:
            # calculate ON time by calc the diff btw start and off times
            current_time = datetime.now()
            # convert str to datetime object
            old_start_time = datetime.fromisoformat(device[0]['device_start_time'])
            on_time = current_time - old_start_time
            consumption_time_hours = (on_time.total_seconds()) / 3600

            power_rating = device[0]['device_power_rating']
            old_power_consumption = device[0]['device_consumption']

            power_Wh = power_rating * consumption_time_hours
            new_power_consumption = old_power_consumption + power_Wh

            new_power_consumption = float("{0:.2f}".format(new_power_consumption))

            c.execute(''' UPDATE all_devices SET device_state = ?,
                            device_consumption = ? 
                            WHERE device_id = ? ''', (0, new_power_consumption, device_id))
        return {'status': 'OK'}



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)