class Item(object):
    def __init__(self, name, weight, uses, healthBuff, armorBuff, meleeBuff, 
               			rangedBuff, rangeBuff, carryBuff, needsTarget=False):
        self.name = name
        self.weight = weight
        self.remainingUses = uses
        self.healthBuff = healthBuff
        self.armorBuff = armorBuff
        self.meleeBuff = meleeBuff
        self.rangedBuff = rangedBuff
        self.rangeBuff = rangeBuff
        self.carryBuff = carryBuff
        self.needsTarget = needsTarget

    def copy(self):
        return globals()[self.__class__.__name__](self.name, self.weight, 
                            self.remainingUses, self.healthBuff, self.armorBuff,
                            self.meleeBuff, self.rangedBuff, self.rangeBuff,
                            self.carryBuff, self.needsTarget)
    
    def used(self, entity):
        return entity.name + " tried to use " + self.name + ". Nothing happened"

class Weapon(Item):
    def __init__(self, name, weight, uses, healthBuff, armorBuff, meleeBuff, 
                 rangedBuff, rangeBuff, carryBuff, needsTarget=True, melee=True):
        super(Weapon, self).__init__(name, weight, uses, healthBuff, armorBuff,
                            meleeBuff, rangedBuff, rangeBuff, carryBuff, needsTarget)
        self.melee = melee
    
    def used(self, entity, targetRow=-1, targetCol=-1):
        if self.needsTarget and (targetRow, targetCol) == (-1, -1):
            raise Exception("Something fucked up (besides my error handling)")
        self.remainingUses -= 1
        return entity.name + " attacked a nearby rock with " + self.name


items = [ Weapon("a big rock", 50, 999, 100, 0, 999, 20, 7, 500)]

