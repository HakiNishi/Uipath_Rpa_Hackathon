# Uipath_Rpa_Hackathon
UiPath_Hackathon

UIPath RPA Hackathon
Meeting Automation using Google Calendar

Problem statement

Automate user requests made in the form of text. A NLP classifier will determine the users’ intent and call the corresponding bot that would process the users’ requirement. Some user’s intent could be to reschedule meetings, change meeting locations, add or remove people from the meeting invitations, etc.

Proposed Solution

    The user will send an email to a admin team regarding the meeting details. The body of the email is automatically fetched and subjected to NLP to find the context of the email body.
    Once the context is identified then the corressponding UiPath job is started.
    eg: If the user sends email to schedule a meeting, then automatically the schedule job is triggered which will schedule an event in google calendar and invites all the members through email.

Tech Stack

    UiPath Orchestrator
    AWS Lambda
    AWS S3
    Python (Data processing throgh API)
