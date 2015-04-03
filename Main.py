# A primitive roguelike by Algae Elbaum

# Currently working on: projectile weapons
#       *Make range be a property of the weapon

# TODO
#   dungeon generation
#     -Entity and item placement in rooms
#     -Maybe add support for levels being larger than the screen.
#   More entities with non-identical AIs
#   More item types (like projectile weapons)
#   Magic/enchanting
#   Win condition
#   More stuff that doesn't immediately come to mind   

import curses
from Board import *
from Entities import *
from time import sleep


def writeLog(message):
    logfile = open("log", 'a')
    logfile.write(message + '\n')
    logfile.close()


def manageInventory(entity, subwin):
    curses.echo()
    inventoryStringLst = entity.getInventoryString().split('\n')
    actions = ["0: exit", "1: use", "2: equip", "3: unequip", "4: destroy"]
    prompt = "Item: "
    sndPrompt = "Action: "
    while True:
        printList(inventoryStringLst, subwin)
        promptRow = len(inventoryStringLst)
        subwin.addstr(promptRow, 0, prompt)
        item = None
        try:
            item = int(subwin.getstr(promptRow, len(prompt))) - 1
        except:
            pass
        if item == -1:
            curses.noecho()
            return ""
        if item in range(promptRow - 1):
            printList(actions, subwin)
            sndPromptRow = len(actions) + 1
            subwin.addstr(sndPromptRow, 0, sndPrompt)
            action = None
            try:
                action = int(subwin.getstr(sndPromptRow, len(sndPrompt)))
            except:
                pass
            if action in range(sndPromptRow - 1)[1:]:
                message = ""
                if action == 1:
                    message = entity.useItem(item)
                elif action == 2:
                    message = entity.equip(item)
                elif action == 3:
                    message = entity.unequip(item)
                elif action == 4:
                    message = entity.destroyItem(item)
                curses.noecho()
                return message
        subwin.clear()
        subwin.addstr(0, 0, "Invalid input")
        subwin.refresh()
        sleep(1)

# Select a cell within a certain radius of an entity
def locSelect(board, entity, radius, stdscr, subwin):
    level = entity.level
    marker = TimelessGhost(level, entity.row, entity.col, board, entity)
    board.state[level][entity.row][entity.col] = marker
    # allow player to move marker freely within the radius to select a point
    board.display(False, level)
    while(True):
        c = stdscr.getch()
        if 0<c<256:
            c = chr(c)
            if c in "fF":
                board.state[level][marker.row][marker.col] = marker.containedEntity
                return (marker.row, marker.col)
            elif c in "wW":
                newRow, newCol = (marker.row - 1, marker.col)
                if testLoc(entity.row, entity.col, newRow, newCol, radius):
                    marker.move(1)
            elif c in "sS":
                newRow, newCol = (marker.row + 1, marker.col)
                if testLoc(entity.row, entity.col, newRow, newCol, radius):
                    marker.move(2)
            elif c in "aA":
                newRow, newCol = (marker.row, marker.col - 1)
                if testLoc(entity.row, entity.col, newRow, newCol, radius):
                    marker.move(3)
            elif c in "dD":
                newRow, newCol = (marker.row, marker.col + 1)
                if testLoc(entity.row, entity.col, newRow, newCol, radius):
                    marker.move(4)
            board.display(False, level)

def testLoc(baseRow, baseCol, newRow, newCol, radius):
    return radius >= sqrt((newRow - baseRow)**2 + (newCol - baseCol)**2)


def printList(lst, subwin):
    subwin.clear()
    for i, elem in enumerate(lst):
        subwin.addstr(i, 0, elem)


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(False)
    stdscr_y, stdscr_x = stdscr.getmaxyx()
    subwin = stdscr.subwin(stdscr_y, stdscr_x, 0, 0)
    gameBoard = Board(subwin)
    gameBoard.display(False, 0)
    while(True):
        writeLog(str(len(gameBoard.state[0])) + " " + str(len(gameBoard.state)))
        c = stdscr.getch()
        message = ""
        if 0<c<256:
            c = chr(c)
            if c in "qQ":
                return
            elif c in "wW":
                message = gameBoard.player.move(1)[1]
            elif c in "sS":
                message = gameBoard.player.move(2)[1]
            elif c in "aA":
                message = gameBoard.player.move(3)[1]
            elif c in "dD":
                message = gameBoard.player.move(4)[1]
            elif c in "rR":        
                playerClone = MovableEntity('@', "Player", -1, -1, -1, gameBoard,
                                    health=50, meleeDamage=10, maxCarryWeight=100) 
                gameBoard.genState()
                gameBoard.setState()
                gameBoard.player = gameBoard.placeEntity(playerClone, 0)
                gameBoard.display(False, 0)
                continue
            elif c in "eE":
                message = manageInventory(gameBoard.player, subwin)
            elif c in "fF":
                message = gameBoard.player.rangedAttack(*locSelect(gameBoard, gameBoard.player,
                                    gameBoard.player.attackRange, stdscr, subwin))
        gameBoard.display(True, gameBoard.player.level, message)
        writeLog("Finished turns")


if __name__ == '__main__':
    curses.wrapper(main)
