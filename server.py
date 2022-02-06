import socket
import pickle
import pyautogui as pt
from time import sleep
from message_process import *

s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((socket.gethostname(), 47))
print(socket.gethostname())
s.listen(5)
import sqlite3

while True:
    clt, addr = s.accept()
    print("Connection is established with", addr)

    try:
        # try connecting to database
        conn = sqlite3.connect('productivity.sqlite')
        conn.isolation_level = 'EXCLUSIVE'
        conn.execute('BEGIN EXCLUSIVE')
        cur = conn.cursor()
        tosend = 'proceed'
        clt.send(bytes(tosend,"utf-8"))
    except:
        tosend = 'busy'
        clt.send(bytes(tosend,"utf-8"))
        clt.close()
        # continue to listen for connections
        continue

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

    # by default it will be inside productivity manager group
    # locate smiley and click on typing bar
    position = pt.locateOnScreen("smiley_paperclip.png", confidence=.6)
    x = position[0]
    y = position[1]
    pt.moveTo(x+150, y+15, duration=.005)
    pt.click()

    msg = 'Someone is now using the desktop UI of productivity manager. '
    msg += 'Whatsapp service will resume shortly after that user quits.'
    # type msg and send
    pt.typewrite(msg,interval=0.001)
    pt.typewrite("\n",interval=0.001)

    user_using = 'unknown'

    while(True):
        encoded = clt.recv(1024)
        string_command = encoded.decode("utf-8")
        print('got')
        print(string_command)
        if(string_command == 'done'):
            print('closing connection with current client')
            break

        else:
            try:
                # code to identify user using server
                search_query = 'SELECT * FROM USER WHERE user_name ='
                if(string_command.startswith(search_query)):
                    user_using = string_command[len(search_query):]

                cur.execute(string_command)
                conn.commit()
                result = cur.fetchall()
                tosend = 'success'
                clt.send(bytes(tosend,"utf-8"))

            except:
                tosend = 'error'
                clt.send(bytes(tosend,"utf-8"))
                clt.close()
                exit()

            # receive ok response from client
            encoded = clt.recv(1024)

            data=pickle.dumps(result)
            print('data size:',len(data))

            data_size = str(len(data))
            clt.send(bytes(data_size,"utf-8"))

            # receive ok response from client
            encoded = clt.recv(1024)

            clt.send(data)

    clt.close()

    msg = 'The one who used the productivity manager desktop app is ' + user_using

    # type msg and send
    pt.typewrite(msg,interval=0.001)
    pt.typewrite("\n",interval=0.001)

    # minimize whatsapp as there are no new messages
    position = pt.locateOnScreen("wt_bar.png", confidence=.9)
    x = position[0]
    y = position[1]

    # move mouse pointer over minimize icon and click it
    pt.moveTo(x+917, y+17, duration=.05)
    pt.click()
    
    conn.close()
