import socket
import threading
import obd
import signal
import json

from typing import List, Sequence, IO

from .commands import commands as additional_commands

TCP_IP = '127.0.0.1'
TCP_PORT = 2948
BUFFER_SIZE = 1024
OBD_DEVICE = '/dev/rfcomm0'
OBD_CMD_MODES = [1, 2, 3]

connections: List[IO] = []

def handle_client(conn: socket.socket, addr):
    print(f'Handling {addr}')
    conn_io = conn.makefile('w')
    connections.append(conn_io)

def filter_obd_commands(commands: Sequence[obd.OBDCommand]):
    return [cmd for cmd in commands if cmd.mode in OBD_CMD_MODES] + additional_commands

def callback_obd_value(cmd):
    def callback(value):
        data = json.dumps({
                'cmd': cmd,
                'value': value
            })
        for c in connections:
            c.write(f'{data}\n')
    return callback

def run_obd_connection() -> obd.Async:
    conn = obd.Async(OBD_DEVICE)
    cmds = filter_obd_commands(conn.supported_commands)
    for cmd in cmds:
        conn.watch(cmd, callback=callback_obd_value(cmd))
    conn.start()
    return conn

def run_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((TCP_IP, TCP_PORT))
    s.listen(10)

    while True:
        conn, addr = s.accept()
        # threading.Thread(target=handle_client, args=(conn, addr)).run()
        handle_client(conn, addr)

def signal_handler(signal, frame):
    print(f'Signalled ({signal}, {frame})')

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)

    obd_conn = run_obd_connection()
    threading.Thread(target=run_server).run()

    signal.pause()
    obd_conn.close()
