import os

from authlib.integrations.flask_client import OAuth
from flask import Flask, abort, redirect, render_template, request, session, url_for, flash, jsonify
from flask_session import Session
from functools import wraps
from cs50 import SQL
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from google.oauth2 import service_account
import googleapiclient.discovery
import pickle
import json
from groupy.client import Client
from groupy.api.memberships import Memberships
from groupy.api.bots import Bot, Bots
from datetime import datetime

#url = "https://afb8e24f-717d-4d78-ae73-762b8eee933e-ide.cs50.xyz:8080"
url = "https://study-group-me.herokuapp.com"

# Constants for Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'static/studygroupme-09dac6eaa430.json'
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Client token for GroupMe
client = Client.from_token("7b7vsWzmxrF9vKTpQNOlcRiKbIgGtlx4wtHaDpsN")

# Check for environment variables
for variable in ["CLIENT_ID", "CLIENT_SECRET", "SERVER_METADATA_URL"]:
    if not os.environ.get(variable):
        abort(500, f"Missing f{variable}")


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Database
#db = SQL("sqlite:///studygroupme.db")
db = SQL("postgres://qnziyzbwymfsla:3a68a9a35f4c7205ad2475757a6077da1145a5a6d6e461712c360182740f001f@ec2-174-129-253-63.compute-1.amazonaws.com:5432/d9ld1o62ljvagv")

# Configure OAuth
oauth = OAuth(app)
oauth.register(
    "cs50",
    client_id=os.environ.get("CLIENT_ID"),
    client_kwargs={"scope": "openid profile email"},
    client_secret=os.environ.get("CLIENT_SECRET"),
    server_metadata_url=os.environ.get("SERVER_METADATA_URL")
)


# Decorator to require login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("userinfo") is None:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Decorator to require register
def register_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session["user_id"] is None:
            return redirect(url_for("register"))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/", methods=["GET", "POST"])
def index():
    # If user reached home page via GET, check if logged in
    if request.method == "GET":

        # If user is not logged in, display index.html
        if session.get("userinfo") is None:
            return render_template("index.html", userinfo=session.get("userinfo"))

        # If user is logged in
        else:
            # If not registered, redirect to register
            if session["user_id"] is None:
                return redirect(url_for("register"))

            # If registered, display user's calendar
            calendar_id = db.execute("SELECT calendar_id FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["calendar_id"]
            return render_template("calendar.html", userinfo=session.get("userinfo"), calendar_id=calendar_id)

    # If user clicks on login button on home page, redirect to /login
    else:
        return redirect(url_for("login"))



@app.route("/callback")
def callback():
    # Once authenticated via HarvardKey, store user's info
    token = oauth.cs50.authorize_access_token()
    session["userinfo"] = oauth.cs50.parse_id_token(token)

    # Retrieve user id, assuming user already exists
    user = db.execute("SELECT id FROM users WHERE email = :email;", email=session.get("userinfo")["email"])

    # Check if user does not exist in database
    if len(user) == 0:
        session["user_id"] = None
        return redirect(url_for("register"))

    # Store user id as session variable for later use
    session["user_id"] = user[0]["id"]

    return redirect(url_for("index"))



@app.route("/login")
def login():
    return oauth.cs50.authorize_redirect(url + "/callback")
    #(url_for("callback", _external=True))



@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))



@app.route("/register", methods=["GET", "POST"])
@login_required
def register():
    # User reached route via GET (i.e. was redirected from /callback)
    if request.method == "GET":
        # If already registered, cannot access page
        if session["user_id"]:
            return redirect(url_for("index"))

        error = bool(request.args.get('error'))

        # Get courses (dictionary) and subjects (list)
        courses = pickle.load(open("static/courses.p", "rb"))
        subjects = pickle.load(open("static/subjects.p", "rb"))

        # Renders register page
        return render_template("register.html", userinfo=session.get("userinfo"), courses=json.dumps(courses), subjects=subjects, error=error)

    # User reached route via POST (i.e. clicked on register button)
    else:
        count = 0

        # Make sure if a subject is selected, a number is also selected
        for i in range(5):
            sub_name = "subject" + str(i)
            num_name = "number" + str(i)

            # If error found, redirect back to register
            if request.form.get(sub_name) != "Subject" and request.form.get(num_name) == "Number":
                return redirect(url_for("register", error=True))

            if request.form.get(sub_name) == "Subject":
                count += 1

        # Make sure user inputted at least one class
        if count == 5:
            return redirect(url_for("register", error=True))

        service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)

        # Create personal calendar
        calendar = {
            # Set title to
            'summary': session.get("userinfo")["name"] + " - StudyGroupMe",
            'timeZone': 'America/New_York'
        }

        created_calendar = service.calendars().insert(body=calendar).execute()

        print(created_calendar['id'])

        # Set personal calendar viewing permissions to public
        # TODO: Change to private and get user to login?
        rule = {
            'scope': {
                'type': 'default'
            },
            'role': 'reader'
        }

        created_rule = service.acl().insert(calendarId=created_calendar['id'], body=rule).execute()

        # Insert user into users table, set session's user_id
        session["user_id"] = db.execute("INSERT INTO users (name, email, calendar_id) VALUES (:name, :email, :calendar_id)", name=session.get("userinfo")["name"], email=session.get("userinfo")["email"], calendar_id=created_calendar['id'])

        # Insert user's classes into database
        for i in range(5):
            subject = request.form.get("subject" + str(i))
            courseno = request.form.get("number" + str(i))

            # If a subject was selected
            if subject != "Subject":
                course_id = db.execute("SELECT id FROM courses WHERE subject=:subject AND courseno=:courseno", subject=subject, courseno=courseno)[0]["id"]
                db.execute("INSERT INTO classes (user_id, course_id) VALUES (:user_id, :course_id)", user_id=session["user_id"], course_id=course_id)

                # Check if calendar already exists for the course
                calendar_id = db.execute("SELECT id FROM calendars WHERE course_id = :course_id", course_id=course_id)

                # If not, create one
                if len(calendar_id) == 0:
                    service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)

                    # Create calendar
                    calendar = {
                        # Set title to course name
                        'summary': subject + ' ' + courseno,
                        'timeZone': 'America/New_York'
                    }

                    created_calendar = service.calendars().insert(body=calendar).execute()

                    print(created_calendar['id'])

                    # Set calendar viewing permissions to public
                    rule = {
                        'scope': {
                            'type': 'default'
                        },
                        'role': 'reader'
                    }

                    created_rule = service.acl().insert(calendarId=created_calendar['id'], body=rule).execute()

                    # Store calendar_id in database
                    db.execute("INSERT INTO calendars VALUES (:calendar_id, :course_id)", calendar_id=created_calendar['id'], course_id=course_id)

        # Redirect to index
        return redirect(url_for("index"))



@app.route("/create", methods=["GET", "POST"])
@login_required
@register_required
def create():
    # If user reached via GET (i.e., navigated to create page)
    if request.method == "GET":
        # Get list of classes user is in
        courses = db.execute("SELECT * FROM courses WHERE id IN (SELECT course_id FROM classes WHERE user_id = :user_id)", user_id = session["user_id"])

        return render_template("create.html", userinfo=session.get("userinfo"), courses=courses)

    # If user reached via POST (i.e., submitted form to create group)
    else:
        name = request.form.get("name")
        description = request.form.get("description")
        ispublic = True # Uncomment lines below after implementing inviting
        #visibility = request.form.get("visibility")
        #ispublic = False if visibility == "private" else True
        maxsize = request.form.get("maxsize")
        course_id = request.form.get("course")

        # GROUPME STUFF
        new_group = client.groups.create(name=name)
        new_group.update(share=True)
        new_group.create_bot(name="StudyGroupMe", callback_url=url+"/groupme", dm_notification=False)
        groupme_link = client.groups.list()[0].share_url

        group_id = db.execute("INSERT INTO groups (name, description, ispublic, course_id, maxsize, groupme) VALUES (:name, :description, :ispublic, :course_id, :maxsize, :groupme)", name=name, description=description, ispublic=ispublic, course_id=course_id, maxsize=maxsize, groupme=groupme_link)

        db.execute("INSERT INTO members (group_id, user_id) VALUES (:group_id, :user_id)", group_id=group_id, user_id=session["user_id"])

        return redirect(url_for("groups"))


@app.route("/join")
@login_required
@register_required
def join():

    # Didn't click join, so no error/success possible
    error = None

    # If Join Group link was clicked
    if request.args.get("group_id"):
        group_id = request.args.get("group_id")

        # Check if user is already member of the group
        isMember = db.execute("SELECT count(*) FROM members WHERE group_id = :group_id AND user_id = :user_id", group_id=group_id, user_id=session["user_id"])[0]['count(*)']

        # Check if user belongs to the class
        # associated with the group to be joined
        belongsToClass = db.execute("SELECT count(*) FROM classes WHERE user_id = :user_id AND course_id = (SELECT course_id FROM groups WHERE id = :group_id)", user_id=session["user_id"], group_id=group_id)[0]['count(*)']

        # Check if group is private
        isPublic = db.execute("SELECT ispublic FROM groups WHERE id = :group_id", group_id=group_id)[0]["ispublic"]

        # Check if group is at maxsize
        size = db.execute("SELECT count(*) FROM members WHERE group_id = :group_id", group_id=group_id)[0]["count(*)"]
        maxsize = db.execute("SELECT maxsize FROM groups WHERE id = :group_id", group_id=group_id)[0]["maxsize"]
        spaceAvaliable = size < maxsize

        # Error if can't join
        error = True

        # If the user is not already a member of the public group,
        # and is in the corresponding class,
        # and there is space avaliable, then add him to the group
        if not isMember and belongsToClass and isPublic and spaceAvaliable:
            # Successfully joining
            error = False

            db.execute("INSERT INTO members VALUES (:group_id, :user_id)", group_id=group_id, user_id=session["user_id"])

            # TODO: Add all current/future events of group to user's personal Google calendar

            calendar_id = db.execute("SELECT calendar_id FROM users WHERE id = :user_id", user_id=session['user_id'])[0]['calendar_id']

            # Select all current/future events in group
            # TODO: Change -05:00 to dynamic timezone
            events = db.execute("SELECT * FROM events WHERE group_id = :group_id AND replace(end, '-05:00', '') > strftime('%Y-%m-%dT%H:%M:%S', datetime('now', '-5 hours'))", group_id=group_id)

            service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)
            for event in events:
                group_name = db.execute("SELECT name FROM groups WHERE id = :group_id", group_id=group_id)[0]['name']
                course_id = db.execute("SELECT course_id FROM groups WHERE id = :group_id", group_id=group_id)[0]['course_id']
                course = db.execute("SELECT subject, courseno FROM courses WHERE id = :course_id", course_id = course_id)[0]
                gcal_event = {
                  'summary': group_name + " - " +  course['subject'] + " " + course['courseno'] + " " + event['purpose'],
                  'location': event['location'],
                  'description': event['description'],
                  'start': {
                    'dateTime': event['start'],
                    'timeZone': 'America/New_York',
                  },
                  'end': {
                    'dateTime': event['end'],
                    'timeZone': 'America/New_York',
                  }
                }

                gcal_event = service.events().insert(calendarId=calendar_id, body=gcal_event).execute()
                print('Event created: '+ (gcal_event.get('htmlLink')))


    courses = db.execute("SELECT * FROM courses WHERE id IN (SELECT course_id FROM classes WHERE user_id = :user_id)", user_id=session["user_id"])
    calendars = db.execute("SELECT * FROM calendars WHERE course_id IN (SELECT course_id FROM classes WHERE user_id = :user_id)", user_id=session["user_id"])
    return render_template("join.html", userinfo=session.get("userinfo"), courses=courses, calendars=json.dumps(calendars), error=error)


@app.route("/groups", methods=["GET", "POST"])
@login_required
@register_required
def groups():
    # If user navigated to /groups
    if request.method == "GET":
        groups = db.execute("SELECT * FROM groups WHERE id IN (SELECT group_id FROM members WHERE user_id = :user_id)", user_id=session["user_id"])
        for group in groups:
            group["size"] = db.execute("SELECT count(*) FROM members WHERE group_id = :group_id", group_id=group["id"])[0]["count(*)"]
            course = db.execute("SELECT * FROM courses WHERE id=:course_id", course_id=group["course_id"])[0]
            group["course"] = course["subject"] + " " + course["courseno"]
        return render_template("groups.html", userinfo=session.get("userinfo"), groups=groups)

    # If user clicked on 'Details' button
    else:
        group_id = request.form.get("group-id")
        group = db.execute("SELECT * FROM groups WHERE id = :group_id", group_id=group_id)[0]

        group["size"] = db.execute("SELECT count(*) FROM members WHERE group_id = :group_id", group_id=group["id"])[0]["count(*)"]
        course = db.execute("SELECT * FROM courses WHERE id=:course_id", course_id=group["course_id"])[0]
        group["course"] = course["subject"] + " " + course["courseno"]
        group["members"] = db.execute("SELECT name FROM users WHERE id IN (SELECT user_id FROM members WHERE group_id = :group_id) ORDER BY name", group_id=group["id"])



        # If event creation form was submitted
        if request.form.get("create-event"):

            # TODO: Insert only if group is public
            purpose = request.form.get("purpose")
            description = request.form.get("description")
            start_unf = request.form.get("start")
            end_unf = request.form.get("end")
            location = request.form.get("location")

            # Create datetime objects
            start_datetime = datetime.strptime(start_unf, "%m/%d/%Y %I:%M %p")
            end_datetime = datetime.strptime(end_unf, "%m/%d/%Y %I:%M %p")

            # Ensure start is before end and start not in past
            if end_datetime <= start_datetime or start_datetime < datetime.now():
                # Select all current / upcoming events
                # TODO: Change -05:00 to dynamic timezone
                group["events"] = db.execute("SELECT * FROM events WHERE group_id = :group_id AND replace(end, '-05:00', '') > strftime('%Y-%m-%dT%H:%M:%S', datetime('now', '-5 hours'))", group_id=group["id"])
                group["events"] = sorted(group["events"], key = lambda i: i["start"])

                for event in group["events"]:
                    event["start"] = datetime.strptime(event["start"].rsplit('-', 1)[0], "%Y-%m-%dT%H:%M:%S").strftime("%b %d, %Y - %I:%M %p")
                    event["end"] = datetime.strptime(event["end"].rsplit('-', 1)[0], "%Y-%m-%dT%H:%M:%S").strftime("%b %d, %Y - %I:%M %p")

                # Show group home with error
                return render_template("grouphome.html", userinfo=session.get("userinfo"), group=group, error=True)

            # Format datetimes in the Google Calendar API format
            start = start_datetime.strftime("%Y-%m-%dT%H:%M:%S")
            end = end_datetime.strftime("%Y-%m-%dT%H:%M:%S")

            # Append timezone
            start += "-05:00" # TODO: change to dynamic timezone based on DST
            end += "-05:00"

            # Get associated course, calendar, and group info
            course_id = db.execute("SELECT course_id FROM groups WHERE id = :group_id", group_id=group_id)[0]['course_id']
            course = db.execute("SELECT subject, courseno FROM courses WHERE id = :course_id", course_id = course_id)[0]

            calendar_id = db.execute("SELECT id FROM calendars WHERE course_id = (SELECT course_id FROM groups WHERE id = :group_id)", group_id=group_id)[0]['id']

            group_name = db.execute("SELECT name FROM groups WHERE id = :group_id", group_id=group_id)[0]['name']

            # Create event in public calendar of associated class
            # TODO: make sure none of the fields are left blank -- error when concatenating the "NoneType" to str
            # TODO: open Join in same tab
            service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)
            event = {
              'summary': group_name + " - " +  course['subject'] + " " + course['courseno'] + " " + purpose,
              'location': location,
              'description': description + "\n<a target='_top' href='" + url + "/join?group_id=" + group_id + "')'>Join Group!</a>",
              'start': {
                'dateTime': start,
                'timeZone': 'America/New_York',
              },
              'end': {
                'dateTime': end,
                'timeZone': 'America/New_York',
              }
            }

            event = service.events().insert(calendarId=calendar_id, body=event).execute()
            print('Event created: '+ (event.get('htmlLink')))

            calendars = db.execute("SELECT calendar_id FROM users WHERE id IN (SELECT user_id FROM members WHERE group_id = :group_id)", group_id=group_id)
            personal_event = {
              'summary': group_name + " - " +  course['subject'] + " " + course['courseno'] + " " + purpose,
              'location': location,
              'description': description,
              'start': {
                'dateTime': start,
                'timeZone': 'America/New_York',
              },
              'end': {
                'dateTime': end,
                'timeZone': 'America/New_York',
              }
            }

            for calendar in calendars:
                event = service.events().insert(calendarId=calendar["calendar_id"], body=personal_event).execute()

            # Insert event into database
            db.execute("INSERT INTO events (group_id, purpose, location, description, start, end) VALUES (:group_id, :purpose, :location, :description, :start, :end)", group_id=group_id, purpose=purpose, location=location, description=description, start=start, end=end)

        # Select all current / upcoming events
        # TODO: Change -05:00 to dynamic timezone
        group["events"] = db.execute("SELECT * FROM events WHERE group_id = :group_id AND replace(end, '-05:00', '') > strftime('%Y-%m-%dT%H:%M:%S', datetime('now', '-5 hours'))", group_id=group["id"])

        group["events"] = sorted(group["events"], key = lambda i: i["start"])

        for event in group["events"]:
            event["start"] = datetime.strptime(event["start"].rsplit('-', 1)[0], "%Y-%m-%dT%H:%M:%S").strftime("%b %d, %Y - %I:%M %p")
            event["end"] = datetime.strptime(event["end"].rsplit('-', 1)[0], "%Y-%m-%dT%H:%M:%S").strftime("%b %d, %Y - %I:%M %p")

        return render_template("grouphome.html", userinfo=session.get("userinfo"), group=group)

'''
@app.route("/settings")
@login_required
@register_required
def settings():
    return render_template("settings.html", userinfo=session.get("userinfo"))
'''

@app.route("/groupme", methods=["POST"])
def groupme():

    print(request.json.get("system"))
    print(request.json.get("text"))

    # When the first group member joins the GroupMe group
    if request.json.get("system") and "joined the group" in request.json.get("text"):
        groupme_id = request.json.get("group_id")
        group = client.groups.get(id=groupme_id)

        # Delete the bot associated with this group
        for bot in client.bots.list():
            if bot.group_id == groupme_id:
                bot.destroy()

        # Make the newly joined member the owner
        for member in group.members:
            if member.user_id != client.user.get_me()['id']:
                group.change_owners(member.user_id)
                break

        # Leave the group
        group.leave()

    return redirect("/")