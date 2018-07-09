import struct,serial,sys,glob

def getConnected():
    ports = glob.glob('/dev/tty.*')
    if ports:
        print("Listing all ports below:")
        for i,port in enumerate(ports):
            print(str(i) + '    ' + port)
        port = ports[int(raw_input('Enter USB Port Index: '))]
        try:
            return serial.Serial(port, baudrate=115200, timeout=1)
            print("Connection Established!")
        except:
            print("Connection Failed! Exiting...")
            quit()
    else:
        print("No Ports Found! Exiting...")
        quit()

connection=getConnected()

while True:
    try:
        b=bytes(''.join(chr(int(x))for x in raw_input("Enter Command: ").split(' ')))
        print("Sent: "+repr(b))
        connection.write(b)
    except Exception:
        print("Bad Input! Error: "+str(Exception))
