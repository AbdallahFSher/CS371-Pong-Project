# =================================================================================================
# Contributing Authors:	    Ty Gordon, Caleb Fields, Abdallah Sher
# Email Addresses:          wtgo223@uky.edu, cwfi224@uky.edu, afsh230@uky.edu
# Date:                     11/17/2023
# Purpose:                  To implement the server logic
# Misc:                     N/A
# =================================================================================================

import socket
import threading
import json # For packing and sending data
from typing import Optional, Union # For type hinting
import time
import http.server
import socketserver


# Use this file to write your server logic
# You will need to support at least two clients
# You will need to keep track of where on the screen (x,y coordinates) each paddle is, the score 
# for each player and where the ball is, and relay that to each client
# I suggest you use the sync variable in pongClient.py to determine how out of sync your two
# clients are and take actions to resync the games

SERVER_IP = "localhost"
__gameList__ = [] # Private global list that stores dictionaries pairs of left and right players, which contain gameStates


leaderboard = {}

# Author(s):   Ty Gordon, Caleb Fields, Abdallah Sher
# Purpose:  To store 2-tuples of data in a concise way
class Vec2D():
    # Default constructor
    def __init__(self, x=None, y=None) -> None:
        self._x = x if x is not None else 0.0
        self._y = y if y is not None else 0.0

    # Change x and y coordinates
    def setPos(self, x: float, y: float) -> None:
        self._x = x
        self._y = y

    @property # x getter
    def x(self) -> float:
        return self._x

    @x.setter # x setter
    def x(self, x: float) -> None:
        self._x = x

    @property # y getter
    def y(self) -> float:
        return self._y

    @y.setter # y setter
    def y(self, y: float) -> None:
        self._y = y


# Author(s):   Ty Gordon, Caleb Fields, Abdallah Sher
# Purpose:  To store game state data in a concise way
class GameState():
    # Default constructor
    def __init__(self, sync: Optional[int] = None, leftPaddle: Optional[Vec2D] = None, rightPaddle: Optional[Vec2D] = None, ball: Optional[Vec2D] = None, score: Optional[Vec2D] = None, start:bool = False):
        self._sync = 0 if sync is None else sync
        self._leftPaddle = Vec2D() if leftPaddle is None else leftPaddle
        self._rightPaddle = Vec2D() if rightPaddle is None else rightPaddle
        self._ball = Vec2D() if ball is None else ball
        self._score = Vec2D() if score is None else score  # x is left score, y is right score
        self._start = False if start is None else start
        
    # Change all variables in state
    def setState(self, sync: Optional[int], leftPaddle: Union[Vec2D, None], rightPaddle: Union[Vec2D, None], ball: Union[Vec2D, None], score: Union[Vec2D, None]):
        self._sync = sync
        self._leftPaddle = leftPaddle
        self._rightPaddle = rightPaddle
        self._ball = ball
        self._score = score  # x is left score, y is right score

    @property
    def sync(self) -> int:
        return self._sync
    
    @sync.setter # Sync setter
    def sync(self, sync: int) -> None:
        self._sync = sync

    @property # Sync getter
    def leftPaddle(self) -> Vec2D:
        return self._leftPaddle
    
    @leftPaddle.setter # LeftPaddle setter
    def leftPaddle(self, leftPaddle: Vec2D) -> None:
        self._leftPaddle = leftPaddle

    @property # RightPaddle getter
    def rightPaddle(self) -> Vec2D:
        return self._rightPaddle
    
    @rightPaddle.setter # RightPaddle setter
    def rightPaddle(self, rightPaddle: Vec2D) -> None:
        self._rightPaddle = rightPaddle

    @property # Ball getter
    def ball(self) -> Vec2D:
        return self._ball
    
    @ball.setter # Ball setter
    def ball(self, ball: Vec2D) -> None:
        self._ball = ball

    @property # Score getter
    def score(self) -> Vec2D:
        return self._score
    
    @score.setter # Score setter
    def score(self, score: Vec2D) -> None:
        self._score = score

    @property # Start setter
    def start(self) -> bool:
        return self._start

    @start.setter # Start getter
    def start(self, start: bool) -> None:
        self._start = start


# Author(s):   Ty Gordon, Caleb Fields, Abdallah Sher
# Purpose:  To manage the interactions between the server and each client
# Pre:  A clientSocket object must be passed in order to know which client this thread regulates
# Post: The thread will persist and handle its client's transmissions
def clientThread(name:str, clientSocket: socket, clientAddress, gameId: int, isLeft: bool) -> None:

    # Game constants
    SCREEN_HEIGHT = 480
    SCREEN_WIDTH = 640
    SYNC_OFFSET = 1

    leaderboard[name] = 0 

    sideString = 'left' if isLeft else 'right' # Send player's side (left or right)
    oppString = 'right' if isLeft else 'left'  # Opponent's side (left or right)

    # Construct a preliminary data dict to send
    preliminaryData = {'side': sideString,
        'height': SCREEN_HEIGHT,
        'width': SCREEN_WIDTH}
    
    jPreliminaryData = json.dumps(preliminaryData)  # Dump the data
    clientSocket.send(jPreliminaryData.encode()) # Send side, screen height and screen width

    # Initialize game state variables
    clientGameState = GameState()
    clientGameState.ball = Vec2D(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
    clientGameState.start = True

    # -_-_-_-_-_-_-_ PERPETUAL LISTENING LOOP _-_-_-_-_-_-_-
    while(__gameList__[gameId]['left'].start and __gameList__[gameId]['right'].start):
        time.sleep(0.01)

        # Recieve game state from client
        print("Recieving data from client..." + sideString)
        received = clientSocket.recv(1024) # Recieve socket data
        data = received.decode()    # Decode socket data
        jsonData = json.loads(data) # Parse Json data

        syncNeeded = False

        if not received: # Close connection
            print("No data")
            break

        # Construct score, sync, and ball pos from recieved Json
        clientGameState.score = Vec2D(jsonData['score'][0], jsonData['score'][1])
        clientGameState.sync = jsonData['sync']

        #Default to left side's ball being the correct one
        if isLeft:
            clientGameState.ball = Vec2D(jsonData['ball'][0], jsonData['ball'][1])
        else:
            clientGameState.ball = __gameList__[gameId][oppString].ball

        # Construct paddle positions from recieve Json
        if isLeft:
            clientGameState.leftPaddle = Vec2D(jsonData['paddle'][0], jsonData['paddle'][1])
            clientGameState.rightPaddle = __gameList__[gameId]['right'].rightPaddle
        else:
            clientGameState.leftPaddle = __gameList__[gameId]['left'].leftPaddle
            clientGameState.rightPaddle = Vec2D(jsonData['paddle'][0], jsonData['paddle'][1])

        __gameList__[gameId][sideString] = clientGameState # Update the global game state

        # Sync game if out of sync
        if clientGameState.sync < __gameList__[gameId][oppString].sync:
            clientGameState = __gameList__[gameId][oppString]
            print("Syncing " + sideString + " to " + oppString)

        print(clientGameState.sync)

        # Send back the data
        data = {'sync': clientGameState.sync,   # Assemble the Json dictionary
            'left': [clientGameState.leftPaddle.x, clientGameState.leftPaddle.y],
            'right': [clientGameState.rightPaddle.x, clientGameState.rightPaddle.y],
            'ball': [clientGameState.ball.x, clientGameState.ball.y],
            'score': [clientGameState.score.x, clientGameState.score.y]}
        
        jsonData = json.dumps(data) # Dump (package) the data
        clientSocket.send(jsonData.encode()) # Send the data

        if clientGameState.score.x >= 5 or clientGameState.score.y >= 5:
            __gameList__[gameId]['left'].start = False
            __gameList__[gameId]['right'].start = False
            print("Game " + str(gameId) + " over")
            if isLeft:
                if clientGameState.score.x >= 5:
                    leaderboard[name] += 1
            else:
                if clientGameState.score.y >= 5:
                    leaderboard[name] += 1
            break

    clientSocket.close()    # Close the connection after client goes silent


# Author(s): Ty Gordon, Caleb Fields, Abdallah Sher
# Purpose: To establish the server's connection on a specific port, and to perpetually listen for and
#   instanciate client-server interactions through instanced threads
# Pre: It is expected that a server has not already been established
# Post: A server will have been created and will 
def establishServer() -> None:
    port = 7777

    htmlThread = threading.Thread(target=startLeaderboardServer)
    htmlThread.start()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create the server
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)    # Work with localhost

    server.bind((SERVER_IP, port))    # Connect server to port and enter listening mode
    server.listen(5)

    isLeft = True   # Designates the first client as the "left" player
    threadList = [] # Stores all threads to be used and joined later

    gameItr = 0

    # PERPETUAL CONNECTION LOOP
    while(True):

        clientSocket, clientAddress = server.accept()   # Connect with a client
        name = clientSocket.recv(1024).decode()
        if not name.isalnum():
            clientSocket.close()
            continue
        print(name, " Connected. | Address: ", clientAddress[0], " Port: ", clientAddress[1])   # Print connection details

        newThread = threading.Thread(target=clientThread, args=(name, clientSocket, clientAddress, gameItr, isLeft))  # Start the thread at the function clientThread

        # Decide if player is left or right and pass this decision
        if isLeft:
            __gameList__.insert(gameItr, {'left': GameState(), 'right': GameState()})
            isLeft = False
        else:
            __gameList__[gameItr]['right'].start = True
            __gameList__[gameItr]['left'].start = True
            gameItr += 1
            isLeft = True

        threadList.append(newThread) # Add the thread to the list and start it
        if(__gameList__[gameItr - 1]['left'].start and __gameList__[gameItr - 1]['right'].start) and isLeft:
            print("Starting game " + str(gameItr - 1))
            threadList[-1].start()
            threadList[-2].start()
            threadList[-1].join()
            threadList[-2].join()

            #Load in old leaderboard
            with open('leaderboard.json', 'r') as leaderboardFile:
                tempLeaderboard = json.load(leaderboardFile)
                leaderboardFile.close()
            #Sort in descending order
            #Update leaderboard
            del(tempLeaderboard[0])
            for item in tempLeaderboard:
                if item['name'] not in leaderboard:
                    leaderboard[item['name']] = 0
                leaderboard[item['name']] += item['score']
            sortedLeaderboard = sorted(leaderboard.items(), key=lambda x:x[1], reverse=True)
            sortedLeaderboard = dict(sortedLeaderboard)
            with open('leaderboard.json', 'w') as leaderboardFile:
                leaderboardFile.write("[{}")
                for key in sortedLeaderboard.keys():
                    leaderboardFile.write(",{\"name\":\""+key+"\",\"score\":"+str(leaderboard[key])+"}\n")
                leaderboardFile.write("]")
                leaderboardFile.close()
            #leaderboard = {}

    htmlThread.join()

    for t in threadList:    # Iterate and join all threads
        t.join()

    server.close()  # Close the server after connection termination

def startLeaderboardServer():
    PORT = 80
    Handler = http.server.SimpleHTTPRequestHandler

    # Host leaderboard.html on port 80
    with socketserver.TCPServer((SERVER_IP, PORT), Handler) as httpd:
        print("serving at port", PORT)
        httpd.serve_forever()

# Author(s):   Ty Gordon
# Purpose:  To start the server program
# Pre:  It is expected that the server program hasn't run yet, and must start here
# Post: Begins execution of the server program starting with the establishServer() function
if __name__ == "__main__":
    establishServer()