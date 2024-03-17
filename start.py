import os
from django.core.management import execute_from_command_line
import webbrowser
import os
os.system('color')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "starlight.settings")

def print_wellcome_message():
    COLOR = '\033[104m'  # change it, according to the color need

    END = '\033[0m'

    welcome_message = '''\t\tWelcome to STAR_light fot T-Mobile team!\n
\t\tThis application is created by Timur Samatov.

\t\tI hope you find this application useful and enjoyable.
\t\tIf you do, please consider visiting my LinkedIn page and endorsing my skills
\t\tin Python, Django, XML, Wireshark that I used to wrote this application.
\t\tIt would mean a lot to me and help me improve my professional profile.\n

\t\tYou can find my LinkedIn page here https://www.linkedin.com/in/samatov-timur\n
\t\tThank you for your support!\n\n'''

    print(COLOR + welcome_message + END) #print a message

def run_server():
    webbrowser.open('http://127.0.0.1:8000/')
    print_wellcome_message()
    execute_from_command_line(["manage.py", "runserver", "--noreload", "--skip-checks"])


if __name__ == "__main__":
    run_server() 