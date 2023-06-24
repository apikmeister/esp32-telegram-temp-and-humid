
# This file is executed on every boot (including wake-boot from deepsleep)

#import esp

#esp.osdebug(None)

#import webrepl

#webrepl.start()

import config.py
import utelegram.py
import main.py

exec(open('main.py').read(),globals())
