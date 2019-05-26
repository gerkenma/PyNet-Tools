import sys
import socket
import getopt
import threading
import subprocess

# define some global variables
listen = False
command = False
upload = False
execute = ""
target = ""
upload_destination = ""
port = 0


def usage():
    print("taCteN0")
    print()
    print("Usage: bad_tacten.py -t target_host -p port")
    print("-l --listen              - listen on [host]:[port] for incoming connections")
    print("-e --execute=file_to_run  - execute the given file upon receiving a connection")
    print("-c --command             - initialize a command shell")
    print("-u --upload=destination   - upon receiving a connection, upload a file and write to [destination]")
    print()
    print()
    print("Examples: ")
    print("bad_tacten.py -t 192.168.0.1 -p 5555 -l -c")
    print("bad_tacten.py -t 192.168.0.1 -p 5555 -l -u=c:\\target.exe")
    print("bad_tacten.py -t 192.168.0.1 -p 5555 -l -e=\"cat /etc/passwd\"")
    print("echo 'ABCDEFHI' | ./bad_tacten.py -t 192.168.11.12 -p 135")
    sys.exit(0)


def client_sender(buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # connect to our target host
        client.connect((target, port))

        if len(buffer):
            client.send(buffer.encode())

        while True:

            # now wait for data back
            recv_len = 1
            response = ""
            while recv_len:

                data = client.recv(4096)
                recv_len = len(data)
                response += data.decode()

                if recv_len < 4096:
                    break

            print(response,)

            buffer = input("Enter message: ")
            buffer += "\n"

            # send it off
            client.send(buffer.encode())

    except Exception as e:
        print(str(e))
        print("[*] Exception! Exiting.")
        client.close()
        sys.exit(-1)


def run_command(command):

    # trim the newline
    command = command.rstrip()

    # run the command and get the output back
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except:
        output = "Failed to execute command.\r\n"

    # send the output back to client
    return output


def client_handler(client_socket):
    global upload
    global execute
    global command

    # check for upload
    if len(upload_destination):
        print("I'm checking your upload!")
        # read in all of the bytes and write to our destination
        file_buffer = ""

        # keep reading data until none is available
        while True:
            data = client_socket.recv(1024)

            if not data:
                break

            else:
                file_buffer += data

        # now we take these bytes and try to write them out
        try:
            file_descriptor = open(upload_destination, "wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()

            # acknowledge that we wrote the file out
            client_socket.send("Successfully saved file to %s\r\n" % upload_destination)

        except:
            client_socket.send("Failed to save file to %s\r\n" % upload_destination)

    # check for command execution
    if len(execute):
        print("Attempting to execute", execute)
        # run the command
        output = run_command(execute)

        client_socket.send(output.encode())


def server_loop():
    global target

    # if no target is defined, we listen on all interfaces
    if not len(target):
        target = "0.0.0.0"

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))
    server.listen(5)

    while True:
        client_socket, addr = server.accept()

        # spin off a thread to handle our new client
        client_thread = threading.Thread(target=client_handler, args=(client_socket,))
        client_thread.start()



def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    # display help if arguments are empty
    if not len(sys.argv[1:]):
        usage()

    # read the commandline options
    # list all short hand options allowed in second parameter
    # follow any letters that require an argument with a colon (:)
    # opts is a list of (option, value) pairs
    # args is a trailing slice of args after option list is stripped
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hle:t:p:cu:", ["help", "listen", "execute", "target", "port",
                                                                 "command", "upload"])
    except getopt.GetoptError as err:
        print(str(err))
        usage()

    for o,a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-l", "--listen"):
            listen = True
        elif o in ("-e", "--execute"):
            execute = a
        elif o in ("-c", "--command"):
            command = True
        elif o in ("-u", "--upload"):
            upload_destination = a
        elif o in ("-t", "--target"):
            target = a
        elif o in ("-p", "--port"):
            port = int(a)
        else:
            assert False, "Unhandled Option"

    # if not listening, sending data from stdin
    if not listen and len(target) and port > 0:
        # read in the buffer from the commandline
        # this will block, so send CTRL-D if not sending input to stdin
        buffer = sys.stdin.read()

        # send data off
        client_sender(buffer)

    # if program is listening
    if listen:
        print("Starting server_loop")
        server_loop()

main()