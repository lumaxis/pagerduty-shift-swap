# PagerDuty Shift Swap

This Python script enables automatic swapping of shifts between two users in a PagerDuty schedule.
Given a schedule name and two dates marking the start of each user's on-call weeks, it will swap the shifts of both users using overrides.

## Prerequisites

A working Python 3 environment.

## Installation

Clone the repository to your local machine.
Set up a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

Install the required packages:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the root directory of the project and add the following variable:

```plaintext
PAGERDUTY_API_TOKEN=your_api_token_here
```

## Usage

Run the script with the following command:

```bash
python pagerduty_shift_swap.py --schedule schedule-name --current_user_week YYYY-MM-DD --other_username "Other User's Username" --other_user_week YYYY-MM-DD --dry-run
```
`--dry-run`: Use this flag to simulate the shift swap without making actual changes.

## Contributing

Contributions are welcome! Please feel free to submit pull requests.
