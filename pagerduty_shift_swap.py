import requests
import datetime
import argparse
import os
import logging

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from a .env file

# Configure logging with dynamically set log level
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=getattr(logging, log_level, logging.INFO), format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for the PagerDuty API
API_BASE_URL = 'https://api.pagerduty.com'
HEADERS = {
    'Accept': 'application/vnd.pagerduty+json;version=2',
    'Authorization': f'Token token={os.getenv('PAGERDUTY_API_TOKEN')}'  # Secure API token usage
}

def get_current_user():
    """Fetch the current user's information from PagerDuty."""
    url = f"{API_BASE_URL}/users/me"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    logging.debug(f"Current user fetched successfully: {response.text}")
    return response.json()['user']

def get_user_by_username(username):
    """Retrieve a user by username, which can be an email or name."""
    url = f"{API_BASE_URL}/users"
    params = {'query': username}
    logging.info(f"Searching for user by username: {username}")
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    users = response.json()['users']
    if users:
        logging.debug(f"User found: {users[0]}")
        return users[0]
    else:
        logging.error("No user found with that username.")
        return None

def get_schedule_id_by_name(schedule_name):
    """Retrieve a schedule ID by its name."""
    
    url = f"{API_BASE_URL}/schedules"
    params = {'query': schedule_name}
    logging.info(f"Searching for schedule by name: {schedule_name}")
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    schedules = response.json()['schedules']
    if schedules:
        logging.debug(f"Schedule found: {schedules[0]}")
        return schedules[0]['id']
    else:
        logging.error("No schedule found with that name.")
        return None

def get_schedule(schedule_id, start_date, end_date):
    """Fetch schedule details for a given period"""

    url = f"{API_BASE_URL}/schedules/{schedule_id}"
    params = {'since': start_date, 'until': end_date, 'time_zone': 'UTC'}
    logging.info(f"Fetching schedule from {start_date} to {end_date} for schedule ID {schedule_id}")
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    logging.debug(f"Schedule fetch successful: {response.text}")
    schedule_data = response.json()['schedule']
    return schedule_data['final_schedule']['rendered_schedule_entries']

def create_override(schedule_id, user, start, end, dry_run):
    """Create or simulate an override in a schedule"""

    override = {
        'override': {
            'user': {'id': user['id'], 'type': 'user_reference'},
            'start': start, 'end': end, 'type': 'schedule_override'
        }
    }
    if dry_run:
        logging.info(f"Dry Run: Would create override for {user['summary']} from {start} to {end} in schedule {schedule_id}")
    else:
        url = f"{API_BASE_URL}/schedules/{schedule_id}/overrides"
        logging.info(f"Creating override for {user['summary']} from {start} to {end} in schedule {schedule_id}")
        response = requests.post(url, headers=HEADERS, json=override)
        response.raise_for_status()
        logging.debug(f"Override creation successful: {response.text}")

def swap_shifts(schedule_id, current_user, other_user, current_user_shifts, other_user_shifts, dry_run):
    """Swap shifts between two users"""

    logging.info("Starting shift swap process...")
    for shift in current_user_shifts:
        create_override(schedule_id, other_user, shift['start'], shift['end'], dry_run)

    for shift in other_user_shifts:
        create_override(schedule_id, current_user, shift['start'], shift['end'], dry_run)

def main(schedule_name, current_user_week, other_user_username, other_user_week, dry_run):
    """Main function to orchestrate the shift swapping process."""

    logging.info("Script execution started...")
    current_user = get_current_user()
    other_user = get_user_by_username(other_user_username)
    if not other_user:
        logging.error("Unable to find other user.")
        return

    schedule_id = get_schedule_id_by_name(schedule_name)
    if not schedule_id:
        logging.error("Unable to find schedule.")
        return

    current_user_start_date = current_user_week
    current_user_end_date = (datetime.datetime.strptime(current_user_start_date, "%Y-%m-%d") + datetime.timedelta(days=8)).strftime("%Y-%m-%d")
    other_user_start_date = other_user_week
    other_user_end_date = (datetime.datetime.strptime(other_user_start_date, "%Y-%m-%d") + datetime.timedelta(days=8)).strftime("%Y-%m-%d")

    current_user_week_shifts = get_schedule(schedule_id, current_user_start_date, current_user_end_date)
    current_user_shifts = [shift for shift in current_user_week_shifts if shift['user']['id'] == current_user['id']]
    other_user_week_shifts = get_schedule(schedule_id, other_user_start_date, other_user_end_date)
    other_user_shifts = [shift for shift in other_user_week_shifts if shift['user']['id'] == other_user['id']]

    swap_shifts(schedule_id, current_user, other_user, current_user_shifts, other_user_shifts, dry_run)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Swap shifts between the current user and another user for specified weeks.')
    parser.add_argument('--schedule', required=True, help='Name of the schedule')
    parser.add_argument('--current_user_week', required=True, help='Start date of the current user\'s week (YYYY-MM-DD)')
    parser.add_argument('--other_username', required=True, help='Username of the other user')
    parser.add_argument('--other_user_week', required=True, help='Start date of the other user\'s week (YYYY-MM-DD)')
    parser.add_argument('--dry-run', action='store_true', help='Run script in dry-run mode without making actual changes')

    args = parser.parse_args()
    main(args.schedule, args.current_user_week, args.other_username, args.other_user_week, args.dry_run)
