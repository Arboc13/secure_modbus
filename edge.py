import hmac, hashlib
import struct
import time
import socket

key = b"secret-key"

def edge(tamper=False, expired=False):
    register_bytes = struct.pack(">6H", 2305, 2298, 2311, 5002, 450, 4)

    if expired:
        date_bytes = struct.pack(">I", int(time.time()-3600))
    else:
        date_bytes = struct.pack(">I", int(time.time()))
    payload = register_bytes + date_bytes
    message = payload + hmac.new(key, payload, hashlib.sha256).digest()

    if tamper:
        message = bytes([message[0] ^ 0x01]) + message[1:]

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(("127.0.0.1", 5001))
        s.sendall(message)

    s.sendall(message)
    print("Message sent.")



if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    edge(tamper=(mode == "tamper"), expired=(mode == "expired"))