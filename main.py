import RPi.GPIO as GPIO
import time
import constants as ct
import socket

usleep = lambda x: time.sleep(x/1000000.0)

def initAll(bl):
    pinInit()
    turnOn(bl)
    clearAll()    

def pinInit():
    #Initialize GPIO pins 7, 8 and 10 as out
    #DIO
    GPIO.setup(ct.DIO, GPIO.OUT, initial=GPIO.HIGH)
    #STB
    GPIO.setup(ct.STB, GPIO.OUT, initial=GPIO.HIGH)
    #CLK
    GPIO.setup(ct.CLK, GPIO.OUT, initial=GPIO.HIGH)

def sendByte(data):
    #We assume STB is already LOW
    for i in range(8):
        GPIO.output(ct.CLK, GPIO.LOW)
        GPIO.output(ct.DIO, (data & 1) == 1)
        data >>= 1
        GPIO.output(ct.CLK, GPIO.HIGH)

def setMode(wr_mode, addr_mode):
    sendByte(0x40 | wr_mode | addr_mode)

def sendCmd(cmd):
    GPIO.output(ct.STB, GPIO.LOW)
    sendByte(cmd)
    GPIO.output(ct.STB, GPIO.HIGH)

def sendData(addr, data):
    GPIO.output(ct.STB, GPIO.LOW)
    setMode(ct.WRITE_MODE, ct.FIXED_ADDR)
    GPIO.output(ct.STB, GPIO.HIGH)
    GPIO.output(ct.STB, GPIO.LOW)
    sendByte(0xC0 | addr)
    sendByte(data)
    GPIO.output(ct.STB, GPIO.HIGH)

def turnOn(brightness):
    sendCmd(0x88 | brightness & 7)

def setLED(index, value):
    sendData((index % 8) * 2 + 1, 1 if value else 0)

def clearLEDs():
    for i in range(8):
        TM.leds[i] = False

def setLEDs(num):
    clearLEDs()
    for i in range(num):
        TM.leds[i] = True

def clearDisplay():
    GPIO.output(ct.STB, GPIO.LOW)
    setMode(ct.WRITE_MODE, ct.INCR_ADDR)
    sendByte(0xC0)
    for i in range(16):
        sendByte(0x00)
    GPIO.output(ct.STB, GPIO.HIGH)

def clearAll():
    clearDisplay()
    clearLEDs()

def writeChar(index, val):
    sendData((index % 8) * 2, val)

def writeStr(index, str):
    trans_str = []
    for char in str:
        if char == ".":
            trans_str.append(trans_str.pop() | 128)
        elif char in ct.FONT_DICT:
            BCD = ct.FONT_DICT[char]
            trans_str.append(BCD)
    for char in trans_str:
        writeChar(index, char)
        index += 1

def clearLEDs():
    for i in range(8):
        setLED(i, False)

def setLEDs(num):
    for i in range(num):
        setLED(i, True)
    for i in range(num, 8):
        setLED(i, False)

#Set pin numbering as BCM
GPIO.setmode(GPIO.BCM)

initAll(3)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host = "192.168.1.56"
port = 8086

s.connect((host, port))

while True:
    data = s.recv(13).decode()
    if data != "":
        items = data.split()
        led = int(items[0])
        speed = items[1]
        rpm = items[2]
        rpm = "{:02d}".format(int(int(rpm)/100))
        rpm = rpm[0] + "." + rpm[1]
        gear = int(items[3])-1
        if gear == -1:
            gear = '-'
        else:
            gear = str(gear)
        setLEDs(int(led))
        writeStr(0, speed + " " + gear + " " + rpm)
s.close()

GPIO.cleanup()
