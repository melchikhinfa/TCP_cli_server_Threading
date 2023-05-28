import selectors
import socket
from inspect import isgenerator

# Loop

_ready = []
_current_gen = None
_selector = selectors.DefaultSelector()

def loop(main_gen):
    # global _ready, _selector
    assert isgenerator(main_gen)
    create_task(main_gen)
    while True:
        # Ready tasks
        while _ready:
            print(f"(Run task {_ready[0]}...)")
            _run(_ready.pop(0))

        # Ready IO
        print("Waiting for connections or data...")
        events = _selector.select()
        for key, mask in events:
            _selector.unregister(key.fileobj)
            gen = key.data
            _run(gen)

def create_task(gen):
    # global _ready
    assert isgenerator(gen)
    print(f"(Create task {gen}...)")
    _ready.append(gen)

def _run(gen):
    global _current_gen
    _current_gen = gen
    try:
        next(gen)
    except StopIteration:
        # Generator returns, not yields (on disconnect)
        pass

def wait_for(fileobj):
    # global _current_gen, _selector
    _selector.register(fileobj, selectors.EVENT_READ, _current_gen)

# Server

def main(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serv_sock:
        serv_sock.bind((host, port))
        serv_sock.listen(1)
        # serv_sock.setblocking(False)
        print("Server started")

        while True:
            wait_for(serv_sock)
            yield
            sock, addr = serv_sock.accept()  # Should be ready after wait_for()
            print("Connected by", addr)
            create_task(handle_connection(sock, addr))

def handle_connection(sock, addr):
    while True:
        # Receive
        try:
            yield wait_for(sock)
            data = sock.recv(1024)  # Should be ready after wait_for()
        except ConnectionError:
            print(f"Client suddenly closed while receiving")
            break
        print(f"Received {data} from: {addr}")
        if not data:
            break
        if data == b"close":
            break
        data = data.upper()
        print(f"Send: {data} to: {addr}")
        try:
            sock.send(data)  # Hope it won't block
        except ConnectionError:
            print(f"Client suddenly closed, cannot send")
            break
    sock.close()
    print("Disconnected by", addr)

HOST = ""  # Symbolic name meaning all available interfaces
PORT = 50007  # Arbitrary non-privileged port

if __name__ == "__main__":
    loop(main(HOST, PORT))