# =================================================================================================
# Contributing Authors:	    Ty Gordon
# Email Addresses:          wtgo223@uky.edu
# Date:                     11/1/2023
# Purpose:                  To implement the server logic
# Misc:                     N/A
# =================================================================================================

import socket
import threading
import json # For packing and sending

# Use this file to write your server logic
# You will need to support at least two clients
# You will need to keep track of where on the screen (x,y coordinates) each paddle is, the score 
# for each player and where the ball is, and relay that to each client
# I suggest you use the sync variable in pongClient.py to determine how out of sync your two
# clients are and take actions to resync the games

__gameList__ = [] # Private global list that stores dictionaries pairs of left and right players, which contain gameStates

# Author(s):   Ty Gordon
# Purpose:  To store game state data in a concise way
class GameState():

    def __init__(self, sync=None, leftPaddle=None, rightPaddle=None, ball=None, score=None):
        self._sync = 0 if None else sync
        self._leftPaddle = Vec2D() if None else leftPaddle
        self._rightPaddle = Vec2D() if None else rightPaddle
        self._ball = Vec2D() if None else ball
        self._score = Vec2D() if None else score # x is left score, y is right score

    def setState(self, sync, leftPaddle, rightPaddle, ball, score):
        self._sync = sync
        self._leftPaddle = leftPaddle
        self._rightPaddle = rightPaddle
        self._ball = ball
        self._score = score # x is left score, y is right score

    @property
    def sync(self):
        return self._sync
    
    @id.setter
    def sync(self, sync):
        self._sync = sync

    @property
    def leftPaddle(self):
        return self._leftPaddle
    
    @leftPaddle.setter
    def leftPaddle(self, leftPaddle):
        self._leftPaddle = leftPaddle

    @property
    def rightPaddle(self):
        return self._rightPaddle
    
    @rightPaddle.setter
    def rightPaddle(self, rightPaddle):
        self._rightPaddle = rightPaddle

    @property
    def ball(self):
        return self._ball
    
    @ball.setter
    def ball(self, ball):
        self.ball = ball

    @property
    def score(self):
        return self._score
    
    @score.setter
    def score(self, score):
        self.ball = score

# Author(s):   Ty Gordon
# Purpose:  To store 2-tuples of data in a concise way
class Vec2D():
    def __init__(self, x=None, y=None):
        self._x = 0.0 if None else x
        self._y = 0.0 if None else y

    def setPos(self, x, y):
        self._x = x
        self._y = y

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, x):
        self._x = x

    @property
    def y(self):
        return self._y

    @x.setter
    def y(self, y):
        self._y = y


# Author(s):   Ty Gordon
# Purpose:  To manage the interactions between the server and each client
# Pre:  A clientSocket object must be passed in order to know which client this thread regulates
# Post: The thread will persist and handle its client's transmissions
def clientThread(clientSocket, clientAddress, gameId, isLeft):

    # These constants are arbitrary and may change
    SCREEN_HEIGHT = 640
    SCREEN_WIDTH = 480
    SYNC_OFFSET = 2

    sideString = 'left' if isLeft else 'right' # Send player's side (left or right)

    preliminaryData = {'side': sideString,
        'height': SCREEN_HEIGHT,
        'width': SCREEN_WIDTH}
    
    jPreliminaryData = json.dumps(preliminaryData)  # Dump the data
    clientSocket.send(jPreliminaryData.encode()) # Send side, screen height and screen width

    clientGameState = GameState()

    # -_-_-_-_-_-_-_ PERPETUAL LISTENING LOOP _-_-_-_-_-_-_-
    while(True):
        
        # Recieve game state from client
        recieved = clientSocket.recv(1024) # Recieve socket data
        data = recieved.decode()    # Decode socket data
        jsonData = json.loads(data) # Parse Json data

        syncNeeded = False

        if not recieved: # Close connection
            break

        # If sync is outside of limits, overwrite the state of the sender
        if isLeft:  # Self is left player
            if abs(jsonData['sync'] - __gameList__[gameId]['right'].sync) <= SYNC_OFFSET:   # Out of sync
                if jsonData['sync'] < __gameList__[gameId]['right'].sync:   # Self is behind, fix
                    __gameList__[gameId]['left'] = __gameList__[gameId]['right']
                    syncNeeded = True
        else:   # Self is right player
            if abs(jsonData['sync'] - __gameList__[gameId]['left'].sync) >= SYNC_OFFSET:    # Out of sync
                if jsonData['sync'] < __gameList__[gameId]['left'].sync:    # Self is behind, fix
                    __gameList__[gameId]['right'] = __gameList__[gameId]['left']
                    syncNeeded = True

        # If in sync, update the server state model and parrot back the sent data
        if not syncNeeded:    
            # Update clientGameState using recieved data
            if isLeft:
                clientGameState.leftPaddle = Vec2D(jsonData['paddle'][0], jsonData['paddle'][1])
                clientGameState.rightPaddle = __gameList__[gameId]['right'].rightPaddle
            else:
                clientGameState.leftPaddle = __gameList__[gameId]['left'].leftPaddle
                clientGameState.rightPaddle = Vec2D(jsonData['paddle'][0], jsonData['paddle'][1])

            clientGameState.sync = jsonData['sync']
            clientGameState.ball = Vec2D(jsonData['ball'][0], jsonData['ball'][1])
            clientGameState.score = Vec2D(jsonData['score'][0], jsonData['score'][1])

            __gameList__[gameId][sideString] = clientGameState # Update the global game state

        # Send back the data
        data = {'sync': clientGameState.sync,   # Assemble the Json dictionary
            'left': [clientGameState.leftPaddle.x, clientGameState.leftPaddle.y],
            'right': [clientGameState.rightPaddle.x, clientGameState.rightPaddle.y],
            'ball': [clientGameState.ball.x, clientGameState.ball.y],
            'score': [clientGameState.score.x, clientGameState.score.y]}
        
        jsonData = json.dumps(data) # Dump (package) the data
        clientSocket.send(jsonData.encode()) # Send the data

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

    isLeft = True   # Designates the first client as the "left" player
    threadList = [] # Stores all threads to be joined later (Probably unnecessary)

    gameItr = 0

    # PERPETUAL CONNECTION LOOP
    while(True):

        clientSocket, clientAddress = server.accept()   # Connect with a client
        print("Client Connected. | Address: ", clientAddress[0], " Port: ", clientAddress[1])   # Print connection details

        newThread = threading.Thread(target=clientThread, args=(clientSocket, clientAddress, gameItr, isLeft))  # Start the thread at the function clientThread

        if isLeft:
            __gameList__.insert(gameItr, {'left': GameState(), 'right': GameState()})
            isLeft = False
        else:
            gameItr += 1
            isLeft = True

        threadList.append(newThread) # Add the thread to the list and start it   (Probably unnecessary)
        newThread.start()

    for t in threadList:    # Iterate and join all threads  (Probably unnecessary)
        t.join()

    server.close()  # Close the server after connection termination


# Author(s):   Ty Gordon
# Purpose:  To start the server program
# Pre:  It is expected that the server program hasn't run yet, and must start here
# Post: Begins execution of the server program starting with the establishServer() function
if __name__ == "__main__":
    establishServer()