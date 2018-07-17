import struct,serial,sys,glob,readline
from time import sleep

arduino=roomba=None
taken_ports=set()
def get_serial_connections(baudrate=115200):
	global taken_ports,arduino,roomba
	while True:
        #ports = set(glob.glob('/dev/tty[A-Za-z]*'))-taken_ports #RPi
		ports = list(set(glob.glob('/dev/tty.*'))-taken_ports) #macOS
		if arduino is None or roomba is None:
			if ports:
				print("Listing all ports below:")
				for i,port in enumerate(ports):
					print(str(i) + '\t' + port)
				port = ports[int(raw_input('Enter USB Port Index: '))]
				# try:
				print("Connection Established! (At "+port+")")
				taken_ports.add(port)
				test =  serial.Serial(port, baudrate=baudrate, timeout=1)
				test.readall()
				sleep(.2)
				if test.read(1) == "0":
					print('Arduino Detected!')
					arduino=test
					print('Arduino Connection Established!')
					while arduino.read()=='0':
						print('Beginning QTR Calibration')
						arduino.write(b'1234')#get the arduino to shut the f up (it doesn't matter what we send it)
						sleep(.2)
						arduino.readall()

					continue
				else:
					print("Roomba Detected!")
					roomba=test
					roomba.write(byte(128,131))#Enter Passive -> Safe Modes
					print('Roomba Connection Established!')
                    beep()
					continue
				# except:
					# print("Connection Failed! Please try again...")
					# continue
			else:
				print("No Ports Found! Please try again...")
				continue
		else:
			return

def to_bytes(n, length, big_endian=True):
	h = '%x' % n
	s = ('0'*(len(h) % 2) + h).zfill(length*2).decode('hex')
	return s if big_endian else s[::-1]

def twos_complement(val, nbits):
	"""Compute the 2's complement of int value val"""
	if val < 0:
		val += (1 << nbits)
	elif val & (1 << (nbits - 1)):# If sign bit is set.
		val -= (1 << nbits)#Compute negative value.
	return val

def byte(*n):
	#Combines an indefinite number of integer arguments into a bytestring
	#Example: byte(65,66,67)==bytes('ABC')  Note: ord('A')==65
	return bytes(''.join(chr(x)for x in n))

def to_signed_short(n,number_of_bytes=2):
	assert -32768<=n<=32767,'to_signed_short: error: '+str(n)+' is not a valid signed short'
	return to_bytes(twos_complement(n,8*number_of_bytes),number_of_bytes)

# getDecodedBytes returns a n-byte value decoded using a format string.
# Whether it blocks is based on how the connection was set up.
def getDecodedBytes(self, n, fmt):
    global roomba
    try:
        return struct.unpack(fmt, roomba.read(n))[0]
    except serial.SerialException:
        print ("Lost connection!")
        return None
    except struct.error:
        print ("Got unexpected data from serial port.")
        return None

# get8Unsigned returns an 8-bit unsigned value.
def get8Unsigned(self):
    return getDecodedBytes(1, "B")

# get8Signed returns an 8-bit signed value.
def get8Signed(self):
    return getDecodedBytes(1, "b")

# get16Unsigned returns a 16-bit unsigned value.
def get16Unsigned(self):
    return getDecodedBytes(2, ">H")

# get16Signed returns a 16-bit signed value.
def get16Signed(self):
    return getDecodedBytes(2, ">h")

def set_motors(left,right):
	roomba.write(byte(146)+to_signed_short(left)+to_signed_short(right))

def beep():
	roomba.write(byte(140,3,1,64,16,141,3))

def get_tilt():
	#If the robot is on the line, returns a value between -1 and 1.
	#If the robot is NOT on line, returns None.
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
		return (-1+2*float(w)/7)
	else:
		return None

# def move_forward():

def readEncoders():
    roomba.write(byte(149,43,44)) #Request Packet 42 & 43 (Left / Right Encoder Counts)
    leftEncoderCount = get16Unsigned()
    rightEncoderCount = get16Unsigned()
    encoderCounts = []
    encoderCounts.extend(leftEncoderCount,rightEncoderCount)
    return encoderCounts

get_serial_connections()

arduino.readall()
while True:
	try:
		exec(raw_input(">>> "))
	except Exception as e:
		print("Bad Input! Error: "+str(e))
	except KeyboardInterrupt:
		pass
