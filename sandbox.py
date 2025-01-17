
import pickle
from cs50 import SQL
from google.oauth2 import service_account
import googleapiclient.discovery

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'static/studygroupme-09dac6eaa430.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)


'''
courses = pickle.load(open("static/courses.p", "rb"))
db = SQL("sqlite:///studygroupme.db")

for subject in courses:
    for courseno in courses[subject]:
        db.execute("INSERT INTO courses (subject, courseno) VALUES (:subject, :courseno)", subject=subject, courseno=courseno)


@app.route("/create", methods=["GET", "POST"])
@login_required
def create():

    if request.method == "GET":
        return render_template("create.html", userinfo=session.get("userinfo"))
    else:
        name = request.form.get("name")
        description = request.form.get("description")
        visibility = request.form.get("visibility")
        ispublic = True if visibility == "public" else False
        maxsize = request.form.get("maxsize")
        course_id = request.form.get("course")

        print(name + description + visibility + ispublic + maxsize + course_id)

        #db.execute("INSERT INTO groups (name, description, ispublic, course_id, maxsize) VALUES (:name, :description, :ispublic, :course_id, :maxsize)", name=name, description=description, ispublic=ispublic, course_id=course_id, maxsize=maxsize)

        return redirect(url_for("groups"))

'''

'''
rule = {
    'scope': {
        'type': 'default'
    },
    'role': 'reader'
}

created_rule = service.acl().insert(calendarId='cm5uqi608rg59bd03bmlsiea1k@group.calendar.google.com', body=rule).execute()

print(created_rule['id'])
'''

'''
from groupy.client import Client
from groupy.api.memberships import Memberships
from groupy.api.bots import Bot, Bots

client = Client.from_token("gtKf44NKan6p9pvI4ankqZKNFZ4mwInFC5SxwNZA")

new_group = client.groups.create(name="GP Test")
new_group.update(share=True)
new_group.create_bot(name="StudyGroupMe", callback_url="https://afb8e24f-717d-4d78-ae73-762b8eee933e-ide.cs50.xyz:8080/groupme", dm_notification=False)
'''

page_token = None
while True:
    print("Main loop")
    calendar_list = service.calendarList().list(pageToken=page_token).execute()
    for calendar in calendar_list['items']:
        print(calendar['id'])
        #service.calendars().delete(calendarId=calendar['id']).execute()
    page_token = calendar_list.get('nextPageToken')
    if not page_token:
        break