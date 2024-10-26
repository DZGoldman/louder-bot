## Email Client Setup

#### Step 1: Create a Google Cloud Project

- Go to Google Cloud Console: Visit [Google Cloud Console](https://console.cloud.google.com) with the email address the bot will be using.
- Create a New Project:
- Click on the project dropdown in the top-left corner.
- Click on New Project and give it a name, then click Create.

Enable Gmail API:

- In the left sidebar, go to APIs & Services > Library.
- Search for "Gmail API" and click on it.
- Click on Enable to enable the API for your project.

#### Step 2: Configure OAuth Consent Screen

Set Up the Consent Screen:

- In the left sidebar, go to APIs & Services > OAuth consent screen.
- Select External and click Create.
- Fill in the necessary information (App name, user support email, etc.), then click Save and Continue.

#### Step 3: Create OAuth 2.0 Credentials

Create Credentials:

- Go to APIs & Services > Credentials.
- Click on Create Credentials and select OAuth client ID.
- Select Desktop app as the application type and click Create.
- Download the JSON file with your client ID and secret by clicking the download icon next to your newly created credentials.

#### Step 4: Include Credentials in Repo

- Rename the JSON file `credentials.json`
- Move it into the root directory of this repo

#### Step 5: Add Yourself as a Test User

- Go to Google Cloud Console and open your project.
- In the left sidebar, navigate to APIs & Services > OAuth consent screen.
- Scroll down to the Test users section.
- Click Add users and enter the email address you’re using to authenticate.

## Environmental Variables:

GOOGLE_EMAIL: Email address (same as address you used to create google gloud project)

## Installation

From root directory:

```
pip install -r requirements.txt
```

## Run Bot

From root directory:

```
python main.py
```
