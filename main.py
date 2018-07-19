import struct,serial,sys,glob,readline,struct,traceback
from time import sleep

arduino=roomba=None
taken_ports=set()
def get_serial_connections(baudrate=115200):
	global taken_ports,arduino,roomba
	while arduino is None or roomba is None:
		ports = list(x for x in (set(glob.glob('/dev/tty.*')+glob.glob('/dev/tty[A-Za-z]*'))-taken_ports) if ("USB" in x or "tty." in x and "Bluetooth" not in x)) #for both macOS AND raspi
		assert ports,'No ports detected!'
		print("Listing Remaining Ports:")
		for i,port in enumerate(ports):
			print(port)
		while True:
			try:port = ports[0];break
			except Exception as e:print("Bad input! Please try again. Error: "+str(e))
		print("Connection Available! (At "+port+")")
		taken_ports.add(port)
		test =  serial.Serial(port, baudrate=baudrate, timeout=1)
		test.readall()
		sleep(.2)
		if test.read(1) == "0":
			print('Arduino Detected!')
			arduino=test
			print('Connecting...')
			while arduino.read()=='0':
				arduino.write(b'15')#get the arduino to shut the f up (it doesn't matter what we send it)
				sleep(.2)
				arduino.readall()
				if arduino.read()=='0':
					print("Waiting for Calibration to Finish...")
			print('Arduino Connection Established!')
			continue
		else:
			print("Roomba Detected!")
			roomba=test
			print("Entering Passive/Safe Modes...")
			for i in range(10):#Gotta ake hecka-gosh-darn sure this actually works...
				roomba.write(byte(128,132))#Enter Start -> Full Mode.
				sleep(.1)
			print('Roomba Connection Established!')
			beep()
			continue
	#Clear Incoming Serial Buffers
	arduino.readall()
	roomba.readall()

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
def get8Signed():	return get_decoded_bytes(1, "b")
def get16Unsigned(): return get_decoded_bytes(2,">H")
def get16Signed():   return get_decoded_bytes(2,">h")

def beep():
	roomba.write(byte(140,3,1,64,16,141,3))

def get_bumper():
	roomba.read_all()
	roomba.write(byte(142,7)) #Request Packet 45 (Bumper Sensor Values)
	return (get8Unsigned() & 0b000011)

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
#
# def pester_the_roomba():
# 	roomba.write(byte(128,132))
#	beep()

def move_timed_distance(left,right,time=None,speed=None):
	if time is None:time=default_time
	set_motors(left, right,speed)
	sleep(time)
	halt_motors()

default_offset=50#TODO: Calibrate this!
default_time=.75
def step_forward(tiltyness=.8,offset=None,speed=None):
	#pester_the_roomba()
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
	# move_encoder_distance(offset,offset,speed)

	move_timed_distance(left=1, right=1, time=None)

def rotate(degrees,speed=None):
	#Unlike sine and cosine on the unit circle etc, degrees here increase clockwise. So, for example, 90 degrees is a right turn.
	def rot(direction,speed=None):
		#direction is normally -1 or 1
		set_motors(-direction,direction,speed)
		while get_tilt() is not False:print("STEP 1")
		while get_tilt() is	    False:print("STEP 2")
		halt_motors()
	degrees %= 360
	assert degrees in {0,90,180,270},str(degrees)+" is an unsupported angle; only multiples of 90 are supported"
	if     degrees is    0:return
	elif   degrees is   90:rot( 1,speed)
	elif   degrees is  180:rot( 1,speed);rot(1,speed)
	elif   degrees is  270:rot(-1,speed)

#basic setup
get_serial_connections()
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
		#pester_the_roomba()#Just in case it doesn't listen to the next command...
		halt_motors()#Halt the roomba
	except Exception as e:
		print("Bad Input! Error: "+str(e))
		traceback.print_exc()
