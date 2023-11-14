# =================================================================================================
# Contributing Authors:	    Ty Gordon, Caleb Fields
# Email Addresses:          wtgo223@uky.edu, cwfi224@uky.edu
# Date:                     11/1/2023
# Purpose:                  To implement the server logic
# Misc:                     N/A
# =================================================================================================

import socket
import threading
import json # For packing and sending
from typing import Optional, Union # For type hinting
import time

# Use this file to write your server logic
# You will need to support at least two clients
# You will need to keep track of where on the screen (x,y coordinates) each paddle is, the score 
# for each player and where the ball is, and relay that to each client
# I suggest you use the sync variable in pongClient.py to determine how out of sync your two
# clients are and take actions to resync the games

__gameList__ = [] # Private global list that stores dictionaries pairs of left and right players, which contain gameStates

# Author(s):   Ty Gordon, Caleb Fields
# Purpose:  To store 2-tuples of data in a concise way
class Vec2D():
    def __init__(self, x=None, y=None) -> None:
        self._x = x if x is not None else 0.0
        self._y = y if y is not None else 0.0

    def setPos(self, x: float, y: float) -> None:
        self._x = x
        self._y = y

    @property
    def x(self) -> float:
        return self._x

    @x.setter
    def x(self, x: float) -> None:
        self._x = x

    @property
    def y(self) -> float:
        return self._y

    @x.setter
    def y(self, y: float) -> None:
        self._y = y


# Author(s):   Ty Gordon, Caleb Fields
# Purpose:  To store game state data in a concise way
class GameState():
    def __init__(self, sync: Optional[int] = None, leftPaddle: Optional[Vec2D] = None, rightPaddle: Optional[Vec2D] = None, ball: Optional[Vec2D] = None, score: Optional[Vec2D] = None, start:bool = False):
        self._sync = 0 if sync is None else sync
        self._leftPaddle = Vec2D() if leftPaddle is None else leftPaddle
        self._rightPaddle = Vec2D() if rightPaddle is None else rightPaddle
        self._ball = Vec2D() if ball is None else ball
        self._score = Vec2D() if score is None else score  # x is left score, y is right score
        self._start = False if start is None else start
        
    def setState(self, sync: Optional[int], leftPaddle: Union[Vec2D, None], rightPaddle: Union[Vec2D, None], ball: Union[Vec2D, None], score: Union[Vec2D, None]):
        self._sync = sync
        self._leftPaddle = leftPaddle
        self._rightPaddle = rightPaddle
        self._ball = ball
        self._score = score  # x is left score, y is right score

    @property
    def sync(self) -> int:
        return self._sync
    
    @sync.setter
    def sync(self, sync: int) -> None:
        self._sync = sync

    @property
    def leftPaddle(self) -> Vec2D:
        return self._leftPaddle
    
    @leftPaddle.setter
    def leftPaddle(self, leftPaddle: Vec2D) -> None:
        self._leftPaddle = leftPaddle

    @property
    def rightPaddle(self) -> Vec2D:
        return self._rightPaddle
    
    @rightPaddle.setter
    def rightPaddle(self, rightPaddle: Vec2D) -> None:
        self._rightPaddle = rightPaddle

    @property
    def ball(self) -> Vec2D:
        return self._ball
    
    @ball.setter
    def ball(self, ball: Vec2D) -> None:
        self._ball = ball

    @property
    def score(self) -> Vec2D:
        return self._score
    
    @score.setter
    def score(self, score: Vec2D) -> None:
        self._score = score

    @property
    def start(self) -> bool:
        return self._start

    @start.setter
    def start(self, start: bool) -> None:
        self._start = start

# Author(s):   Ty Gordon, Caleb Fields
# Purpose:  To manage the interactions between the server and each client
# Pre:  A clientSocket object must be passed in order to know which client this thread regulates
# Post: The thread will persist and handle its client's transmissions
def clientThread(clientSocket: socket, clientAddress, gameId: int, isLeft: bool) -> None:

    # These constants are arbitrary and may change
    SCREEN_HEIGHT = 640
    SCREEN_WIDTH = 480
    SYNC_OFFSET = 1

    

    sideString = 'left' if isLeft else 'right' # Send player's side (left or right)
    oppString = 'right' if isLeft else 'left'  # Opponent's side (left or right)

    preliminaryData = {'side': sideString,
        'height': SCREEN_HEIGHT,
        'width': SCREEN_WIDTH}
    
    jPreliminaryData = json.dumps(preliminaryData)  # Dump the data
    clientSocket.send(jPreliminaryData.encode()) # Send side, screen height and screen width

    clientGameState = GameState()

    # Make sure both players have connected
    while not (__gameList__[gameId]['left'].start and __gameList__[gameId]['right'].start):
     time.sleep(1)  # Wait for a second before checking again

    # -_-_-_-_-_-_-_ PERPETUAL LISTENING LOOP _-_-_-_-_-_-_-
    while(True):
        clientGameState.start = True
        # Recieve game state from client
        print("Recieving data from client..." + sideString)
        received = clientSocket.recv(1024) # Recieve socket data
        data = received.decode()    # Decode socket data
        jsonData = json.loads(data) # Parse Json data

        syncNeeded = False

        if not received: # Close connection
            print("No data")
            break

        # If sync is outside of limits, overwrite the state of the sender
        if isLeft:  # Self is left player
            if abs(jsonData['sync'] - __gameList__[gameId]['right'].sync) >= SYNC_OFFSET:   # Out of sync
                if jsonData['sync'] < __gameList__[gameId]['right'].sync:   # Self is behind, fix
                    __gameList__[gameId]['left'] = __gameList__[gameId]['right']
                    clientGameState = __gameList__[gameId]['left']
                    syncNeeded = True
                    print("Syncing left")
        else:   # Self is right player
            if abs(jsonData['sync'] - __gameList__[gameId]['left'].sync) >= SYNC_OFFSET:    # Out of sync
                if jsonData['sync'] < __gameList__[gameId]['left'].sync:    # Self is behind, fix
                    __gameList__[gameId]['right'] = __gameList__[gameId]['left']
                    clientGameState = __gameList__[gameId]['right']
                    syncNeeded = True
                    print("Syncing right")

        # If in sync, update the server state model and parrot back the sent data
        if not syncNeeded:    
            # Update clientGameState using received data
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

        print(clientGameState.sync)
        # Send back the data
        data = {'sync': clientGameState.sync,   # Assemble the Json dictionary
            'left': [clientGameState.leftPaddle.x, clientGameState.leftPaddle.y],
            'right': [clientGameState.rightPaddle.x, clientGameState.rightPaddle.y],
            'ball': [clientGameState.ball.x, clientGameState.ball.y],
            'score': [clientGameState.score.x, clientGameState.score.y]}
        
        jsonData = json.dumps(data) # Dump (package) the data
        clientSocket.send(jsonData.encode()) # Send the data

    clientSocket.close()    # Close the connection after client goes silent


# Author(s): Ty Gordon, Caleb Fields
# Purpose: To establish the server's connection on a specific port, and to perpetually listen for and
#   instanciate client-server interactions through instanced threads
# Pre: It is expected that a server has not already been established
# Post: A server will have been created and will 
def establishServer() -> None:
    port = 7777

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create the server
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)    # Work with localhost

    server.bind(("10.54.185.2", port))    # Connect server to port and enter listening mode
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
            __gameList__[gameItr]['right'].start = True
            __gameList__[gameItr]['left'].start = True
            gameItr += 1
            isLeft = True

        threadList.append(newThread) # Add the thread to the list and start it   (Probably unnecessary)
        if(__gameList__[gameItr - 1]['left'].start and __gameList__[gameItr - 1]['right'].start):
            print("Starting game " + str(gameItr - 1))
            threadList[-1].start()
            threadList[-2].start()

    for t in threadList:    # Iterate and join all threads  (Probably unnecessary)
        t.join()

    server.close()  # Close the server after connection termination


# Author(s):   Ty Gordon
# Purpose:  To start the server program
# Pre:  It is expected that the server program hasn't run yet, and must start here
# Post: Begins execution of the server program starting with the establishServer() function
if __name__ == "__main__":
    establishServer()