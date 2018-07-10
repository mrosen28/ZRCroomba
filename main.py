import struct,serial,sys,glob

def get_serial_connection(baudrate):
    ports = glob.glob('/dev/tty[A-Za-z]*')
    while True:
        if ports:
            print("Listing all ports below:")
            for i,port in enumerate(ports):
                print(str(i) + '    ' + port)
            port = ports[int(raw_input('Enter USB Port Index: '))]
            try:
                print("Connection Established! (At "+port+")")
                return serial.Serial(port, baudrate=baudrate, timeout=1)
            except:
                print("Connection Failed! Please try again...")
                continue
        else:
            print("No Ports Found! Please try again...")
            continue

def line_reader():
    s=get_serial_connection()
    def get():
        s.write(b' ')
        out=s.read()
        s.read_all()
        out=bin(ord(out))[2:]
        return list(map(bool,map(int,'0'*(8-len(out))+out)))
    def getTilt():
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
    return getTilt
front_tilt=line_reader(9600)
roomba=get_serial_connection(115200)

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

def
bytes(''.join(chr(int(x))for x in raw_input("Enter Command: ").split(' ')))

while True:
    try:
        b=bytes(''.join(chr(int(x))for x in raw_input("Enter Command: ").split(' ')))
        print("Sent: "+repr(b))
        connection.write(b)
    except Exception:
        print("Bad Input! Error: "+str(Exception))
