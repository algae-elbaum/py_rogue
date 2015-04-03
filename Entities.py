# Contains all Entity classes and a set of standard instances from some of
# those classes.
#
# The classes Entity and Movable Entity are essentially abstract classes,
# though Entity objects do make good walls, and for now the player is just a
# MovableEntity. Besides those two exceptions, all other entites will be
# subclasses of Entity or MovableEntity and most will have unique definitions 
# for methods like onTurn() or onDeath()


# TODO find a better way of copying. Having mostly the same method in each
# class makes me sad

from math import sqrt
from random import shuffle

def writeLog(message):
    logfile = open("log", 'a')
    logfile.write(message + '\n')
    logfile.close()


class Entity(object):
    def __init__(self, body, name, level, row, col, home, health=0, alive=True,
                    wasAlive=False, armor=0, meleeDamage=0, rangedDamage=0, 
                    attackRange=0, inventory=[], weaponEquip=None, armorEquip=None, 
                    maxCarryWeight=0, passive=False, opaque=False):
        self.body = body
        self.name = name
        self.level = level
        self.row = row
        self.col = col
        self.home = home
    
        # Death is triggered by going from pos to neg health. So 0 is immortal
        self.health = health 
        self.alive = alive
        # Entities that move after other Entities want to see whether the other 
        # Entity was alive at the beginning of the turn, they don't necessarily 
        # care if the other Entity survived their turn. wasAlive is useful for 
        # this.
        self.wasAlive = wasAlive
        self.armor = armor
        self.meleeDamage = meleeDamage
        self.rangedDamage = rangedDamage
        self.attackRange = attackRange
        self.inventory = inventory
        self.weaponEquip = weaponEquip
        self.armorEquip = armorEquip
        self.maxCarryWeight = maxCarryWeight
        self.currCarryWeight = sum([item.weight for item in inventory])
        self.passive = passive
        self.opaque = opaque
        self.foughtThisTurn = False

    def fight(self, other):
        return (self.onBattle(other) + '\n' + other.onBattle(self))

    def onBattle(self, opponent, melee=True):
        damage = self.meleeDamage if melee else self.rangedDamage
        self.foughtThisTurn = True
        if opponent.passive or self.passive:
            return ""
        opponent.takeDamage(damage)
        return (self.name + " dealt " + str(damage)
                                    + " damage to " + opponent.name)

    def takeDamage(self, damage):
        initHealth = self.health
        self.health -= (damage - self.armor);
        if initHealth > 0 and self.health <= 0:
            self.alive = False
        # Haven't decided yet if armor takes damage. For now, it doesn't.

    def rangedAttack(self, row, col):
        writeLog(str(row) + " " + str(col))
        writeLog(str(len(self.home.state)) + " " + str(len(self.home.state[0])))
        if (sqrt((row-self.row)**2 + (col-self.col)**2) < self.attackRange
                and self.home.state[row][col]):
            return self.onBattle(self.home.state[row][col], melee=False)
        else:
            return "Attack out of range"


    def equip(self, inventoryIndex):
        if self.inventory[inventoryIndex].__class__.__name__ == "Weapon":
            if self.weaponEquip != None:  # debuff from old equipped weapon
                self.modStatsBuff(self.weaponEquip, False)
            self.weaponEquip = self.inventory[inventoryIndex] 
            self.modStatsBuff(self.weaponEquip, True) # buff from new equipped weapon
            return self.name + " equipped " + self.weaponEquip.name

        elif self.inventory[inventoryIndex].__class__.__name__ == "Armor":
            if self.armorEquip != None:  # debuff from old equipped armor
                self.modStatsBuff(armorEquip, False)
            self.armorEquip = self.inventory[inventoryIndex] 
            self.modStatsBuff(armorEquip, True) # buff from new equipped armor
            return self.name + " equipped " + self.armorEquip.name
        return (self.name + " tried and failed to equip " 
                                + self.inventory[inventoryIndex].name)
        
    def unequip(self, inventoryIndex):
        if self.inventory[inventoryIndex] == self.weaponEquip:
            oldWeaponEquip  = self.weaponEquip
            self.modStatsBuff(self.weaponEquip, False)
            self.weaponEquip = None
            return self.name + " unequipped " + oldWeaponEquip.name
        elif self.inventory[inventoryIndex] == self.armorEquip:
            oldArmorEquip = self.armorEquip
            self.modStatsBuff(self.armorEquip, False)
            self.armorEquip = None
            return self.name + " unequipped " + oldArmorEquip.name
        return (self.name + " tried and failed to unequip "
                                + self.inventory[inventoryIndex].name)
    
    def getInventoryString(self):
        retString = "0: exit\n"
        for i in range(len(self.inventory)):
            retString += str(i+1) + ": " + self.inventory[i].name + "\n"
        return retString

    def receiveItem(self, gift):
        if (self.maxCarryWeight - self.currCarryWeight) >= gift.weight:
            self.inventory.append(gift)
            self.currCarryWeight += gift.weight
            return True
        return False

    def useItem(self, inventoryIndex):
        message = self.inventory[inventoryIndex].used(self)
        if self.inventory[inventoryIndex].remainingUses <= 0:
            self.inventory.pop(inventoryIndex)
        return message

    def destroyItem(self, inventoryIndex):
        self.unequip(inventoryIndex)
        destroyedItem = self.inventory[inventoryIndex]
        self.inventory.pop(inventoryIndex)
        self.currCarryWeight -= destroyedItem.weight
        return self.name + " destroyed " + destroyedItem.name

    def modStatsBuff (self, item, addingItem):
        sign = 1
        if not addingItem:
            sign = -1

        self.health               += sign * item.healthBuff
        self.armor                += sign * item.armorBuff
        self.meleeDamage          += sign * item.meleeBuff
        self.rangedDamage         += sign * item.rangedBuff
        self.attackRange          += sign * item.rangeBuff
        self.maxCarryWeight       += sign * item.carryBuff

    def onDeath(self):
        self.home.state[self.level][self.row][self.col] = None
        return ""

    def onTurn(self):
        self.wasAlive = True
        self.foughtThisTurn = False
        return ""

    def copy(self, level, row, col):
        """Copy the Entity into the given cell"""
        retEntity = Entity(self.body, self.name, level, row, col, self.home)
        retEntity.health = self.health 
        retEntity.alive = self.alive
        retEntity.wasAlive = self.wasAlive
        retEntity.armor = self.armor
        retEntity.meleeDamage = self.meleeDamage
        retEntity.rangedDamage = self.rangedDamage
        retEntity.attackRange = self.attackRange
        retEntity.inventory = [i.copy() for i in self.inventory]
        retEntity.maxCarryWeight = self.maxCarryWeight
        retEntity.currCarryWeight = self.currCarryWeight
        retEntity.passive = self.passive
        retEntity.opaque = self.opaque

        if self.weaponEquip != None:
            retEntity.weaponEquip = self.weaponEquip.copy()
        else:
            retEntity.weaponEquip = None

        if self.armorEquip != None:
            retEntity.armorEquip = self.armorEquip.copy()
        else:
            retEntity.armorEquip = None
        return retEntity

    def getState(self):
        return ("Health: " + str(self.health) + 
                "   Armor: " + str(self.armor) +
                "   Melee attack: " + str(self.meleeDamage) +
                "   Ranged attack: " + str(self.rangedDamage) +
                "   Range: " + str(self.attackRange) +
                "   Carrying " + str(self.currCarryWeight) + "/" + str(self.maxCarryWeight))
   
    def update(self):
        pass


class MovableEntity(Entity):
    def __init__ (self, body, name, level, row, col, home, health=0, alive=True,
                    wasAlive=False, armor=0, meleeDamage=0, rangedDamage=0, 
                    attackRange=0, inventory=[], weaponEquip=None, armorEquip=None, 
                    maxCarryWeight=0, passive=False, opaque=False):
        super(MovableEntity, self).__init__(body, name, level, row, col, home,
                                                health=health, alive=alive,
                                                wasAlive=wasAlive, armor=armor,
                                                meleeDamage=meleeDamage,
                                                rangedDamage=rangedDamage,
                                                attackRange=attackRange,
                                                inventory=inventory,
                                                weaponEquip=weaponEquip,
                                                armorEquip=armorEquip,
                                                maxCarryWeight=maxCarryWeight,
                                                passive=passive, opaque=opaque)

    def move(self, direction): # 1: up, 2: down, 3: left, 4: right
        assert str(direction) in "1234"
        row = self.row
        col = self.col
        home = self.home

        if direction == 1: # Move up
            if row == 0:
                return (False, "")
            if home.state[self.level][row-1][col] != None:
                return (False, self.fight(home.state[self.level][row-1][col]))
            home.state[self.level][row-1][col] = self
            home.state[self.level][row][col] = None
            self.row -= 1
            return (True, "")

        elif direction == 2: # Move down
            if row == len(home.state[self.level]) - 2: # Not sure why 2 instead of 1
                return (False, "")
            if home.state[self.level][row+1][col] != None:
                return (False, self.fight(home.state[self.level][row+1][col]))
            home.state[self.level][row+1][col] = self
            home.state[self.level][row][col] = None
            self.row += 1
            return (True, "")

        elif direction == 3: # Move left
            if col == 0:
                return (False, "")
            if home.state[self.level][row][col-1] != None:
                return (False, self.fight(home.state[self.level][row][col-1]))
            home.state[self.level][row][col-1] = self
            home.state[self.level][row][col] = None
            self.col -= 1
            return (True, "")

        else: # Move right
            if col == len(home.state[self.level][row]) - 1:
                return(False, "")
            if home.state[self.level][row][col+1] != None:
                return (False, self.fight(home.state[self.level][row][col+1]))
            home.state[self.level][row][col+1] = self
            home.state[self.level][row][col] = None
            self.col += 1
            return (True, "")

    def copy(self, level, row, col):
        """Copy the Entity into the given cell"""
        retEntity = MovableEntity(self.body, self.name, level, row, col, self.home)
        retEntity.health = self.health 
        retEntity.alive = self.alive
        retEntity.wasAlive = self.wasAlive
        retEntity.armor = self.armor
        retEntity.meleeDamage = self.meleeDamage
        retEntity.rangedDamage = self.rangedDamage
        retEntity.attackRange = self.attackRange
        retEntity.inventory = [i.copy() for i in self.inventory]
        retEntity.maxCarryWeight = self.maxCarryWeight
        retEntity.currCarryWeight = self.currCarryWeight
        retEntity.passive = self.passive
        retEntity.opaque = self.opaque 

        if self.weaponEquip != None:
            retEntity.weaponEquip = self.weaponEquip.copy()
        else:
            retEntity.weaponEquip = None

        if self.armorEquip != None:
            retEntity.armorEquip = self.armorEquip.copy()
        else:
            retEntity.armorEquip = None
        return retEntity


## From here on are the actual entities.

# For historical and debugging purposes, OBJECTS OF THIS CLASS ARE NOT CATS
class PokeyKillBeast(MovableEntity):
    def __init__(self, body, level, row, col, home):
        assert body is '>' or body is '<'
        super(PokeyKillBeast, self).__init__(body, "PokeyKillBeast",
                                                   level, row, col, home,
                                                   meleeDamage=20, health=20)

    def onTurn(self):
        if self.foughtThisTurn:
            writeLog("Passing because fought")
            self.foughtThisTurn = False
            return ""
        self.foughtThisTurn = False
        # uncomment this next line for a fun show (play around with wasd)
        #print "\a"
        if self.body is '>':
            success, output = self.move(4)
            if not success:
                self.body = '<'
            return output

        # elif self.body is '<'
        success, output = self.move(3)
        if not success:
            self.body = '>'
        return output

    def copy(self, level, row, col):
        """Copy the Entity into the given cell"""
        retEntity = PokeyKillBeast(self.body, row, col, level, self.home)
        retEntity.health = self.health 
        retEntity.alive = self.alive
        retEntity.wasAlive = self.wasAlive
        retEntity.armor = self.armor
        retEntity.meleeDamage = self.meleeDamage
        retEntity.rangedDamage = self.rangedDamage
        retEntity.attackRange = self.attackRange
        retEntity.inventory = [i.copy() for i in self.inventory]
        retEntity.maxCarryWeight = self.maxCarryWeight
        retEntity.currCarryWeight = self.currCarryWeight
        retEntity.passive = self.passive
        retEntity.maxCarryWeight = self.maxCarryWeight

        if self.weaponEquip != None:
            retEntity.weaponEquip = self.weaponEquip.copy()
        else:
            retEntity.weaponEquip = None

        if self.armorEquip != None:
            retEntity.armorEquip = self.armorEquip.copy()
        else:
            retEntity.armorEquip = None
        return retEntity

class GenericPlayerHater(MovableEntity):
    def __init__(self, level, row, col, home):
        super(GenericPlayerHater, self).__init__('x', "Generic Player Hater", 
                                                    level, row, col, home, 
                                                    health=20, meleeDamage=20)
        self.lastSawPlayerAt = (row, col)
        self.pseudoRow = float(row)
        self.pseudoCol = float(col)

    def onTurn(self):
        if self.foughtThisTurn:
            self.foughtThisTurn = False
            return ""
        if playerVisible(self):
            self.lastSawPlayerAt = (self.home.player.row, self.home.player.col)
        self.pseudoRow, self.pseudoCol = nextUnitFromPointToPoint(self.pseudoRow, self.pseudoCol, *self.lastSawPlayerAt)
        destRow = round(self.pseudoRow)
        destCol = round(self.pseudoCol)
        message = ""
        if destRow < self.row:
            movement = self.move(1)
            if not movement[0]:
                self.pseudoRow = self.row
            message += movement[1]
        elif destRow > self.row:
            movement = self.move(2)
            if not movement[0]:
                self.pseudoRow = self.row
            message += movement[1]
        if destCol < self.col:
            movement = self.move(3)
            if not movement[0]:
                self.pseudoCol = self.col
            message += movement[1]
        elif destCol > self.col:
            movement = self.move(4)
            if not movement[0]:
                self.pseudoCol = self.col
            message += movement[1]

        if (self.row, self.col) == self.lastSawPlayerAt:
            self.pseudoRow = self.row
            self.pseudoCol = self.col
        self.foughtThisTurn = False
        return message

    def copy(self, level, row, col):
        """Copy the Entity into the given cell"""
        retEntity = GenericPlayerHater(level, row, col, self.home)
        retEntity.lastSawPlayerAt = (row, col)
        retEntity.pseudoRow = float(row)
        retEntity.pseudoCol = float(col)
        retEntity.health = self.health 
        retEntity.alive = self.alive
        retEntity.wasAlive = self.wasAlive
        retEntity.armor = self.armor
        retEntity.meleeDamage = self.meleeDamage
        retEntity.rangedDamage = self.rangedDamage
        retEntity.attackRange = self.attackRange
        retEntity.inventory = [i.copy() for i in self.inventory]
        retEntity.maxCarryWeight = self.maxCarryWeight
        retEntity.currCarryWeight = self.currCarryWeight
        retEntity.passive = self.passive
        retEntity.opaque = self.opaque 

        if self.weaponEquip != None:
            retEntity.weaponEquip = self.weaponEquip.copy()
        else:
            retEntity.weaponEquip = None

        if self.armorEquip != None:
            retEntity.armorEquip = self.armorEquip.copy()
        else:
            retEntity.armorEquip = None
        return retEntity

    def update(self):
        self.lastSawPlayerAt = (self.row, self.col)
        self.pseudoRow = self.row
        self.pseudoCol = self.col

class ItemHolder(Entity):
    def __init__(self, level, row, col, home, item):
        super(ItemHolder, self).__init__('i', item.name, level, row, col, home, passive=True)
        self.item = item

    def onBattle(self, opponent):
        if opponent.receiveItem(self.item):
            self.alive = False
            return opponent.name + " received " + self.item.name
        else:
            return self.item.name + " is too heavy for " + opponent.name + " to pick up"

    def copy(self, level, row, col):
        """Copy the Entity into the given cell"""
        retEntity = ItemHolder(level, row, col, self.home, self.item)
        retEntity.health = self.health 
        retEntity.alive = self.alive
        retEntity.wasAlive = self.wasAlive
        retEntity.armor = self.armor
        retEntity.meleeDamage = self.meleeDamage
        retEntity.rangedDamage = self.rangedDamage
        retEntity.attackRange = self.attackRange
        retEntity.inventory = [i.copy() for i in self.inventory]
        retEntity.maxCarryWeight = self.maxCarryWeight
        retEntity.currCarryWeight = self.currCarryWeight
        retEntity.passive = self.passive
        retEntity.opaque = self.opaque 

        if self.weaponEquip != None:
            retEntity.weaponEquip = self.weaponEquip.copy()
        else:
            retEntity.weaponEquip = None

        if self.armorEquip != None:
            retEntity.armorEquip = self.armorEquip.copy()
        else:
            retEntity.armorEquip = None
        return retEntity

class Stairway(Entity):
    def __init__(self, body, partnerStair, level, row, col, home):
        assert body in "^v"
        super(Stairway, self).__init__(body, "stairway", level, row, col, home, passive=True)
        self.partnerStair = partnerStair

    def onBattle(self, opponent):
        writeLog("Stairway used")
        if self.partnerStair is None:
            return "These stairs don't go anywhere. I guess you've won"
        spawnPriorityOrder = [(i, j) for i in range(self.partnerStair.row-1, self.partnerStair.row+2)
                                     for j in range(self.partnerStair.col-1, self.partnerStair.col+2)]
        shuffle(spawnPriorityOrder)
        for spawnLoc in spawnPriorityOrder:
            if self.home.state[self.partnerStair.level][spawnLoc[0]][spawnLoc[1]] is None:
                self.home.state[opponent.level][opponent.row][opponent.col] = None
                self.home.state[self.partnerStair.level][spawnLoc[0]][spawnLoc[1]] = opponent
                opponent.row, opponent.col = spawnLoc
                opponent.level = self.partnerStair.level
                opponent.update()
                return ""
        return "The stairs are blocked on the other end"

    def copy(self, level, row, col):
        """Copy the Entity into the given cell"""
        retEntity = Stairway(self.body, self.partnerStair, level, row, col, self.home)
        retEntity.health = self.health 
        retEntity.alive = self.alive
        retEntity.wasAlive = self.wasAlive
        retEntity.armor = self.armor
        retEntity.meleeDamage = self.meleeDamage
        retEntity.rangedDamage = self.rangedDamage
        retEntity.attackRange = self.attackRange
        retEntity.inventory = [i.copy() for i in self.inventory]
        retEntity.maxCarryWeight = self.maxCarryWeight
        retEntity.currCarryWeight = self.currCarryWeight
        retEntity.passive = self.passive
        retEntity.opaque = self.opaque

        if self.weaponEquip != None:
            retEntity.weaponEquip = self.weaponEquip.copy()
        else:
            retEntity.weaponEquip = None

        if self.armorEquip != None:
            retEntity.armorEquip = self.armorEquip.copy()
        else:
            retEntity.armorEquip = None
        return retEntity

class TimelessGhost(MovableEntity):
    def __init__(self, level, row, col, home, containedEntity=None):
        super(TimelessGhost, self).__init__('X', "Timeless Ghost", level,
                                                    row, col, home, passive=True)
        assert type(containedEntity) != TimelessGhost
        self.containedEntity = containedEntity

    def move(self, direction): # 1: up, 2: down, 3: left, 4: right
        assert str(direction) in "1234"
        row = self.row
        col = self.col
        home = self.home

        if direction == 1: # Move up
            if row == 0:
                return
            newContainedEntity = home.state[self.level][row-1][col]
            home.state[self.level][row-1][col] = self
            home.state[self.level][row][col] = self.containedEntity
            self.containedEntity = newContainedEntity
            self.row -= 1

        elif direction == 2: # Move down
            if row == len(home.state[self.level]) - 2: # Not sure why 2 instead of 1
                return
            newContainedEntity = home.state[self.level][row+1][col]
            home.state[self.level][row+1][col] = self
            home.state[self.level][row][col] = self.containedEntity            
            self.containedEntity = newContainedEntity
            self.row += 1

        elif direction == 3: # Move left
            if col == 0:
                return
            newContainedEntity = home.state[self.level][row][col-1]
            home.state[self.level][row][col-1] = self
            home.state[self.level][row][col] = self.containedEntity           
            self.containedEntity = newContainedEntity
            self.col -= 1

        else: # Move right
            if col == len(home.state[self.level][row]) - 1:
                return
            newContainedEntity = home.state[self.level][row][col+1]
            home.state[self.level][row][col+1] = self
            home.state[self.level][row][col] = self.containedEntity
            self.containedEntity = newContainedEntity
            self.col += 1



def nextUnitFromPointToPoint(y1, x1, y2, x2):
    # x and y dists to point 1 unit along line b/w entity and given point
    if x2 == x1 and y2 == y1:
        return (y1, x1)
    xDist = (x2 - x1)/sqrt((x2 - x1)**2 + (y2 - y1)**2)
    yDist = (y2 - y1)/sqrt((x2 - x1)**2 + (y2 - y1)**2)
    return (y1 + yDist, x1 + xDist)

def pathToPlayer(entity):
    path = []
    nextY = entity.pseudoRow
    nextX = entity.pseudoCol
    while True:
        nextY, nextX = nextUnitFromPointToPoint(nextY, nextX, entity.home.player.row, entity.home.player.col)
        path.append((int(round(nextY)), int(round(nextX))))
        if path[-1] == (entity.home.player.row, entity.home.player.col):
            return path
        
def playerVisible(entity):
    for row, col in pathToPlayer(entity):
        if entity.home.state[entity.level][row][col] != None and entity.home.state[entity.level][row][col].opaque:
            return False
    return True


genericEnemies = [PokeyKillBeast('>', -1, -1, -1, None), GenericPlayerHater(-1, -1, -1, None)]
