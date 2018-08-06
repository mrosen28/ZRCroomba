import struct,serial,sys,glob,readline,struct,traceback,pyzbar
from time import sleep
from picamera.array import PiRGBArray
from picamera import PiCamera
from pyzbar.pyzbar import decode
from pyzbar.pyzbar import ZBarSymbol
from PIL import Image
from serial.tools import list_ports as lp
import time

piCam=arduino=roomba=arm=tasks=None
bins = [False for i in range(3)] #contains ID of item in Bin 0, 1, 2

try:piCam = PiCamera()
except Exception as E:print("Failed to initialize PiCamera: "+str(E))

def getConnected():
	global piCam,arduino,roomba,arm
	baudrate=115200
	armBaudRate = 9600
	arduinoVID = 6790
	roombaPID = 24597
	armPID = 24577

	time.sleep(0.1)
	if piCam is not None:
		cameraConnection = True
		print ("Camera Connected.")
		# piCam.resolution = (1280, 720)
		# piCam.framerate = 32
	else:
		cameraConnection = False
		print("Error Connecting Camera!")

	device_list = lp.comports()
	print("Getting Serial Connections...")
	for device in device_list:
		print(str(device.device) + " " + str(device.pid))
		if(device.pid == roombaPID):
			print("Roomba Detected @ " + str(device.device) + " (Entering Start/Full Mode)")
			roomba = serial.Serial(device.device,baudrate,timeout=1)
			roomba.write(byte(128,132))#Enter Start -> Full Mode.
			beep()
		if(device.pid == armPID):
			print("Found Arm!")
			arm = serial.Serial(device.device,armBaudRate,timeout=1)
			#Arm Command Format: '##\r'
			arm.write(b'aa\r')
		if(device.vid == arduinoVID):
			print("Arduino Detected @ " + str(device.device) + " (Beginning QTR Calibration)")
			arduino = serial.Serial(device.device, baudrate=baudrate, timeout=1)
			arduino.write(b"0")# Begin QTR Calibration
	if (roomba == None or arduino == None or arm == None or cameraConnection == False):
		print("We Forgot Someone...")
		#quit()
	else:
		#Clear Incoming Serial Buffers
		arduino.readall()
		roomba.readall()
		arm.readall()
		print("All Devices Successfully Connected!")
def takePic():
	rawCapture = PiRGBArray(piCam)
	piCam.capture(rawCapture,format='bgr')
	return rawCapture.array


def takePicUntilBarcode(timeout=10,show_image=False,):
	from time import time
	start=time()
	barcodes=[]
	while time()-start<timeout and all(x.type=='CODE39' for x in barcodes):
		#Is there a Barcode Present?
		barcode=decode(takePic())
		barcodes+=barcode
		print("Tadaa! Found: "+repr(barcode))
		try:
			beep()
			if show_image():
				cv2.imshow("Image", image)
				cv2.waitKey(10)
		except:pass
	box=location=None
	for x in barcodes:
		if x.type=='CODE39':
			location=x.data
		else:
			box=x.data
	return box,location

# Creates an array of the tasklist data out of the string read from the barcode
def parseTaskData(data):
	data = data.split('\n')
	taskList = []
	for row in data:
		row = row.split(',')
		taskList.append(row)
	#convert into a 3 by 3 matrix
	taskMatrix = [ [0, 0, 0] for i in range(3)]
	for task in taskList:
		shelfName = 0
		if task[0] == 'S1':
			shelfName = 0
		elif task[0] == 'A1':
			shelfName = 1
		else:
			shelfName = 2
		position = int(task[1]) - 1
		taskMatrix[shelfName][position] = task[2].strip()
		#print(int(task[1]))
	return taskMatrix

# See which of our bins has space to put stuff in
def findEmptyBin():
	global bins
	if bins[0] == False:
		return 0
	elif bins[1] == False:
		return 1
	elif bins[2] == False:
		return 2
	else: return -1

def allBinsEmpty(): return ((bins[0] == False) and (bins[1] == False) and (bins[2] == False))

# Check which bin is empty
# Update record keeping of bins
# Actually mechanically put item in bin
# remove item from shelf record keeping
def putInBin(barcodeData):
	global bins
	global itemPositions
	emptyBin = findEmptyBin()
	if emptyBin == 0:pass
		#PLACE IN BIN ONE
	elif emptyBin == 1:pass
		#PLACE IN BIN TWO
	elif emptyBin == 2:pass
		#PLACE IN BIN THREE
	else:
		#WERE OUT OF BINS?
		return -1
	bins[emptyBin] = barcodeData
	#itemPositions[getCurrShelf()][getCurrShelfPos()] = 0

def decipherBarcode(image): #, symbology):
	barcodes = decode(Image.open(image)) #, symbols=[ZBarSymbol.QRCODE]) #optional
	if barcodes:
		for barcode in barcodes:
			barcodeData = barcode.data.decode("utf-8")[1:] 		#returns the ID in this case, ID is a string
			symbol = barcode.type
			print("[INFO] Found {} barcode: {}".format(symbol, barcodeData))
		if symbology == 'QRCODE':
			global tasks
			tasks = parseTaskData(barcodeData)
			return 1
		else: #if symbology == UPCA: (we have an item)
			global itemPositions
			print("about to update itemPositions")
			itemPositions[getCurrShelf()][getCurrShelfPos()] = barcodeData
			if not inCorrectSpot():
				putInBin(barcodeData)
			putOnShelf() # check if we need to put something from our bins in the spot (either we took something off)

def sign(x):
	if x>0:return 1
	if x<0:return-1
	return 0

def byte(*n):
	#Combines an indefinite number of integer arguments into a bytestring
	#Example: byte(65,66,67)==bytes('ABC')  Note: ord('A')==65

	return bytes(bytes('').join(chr(x)for x in n))

def get_decoded_bytes(number_of_bytes,format):#n-byte value decoded using a format string. Whether it blocks ...
					 return struct.unpack(format,roomba.read(number_of_bytes))[0]# ... is based on how the connection was set up.
def get8Unsigned():  return get_decoded_bytes(1, "B")
def get8Signed():	 return get_decoded_bytes(1, "b")
def get16Unsigned(): return get_decoded_bytes(2,">H")
def get16Signed():   return get_decoded_bytes(2,">h")

def beep():
	roomba.write(byte(140,3,1,64,16,141,3))

def get_bumpers():
	#returns 0 if no bumpers
	roomba.read_all() #Clear Serial Buffer
	roomba.write(byte(142,7)) #Request Packet 45 (Bumper Sensor Values)
	return (get8Unsigned() & 0b000011) #Bitmask Bits 7 downto 2 because we only need 1 downto 0

def move_until_bumpers():
	set_motors(.5,.5)
	while not get_bumpers():pass
	halt_motors()

last_tilt=0#is remembered even when we're not on the line
def get_tilt():
	#If the robot is on the line, returns a float between -1 and 1.
	#If the robot is NOT on line, returns a boolean value: True if there's ANY
	#black on the sensor, and False if there isn't.
	s=arduino
	def get():
		s.write(b' ')
		out=s.read()
		s.read_all()
		out=bin(ord(out))[2:]
		return list(map(bool,map(int,'0'*(8-len(out))+out)))
	#print(' '.join(['X' if x else '-' for x in get()]))
	def on_the_line(l):
		l=''.join(map(str,map(int,l)))
		if not '1' in l:return False
	  #  print(l)
		for sub in '111 11 1'.split(' '):
			if sub in l:
				l=l.replace(sub,'',1)
				break
		return '1' not in l
	L=get()
	print (' '.join(['X' if x else '-' for x in L])), 'ON THE LINE' if on_the_line(L) else 'offline'
	if on_the_line(L):
		w=[]
		for i in range(8):
			if L[i]:w.append(i)
		w=sum(w)/float(len(w))
		global last_tilt
		last_tilt=-(-1+2*float(w)/7)
		return last_tilt
	else:
		return any(L)

default_speed=100
def set_motors(left,right,speed=None):
	roomba.write(byte(128,132))
	if speed is None:speed=default_speed
	#Left and right should conventionally be between -1 and 1
	assert -32768<=speed<=32767
	def to_bytes(n, length, big_endian=True):
		h = '%x' % n
		s = ('0'*(len(h) % 2) + h).zfill(length*2).decode('hex')
		return s if big_endian else s[::-1]
	def to_signed_short(n,number_of_bytes=2):
		assert -32768<=n<=32767,'to_signed_short: error: '+str(n)+' is not a valid signed short'
		return to_bytes(twos_complement(n,8*number_of_bytes),number_of_bytes)
	def twos_complement(val, nbits):
		"""Compute the 2's complement of int value val"""
		if   val < 0:				 val += (1 << nbits)
		elif val & (1 << (nbits - 1)):val -= (1 << nbits)#Compute negative value if sign bit is set.
		return val
	roomba.write(byte(146)+to_signed_short(int(left*speed))+to_signed_short(int(right*speed)))

def halt_motors(): set_motors(0,0)

def move_timed_distance(left,right,time=None,speed=None):
	if time is None:time=default_time
	set_motors(left, right,speed)
	sleep(time)
	halt_motors()

default_offset=50#TODO: Calibrate this!
default_time=.75
def step_forward(tiltyness=.8,offset=None,speed=None):
	#TODO: Implement offset
	while True:
		tilt=get_tilt()
		if tilt is True:break #Quick python tip: "1==True" is true, but "1 is True" is false. We're hopefully on an intersection
		if tilt is False:tilt=last_tilt #This happens if the robot's line following algorithm was too sloppy to follow the line perfectly,
									   #and the sensor is now on the white area. Remember what our tilt was before we left the line and use that...
		assert isinstance(tilt,float) #get_tilt only returns floats or booleans
		tilt*=abs(tilt)
		tilt*=tiltyness
		print("Stepping Forward...")
		set_motors(1+tilt,1-tilt,speed)
	move_timed_distance(left=1, right=1, time=None)

def approach(atWallOptions):
	while not get_bumpers():
		tilt=get_tilt()
		tilt*=abs(tilt)
		tilt*=tiltyness
		set_motors(1+tilt,1-tilt,speed)
	for x in atWallOptions:
		if x == "p": #Picture
			image = takePicUntilBarcode()
			return image
		elif x == "s":pass #Store on Shelf
			###arm.write("aa/r")#Grab Item Off Shelf
		elif x == "S":pass #Retrieve from Shelf
		elif x == "x":pass #Store in Bin One
		elif x == "X":pass #Retrieve from Bin One
		elif x == "y":pass #Store in Bin Two
		elif x == "Y":pass #Retrieve from Bin Three
		elif x == "z":pass #Store in Bin Three
		elif x == "Z":pass #Retrieve from Bin Three

def rotate(degrees,speed=None):
	#Unlike sine and cosine on the unit circle etc, degrees here increase clockwise. So, for example, 90 degrees is a right turn.
	def rot(direction,speed=None):
		#direction is normally -1 or 1
		set_motors(-direction,direction,speed)
		from time import sleep
		sleep(.25)
		while get_tilt() is not False:print("STEP 1")
		while get_tilt() is		False:print("STEP 2")
		halt_motors()
	degrees %= 360
	assert degrees in {0,90,180,270},str(degrees)+" is an unsupported angle; only multiples of 90 are supported"
	if	 degrees is	0:return
	elif   degrees is   90:rot( 1,speed)
	elif   degrees is  180:rot( 1,speed);rot(1,speed)
	elif   degrees is  270:rotate(90,-default_speed)
	tilt=get_tilt()
	while tilt not in (True,False):
		tilt=get_tilt()
		s=.5
		if tilt < 0:
			set_motors(-s,s,speed)
		elif tilt>0:
			set_motors(s,-s,speed)
		else:
			break
	halt_motors()

def arm_write(x):
	arm.write(bytes(x+'\r'))
def cup_up(i=0):
	arm_write('a'+chr(ord('b')+i))
def cup_down(i=0):
	arm_write('a'+chr(ord('f')+i))
def shelf_up():
	arm_write('ae')
def shelf_down():
	arm_write('ai')
def grip_close():
	arm_write('s5000\r')
def grip_open():
	arm_write('s5512\r')

#Ability for manual arm control:
#b is base
#l is lower arm
#u is upper arm
#w is wrist
#g is gripper
arm_pose={'b':.5,'l':-1,'u':1,'w':1,'g':1}
def pose(speed=.1,**joint_values):
	def set_joint(j,x):
		print("SetJoin",j,x)
		#j is joint number, x is value between 0 and 1
		if not 0<=x<=1:
			print("WARNING: Set joint problem: x not between 0 and 1: j="+str(j)+' and x='+str(x))
		x=str(max(0,min(int(x*1024),999)))
		msg='s'+str(j)+'0'*(3-len(x))+x
		assert len(msg)==5,'BAD custom arm code: '+msg 
		arm_write(msg)	
	for joint in joint_values:
		dict(g=lambda x:set_joint(1,x/2),
			 b=lambda x:set_joint(2,.5+.3*x),#clockwise from above: 1 is 90, -1 is -90
			 u=lambda x:set_joint(3,.5+.3*x),#Larger angles curl the arm into itself...
			 l=lambda x:set_joint(4,.5+.3*x),
			 w=lambda x:set_joint(5,.5-.3*x))[joint](joint_values[joint])
	print(kw)
	arm_pose.update(kw)
{'b':.5,'l':-1,'u':1,'w':1,'g':1}
set_pose()


# def sequencedMovement(sequence):
# 	for x in sequence:dict(
# 		r=lambda:rotate(-90),#Face Right
# 		l=lambda:rotate(90), #Face Left
# 		t=lambda:rotate(180),#Turn Around
# 		f=lambda:step_forward(),#Move Forward
# 		s=lambda:arm.write('aa\r'),#Store on Shelf
# 		x=lambda:arm.write('aa\r'),#Store in Bin One
# 		y=lambda:arm.write('aa\r'),#Store in Bin Two
# 		z=lambda:arm.write('aa\r'),#Store in Bin Three
# 		S=lambda:arm.write('aa\r'),#Retrieve from Shelf
# 		X=lambda:arm.write('aa\r'),#Retrieve from Bin One
# 		Y=lambda:arm.write('aa\r'),#Retrieve from Bin Two
# 		Z=lambda:arm.write('aa\r'),#Retrieve from Bin Three
# 		#picture?

#basic setup
getConnected()
pic=takePic
bar=takePicUntilBarcode
f=step_forward
r=lambda:rotate(90)
l=lambda:rotate(-90)

