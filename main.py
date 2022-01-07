import pyautogui as pt
from time import sleep
import pyperclip
from plyer import notification

sleep(3)

position = pt.locateOnScreen("smiley_paperclip.png", confidence=.6)
x = position[0]
y = position[1]

pt.moveTo(x+50, y-35, duration=.05)
pt.tripleClick()
pt.rightClick()
pt.moveRel(12,15)
pt.click()
pt.moveRel(-12,-15)
pt.click()
whatsapp_msg = pyperclip.paste()
print("Message received:" + whatsapp_msg)
notification.notify(
    title = 'Message',
    message = whatsapp_msg,
    app_name = 'whatsapp_bot',
    ticker = '_',
    app_icon = None,
    timeout = 5,
    toast = True,
)
