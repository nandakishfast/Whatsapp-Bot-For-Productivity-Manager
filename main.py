import pyautogui as pt
from time import sleep
import pyperclip
from plyer import notification

sleep(2)

while(True):

    # try to find stop_server image on screen
    position = pt.locateOnScreen("stop_server.png", confidence=.6)
    # if found stop the program
    if(position != None):
        print('Server Stopping')
        break

    # if stop server not found, continue to look for new messages
    try:
        # look for green dot which occurs when a new message is received
        position = pt.locateOnScreen("green_circle.png", confidence=.9)
        x = position[0]
        y = position[1]
        # if we found a green dot, then click on that chat to read the message
        pt.moveTo(x-50, y, duration=.005)
        pt.click()

        # locate smiley
        position = pt.locateOnScreen("smiley_paperclip.png", confidence=.6)
        x = position[0]
        y = position[1]

        # move to the message
        pt.moveTo(x+50, y-35, duration=.005)
        # triple click on the message to select the entire message
        pt.tripleClick()
        # right click to get the Copy dialog, navigate and click on it
        pt.rightClick()
        pt.moveRel(12,15)
        pt.click()
        # move back to message and click again to unselect it
        pt.moveRel(-12,-15)
        pt.click()

        whatsapp_msg = pyperclip.paste()
        print("Message received:" + whatsapp_msg)
        pt.moveTo(x+150, y+15, duration=.005)
        pt.click()
        pt.typewrite(whatsapp_msg,interval=0.001)
        pt.typewrite("\n",interval=0.001)

        # locate group
        position = pt.locateOnScreen("group_icon.png", confidence=.8)
        x = position[0]
        y = position[1]
        # move to the group and click on it
        pt.moveTo(x+150, y+15, duration=.005)
        pt.click()

    except:
        # wait to receive new message
        sleep(0.005)
