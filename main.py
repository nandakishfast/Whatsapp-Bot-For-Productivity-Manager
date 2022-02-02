import pyautogui as pt
from time import sleep
import pyperclip
import os
import pathlib
import string
from plyer import notification
from message_process import *

conn = sqlite3.connect('productivity.sqlite')
cur = conn.cursor()

sleep(2)

# get all the available user dps for identification
path_user_dps = str(pathlib.Path().resolve()) + "\\user_dps_for_identification"
user_dp_list = os.listdir(path_user_dps)

# get all the available sticker commands
path_sticker = str(pathlib.Path().resolve()) + "\\sticker_commands"
stickers_list = os.listdir(path_sticker)

while(True):

    # try to find stop_server image on screen
    position = pt.locateOnScreen("stop_server.png", confidence=.6)
    # if found stop the program
    if(position != None):
        print('Server Stopping')
        break

    # check for new whatsapp message from icon
    position = pt.locateOnScreen("wt_new_msg.png", confidence=.9)
    if(position == None):
        continue

    # if new messages have come, click whatsapp icon and enter wt app
    x = position[0]
    y = position[1]
    pt.moveTo(x+17, y+17, duration=.05)
    pt.click()

    # wait while whatsapp opens
    sleep(1.5)

    # look for green dot which occurs when a new message is received
    position = pt.locateOnScreen("green_circle.png", confidence=.9)

    new_msgs_there = (position != None)

    # loop to continue looking for new messages
    while(new_msgs_there):

        position = pt.locateOnScreen("green_circle.png", confidence=.9)
        x = position[0]
        y = position[1]
        # if we found a green dot, then click on that chat to read the message
        pt.moveTo(x-50, y, duration=.005)
        pt.click()

        sleep(1.5)
        # user identification
        user_name = None
        # open contact info
        position = pt.locateOnScreen("options_contact.png", confidence=.99)
        print('options_contact :',position)
        if(position!=None):
            x = position[0]
            y = position[1]
        else:
            # provided values specific to my pc, just in case it is not able to find coordinates
            x = 1004
            y = 55
        pt.moveTo(x+120, y+60, duration=.05)
        pt.click()
        pt.moveRel(-20, 45, duration=.05)
        pt.click()
        sleep(1)

        # check for matching user
        for user in user_dp_list:
            dp_location = "user_dps_for_identification\\"+user
            position_contact = pt.locateOnScreen(dp_location, confidence=.9)
            if(position_contact!=None):
                # remove .png part and numbers at end
                # one user can have multiple dp's for identification
                user_name = user[:-4].rstrip(string.digits)

        # close contact info
        pt.moveRel(-575, -45, duration=.05)
        pt.click()

        send_to = None # 0 - personal chat, 1 - group
        response_type = None # 0 - text, 1- image
        file_location = None # if reply is an image
        response_msg = None # if reply is a text
        wt_msg = None # msg if any sent from user_id

        result = []
        if(user_name is not None):
            cur.execute('SELECT user_id FROM USER WHERE user_name = ?', (user_name,))
            result = cur.fetchall()
        if(user_name is None or len(result)==0):
            # if unknown user, send the below text to them personally
            response_msg = 'hey this is a bot and you are not a registered user'
            send_to = 0
            response_type = 0

        else:
            user_id = result[0][0]
            # check if the user send a command as a sticker
            command = None
            for sticker in stickers_list:
                sticker_location = "sticker_commands\\"+sticker
                position_sticker = pt.locateOnScreen(sticker_location, confidence=.7)

                if(position_sticker!=None):
                    x_sticker = position_sticker[0]
                    y_sticker = position_sticker[1]

                    # (x,y)>(540,400) to ensure not to read previously sent sticker
                    if(x_sticker>540 and y_sticker>400):
                        # remove .png part at end
                        command = sticker[:-4]

            # check for text msg only if no stickers were sent
            if(command==None):
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

                wt_msg = pyperclip.paste()

            returned = process_response(cur, conn, user_name, user_id, wt_msg, command)
            print('Received ', returned)
            send_to = returned[0]
            response_type = returned[1]
            file_location = returned[2]
            response_msg = returned[3]

        # if we want to send personal msg
        if(send_to==0):
            # locate smiley
            position = pt.locateOnScreen("smiley_paperclip.png", confidence=.6)
            x = position[0]
            y = position[1]
            pt.moveTo(x+150, y+15, duration=.005)
            pt.click()
            if(response_type==0):
                # type msg and send
                pt.typewrite(response_msg,interval=0.001)
                pt.typewrite("\n",interval=0.001)
            elif(response_type==1):
                # copy image to clipboard
                image = Image.open(file_location)
                send_to_clipboard(image)
                # paste image and send
                pt.keyDown('ctrl')
                pt.press('v')
                pt.keyUp('ctrl')
                sleep(1)
                pt.press('enter')

        # locate group
        position = pt.locateOnScreen("group_icon.png", confidence=.8)
        x = position[0]
        y = position[1]
        # move to the group and click on it
        pt.moveTo(x+150, y+15, duration=.005)
        pt.click()

        # if we want to send grp msg
        if(send_to==1):
            # locate smiley
            position = pt.locateOnScreen("smiley_paperclip.png", confidence=.6)
            x = position[0]
            y = position[1]
            pt.moveTo(x+150, y+15, duration=.005)
            pt.click()
            if(response_type==0):
                # type msg and send
                pt.typewrite(response_msg,interval=0.001)
                pt.typewrite("\n",interval=0.001)
            elif(response_type==1):
                # copy image to clipboard
                image = Image.open(file_location)
                send_to_clipboard(image)
                # paste image and send
                pt.keyDown('ctrl')
                pt.press('v')
                pt.keyUp('ctrl')
                sleep(3)
                pt.press('enter')

        # update new_msgs_there flag
        position = pt.locateOnScreen("green_circle.png", confidence=.9)
        new_msgs_there = (position != None)


    # minimize whatsapp as there are no new messages
    position = pt.locateOnScreen("wt_bar.png", confidence=.9)
    x = position[0]
    y = position[1]

    # move mouse pointer over minimize icon and click it
    pt.moveTo(x+917, y+17, duration=.05)
    pt.click()
