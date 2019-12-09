# StudyGroupMe - Design Document

## Introduction
The main goal of our project is to make a functional website that can be used in the future by students in the Harvard College community. Therefore, we had in mind the most common preferences of Harvard students to decide what components to integrate into our website. Two main components are the integration of Google Calendar and GroupMe chats, both widely used by the majority of students on campus.

## Technologies:
For the Python backend, we used Flask. For the frontend, we used Jinja, Bootstrap, HTML, CSS, and JavaScript. We used a SQLite database to store information in the following tables: users, courses, classes, groups, members, calendars, and events. Courses were retrieved from a static JSON file of all Harvard College courses.

### Google Calendar API:
We used the Google Calendar API to integrate a Google Calendar that displays all the study group events the user is attending. We also have separate calendars for each class, displaying all the study groups available in that class. One main advantage of Google Calendar is that the user can easily add the calendar to her/his own Google Calendar account, which is a highly effective way of keeping track of the meeting times of one’s study groups.

### GroupMe:
One of the most important aspects of creating study groups is to be able to contact the people in the group with you. We used Groupy, which is an API client for the GroupMe messaging service, to dynamically create a group chat for each group. The link to join the group chat is displayed on the group’s page so that members can join the group chats. The only caveat to this is that group chats must be created by someone first and GroupMe accounts must be associated with a phone number, so we worked around this by creating groups using Ashley Zhuang’s account. We use a bot to detect when the first group member joins the group, at which point she/he gets ownership automatically transferred to her/him and Ashley Zhuang (along with the bot) leaves the group.

## Design Decisions:
- We display a personal calendar so that the user can see all her/his StudyGroupMe events in a single place.
- Each event is always displayed with time, location, and purpose; these are the main deciding factors when one wants to join a study group (convenience and whether it fits your needs).
- Each group creator can choose a max size, which is capped at 8, based on her/his group’s needs so that the group remains tight-knit and effective.
- Group home page: users can see all upcoming events so that there is a place where events are categorized by the study group. Adding events is also on this page as events are associated with groups.