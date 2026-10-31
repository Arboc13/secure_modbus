import socket
import struct
import threading
import time, hmac, hashlib
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.server import StartTcpServer

store = ModbusSlaveContext(hr=ModbusSequentialDataBlock(0, [0]*100))
context = ModbusServerContext(slaves=store, single=True)

key = b"secret-key"
TIME_WINDOW = 30

def aggregator( ):

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', 5001))
        s.listen(5)
        print("Server started and listening.")
        while True:
            conn, _ = s.accept()
            with conn:
                rcv = conn.recv(48)
            payload, tag = rcv[:16], rcv[16:]
            expected = hmac.new(key, payload, hashlib.sha256).digest()
            if not hmac.compare_digest(tag, expected):
                print("Wrong HMAC key")
                continue

            registers = struct.unpack(">6H", payload[:12])
            t = struct.unpack(">I", payload[12:])[0]

            if abs(t - time.time()) > TIME_WINDOW:
                print("Expired data.")
                continue

            context[0].setValues(3, 0, list(registers))
            print("OK:", registers)


if __name__ == "__main__":
    t = threading.Thread(target=aggregator, daemon=True).start()
    StartTcpServer(context, address=("127.0.0.1", 5020))