import os
import pickle
import pandas as pd

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from global_strings import service_account_file
import traceback
def initialize_google_sheet_api(client_secret_file, scopes, api_service_name, api_version, token_file):
    ##initialize google_sheet API
    # cred = None
    #
    # if os.path.exists(token_file):
    #     with open(token_file, 'rb') as token:
    #         cred = pickle.load(token)
    #
    # if not cred or not cred.valid:
    #     if cred and cred.expired and cred.refresh_token:
    #         cred.refresh(Request())
    #     else:
    #         flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, scopes)
    #         cred = flow.run_local_server()
    #
    #     with open(token_file, 'wb') as token:
    #         pickle.dump(cred, token)

    # service_account initialisation
    #service_account_file = 'C:\\Users\\Administrator\\Downloads\\Nifty-project\\Nifty_Kite\\google_sheets\\artful-wind-402414-edfc43b570ab.json'
    credentials = service_account.Credentials.from_service_account_file(
        filename=service_account_file
    )

    try:
        service = build(api_service_name, api_version, credentials=credentials)
        print('Service created successfully')
        return service
    except Exception as e:
        print(f"Error building service: {e}")
        print(traceback.format_exc())


def add_row_to_sheet(service, values, sheet_details):
    try:
        value_range_body = {
            'majorDimension': 'ROWS',
            'values': values}

        service.spreadsheets().values().append(
            spreadsheetId=sheet_details["gsheetId"],
            valueInputOption='USER_ENTERED',
            range=sheet_details["worksheet_name"] + sheet_details["cell_range_insert"],
            body=value_range_body
        ).execute()

    except Exception as e:
        print(f"Error adding row to Google Sheet: {e}")
        print(traceback.format_exc())


def sheetValues_from_dfRow(row, log_format: list):
    try:
        values = []
        for i in range(0, log_format.__len__()):
            values.append(str(row[log_format[i]]))
        return [values]
    except Exception as e:
        print(f"Error getting sheet values from dataframe: {e}")
        print(traceback.format_exc())
        return [[]]


def add_dataframe_to_sheet(service, df: pd.DataFrame, sheet_details, log_format):
    try:
        values = [log_format]
        add_row_to_sheet(service, values, sheet_details)
        for i in range(0, df.__len__()):
            values = sheetValues_from_dfRow(df.iloc[i], log_format)
            add_row_to_sheet(service, values, sheet_details)
    except Exception as e:
        print(f"Error adding Dataframe to Google Sheet: {e}")
        print(traceback.format_exc())