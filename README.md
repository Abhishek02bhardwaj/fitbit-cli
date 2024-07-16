# pyFitbit

pyFitbit is a CLI tool for managing Fitbit OAuth tokens and extracting intraday heart rate data. The tool provides an easy way to authenticate with Fitbit, refresh tokens, and retrieve detailed heart rate data for specified dates or date ranges. Ideal for developers and data analysts working with Fitbit data, this tool streamlines the process of accessing and managing Fitbit health data programmatically.

## Features

- **OAuth Token Management**: Authenticate and refresh Fitbit OAuth tokens effortlessly.
- **Data Extraction**: Extract intraday heart rate data for specific dates or date ranges.
- **Configurable**: Easily configure your Fitbit app credentials via a `config.json` file.

  ## Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/your-username/pyfitbit.git
    cd pyfitbit
    ```

2. Install the required dependencies:

    ```sh
    pip install -r requirements.txt
    ```

3. Install the CLI tool:

    ```sh
    pip install --editable .
    ```

## Configuration

Create a `config.json` file with your Fitbit app credentials and API settings. Here is an example:

```json
{
  "fitbit": {
    "authorize_uri": "https://www.fitbit.com/oauth2/authorize",
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "redirect_uri": "your_redirect_uri"
  }
}
```

## Usage

### 1. OAuth Token Management

#### Authenticate and Get Tokens

To authenticate and get the authorization token for a Fitbit email:

```sh
pyfitbit token -auth fitbit_email@example.com
```

#### Refresh Tokens

To refresh the tokens for a Fitbit email:

```sh
pyfitbit token -refresh fitbit_email@example.com
```

### 2. Data Extraction

#### Extract intraday heart rate data for a specific date:

```sh
pyfitbit extract intraday-heart-rate date fitbit_email@example.com
```

To extract intraday heart rate data for a date range:

```sh
pyfitbit extract intraday-heart-rate start_date end_date fitbit_email@example.com
```

## Code Overview

### Token Management

- **auth**: Handles the OAuth autharization process and saves the tokens.
- **refresh**: Refreshes the tokens and save new tokens.

### Data Extraction 

- **intraday_heart_rate**: Extracts intraday heart rate data for a given date or date range.

### Utility Functions 

- **get_config**: Loads the configuration from `config.json`.
- **save_tokens**: Saves token to `token.json`.
- **save_refresh_tokens**: Saves refreshed tokens to `refresh_tokens.json`.
- **get_refresh_tokens**: Retrieves tokens from `refresh_tokens.json`.
- **validate_date**: Validates the date format.
- **validate_email**: Validates the email format.
- **fetch_heart_rate_data_for_date**: Fetches heart rate data for a specific date.

## Example

```sh
# Authenticate and get tokens
pyfitbit token -auth example@example.com

# Refresh tokens
pyfitbit token -refresh example@example.com

# Extract intraday heart rate data for a single date
pyfitbit extract intraday-heart-rate 2023-07-01 example@example.com

# Extract intraday heart rate data for a date range
pyfitbit extract intraday-heart-rate 2023-07-01 2023-07-07 example@example.com
```

## License
This project is licensed under the MIT License.
