import curses
from random import randint, random, sample, choice, shuffle
from math import floor
from Entities import *
from Items import *
import os


# Magic numbers!
# TODO put these in a class and different gamemodes
msgBufferSize = 6
roomMin = 7 # min side length
roomMax = 15 # max side length
maxNumRooms = 1000
maxStateGenTries = 1000
pathTurnChance = .4
pathBranchingChance = 0
minPathLen = 8
maxPathLen = 12
numLevels = 5
avgEnemiesPerRoom = 1
chanceOfRoomHavingItem = .1

def writeLog(message):
    logfile = open("log", 'a')
    logfile.write(message + '\n')
    logfile.close()

class Board:
    def __init__(self, scr):
        self.scr = scr
        self.rows, self.cols = self.scr.getmaxyx()
        self.rows -= (msgBufferSize + 1) # Space for messages to be printed
        writeLog("Board is " + str(self.cols) + " " + str(self.rows))
        self.structuresPresent = [] # All rooms present, filled by genState()
        self.genState()
        self.setState()
        playerClone = MovableEntity('@', "Player", -1, -1, -1, self, health=50, meleeDamage=10, maxCarryWeight=100) 
        self.player = self.placeEntity(playerClone, 0)
        self.scr.clear()
        self.scr.refresh()

    def placeEntity(self, entityClone, level):
        entity = None
        structures = self.structuresPresent[level][:]
        shuffle(structures)
        for structure in structures:
            top, left, bottom, right = structure.getSides()
            structureFull = True
            for i in range(top, bottom + 1):
                for j in range(left, right + 1):
                    structureFull &= (self.state[level][i][j] != None)
            if structureFull:
                continue
            while True:
                row = randint(top, bottom)
                col = randint(left, right)
                if self.state[level][row][col] is None:
                    entity = entityClone.copy(level, row, col)
                    break
            break
        if entity == None:
            entity = entityClone.copy(level, 0, 0)
        self.state[level][entity.row][entity.col] = entity
        return entity

    def display(self, takeTurn, level, playerMessage=""):
        """Display a level, optionally computing one generation"""
        messages = [playerMessage]
        if takeTurn:
            # Turns
            stateCopy = self.copyState()
            for row in stateCopy[level]:
                for entity in row:
                    if entity is not None:
                        turnMessage = entity.onTurn()
                        if turnMessage is not "": 
                            messages.append(turnMessage)
            # Deaths
            for i in range(self.rows-1):
                for j in range(self.cols):
                    if self.state[level][i][j] is not None:
                        if not self.state[level][i][j].alive:
                            # kill the entity. If after calling onDeath() the
                            # entity at [i][j] is not the same as the entity 
                            # that was there before (i.e. onDeath() spawned a
                            # new entity there) then do nothing, but otherwise
                            # set the entity at [i][j] to null
                            tmp = self.state[level][i][j]
                            self.state[level][i][j].onDeath()
                            if self.state[level][i][j] == tmp:
                                self.state[level][i][j] = None
        if self.player:
            messages.insert(0, self.player.getState())
        # Printing
        for i in range(self.rows-1):
            for j in range(self.cols):
                if self.state[level][i][j] is None or not self.state[level][i][j].alive:
                    self.scr.addch(i, j, '.')
                else:
                    self.scr.addstr(i, j, self.state[level][i][j].body)


        # Some of the messages will have newlines in them, which could make
        # this try to print off screen. So split the elements of messages at
        # the newlines
        splitMessages = []
        for msg in messages:
            splitMessages += msg.splitlines()

        # Can only display the last (msgBufferSize) messages, so pop all others
        for i in range(len(splitMessages) - msgBufferSize):
            splitMessages.pop(1) # 1, not 0 b/c must keep the player info

        # Wipe all text in message area before printing. Otherwise could have
        # old messages showing when they shouldn't be 
        for i in range(msgBufferSize):
            self.scr.addstr(self.rows+i, 0, " "*self.cols)

        # Finally print the messages
        for line in range(len(splitMessages)):
            self.scr.addstr(self.rows+line, 0, splitMessages[line])
        self.scr.refresh()
        return

    def setState(self):
        wall = Entity('#', "Wall", -1, -1, -1, self)
        wall.passive = True
        wall.opaque = True
        self.state = [[[wall.copy(level, i, j) for j in range(self.cols)] 
                                                for i in range(self.rows)]
                                                for level in range(numLevels)]
        for level in range(numLevels):
            for structure in self.structuresPresent[level]:
                self.addStructure(structure)

        self.addRequiredEntities()

    def genState(self):
        writeLog("\nStarting over")
        self.structuresPresent = [None for level in range(numLevels)]
        for level in range(numLevels):
            initRoom = self.genRandomRoom(level)
            roomsMade = 1
            numTries = 0
            self.structuresPresent[level] = [initRoom]
            while roomsMade < maxNumRooms and numTries < maxStateGenTries:
                currStructure = choice(self.structuresPresent[level])
                newStructure = currStructure.genChild()
                if self.checkStructure(newStructure):
                    if isinstance(newStructure, Board.Room):
                        self.structuresPresent[level].append(newStructure)
                        roomsMade += 1
                    else:
                        newStructures = self.completePath(newStructure)
                        self.structuresPresent[level] += newStructures
                        for structure in newStructures:
                            if isinstance(structure, Board.Room):
                                roomsMade += 1
                else:
                    if isinstance(newStructure, Board.Room):
                        numTries += 1

    def addRequiredEntities(self):
        genericStairDown = Stairway('v', None, -1, -1, -1, self)
        genericStairUp = Stairway('^', None, -1, -1, -1, self)
        oldStairDown = None
        for level in range(numLevels):
            if level != 0:
                oldStairDown.partnerStair = self.placeEntity(genericStairUp, level)
                oldStairDown.partnerStair.partnerStair = oldStairDown
            oldStairDown = self.placeEntity(genericStairDown, level)


    def genRandomRoom(self, level):
        (width, height) = (randint(roomMin, roomMax), randint(roomMin, roomMax))
        row = randint(0 + height/2 + 1, self.rows - height/2 - 1) 
        col = randint(0 + width/2 + 1, self.cols - width/2 - 1)
        newRoom = Board.Room(width, height, level, row, col)
        if self.checkEdgeOverlap(newRoom):
            return newRoom
        else:
            return self.genRandomRoom(level)

    def addStructure(self, structure):
        if isinstance(structure, Board.Room):
            self.addRoom(structure)
        else:
            self.addPath(structure)

    def addRoom(self, newRoom):
        # Add the room to newState
        for i in range(newRoom.height):
            for j in range(newRoom.width):
                level = newRoom.level
                top = newRoom.top
                left = newRoom.left
                self.state[level][top+i][left+j] = newRoom.state[i][j]
                if self.state[level][top+i][left+j] is not None:
                    self.state[level][top+i][left+j].row = top + i
                    self.state[level][top+i][left+j].col = left + j
                    self.state[level][top+i][left+j].home = self
                    self.state[level][top+i][left+j].level = level
                    self.state[level][top+i][left+j].update()
        
    def addPath(self, newPath):
        stepi = -1 if (newPath.start[0] - newPath.end[0]) > 0 else 1
        for i in range(newPath.start[0], newPath.end[0] + stepi, stepi):
            stepj = -1 if (newPath.start[1] - newPath.end[1]) > 0 else 1
            for j in range(newPath.start[1], newPath.end[1] + stepj, stepj):
                self.state[newPath.level][i][j] = None

    def completePath(self, path):
        completedPath = [path]
        while completedPath != [] and isinstance(completedPath[-1], Board.Path):
            completedPath.append(completedPath[-1].genChild())
            if not self.checkStructure(completedPath[-1]):
                completedPath.pop()
                completedPath.pop()
        return completedPath

    def checkStructure(self, structure):
        if not self.checkEdgeOverlap(structure):
            return False
        
        valid = True
        for old in self.structuresPresent[structure.level]:
            newTop, newLeft, newBottom, newRight = structure.getSides()
            oldTop, oldLeft, oldBottom, oldRight = old.getSides()

            newTopInOld = oldTop <= newTop <= oldBottom
            newBottomInOld = oldTop <= newBottom <= oldBottom
            newLeftInOld = oldLeft <= newLeft <= oldRight
            newRightInOld = oldLeft <= newRight <= oldRight
            oldTopInNew = newTop <= oldTop <= newBottom
            oldBottomInNew = newTop <= oldBottom <= newBottom
            oldLeftInNew = newLeft <= oldLeft <= newRight
            oldRightInNew = newLeft <= oldRight <= newRight

            valid &= not ((oldTopInNew and (newLeftInOld or newRightInOld)) or
                          (oldLeftInNew and (newTopInOld or newBottomInOld)) or
                          (oldBottomInNew and (newLeftInOld or newRightInOld)) or
                          (oldRightInNew and (newTopInOld or newBottomInOld)))
        return valid

    def checkEdgeOverlap(self, structure):
        top, left, bottom, right = structure.getSides()
        if (top <= 0 or 
                left <= 0 or 
                bottom >= (self.rows - 2) or 
                right >= (self.cols - 1)):
            return False
        return True

    def copyState(self):
        copy = [[[None for col in range(self.cols)] for row in range(self.rows)] for level in range(numLevels)]
        for level in range(numLevels):
            for row in range(self.rows):
                for col in range(self.cols):
                    copy[level][row][col] = self.state[level][row][col]
        return copy


    class Room:
        def __init__(self, width, height, level, row, col):
            self.height = height
            self.width = width
            self.level = level
            self.top = row
            self.left = col
            self.bottom = row + height - 1
            self.right = col + width - 1
            self.state = [[None for i in range(self.right - self.left + 1)] 
                                    for j in range(self.bottom - self.top + 1)]
            self.populate()

        # TODO make rooms populate themselved with entities based on
        # parameters to be added to the constructor
        def populate(self):
            numEntities = randint(0, 2*avgEnemiesPerRoom)
            for i in range(numEntities):
                row = randint(0, self.height-1)
                col = randint(0, self.width-1)
                if self.state[row][col] is None:
                    self.state[row][col] = choice(genericEnemies).copy(self.level, row, col)
                    # (genericEnemies is in Entities)
            if random() < chanceOfRoomHavingItem:
                row = randint(0, self.height-1)
                col = randint(0, self.width-1)
                if self.state[row][col] is None:
                    item = choice(items)
                    holder = ItemHolder(self.level, row, col, None, item) 
                    self.state[row][col] = holder.copy(self.level, row, col)
                    # (items is in Items)


        # generate a path coming from this room    
        def genChild(self):
            side = randint(1,4)
            length = randint(minPathLen, maxPathLen) - 1
            newPath = None
            if side is 1: # Top
                pos = randint(0, self.width - 1)
                start = (self.top - 1, self.left + pos)
                end = (start[0] - length, start[1])
            elif side is 2: # Right
                pos = randint(0, self.height - 1)
                start = (self.top + pos, self.right + 1)
                end = (start[0], start[1] + length)
            elif side is 3: # Bottom
                pos = randint(0, self.width - 1)
                start = (self.bottom + 1, self.left + pos)
                end = (start[0] + length, start[1])
            elif side is 4: # Left
                pos = randint(0, self.height - 1)
                start = (self.top + pos, self.left - 1)
                end = (start[0], start[1] - length)
            return Board.Path(self.level, start, end)

        def getSides(self):
            return(self.top, self.left, self.bottom, self.right)

    class Path:
        # TODO add support for diagonal paths (maybe)
        def __init__(self, level, start, end):
            self.level = level
            self.start = start
            self.end = end

        def genChild(self):
            if random() < pathTurnChance:
                return self.genPathChild() 
            else:
                return self.genRoomChild()

        def genPathChild(self):
            direction = randint(1,4)
            length = randint(minPathLen, maxPathLen)
            start,  end = None, None
            
            # Get new path start
            if random() < (1 - pathBranchingChance):
                start = self.end
            else:
                if self.start[0] == self.end[0]: # Horizontal path
                    colRange = [self.start[1], self.end[1]]
                    colRange.sort()
                    startCol = randint(*colRange)
                    start = (self.start[0], startCol)
                elif self.start[1] == self.end[1]: # Vertical path
                    rowRange = [self.start[0], self.end[0]]
                    rowRange.sort()
                    startRow = randint(*rowRange)
                    start = (startRow, self.start[1])
           
            # Get new path end
            if direction == 1: # up
                start = (start[0] - 1, start[1])
                end = (start[0] - length, start[1])
            elif direction == 2: # left
                start = (start[0], start[1] - 1)
                end = (start[0], start[1] - length)
            elif direction == 3: # down
                start = (start[0] + 1, start[1])
                end = (start[0] + length, start[1])
            elif direction == 4: # right
                start = (start[0], start[1] + 1)
                end = (start[0], start[1] + length)
            
            return Board.Path(self.level, start, end)

        def genRoomChild(self):
            height, width = (randint(roomMin, roomMax), randint(roomMin, roomMax))
            row, col = None, None # Room coords to be set in the following ifs

            if self.start[0] is self.end[0]: # Horizontal path
                loc = randint(0, height - 1)
                if self.start < self.end: # Adding to right end 
                    row = self.end[0] - loc
                    col = self.end[1] + 1
                else: # Adding to left end
                    row = self.end[0] - loc
                    col = self.end[1] - width
            else: # Vertical path
                loc = randint(0, width - 1)
                if self.start < self.end: # Adding to bottom
                    row = self.end[0] + 1
                    col = self.end[1] - loc
                else: # Adding to top
                    row = self.end[0] - height
                    col = self.end[1] - loc

            return Board.Room(width, height, self.level, row, col)

        def getSides(self):
            top = min(self.start[0], self.end[0])
            bottom = max(self.start[0], self.end[0])
            left = min(self.start[1], self.end[1])
            right = max(self.start[1], self.end[1])
            return (top, left, bottom, right)
