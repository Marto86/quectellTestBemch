import serial
import io
import time
from pylab import *
from rtlsdr import *
import os
from serial import Serial
import serial.tools.list_ports
import pyudev
 
import usb.core
import usb.util
 
curr_at_port = ''
at_cmd = 'AT'
at_rssi = 'AT+CSQ'
response_rssi = "+CSQ:"
sim_error = '+CME ERROR: 10'
sim_mounted = '+CPIN: READY'
at_enable_sim_status = 'AT+QSIMSTAT=1'
at_request_sim_status = 'AT+QSIMSTAT?'
quectel_available = False
com_port = '/dev/ttyUSB1'
at_port = 'Android - Mobile AT Interface'
 
qrf_band = 'GSM900'
qrf_test_mode_on = 'on'
qrf_test_mode_off = 'off'
qrf_chanell = 62
qrf_power = 200
 
 
 
qrf_test_on_command = 'AT+QRFTEST="{}",{},"{}",{}\r\n'.format(qrf_band,qrf_chanell,qrf_test_mode_on,qrf_power)
qrf_test_off_command = 'AT+QRFTEST="{}",{},"{}",{}'.format(qrf_band,qrf_chanell,qrf_test_mode_off,qrf_power)
 
context = pyudev.Context()
monitor = pyudev.Monitor.from_netlink(context)
monitor.filter_by(subsystem='usb')
 
for device in iter(monitor.poll, None):
    if device.action == 'add':
        print('{} connected'.format(device))
        dev = usb.core.find()
        print(dev)
        time.sleep(2)
        # quectel_available = True 
        curr_at_port = com_port
        # while quectel_available:
        print("4G Device detected at port",curr_at_port)
        ser = serial.Serial()
        ser.port = curr_at_port
        ser.baudrate = 115200
        ser.bytesize = serial.EIGHTBITS #number of bits per bytes
        ser.parity = serial.PARITY_NONE #set parity check: no parity
        ser.stopbits = serial.STOPBITS_ONE #number of stop bits
        ser.timeout = 1            #non-block read
        #ser.timeout = 2              #timeout block read
        ser.xonxoff = False     #disable software flow control
        ser.rtscts = False     #disable hardware (RTS/CTS) flow control
        ser.dsrdtr = False       #disable hardware (DSR/DTR) flow control
        ser.writeTimeout = 2       
 
        ser.open()
        time.sleep(2)
        ser.write("AT+CSQ\r\n".encode())
        time.sleep(1)
        csq_result = ser.read(ser.inWaiting()).decode()
        if response_rssi in csq_result:
          res = csq_result.split(" ")
          value = res[1].split(",")
          rssi_signal = int(value[0])
          if rssi_signal > 10 and rssi_signal < 35 :
               print("Rssi signal:",rssi_signal)
          time.sleep(0.5)
          ser.write("AT+CPIN?\r\n".encode())
          time.sleep(0.5)
          sim_result = ser.read(ser.inWaiting()).decode()
          ser.write("AT+GSN\r\n".encode())
          time.sleep(0.3)
          imei_number = ser.read(ser.inWaiting()).decode()

          if sim_error in sim_result:
             print("SIM CARD FAIL !!!! \nCheck SIM card please !")
          if sim_mounted in sim_result:
             print("SIM CARD PASS !!!!!!")     
             # configure device
             sdr = RtlSdr()
             sdr.sample_rate = 3.2e6
             sdr.center_freq = 902e6
             sdr.gain = 'auto' 
 
             ser.write("AT+QRFTESTMODE=0\r\n".encode())
             time.sleep(0.5)
             ser.write("AT+QRFTESTMODE=1\r\n".encode())
             time.sleep(2)
             ser.write(qrf_test_on_command.encode())
             time.sleep(3)
             samples = sdr.read_samples(128*1024)
             signal_value = (10*log10(var(samples)))
             if signal_value > -26.00 and signal_value < -13.00:
              print('Atena Signal: %0.2f dB !!!!!!!!' % signal_value)
              time.sleep(1)
              ser.write(qrf_test_off_command.encode())
              time.sleep(0.5)
              ser.write("AT+QRFTESTMODE=0\r\n".encode())
              sdr.close()
              input_variable = [imei_number,rssi_signal,signal_value]
              print(input_variable)
              time.sleep(2)
              ser.close()
 
              # do something very interesting here.
 
            #   if dev is None:
            #     raise ValueError('Device not found.')
 
            #   try:
            #        dev.detach_kernel_driver()
            #   except:
            #        print ("exception dev.detach_kernel_driver(0)")
            #        pass
 
            #   dev.set_configuration()
            #   print ("all done")
    if device.action == 'remove':
          print('Please Connect device')  
 
 