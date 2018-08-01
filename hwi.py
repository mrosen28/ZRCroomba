import struct,serial,sys,glob,readline,struct,traceback,pyzbar
from time import sleep
from picamera.array import PiRGBArray
from picamera import PiCamera
from serial.tools import list_ports as lp

piCam=arduino=roomba=arm=None

def cameraInterface():
	global piCam
	piCam = PiCamera()
	time.sleep(0.1)
	if piCam not None:
		camera.resolution = (1280, 720)
		camera.framerate = 32
		print ("Camera Connected.")
	else:
		print("Error Connecting Camera!")

def takePicUntilBarcode:
	UPCs = []
	rawCapture = PiRGBArray(piCam, size=(1280, 720))
	for frame in piCam.capture_continuous(rawCapture, format="bgr", use_video_port=True):
		image = frame.array
		#Is there a Barcode Present?
		barcodes = decode(Image.open(image))
		if barcodes:
			return image
			# 	for barcode in barcodes:
			# 		barcodeData = barcode.data.decode("utf-8")[1:]
			# 		symbol = barcode.type
			# 		if symbol == 'QRCODE':
			# 			global tasks
			# 			print("Task List Found!")
			# 			tasks = parseTaskData(barcodeData)
			#
			# 		elif symbol == 'UPCA':
			# 			print("Item Barcode Found.")
			# 			UPCs.append(image)
			# 	#Only UPCs Detected
			# 	return UPCs

		else:
			continue

def get_serial_connections():
	global arduino,roomba,arm
	baudrate=115200
	armBaudRate = 9600
	arduinoVID = 6790
	roombaPID = 24597
	armPID = 24577
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
			arm.write('aa\r')
		if(device.vid == arduinoVID):
			print("Arduino Detected @ " + str(device.device) + " (Beginning QTR Calibration)")
			arduino = serial.Serial(device.device, baudrate=baudrate, timeout=1)
			arduino.write("0")# Begin QTR Calibration
	if (roomba == None or arduino == None or arm == None):
		print("We Forgot Someone...")
		#quit()
	else:
		#Clear Incoming Serial Buffers
		arduino.readall()
		roomba.readall()
		arm.readall()
		print("All Devices Successfully Connected!")

def sign(x):
	if x>0:return 1
	if x<0:return-1
	return 0

def byte(*n):
	#Combines an indefinite number of integer arguments into a bytestring
	#Example: byte(65,66,67)==bytes('ABC')  Note: ord('A')==65
	return bytes(''.join(chr(x)for x in n))

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

# def get_encoders():
# 	while True:
# 		try:
# 			global last_encoders
# 			#TODO: Keep track of when the encoder overflows/underflows; this is very important
# 			roomba.read_all()
# 			roomba.write(byte(142,2,43,44)) #Request Packet 42 & 43 (Left / Right Encoder Counts)
# 			return get8Unsigned(),get8Unsigned()#Left,Right
# 		except:
# 			continue
# def move_encoder_distance(left,right,speed=None):
# 	#left and right are encoder difference values
# 	original_left,original_right=get_encoders()
# 	while True:
# 		current_left,current_right=get_encoders()
# 		delta_left =current_left -original_left
# 		delta_right=current_right-original_right
# 		motor_right=0 if abs(delta_right)>abs(right) else sign(right)
# 		motor_left =0 if abs(delta_left )>abs(left ) else sign(left )
# 		if motor_left or motor_right:set_motors(motor_left,motor_right,speed)
# 		else:break
# 	halt_motors()

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

#basic setup
get_serial_connections()
cameraInterface()
