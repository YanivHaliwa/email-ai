 
# Gmail Automation Interaction Toolkit: 

## Automated Emailing with OpenAI Integration and Command-Line Email Management


### `emi.py` - Email Interaction Tool

This script allows users to read from and send emails via the command line, offering functionality to interact with their Gmail in a more flexible manner.

#### Key Features:
- **Read Emails**: Can fetch and display emails with options to specify how many emails to read.
- **Send Emails**: Provides a command-line interface to send emails, allowing users to input the recipient, subject, and body.
- **Argument Parsing**: Uses argparse to handle input options, making it easy to integrate into other scripts or workflows.

for more scripts using GPT for translation and subtitle check here: [Subtitle Management Tools section in the main README](https://github.com/YanivHaliwa/Linux-Stuff/tree/master?tab=readme-ov-file#subtitle-management-tools).

#### Usage:
- **Read Emails**: Use the `-r` flag to read emails. You can specify the number of emails to read as an argument.
- **Send Emails**: Use the `-s` flag followed by the recipient's email address to send an email. The script will prompt for the subject and message body.

#### Example Command:
```bash
# Read the latest 5 emails
python emi.py -r 5

# Send an email
python emi.py -s example@example.com
```


### `autogmail.py` - Automated Email Sender with OpenAI Integration

This script automates sending emails using Gmail through a scheduled task (like a cron job). It uses the Google API to authenticate and send emails, and OpenAI's API to generate dynamic email content.

#### Key Features:
- **OpenAI Content Generation**: Leverages OpenAI's GPT model to create email content based on a predefined prompt.
- **Automated Email Dispatch**: Configured to send emails at specific intervals using scheduling tools like crontab.
- **Custom Email Configuration**: Users can set their email address, subject, and utilize dynamic content in the body.

#### Usage:
- **Setup**: Ensure `credentials.json` and `token.pickle` are placed in the same directory as the script.
- **Configuration**: Modify the email parameters within the script to match your sender and recipient details.
- **Scheduling**: Add the script to your crontab or another scheduler to run at your desired frequency.

#### Example Cron Setup:
```bash
# Run every day at 9 AM
0 9 * * * /usr/bin/python3 /path/to/autogmail.py
```

# Google API Authentication Setup

This guide provides a step-by-step process for setting up Google API authentication for your Python projects using `credentials.json` and `token.pickle`.

## Prerequisites

- A Google Cloud account


### Step 1: Google Cloud Project Setup

1. **Open Google Cloud Console**: Visit the [Google Cloud Console](https://console.cloud.google.com/apis/dashboard).
2. **Create or Select a Project**: If you haven't already created a project:
    - Click on the project dropdown next to the Google Cloud Platform logo.
    - Click **New Project**, give it a name, and click **Create**.

### Step 2: Enable APIs

1. **Enable Gmail API**:
   - Navigate to the [Gmail API page](https://console.cloud.google.com/apis/library/gmail.googleapis.com?project=email-392618).
   - Click **Enable** to activate the Gmail API for your project.

### Step 3: Configure Credentials

1. **Navigate to Credentials**:
   - Go to the **Credentials** tab on the left sidebar in the Google Cloud Console.
2. **Create OAuth Client ID**:
   - Click **Create credentials** and select **OAuth client ID**.
   - Choose **Desktop app** as the Application type.
   - Click **Create**.
   - In the window that appears, click **Download JSON**.
   - Rename the downloaded file to `credentials.json`.
   - Move this file to the same folder location as your Python script.

## Security Note

Keep your `credentials.json` and `token.pickle` secure, especially if you are using shared machines or deploying your application publicly. Consider using environment variables or other methods to protect sensitive information.



 