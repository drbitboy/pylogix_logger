import pickle
import os.path
from google_auth_oauthlib.flow import InstalledAppFlow as IAF
from google.auth.transport.requests import Request

### SCOPES:
### 0) https://developers.google.com/sheets/api/guides/authorizing
### 1) Read, Write, Edit, Delete spreadsheets
def get_creds(SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
             ,TOKEN_FILE = 'token.pickle'
             ,CREDENTIAL_FILE = 'credentials.json'
             ):
    urlpr = 'Please visit this URL to authorize this application: {url}'
    codepr = 'Enter the authorization code: '
    creds = False

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as ftok: creds = pickle.load(ftok)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = IAF.from_client_secrets_file(CREDENTIAL_FILE,SCOPES)
            creds=flow.run_console(authorization_prompt_message=urlpr
                                  ,authorization_code_message=codepr
                                  )
        # Pickle credentials for future runs
        with open(TOKEN_FILE, 'wb') as ftok: pickle.dump(creds, ftok)

    return creds
