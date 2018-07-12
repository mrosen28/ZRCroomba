import struct,serial,sys,glob
from time import sleep

roomba = None
arduino = None
taken_ports=set()

def get_serial_connections(baudrate=115200):
    global taken_ports
    global arduino
    global roomba
    #ports = set(glob.glob('/dev/tty[A-Za-z]*'))-taken_ports #RPi
    while True:
        ports = list(set(glob.glob('/dev/tty.*'))-taken_ports) #macOS
        if (arduino == None or roomba == None):
            if ports:
                print("Listing all ports below:")
                for i,port in enumerate(ports):
                    print(str(i) + '    ' + port)
                port = ports[int(raw_input('Enter USB Port Index: '))]
                # try:
                print("Connection Established! (At "+port+")")
                taken_ports.add(port)
                test =  serial.Serial(port, baudrate=baudrate, timeout=1)
                test.readall()
                sleep(.1)
                if(test.read() == "0"):
                    print('Arduino Detected!')
                    arduino=test
                    print('Arduino Connection Established!')
                    continue
                else:
                    print("Roomba Detected!")
                    roomba = test
                    print('Roomba Connection Established!')
                    continue

                # except:
                    # print("Connection Failed! Please try again...")
                    # continue
            else:
                print("No Ports Found! Please try again...")
                continue
        else:
            return

get_serial_connections()
#while True:print(test)


def to_bytes(n, length, endianess='big'):
    h = '%x' % n
    s = ('0'*(len(h) % 2) + h).zfill(length*2).decode('hex')
    return s if endianess == 'big' else s[::-1]
def twos_complement(val, nbits):
    """Compute the 2's complement of int value val"""
    if val < 0:
        val = (1 << nbits) + val
    else:
        if (val & (1 << (nbits - 1))) != 0:
            # If sign bit is set.
            # compute negative value.
            val = val - (1 << nbits)
    return val

def to_signed_short(n,number_of_bytes=2):
    assert -32768<=n<=32767,'to_signed_short: error: '+str(n)+' is not a valid signed short'
    return to_bytes(twos_complement(n,8*number_of_bytes),number_of_bytes)

def set_motors(left,right):
    roomba.write(bytes(chr(146))+to_signed_short(left)+to_signed_short(right))

while True:
    try:
        exec(raw_input(">>> "))
        connection.write(b)
    except Exception:
        print("Bad Input! Error: "+str(Exception))
