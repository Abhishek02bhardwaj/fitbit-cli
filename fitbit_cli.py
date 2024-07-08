import click
import json
import requests
import pandas as pd
import base64
import hashlib
import os
import urllib.parse
from datetime import datetime
import re

@click.group()
def fitbit():
    """Fitbit CLI tool for managing OAuth tokens and extracting data."""
    pass

def get_config():
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    return config['fitbit']

def save_tokens(email, tokens):
    try:
        with open('tokens.json', 'r') as tokens_file:
            all_tokens = json.load(tokens_file)
    except FileNotFoundError:
        all_tokens = {}

    all_tokens[email] = tokens

    with open('tokens.json', 'w') as tokens_file:
        json.dump(all_tokens, tokens_file, indent=4)

def save_refresh_tokens(email, token_info):
    try:
        with open('refresh_tokens.json', 'r') as tokens_file:
            all_tokens = json.load(tokens_file)
    except FileNotFoundError:
        all_tokens = {}

    all_tokens[email] = token_info

    with open('refresh_tokens.json', 'w') as tokens_file:
        json.dump(all_tokens, tokens_file, indent=4)

def get_refresh_tokens(email):
    with open('refresh_tokens.json', 'r') as tokens_file:
        all_tokens = json.load(tokens_file)
    return all_tokens.get(email)

@fitbit.command()
@click.option('-auth', 'action', flag_value='auth', help='Get the authorization token for the Fitbit email')
@click.option('-refresh', 'action', flag_value='refresh', help='Get the refresh token for the Fitbit email')
@click.argument('fitbit_email')
def token(action, fitbit_email):
    """Manage Fitbit tokens."""
    if action == 'auth':
        auth(fitbit_email)
    elif action == 'refresh':
        refresh(fitbit_email)
    else:
        click.echo("Invalid action. Use -auth or -refresh.")

def auth(fitbit_email):
    config = get_config()
    authorize_uri = config['authorize_uri']
    client_id = config['client_id']
    client_secret = config['client_secret']
    redirect_uri = config['redirect_uri']

    def generate_code_verifier():
        return base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8').rstrip('=')

    def generate_code_challenge(verifier):
        challenge = hashlib.sha256(verifier.encode('utf-8')).digest()
        return base64.urlsafe_b64encode(challenge).decode('utf-8').rstrip('=')

    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)

    state = base64.urlsafe_b64encode(os.urandom(16)).decode('utf-8').rstrip('=')

    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'activity cardio_fitness electrocardiogram heartrate location nutrition oxygen_saturation profile respiratory_rate settings sleep social temperature weight',
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
        'state': state
    }
    auth_url = f"{authorize_uri}?{urllib.parse.urlencode(params)}"
    print("Go to the following URL and authorize the app:")
    print(auth_url)

    redirect_response = input("Paste the full redirect URL here: ")
    parsed_url = urllib.parse.urlparse(redirect_response)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    authorization_code = query_params.get('code')[0]
    returned_state = query_params.get('state')[0]

    if returned_state != state:
        raise ValueError("State does not match")

    token_url = 'https://api.fitbit.com/oauth2/token'
    client_creds = f"{client_id}:{client_secret}"
    client_creds_b64 = base64.b64encode(client_creds.encode()).decode()

    headers = {
        'Authorization': f'Basic {client_creds_b64}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'client_id': client_id,
        'grant_type': 'authorization_code',
        'code': authorization_code,
        'redirect_uri': redirect_uri,
        'code_verifier': code_verifier
    }

    response = requests.post(token_url, headers=headers, data=data)

    if response.status_code == 200:
        token_info = response.json()
        print("Access Token:", token_info['access_token'])
        print("Refresh Token:", token_info['refresh_token'])

        save_tokens(fitbit_email, {
            'access_token': token_info['access_token'],
            'refresh_token': token_info['refresh_token']
        })
        print("Tokens saved to tokens.json")
    else:
        print("Error:", response.status_code, response.text)

def refresh(fitbit_email):
    config = get_config()
    client_id = config['client_id']
    client_secret = config['client_secret']

    tokens = get_tokens(fitbit_email)
    if not tokens:
        print("No tokens found for the provided email.")
        return

    refresh_token = tokens['refresh_token']

    token_url = 'https://api.fitbit.com/oauth2/token'
    client_creds = f"{client_id}:{client_secret}"
    client_creds_b64 = base64.b64encode(client_creds.encode()).decode()

    headers = {
        'Authorization': f'Basic {client_creds_b64}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id,
        'expires_in': 28800  # 8 hours
    }

    response = requests.post(token_url, headers=headers, data=data)

    if response.status_code == 200:
        token_info = response.json()
        print("New Access Token:", token_info['access_token'])
        print("New Refresh Token:", token_info['refresh_token'])

        save_refresh_tokens(fitbit_email, token_info)
        print("New tokens saved to refresh_tokens.json")
    else:
        print("Error:", response.status_code, response.text)

@fitbit.group()
def extract():
    """Extract Fitbit data."""
    pass

@extract.command('intraday-heart-rate')
@click.argument('start_date')
@click.argument('end_date', required=False)
@click.argument('fitbit_email')
def intraday_heart_rate(start_date, end_date, fitbit_email):
    """Extract intraday heart rate data for a specific date or date range."""
    if not validate_date(start_date):
        print("Invalid start date format. Use YYYY-MM-DD.")
        return
    if end_date and not validate_date(end_date):
        print("Invalid end date format. Use YYYY-MM-DD.")
        return
    if not validate_email(fitbit_email):
        print("Invalid email format.")
        return

    if end_date:
        extract_intraday_heart_rate_range(fitbit_email, start_date, end_date)
    else:
        extract_intraday_heart_rate_single(fitbit_email, start_date)

def validate_date(date_str):
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validate_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def extract_intraday_heart_rate_single(email, specific_date):
    tokens = get_refresh_tokens(email)
    if not tokens:
        print(f'No tokens found for email: {email}')
        return

    access_token = tokens['access_token']
    user_id = tokens['user_id']

    api_url = f'https://api.fitbit.com/1/user/{user_id}/activities/heart/date/{specific_date}/1d/1min.json'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.get(api_url, headers=headers)
    data = response.json()

    if 'activities-heart-intraday' in data:
        heart_rate_data = data['activities-heart-intraday']['dataset']
        for record in heart_rate_data:
            record['date'] = specific_date
            record['email'] = email
            record['id'] = user_id

        df = pd.DataFrame(heart_rate_data)
        if not df.empty:
            df['time'] = df['time'].apply(lambda x: x[:5])
            df = df.rename(columns={'value': 'heart-rate'})
            df = df[['email', 'id', 'date', 'time', 'heart-rate']]
            df.to_csv(f'heart_rate_data_{specific_date}.csv', index=False)
            print(f'Data saved for {email} on {specific_date}.')
        else:
            print(f'No heart rate data available for {email} on {specific_date}.')
    else:
        print(f'No intraday heart rate data available for {specific_date}.')

def extract_intraday_heart_rate_range(email, start_date, end_date):
    tokens = get_refresh_tokens(email)
    if not tokens:
        print(f'No tokens found for email: {email}')
        return

    access_token = tokens['access_token']
    user_id = tokens['user_id']

    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')

    date_list = pd.date_range(start=start_date, end=end_date).to_pydatetime().tolist()
    all_data = pd.DataFrame()

    for date in date_list:
        date_str = date.strftime('%Y-%m-%d')
        daily_data = fetch_heart_rate_data_for_date(user_id, access_token, date_str, email)
        if not daily_data.empty:
            all_data = pd.concat([all_data, daily_data], ignore_index=True)

    email_prefix = email.split('@')[0]
    output_dir = 'Heart-Rate-Data'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not all_data.empty:
        all_data.to_csv(f'{output_dir}/{email_prefix}.csv', index=False)
        print(f'Data saved for {email}.')
    else:
        pd.DataFrame(columns=['email', 'id', 'date', 'time', 'heart-rate']).to_csv(f'{output_dir}/{email_prefix}_heart_rate_data.csv', index=False)
        print(f'No data available for {email}, created an empty file.')

def fetch_heart_rate_data_for_date(user_id, access_token, date, email):
    api_url = f'https://api.fitbit.com/1/user/{user_id}/activities/heart/date/{date}/1d/1min.json'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        try:
            data = response.json()
            if 'activities-heart-intraday' in data:
                heart_rate_data = data['activities-heart-intraday']['dataset']
                for record in heart_rate_data:
                    record['date'] = date
                    record['email'] = email
                    record['id'] = user_id

                df = pd.DataFrame(heart_rate_data)
                if not df.empty:
                    df['time'] = df['time'].apply(lambda x: x[:5])
                    df = df.rename(columns={'value': 'heart-rate'})
                    df = df[['email', 'id', 'date', 'time', 'heart-rate']]
                return df
            else:
                return pd.DataFrame()
        except ValueError:
            print(f'Failed to parse JSON response for {email} on {date}.')
            return pd.DataFrame()
    else:
        print(f'Failed to fetch data for {email}. Status code: {response.status_code}, Message: {response.text}')
        return pd.DataFrame()

if __name__ == '__main__':
    fitbit()
