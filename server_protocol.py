import socket
import select

STREAM_LENGTH = 1024

IP = "127.0.0.1"
PORT = 10023

# Handles message receiving
def receive_message(client_socket):

    try:

        # Receive our "header" containing message length, it's size is defined and constant
        message = client_socket.recv(STREAM_LENGTH)

        #print("message receive: " + message.decode('utf-8'))

        # If we received no data, client gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
        if not len(message):
            return False
        
        message = message.decode('utf-8')

        # Return an object of message header and message data
        return {'data': message.strip()}

    except:

        # If we are here, client closed connection violently, for example by pressing ctrl+c on his script
        # or just lost his connection
        # socket.close() also invokes socket.shutdown(socket.SHUT_RDWR) what sends information about closing the socket (shutdown read/write)
        # and that's also a cause when we receive an empty message
        return False

# Function that format list of active users (clients) for forwarding to the requested socket(user)
def get_users_list(clients):

    list_users = ""

    for _, client in clients.items():

        string = client['data'] + " "
        list_users += string
    
    return list_users.strip()

def remove_socket(sockets_list, socket, clients, clients_chat):
    
    user = clients[socket]
    print('Closed SERVER connection from: {}'.format(user['data']))

    # Remove from list for socket.socket()
    sockets_list.remove(socket)

    # Remove from our list of active users and active chat
    del clients_chat[user['data']]
    del clients[socket]

def main():
    # Create a socket
    # socket.AF_INET - address family, IPv4, some otehr possible are AF_INET6, AF_BLUETOOTH, AF_UNIX
    # socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams, socket.SOCK_RAW - raw IP packets
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # SO_ - socket option
    # SOL_ - socket option level
    # Sets REUSEADDR (as a socket option) to 1 on socket
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind, so server informs operating system that it's going to use given IP and port
    # For a server using 0.0.0.0 means to listen on all available interfaces, useful to connect locally to 127.0.0.1 and remotely to LAN interface IP
    server_socket.bind((IP, PORT))
    
    # This makes server listen to new connections
    server_socket.listen()
    
    # List of sockets for select.select()
    sockets_list = [server_socket]
    
    # List of connected clients - socket as a key, user header and name as data
    clients = {}
    clients_chat = {}
    
    print(f'Listening for INCOMING connections on {IP}:{PORT}...\n')
    
    while True:
    
        # Calls Unix select() system call or Windows select() WinSock call with three parameters:
        #   - rlist - sockets to be monitored for incoming data
        #   - wlist - sockets for data to be send to (checks if for example buffers are not full and socket is ready to send some data)
        #   - xlist - sockets to be monitored for exceptions (we want to monitor all sockets for errors, so we can use rlist)
        # Returns lists:
        #   - reading - sockets we received some data on (that way we don't have to check sockets manually)
        #   - writing - sockets ready for data to be send thru them
        #   - errors  - sockets with some exceptions
        # This is a blocking call, code execution will "wait" here and "get" notified in case any action should be taken
        read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)
    
    
        # Iterate over notified sockets
        for notified_socket in read_sockets:
    
            # If notified socket is a server socket - new connection, accept it
            if notified_socket == server_socket:
                
                #print("init conection server function")
                # Accept new connection
                # That gives us new socket - client socket, connected to this given client only, it's unique for that client
                # The other returned object is ip/port set
                client_socket, client_address = server_socket.accept()
    
                # Client should send his name right away, receive it
                connect = receive_message(client_socket)
    
                # If False - client disconnected before he sent his name
                if connect is False:
                    continue
                
                if connect['data'] == "connect":
                    print("New connection request...")
                    res = "accept".encode('utf-8')
                    client_socket.send(res)

                else:
                    continue

                user = receive_message(client_socket)

                if user is False:
                    continue
                
                print("Got username for new connection")
                clients[client_socket] = user
                clients_chat[user['data']] = None

                list_users = get_users_list(clients)
                client_socket.send(list_users.encode('utf-8'))

                print("Sent list of active users.")

                # Add accepted socket to select.select() list
                sockets_list.append(client_socket)
    
                # Also save username data
                print('Accepted new connection from {}:{}, username: {}\n'.format(*client_address, user['data']))
    
            # Else existing socket is sending a message
            else:

                message = receive_message(notified_socket)

                user = clients[notified_socket]

                if message is False:
                    remove_socket(sockets_list, notified_socket, clients, clients_chat)
                    continue
                
                message_words = message['data'].split(' ')
                
                if clients_chat[user['data']] != None and clients_chat[user['data']][1] == 1 and clients_chat[user['data']][1] == 1 and message['data'] != "disconnect":
                    
                    for key_socket, client_socket in clients.items():
                        if clients_chat[user['data']][0] == client_socket['data']:
                            key_socket.send(message['data'].encode('utf-8'))

                elif message['data'] == "list" and clients_chat[user['data']] is None:

                    list_users = get_users_list(clients)
                    notified_socket.send(list_users.encode('utf-8'))
                
                elif message['data'] == "list" and clients_chat[user['data']] is not None:
                    res = "connect {}".format(clients_chat[user['data']][0])
                    clients_chat[user['data']][1] = 1
                    notified_socket.send(res.encode('utf-8'))

                elif message_words[0] == "connect" and len(message_words) == 2 and clients_chat[user['data']] is None:
                    clients_chat[user['data']] = [message_words[1], 1]
                    clients_chat[message_words[1]] = [user['data'], 0]

                elif message['data'] == "disconnect" and clients_chat[user['data']] is None:
                    remove_socket(sockets_list, notified_socket, clients, clients_chat)

                elif message['data'] == "disconnect" and clients_chat[user['data']] is not None:
                    print("Disconnect CHAT from: {} to {}".format(user['data'], clients_chat[user['data']][0]))
                    connected_to = clients_chat[user['data']][0]

                    for key_socket, client_socket in clients.items():
                        if connected_to == client_socket['data']:
                            key_socket.send("disconnect".encode('utf-8'))

                    clients_chat[connected_to] = None
                    clients_chat[user['data']] = None

                    notified_socket.send(get_users_list(clients).encode('utf-8'))

                                
    
        # It's not really necessary to have this, but will handle some socket exceptions just in case
        for notified_socket in exception_sockets:

            remove_socket(sockets_list,notified_socket,clients, clients_chat)

    
if __name__ == "__main__":
    main()
