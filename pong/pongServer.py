# =================================================================================================
# Contributing Authors:	    Ty Gordon
# Email Addresses:          wtgo223@uky.edu
# Date:                     10/26/2023
# Purpose:                  To implement the server logic
# Misc:                     N/A
# =================================================================================================

import socket
import threading

# Use this file to write your server logic
# You will need to support at least two clients
# You will need to keep track of where on the screen (x,y coordinates) each paddle is, the score 
# for each player and where the ball is, and relay that to each client
# I suggest you use the sync variable in pongClient.py to determine how out of sync your two
# clients are and take actions to resync the games



# Author(s):   Ty Gordon
# Purpose:  To manage the interactions between the server and each client
# Pre:  A clientSocket object must be passed in order to know which client this thread regulates
# Post: The thread will persist and handle its client's transmissions
def clientThread(clientSocket):

    # PERPETUAL LISTENING LOOP
    while(True):

        message = clientSocket.recv(1024)   # Expect LEFT or RIGHT

        if not message: # Close connection if not message
            break

        # clientSocket.send() # Send data to the client

    clientSocket.close()    # Close the connection after client goes silent


# Author(s):   Ty Gordon
# Purpose:  To establish the server's connection on a specific port, and to perpetually listen for and
#   instanciate client-server interactions through instanced threads
# Pre:  It is expected that a server has not already been established
# Post: A server will have been created and will 
def establishServer():
    port = 7777

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create the server
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)    # Work with localhost

    server.bind(("localhost", port))    # Connect server to port and enter listening mode
    server.listen(5)

    threadList = [] # Stores all threads to be joined later

    # PERPETUAL CONNECTION LOOP
    while(True):

        clientSocket, clientAddress = server.accept()   # Connect with a client
        print("Client Connected. | Address: ", clientAddress[0], " Port: ", clientAddress[1])   # Print connection details

        newThread = threading.Thread(target=clientThread, args=(clientSocket))  # Start the thread at the function clientThread

        threadList.append(newThread) # Add the thread to the list and start it
        newThread.start()
    
    for t in threadList:    # Iterate and join all threads
        t.join()

    server.close()  # Close the server after connection termination


# Author(s):   Ty Gordon
# Purpose:  To start the server program
# Pre:  It is expected that the server program hasn't run yet, and must start here
# Post: Begins execution of the server program starting with the establishServer() function
if __name__ == "__main__":
    establishServer()