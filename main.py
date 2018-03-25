from threading import Thread

from ltm import app
from breakserver import BreakServer
from config import HOST, PORT

def main():
    try:
        server = BreakServer(HOST, PORT)
        break_server_thread = Thread(target=server.start)
        alexa_server_thread = Thread(target=app.run)

        break_server_thread.start()
        alexa_server_thread.start()

        break_server_thread.join()
        alexa_server_thread.join()

    except Exception:
        print("Unknown exception has occurred")
        raise
if __name__ == '__main__':
    main()
