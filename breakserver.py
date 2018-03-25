import json
import select
import socket
import SocketServer
import SimpleHTTPServer
from threading import Thread
from tinydb import Query
from DBHandler import DBHandler as TinyDB
from config import DB_PATH, UTF_FORMAT, LAST_TIME_MOVED, LTM_DATA_TABLE

CONNECTION_CLOSE_MESSAGE = "Connection is Closed"
BACKLOG = 5
MAX_MESSAGE_SIZE = 1024
CONNECTION_SOCKET_INDEX = 0
ADDRESS_INDEX = 1
SELECT_TIMEOUT = 5
Handler = SimpleHTTPServer.SimpleHTTPRequestHandler


#class MyTCPServer(SocketServer.TCPServer):
#    def server_bind(self):
#        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
#        self.socket.bind(self.server_address)
        
class BreakServer:
    def __init__(self,ip,port):
        
        try:
            self.server_address = ip, port
            self.socket_server = SocketServer.TCPServer(self.server_address, Handler)
        except SocketServer.socket.error as exc:
            if exc.args[0] != 48:
                raise
            print('Port', port, 'already in use')
            port += 1
        #self.server_socket = socket.socket()
        #self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        #self.server_socket.bind((ip, port))
        #self.server_socket.connect((ip, port))
        #self.server_socket = MyTCPServer(self.server_address, Handler)
        #self.server_socket = socket.socket()
        #self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        #self.socket.bind(self.server_address)
        #self.server_socket.listen(BACKLOG)
        self.ltm_db = TinyDB(DB_PATH,default_table=LTM_DATA_TABLE)
        self.break_ltm = Query()
        self.connections = []
    def start(self):
        print("Starting server, listening on address {0}".format(self.server_address))
        connections_thread = Thread(target=self.handle_clients)
        connections_thread.start()
        print("Starting to handle clients")
        handle_clients_thread=Thread(target=self.handle_clients)
        handle_clients_thread.start()

    def accept_connections(self):
        while True:
            print("Waiting for new connections")
            client_socket, address = self.server_socket.accept()
            print("Got connection from -> {0}".format(address))
            print("Putting connection in the shared queue")
            self.connections.append((client_socket,address))

    def handle_connection_close(self, client_connection, address):
        print("Connection has been closed by client {0}".format(address))
        client_connection.close()

        self.connections.remove((client_connection,address))
        print("Client {0} was removed from the connections list".format(address))

    def handle_client(self, client_connection, address):
        
        try:
            msg = client_connection.recv(MAX_MESSAGE_SIZE).decode(UTF_FORMAT)

            if msg == CONNECTION_CLOSE_MESSAGE:
                self.handle_connection_close(client_connection, address)
                print("Message received from Walabot.")

            else:
                data =json.loads(msg)
                print("Got {0} from client {1}".format(data,address))
                if not self.ltm_db.search(self.ltm_db.last_time_moved.exists()):
                    print("Inserting new row.")
                    self.ltm_db.insert(data)
                else:
                    print("Updating with new data, last time moved is: {0}".format(data[LAST_TIME_MOVED]))
                    self.ltm_db.update({LAST_TIME_MOVED: data[LAST_TIME_MOVED]})
                    print("Database updated successfully")
        except socket.error:
            self.handle_connection_close(client_connection, address)
        except:
            print("JSON Error")
    def handle_clients(self):
        while True:
            client_connections = [connection_tuple[CONNECTION_SOCKET_INDEX] for connection_tuple in self.connections]
            if client_connections:
                rlist, wlist, exlist = select.select(client_connections, [], [], SELECT_TIMEOUT)
                for connection in rlist:
                    address = [connection_tuple[ADDRESS_INDEX] for connection_tuple in self.connections
                               if connection_tuple[CONNECTION_SOCKET_INDEX] == connection]
                    self.handle_client(connection, address[0])
