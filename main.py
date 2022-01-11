import pyautogui as pt
from time import sleep
import pyperclip
import os
import pathlib
import string
from plyer import notification

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
    sleep(0.5)

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

        # user identification
        user_name = None
        user_id = None

        # open contact info
        position = pt.locateOnScreen("options_contact.png", confidence=.99)
        x = position[0]
        y = position[1]
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

        print(user_name)
        if(user_name is None):
            response_msg = 'hey this is a bot and you are not a registered user'

        else:
            # check if the user send a command as a sticker
            command = None
            for sticker in stickers_list:
                sticker_location = "sticker_commands\\"+sticker
                position_sticker = pt.locateOnScreen(sticker_location, confidence=.8)

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

                whatsapp_msg = pyperclip.paste()
                print("Message received:" + whatsapp_msg)
                response_msg = 'hi '+ user_name + '\n you typed' + whatsapp_msg

            else:
                response_msg = 'hi '+ user_name + '\n you asked for ' + command

        # locate smiley
        position = pt.locateOnScreen("smiley_paperclip.png", confidence=.6)
        x = position[0]
        y = position[1]
        pt.moveTo(x+150, y+15, duration=.005)
        pt.click()
        pt.typewrite(response_msg,interval=0.001)
        pt.typewrite("\n",interval=0.001)

        # locate group
        position = pt.locateOnScreen("group_icon.png", confidence=.8)
        x = position[0]
        y = position[1]
        # move to the group and click on it
        pt.moveTo(x+150, y+15, duration=.005)
        pt.click()

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
