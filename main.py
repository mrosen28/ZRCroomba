from hwi import *
from pathfinder import *

q=quit
s=step_forward
while True:
	try:
		raw=raw_input(">>> ")
		if raw=='PASTE':
			import pyperclip
			raw=pyperclip.paste()
			print(">>>>>PASTED:")
			print(raw)
		exec(raw)
	except KeyboardInterrupt:
		print("\t\tROOMBA EMERGENCY HALT")
		halt_motors()#Halt the roomba
	except Exception as e:
		print("Bad Input! Error: "+str(e))
		traceback.print_exc()
