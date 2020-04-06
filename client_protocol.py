import socket
import sys
import errno

STREAM_LENGTH = 1024

IP = "127.0.0.1"
PORT = 10023

# Function that receive list message as STRING UTF-8 and format to output
def print_list(message, sep):

    list_users = message.split(sep)

    to_return = "List of active users:"

    for user in list_users:
        to_return += f'\n\t*{user}'

    return to_return

# Handles message receivings
def receive_message(client_socket):

    try:

        # Receive our "header" containing message length, it's size is defined and constant
        message = client_socket.recv(STREAM_LENGTH)

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

# Function that creates the connection to the socket server, three initial phases: connect (receive accept)
# send identidad (Receive list of active users), end
def create_connection(client_socket):

    try: 

        while True:

            command = input("Insert command (connect [IP]): ")

            if command != "":

                words = command.split(' ')

                if words[0] == "connect":
                    
                    if len(words) == 2:
                        client_socket.connect((words[1],PORT))
                        
                    elif len(words) == 1:
                        client_socket.connect((IP, PORT))

                    else:
                        continue

                    client_socket.setblocking(True)
                    client_socket.send(words[0].encode('utf-8'))
                    res = receive_message(client_socket)

                    if res is False:
                        continue
                    
                    if res['data'] == "accept":

                        print("Message receive: {}".format(res['data']))

                        username = input("Insert your username: ")
                        client_socket.send(username.encode('utf-8'))

                        list_users = receive_message(client_socket)

                        if list_users is False:
                            continue

                        # Format list for stdout, with separator
                        print(print_list(list_users['data'], ' '))

                        return username

                    else:
                        print("Error initial connect to server")
                        sys.exit(1)

    except IOError as e:

        # Input exception when reading from the socket
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('Reading error: {}'.format(str(e)))
            sys.exit(1)
    
    except Exception as e:

        # Any other exception - something happened, exit
        print('Reading any error: '.format(str(e)))
        sys.exit(1)


def main():
    
    # Create a socket
    # socket.AF_INET - address family, IPv4, some otehr possible are AF_INET6, AF_BLUETOOTH, AF_UNIX
    # socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams, socket.SOCK_RAW - raw IP packets
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    USERNAME = create_connection(client_socket)

    chat_connection = False
    chat_friend = ""
    
    while True:

        message = input(f'{USERNAME} > ')
        message = message.strip()
        message_words = message.split(' ')

        if message:
    
            # Encode message to bytes, prepare header and convert to bytes, like for username above, then send
            #print("msg: " + message)
            client_socket.send(message.encode('utf-8'))

            try:
                
                if message == "list" and not chat_connection:

                    stream = receive_message(client_socket)
                    stream_words = stream['data'].split(' ')
                    
                    if len(stream_words) == 2 and stream_words[0] == "connect":
                        chat_connection = True
                        chat_friend = stream_words[1]
                        print("Chating request found!")
                        print("START chat with {}".format(chat_friend))
                    else:
                        print(print_list(stream['data'], ' '))
                
                elif message_words[0] == "connect" and len(message_words) == 2 and not chat_connection:
                    chat_connection = True

                    print("Waiting for {} to chat...".format(message_words[1]))

                    chat_message = receive_message(client_socket)
                    chat_friend = message_words[1]

                    print("START chat with {}".format(chat_friend))
                    print("\t{} > {}".format(chat_friend, chat_message['data']))

                elif message == "disconnect" and not chat_connection:
                    print("Disconnected from the server. Connection ended")
                    
                    chat_connection = False
                    chat_friend = ""

                    client_socket.close()
                    sys.exit()

                elif message == "disconnect" and chat_connection:
                    
                    print("\tDisconnected from chat.")

                    stream = receive_message(client_socket)
                    print(print_list(stream['data'], ' '))
                    
                    chat_connection = False
                    chat_friend = ""

                elif chat_connection:
                    chat_message = receive_message(client_socket)

                    if chat_message['data'] != "disconnect":
                        print("\t{} > {}".format(chat_friend, chat_message['data']))
                    else: 
                        print("\t{} disconnected from the chat".format(chat_friend))
                        chat_connection = False
                        chat_friend = ""
        

            except IOError as e:
                # This is normal on non blocking connections - when there are no incoming data error is going to be raised
                # Some operating systems will indicate that using AGAIN, and some using WOULDBLOCK error code
                # We are going to check for both - if one of them - that's expected, means no incoming data, continue as normal
                # If we got different error code - something happened
                if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                    print('Reading error: {}'.format(str(e)))
                    sys.exit()
        
                # We just did not receive anything
                continue
        
            except Exception as e:
                # Any other exception - something happened, exit
                print('Reading any error: '.format(str(e)))
                sys.exit()

    sys.exit(0)  
    
if __name__ == "__main__":
    main()