# StudyGroupMe

## Description
StudyGroupMe is a web application that facilitates the creation/scheduling of study groups in classes at Harvard College. You can see when/where study groups are meeting in your classes on a publicly-viewable class calendar, and you can join those groups. You can also create new groups and create new events for your groups.

## Access
First, make note of your CS50 IDE's Web Server URL (in this example, we will use http://afb8e24f-717d-4d78-ae73-762b8eee933e-ide.cs50.xyz:8080). Then, log in to CS50 ID at https://id.cs50.io/ and create a client with any description and a callback URL of http://afb8e24f-717d-4d78-ae73-762b8eee933e-ide.cs50.xyz:8080/callback (replacing the base URL with your own).

Next, execute the following exports in the terminal of your CS50 IDE, with the values obtained from the client created in CS50 ID. We give our example below:

```export BASE_URL=https://afb8e24f-717d-4d78-ae73-762b8eee933e-ide.cs50.xyz:8080
export CLIENT_ID=U32mPdjv1ZWLiGRfLgux3zxtDRu0HC5C
export CLIENT_SECRET=q35gxqRhjfX1177Otr9EgVFL6SaC1y7BHV_e1hCIMwfze0_5HYj14q01WYIRf00R
export SERVER_METADATA_URL=https://id50.auth0.com/.well-known/openid-configuration
```

Important note: `BASE_URL` should NOT have a forward slash at the end.

Finally, execute the following `pip` installs in the terminal of your CS50 IDE:

```sudo pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
sudo pip install authlib
sudo pip install GroupyAPI
```

Now you are ready to run `flask run` in the `studygroupme` directory to get the app running.

## Functionality
When you open the website, a welcome page is displayed with a brief description of the goal of the site and a “Log In” button. We use HarvardKey authentication for the login to ensure that only students belonging to Harvard University can access the website.

When you log in to the website for the first time, a registration page will appear prompting you for the courses you are currently taking. The complete list of Harvard College courses is available with two drop-downs, one for the subject of the course and the other for its catalog number.

After registration, or directly after logging in if already registered, you will be redirected to the home page, where you can find a personal Google Calendar displayed containing the events of the study groups you belong to. Through the navigation bar, you can access the “Home,” “Join Group,” “Create Group,” and “My Groups” pages.

“Join Group” leads you to a page with a list of all your courses. By clicking each one of them, a course calendar is displayed in the center of the page with all the study group events that students taking that class have created. By clicking the events on the calendar, you can see the name of the study group, the start and end times of the event created, the location, a link to the Google Maps, and a description of the event. There is also a link available to join the group, which would add you to that study group. In the footer, you can also find the option of adding the event to your own Google Calendar. A brief description of how the page works is presented on the top of the page.

If you don’t find any study groups that work with your schedule, you can instead create your own group through the “Create Group” page. You can enter the name and description of the group, the class with which it is associated, and the maximum number of people you want in the study group.

“My Groups” leads you to a page where you can view the study groups of which you are a member. In each of the cards displayed, you can click on “Details” to view a more detailed page about the group (including a list of upcoming events, members, and a GroupMe chat link that allows you to join a group chat created specifically for that study group).

At the top-right corner of the page, you can find a button to log out of the website which takes you back to the welcome page.