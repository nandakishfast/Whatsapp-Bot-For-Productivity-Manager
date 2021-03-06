import pyautogui as pt
from time import sleep
import pyperclip
import os
import pathlib
import string
from plyer import notification
from message_process import *

# flag for sending automatic report to Users
today_date = date.today()
td = timedelta(5)
report_last_sent = today_date - td

# send a message stating that whatsapp server is up
# identify whatsapp icon, even if it has new msgs or not
position = pt.locateOnScreen("wt_new_msg.png", confidence=.9)
if(position == None):
    position = pt.locateOnScreen("wt_no_new_msg.png", confidence=.9)

# if unable to identify wt icon, stop program
if(position == None):
    print('Some trouble in finding wt icon, stoping server')
    exit()

# open whatsapp by clicking on whatsapp icon
x = position[0]
y = position[1]
pt.moveTo(x+17, y+17, duration=.05)
pt.click()

sleep(1)
# by default it will be inside productivity manager group
# locate smiley and click on typing bar
position = pt.locateOnScreen("smiley_paperclip.png", confidence=.6)
x = position[0]
y = position[1]
pt.moveTo(x+150, y+15, duration=.005)
pt.click()

msg = 'Whatsapp server is up and running. '

# type msg and send
pt.typewrite(msg,interval=0.001)
pt.typewrite("\n",interval=0.001)

# minimize whatsapp
position = pt.locateOnScreen("wt_bar.png", confidence=.9)
x = position[0]
y = position[1]

# move mouse pointer over minimize icon and click it
pt.moveTo(x+917, y+17, duration=.05)
pt.click()

sleep(2)

# get all the available sticker commands
path_sticker = str(pathlib.Path().resolve()) + "\\sticker_commands"
stickers_list = os.listdir(path_sticker)

while(True):

    # try to find stop_server image on screen
    position = pt.locateOnScreen("stop_server.png", confidence=.6)
    # if found stop the program
    if(position != None):
        print('Server Stopping')
        # send a message stating that whatsapp server is up
        # identify whatsapp icon, even if it has new msgs or not
        position = pt.locateOnScreen("wt_new_msg.png", confidence=.9)
        if(position == None):
            position = pt.locateOnScreen("wt_no_new_msg.png", confidence=.9)

        # if unable to identify wt icon, stop program
        if(position == None):
            print('Some trouble in finding wt icon, stoping server')
            exit()

        # open whatsapp by clicking on whatsapp icon
        x = position[0]
        y = position[1]
        pt.moveTo(x+17, y+17, duration=.05)
        pt.click()

        sleep(1)
        # by default it will be inside productivity manager group
        # locate smiley and click on typing bar
        position = pt.locateOnScreen("smiley_paperclip.png", confidence=.6)
        x = position[0]
        y = position[1]
        pt.moveTo(x+150, y+15, duration=.005)
        pt.click()

        msg = 'Whatsapp server is now stopping for maintenance. Will send an update when it is up.'

        # type msg and send
        pt.typewrite(msg,interval=0.001)
        pt.typewrite("\n",interval=0.001)

        # minimize whatsapp
        position = pt.locateOnScreen("wt_bar.png", confidence=.9)
        x = position[0]
        y = position[1]

        # move mouse pointer over minimize icon and click it
        pt.moveTo(x+917, y+17, duration=.05)
        pt.click()
        break

    # check for new whatsapp message from icon
    position = pt.locateOnScreen("wt_new_msg.png", confidence=.9)
    if(position == None):
        continue
    try:
        # try to connect to database with lock
        conn = sqlite3.connect('productivity.sqlite')
        conn.isolation_level = 'EXCLUSIVE'
        conn.execute('BEGIN EXCLUSIVE')
        cur = conn.cursor()
        print('got connection')
    except:
        # if server.py already has lock, then wait
        print('new msgs have come, tried getting db connection, but db locked.')
        sleep(3)
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

        # move to position where phone number is located and select it
        pyperclip.copy("")
        pt.moveRel(-263,253)
        pt.tripleClick()
        pt.keyDown('ctrl')
        pt.press('c')
        pt.keyUp('ctrl')

        # if it is a group, then there is no number
        if(pyperclip.paste()==''):
            ph_no = None
        # if it is a number, then cpy phone number for identification
        else:
            pt.moveRel(0,10)
            pt.tripleClick()
            # copy phone number to clipboard
            pt.keyDown('ctrl')
            pt.press('c')
            pt.keyUp('ctrl')

            # convert +91 99524 02150 to 9952402150
            # convert +91 6374 681 767 to 6374681767
            ph_no_with_space = pyperclip.paste()
            phn_num_sep = ph_no_with_space.split(' ')
            ph_no = ""
            for ph_ind in range(1,len(phn_num_sep)):
                ph_no += phn_num_sep[ph_ind]

        # close contact info
        pt.moveRel(-312, -298, duration=.05)
        pt.click()
        sleep(1.5)

        send_to = None # 0 - personal chat, 1 - group
        response_type = None # 0 - text, 1- image
        file_location = None # if reply is an image
        response_msg = None # if reply is a text
        wt_msg = None # msg if any sent from user_id

        result = []
        if(ph_no is not None):
            cur.execute('SELECT user_id,user_name FROM USER WHERE phone = ?', (ph_no,))
            result = cur.fetchall()
        if(ph_no is None or len(result)==0):
            # if unknown user, send the below text to them personally
            response_msg = 'hey this is a bot and you are not a registered user'
            send_to = 0
            response_type = 0

        else:
            user_id = result[0][0]
            user_name = result[0][1]
            #check if the user send a message
            # locate smiley
            position = pt.locateOnScreen("smiley_paperclip.png", confidence=.6)
            x = position[0]
            y = position[1]

            # move to the message
            pt.moveTo(x+50, y-35, duration=.005)
            # triple click on the message to select the entire message
            pt.tripleClick()
            # if it is an hyperlink, on triple clicking, it will prompt to open with browser
            # press esc to close that dialog box
            sleep(1.5)
            # copy the selected msg
            pt.press('esc')
            pt.keyDown('ctrl')
            pt.press('c')
            pt.keyUp('ctrl')

            wt_msg = pyperclip.paste()
            # check if the user send a command as a sticker only if no msg was sent
            command = None
            if(wt_msg==''):
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
                sleep(1)
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

        sleep(2)
        # locate group
        position = pt.locateOnScreen("group_icon.png", confidence=.8)
        x = position[0]
        y = position[1]
        # move to the group and click on it
        pt.moveTo(x+150, y+15, duration=.005)
        pt.click()
        sleep(2)
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
                sleep(1)
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

        # check if we need to send the automatic report
        today_date = date.today()
        td = timedelta(1)
        yesterday = today_date - td
        if(report_last_sent<yesterday):
            cur.execute('SELECT user_id, user_name FROM USER')
            users = cur.fetchall()

            # locate smiley
            position = pt.locateOnScreen("smiley_paperclip.png", confidence=.6)
            x = position[0]
            y = position[1]
            pt.moveTo(x+150, y+15, duration=.005)
            pt.click()

            msg = "Here is the yesterday's report"
            pt.typewrite(msg,interval=0.001)
            pt.typewrite("\n",interval=0.001)

            for us in range(len(users)):
                user_id = users[us][0]
                user_name = users[us][1]
                command = None
                wt_msg = 'hour '
                wt_msg += yesterday.strftime("%Y-%m-%d")
                returned = process_response(cur, conn, user_name, user_id, wt_msg, command)
                file_location = returned[2]

                # copy image to clipboard
                image = Image.open(file_location)
                send_to_clipboard(image)
                # paste image and send
                pt.keyDown('ctrl')
                pt.press('v')
                pt.keyUp('ctrl')
                sleep(3)
                pt.press('enter')

            report_last_sent=yesterday

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

    # close the db connection
    conn.commit()
    conn.close()
