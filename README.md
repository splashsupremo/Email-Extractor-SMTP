Pro Email Extractor - Setup Guide


Requirements
Operating System: macOS 10.15+ or Windows 10/11
Python: Version 3.8 - 3.11 (Python 3.12+ has some compatibility issues with dependencies)
Step 1: Install Python
macOS
1. Download from python.org (use 3.10 or 3.11)
2. Run the installer
3. Open Terminal and verify:

python3 --version

Windows
1. Download from python.org
2. IMPORTANT: Check "Add Python to PATH" during installation
3. Open Command Prompt and verify:

python --version

Step 2: Install Dependencies
Open Terminal (macOS) or Command Prompt (Windows) and run:

pip install customtkinter requests beautifulsoup4 lxml fake-useragent dnspython

If you get a permission error on macOS, use:

pip3 install --user customtkinter requests beautifulsoup4 lxml fake-useragent dnspython

If you get a pip not found error, try:

python3 -m pip install customtkinter requests beautifulsoup4 lxml fake-useragent dnspython

Step 3: Run the Bot
macOS

cd ~/Desktop/Emails
python3 email_extractor.py

Windows
cd C:\Users\YourName\Desktop\Emails
python email_extractor.py

SMTP Setup (for sending emails)
1. Click ⚙️ Manage SMTP in the app
2. Enter your SMTP details (host, port, username, password)
3. Port 465 → UNCHECK "Use STARTTLS"
4. Port 587 → CHECK "Use STARTTLS"
5. Click 💾 Save Profile
6. Click 🔍 Test Connection
