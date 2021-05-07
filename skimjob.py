import argparse, os, usb, subprocess;
import RPi.GPIO as GPIO
from time import sleep
from datetime import datetime
from shutil import copyfile
from shutil import which
import serial.tools.list_ports

#from gpiozero import LED
#from time import sleep

# prints the banner
def banner():
    print(style.RED + " $$$$$$\  $$\       $$\                  $$$$$\           $$\ ")
    print("$$  __$$\ $$ |      \__|                 \__$$ |          $$ | ")
    print("$$ /  \__|$$ |  $$\ $$\ $$$$$$\$$$$\        $$ | $$$$$$\  $$$$$$$\ ")
    print("\$$$$$$\  $$ | $$  |$$ |$$  _$$  _$$\       $$ |$$  __$$\ $$  __$$\ ")
    print(" \____$$\ $$$$$$  / $$ |$$ / $$ / $$ |$$\   $$ |$$ /  $$ |$$ |  $$ | ")
    print("$$\   $$ |$$  _$$<  $$ |$$ | $$ | $$ |$$ |  $$ |$$ |  $$ |$$ |  $$ | ")
    print("\$$$$$$  |$$ | \$$\ $$ |$$ | $$ | $$ |\$$$$$$  |\$$$$$$  |$$$$$$$  | ")
    print(" \______/ \__|  \__|\__|\__| \__| \__| \______/  \______/ \_______/" + style.RESET)
    print()
    print()


# for color
class style():
    BLACK = '\033[30m'
    RED = '\033[31;1m'
    GREEN = '\033[32;1m'
    YELLOW = '\033[33m'
    BLUE = '\033[34;1m'
    MAGENTA = '\033[35;1m'
    CYAN = '\033[36;1m'
    WHITE = '\033[37m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

# checks for dependencies
def preflightCheck():
    print(style.MAGENTA + "=== Checking for dependencies ===" + style.RESET)

    # Checks that screen is available
    screen = which("screen")
    if (screen):
        print(style.GREEN + "[+]" + style.RESET + " screen command found")
    else:
        print(style.RED + "[-]" + style.RESET + " screen command not found")

    # Checks that proxmark3 is available
    proxmark3 = which("proxmark3")
    if (proxmark3):
        print(style.GREEN + "[+]" + style.RESET + " proxmark3 command found")
    else:
        print(style.RED + "[-] ERROR" + style.RESET + " proxmark3 command not found")
    print()

    # Removing old screen sessions for proxmark_capture
    print("[+] removing existing screen sessions for proxmark captures")
    os.system("screen -ls | grep 'proxmark_capture' | awk '{print $1}' | xargs -I % -t screen -X -S % quit > /dev/null 2>&1")

    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(7, GPIO.OUT)
    GPIO.setup(7,1)

    if not proxmark3 or not screen:
        exit(1)

# searches for the proxmark
def findProxmark():
    # instantiating dev
    dev = None

    # to find proxmark
    ports = serial.tools.list_ports.comports()
    for p in ports:
        if ("proxmark" in str(p) or "ttyACM0" in str(p)):
            dev = str(p).split(' ')[0]

    if dev is None:
        print(style.RED + "[-] ERROR:" + style.RESET + " Proxmox not found  :`(")
        exit()
    else:
        print(style.GREEN + "[+]" + style.RESET + " Proxmox found at " + dev)

        # validates access rights to use the proxmark
        access = os.popen("[ -r "+dev+" ] && [ -w "+dev+" ] && echo ok").readlines()
        if "ok" in str(access):
            print(style.GREEN + "[+]" + style.RESET + " Access rights validated to read proxmark")
        else:
            print(style.RED + "[-] ERROR:" + style.RESET + " You do not have the necessary rights to read the proxmark")
            print()
            print(style.RED + "Abort in progress..." + style.RESET)
            exit()
    return dev

# function to enable and disable GPIO pins to restart proxmark
def restartProxmark():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(7,GPIO.OUT)
    print(GPIO.input(7))
    #GPIO.output(7,0)
    #sleep(3)
    GPIO.output(7,1)

# begins the proxmark capture
def runProxmarkCapture(dev):
    # starting up screens
    print(style.GREEN + "[+]" + style.RESET + " Starting screen session proxmark_capture")
    os.system("screen -Ldm -S proxmark_capture")

    # executing proxmark in screen session
    print(style.GREEN + "[+]" + style.RESET + " Executing proxmark3 with " + dev)
    os.system("screen -R proxmark_capture -X exec proxmark3 "+ dev)
    sleep(6)

    print(style.GREEN + "[+]" + style.RESET + " Proxmox searching for hid card")
    os.system('screen -R proxmark_capture -X stuff "lf hid read' + os.linesep + '"')

# Follows proxmark3.log and looks for a capture
def checkForCaptures():
    print(style.GREEN + "[+]" + style.RESET + " Looking for victims...")
    status = False;

    while(status == False):
        with open('proxmark3.log') as f:
            if "#db# TAG ID:" in f.read():
                print(style.GREEN + "[+]" + style.RESET + " Capture found")
                saveCaptureLogs()
                status = True
                os.system("screen -ls | grep 'proxmark_capture' | awk '{print $1}' | xargs -I % -t screen -X -S % quit > /dev/null 2>&1")
        f.close()
    print("[+] Cutting power to proxmark")
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(7, GPIO.OUT)
    GPIO.setup(7,0)

# Saves capture to a timestamped file
def saveCaptureLogs():
    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("%Y-%b-%d_%H:%M:%S-proxmark_card.log")
    try:
        copyfile(os.getcwd()+'/proxmark3.log', os.getcwd()+'/'+timestampStr)
        print(style.GREEN + "[+]" + style.RESET + " Saved Capture to " + style.CYAN + timestampStr + style.RESET)
        os.remove("proxmark3.log")
    except:
        print(style.RED + "[-] ERROR:" + style.RESET + " Unable to save Capture log: " + style.CYAN + timestampStr + style.RESET)
        print()
        print(style.RED + "Abort in progress..." + style.RESET)
        exit()


def evasionMode():
    print()
    print(style.GREEN + "[+]" + style.RESET + style.RED + " RFID 0wnage" + style.RESET + " has completed.... will continue to run every " + style.BLUE + "10 minutes " + style.RESET + "to keep employees from becoming suspicious....")
    print()
    print("Enj0y")
    print()
    print("xbadbiddy")
    #sleep(600)
    sleep(120)
    print()
    print(style.GREEN + "[+]" + style.RESET + " Sleep time over restarting proxmark...")
    print()


# runs the things
def main():

    '''
    # argparse declaration
    parser = argparse.ArgumentParser(description='Automated card cloning.')
    parser.add_argument('-f', '--frequency', help='Output file name', default='stdout')
    parser.add_argument('-t', '--type', help='Output file name', default='stdout')
    parser.add_argument('-l', '--logfile', help='location of Proxmark3 logfile', default='./proxmark3.log')
    args = parser.parse_args()
    '''

    # checks for dependencies prior to running
    preflightCheck();

    while(True):
        # banner setup process beginning
        print(style.MAGENTA + "=== Setuping up Proxmark ===" + style.RESET)

        # Delay for usb devices to power on
        print(style.GREEN + "[+]" + style.RESET + " Waiting for " + style.BLUE + "USB devices" + style.RESET + " to power on...")
        sleep(7)

        # Determines if the proxmark is connected
        print(style.GREEN + "[+]" + style.RESET + " Searching for proxmark...")
        dev = findProxmark()
        print()

        # banner beginning scanning
        print(style.MAGENTA + "=== Starting the 0wnage ===" + style.RESET)

        # Starting up proxmox capture
        runProxmarkCapture(dev)

        # Saves logs after successful capture
        checkForCaptures()

        # Restarting proxmark
        evasionMode()
        restartProxmark()

if __name__ == "__main__":
    banner()
    main()

