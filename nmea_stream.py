from serial import Serial
from pynmeagps import NMEAReader
stream = Serial('/dev/ttyAMA0', 9600, timeout=3)
with stream:
    while(True):
        nmr = NMEAReader(stream)
        (raw_data, parsed_data) = nmr.read()
        print(parsed_data)