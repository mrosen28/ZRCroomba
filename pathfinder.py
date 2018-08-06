import math
from main import *
from hwi import *
from pathfinding.core.grid import Grid
from pathfinding.finder.breadth_first import BreadthFirstFinder
from time import sleep
delay = 0
layout = [
  [1, 1, 1, 1, 1, 0, 0, 0],
  [0, 0, 0, 1, 1, 1, 1, 1],
  [1, 1, 1, 1, 1, 1, 1, 1],
  [1, 1, 1, 1, 1, 1, 1, 1],
  [0, 0, 0, 1, 1, 1, 1, 1],
  [1, 1, 1, 1, 1, 1, 1, 1],
  [1, 1, 1, 1, 1, 1, 1, 1],
  [1, 1, 1, 1, 1, 1, 1, 1],
]
grid = Grid(matrix=layout)

# returns the shelf the roomba is at / picking up items from
def getCurrShelf():
	global currY
	if currY == 1:
		return 0			#return stockroom
	if currY == 2:
		return 1 			#return shelf # 1
	if currY == 3:
		return 2		# shelf number 2

def getCurrShelfPos():
	global currX
	return currX % 5

def inCorrectSpot():
	return itemPositions[getCurrShelf()][getCurrShelfPos()] == tasks[getCurrShelf()][getCurrShelfPos()]

def putOnShelf():
	global bins
	global itemPositions
	global tasks

	item = tasks[getCurrShelf()][getCurrShelfPos()] # what we want to put on the spot

	for i in range(3):
		if bins[i] == item:
			# serially pick up item from bin[i]
			# serial put item on shelf
			itemPositions[getCurrShelf()][getCurrShelfPos()] = item
			bins[i] = False

# Fill in with Mechanical/ serial aspect of rotation, also updates currRotation in record-keeping
# same as your rotate(degrees, speed = None) except added last 2 lines
def rotateRoombaDegrees(degrees):
	degrees %= 360	 	# negative numbers become positive ( - 90 becomes 270)
	if (degrees < 1 and degrees > 0):
		degrees = 0
	if (degrees == 90):
		rotate(90)# serial commands to turn left 90
		pass
	elif (degrees == 180):
		rotate(180)
		pass
	elif (degrees == 270): 		# serial to turn right 90
		rotate(270)
		pass
	global currRotation
	currRotation = (currRotation + degrees) % 360

def faceShelf():
	if getCurrShelf() == 0 or 1:	 	#if at stockroom or shelf 1
		faceDegree(90)
	else: #getCurrShelf() == 2:			#at shelf 2
		faceDegree(270)

def faceDegree(degreeToFace): #Fix determinant sign so we can reuse the code
	bx = math.cos(math.radians( degreeToFace ))
	by = math.sin(math.radians( degreeToFace ))
	desiredVector = (bx, by)
	calculateDegreesToRotate(desiredVector, 1) # OPPOSITE SAD

# Calculates degrees to rotate and then actually makes the roomba rotate by calling rotateRoombaDegrees
# desiredVector is of degrees that we want to face (with moveOneSpot, because of direction we want to face)
def calculateDegreesToRotate(desiredVector, determinantSign): ###Fix determinant sign
	ax = math.cos(math.radians( currRotation ))
	ay = math.sin(math.radians( currRotation ))
	currOrientationVector = ( ax, ay )		#convert degrees to radians for math library. cos(theta), sin(theta)
	(bx, by) = desiredVector
	determinant = ax*by - bx*ay 	# -1, 0, or 1
	if (determinant < 1 and determinant > 0): # fix rounding
		determinant = 0
	if determinant == 0:  		#determinant of two vectors of matrices, either orientation aligned with direction of travel or not
		if desiredVector != currOrientationVector: # not aligned with direction of travel (facing 180 away from it)
			rotateRoombaDegrees(180)
	else:   								# roomba needs to turn 90 degrees in a particular direction
		rotateRoombaDegrees(determinantSign*90*determinant) 	#sign is -1 with moveOneSpot, 1 for faceDegree

# Record-keeping, decides orientation and how many degrees necessary to turn/rotate. Also claculates number of degrees to rotate
def moveOneSpot(x, y): 	#destination coordinates
	sleep(delay)
	printPos()
	global currX, currY, currRotation
	if x >= 0  and  x <= 7 and y >= 0 and y <= 7 : # make sure new spot is in bounds. There is a grid.inside(x, y) bool function, how to access grid??
		# ROTATION STUFF
		bx = x - currX  		#delta position is (bx, by)
		by = y - currY		#tuple / vector of how much to go in each direciton, either -1, 0, or 1
		deltaPosVector = (bx, by)
		calculateDegreesToRotate(deltaPosVector, -1)
 		# MOVEMENT STUFF
		currX = x 			# update where we are in record-keeping
		currY = y
		step_forward()()

def goToPosition(endX, endY): # feed it a destination coordinate
	global currX, currY
	path = findPath(currX, currY, endX, endY, 0)
	for coordinate in path[1:]:
		(x, y) = coordinate
		moveOneSpot(x, y)

def printPos(): #for debugging to see where we are
	print(grid.grid_str(start = grid.node(currX, currY)))
	print("Facing: ")
	print(currRotation)
	print(currX, currY)

#from pathfinding.core.diagonal_movement import DiagonalMovement
# 0 is path, 1 is length
def findPath(sx, sy, ex, ey, pathOrlength):
	grid = Grid(matrix=layout) # to reset the grid and remove old marks
	start = grid.node(sx, sy)
	end = grid.node(ex, ey)
	finder = BreadthFirstFinder() #finder = BreadthFirstFinder(diagonal_movement=DiagonalMovement.never)
	path, runs = finder.find_path(start, end, grid)
	# print('operations:', runs, 'path length:', len(path))
	# print(grid.grid_str(path=path, start=start, end=end))
	# print(path)
	if pathOrlength: return len(path)
	else: return path

# Serial necessary here
def goUpToShelfAndBack():
	faceShelf()
	image = approach("p") #Approach Shelf and Find Barcode
	decipherBarcode(image)
	rotateRoombaDegrees(180) #turn around
	# serial move, go back until we are back on the intersection
	# faceDegree(shelfDirectionOfTravel) MOVED SOMEWHERE ELSE

# go to the end of the destination shelf that is closest to us
# 3 variables: where we are (shelf and position), shelf we want to go to
def goToClosestEndOfDesiredShelf(desiredShelf):
	shelfY = 0;
	if desiredShelf == 0:
		shelfY = 1 				#where roomba needs to go
	elif desiredShelf == 1:
		shelfY = 2
	else:
		shelfY = 3

	shelfX = 0

	print(shelfY, getCurrShelf(), getCurrShelfPos(), desiredShelf)
	if currX == 7 and currY == 4: # reading task list at the beginning
		shelfX = 7 	# go to stock room third spot
	elif (getCurrShelfPos() == 0) and (desiredShelf == (1 or 2)) and (getCurrShelf() == 0):
		print("going to shelf1. or even shelf2 from stockroom")
		shelfX = 2
	elif (getCurrShelfPos() == 0) and (desiredShelf == (1 or 2)) and (getCurrShelf() == (1 or 2)): #at normal shelves
		print("going between shelves 1, 2[0]")
		shelfX = 0
	elif (getCurrShelfPos() == 2) and (desiredShelf == (1 or 2)) and (getCurrShelf() == (1 or 2)): # at normal shelves
		print("going between shelves 1, 2[2]")
		shelfX = 2
	# elif (desiredShelf == 1 or 2) and (getCurrShelf() == 0): # at stockroom
	# 	shelfX = 2
	elif ((getCurrShelf() == (1 or 2)) and (desiredShelf == 0)): #trying to go stockroom, always go to one spot
		print("going back to stockroom") 				# ISSUE: it's not going back to stock room/ entering this
		# while True:
		# 	try:exec(input("DEBUG: "))
		# 	except KeyboardInterrupt:break
		# 	except Exception as E:print("ERROR:"+str(E))
		shelfX = 5
	elif (getCurrShelf() ==  2 and (desiredShelf == 0) and getCurrShelfPos()==2):
		print("shelf 2, pos 2, going to stockroom")
		shelfX = 5
	goToPosition(shelfX , shelfY)

def getShelfDirectionOfTravel():
	return getCurrShelfPos() * 90 # shelf spot 0 is 0 degrees, shelf spot 2 is 180

# unlike the other moveOneSpot, this one doesn't take desitnation coordinates. instead just serially moves forward in whichever
# direction it is already facing, and updates record keeping of curr information
def moveOneForward():
	sleep(delay)
	global currX, currY
	orientation = currRotation % 360
	if orientation == 0:
		currX += 1
	elif orientation == 180:
		currX -= 1
	elif orientation == 90:
		currY -= 1
	else: #orientation == 270
		currY += 1
	printPos()
	step_forward()()

# reads all 3 barcodes/positions along a shelf
# maintains direction of travel, except after the last barcode / image
# must be at position 0 or position 2 (not the middle of the shelf) when calling this
def traverseShelf():
	global currX, currY
	shelfDirectionOfTravel = getShelfDirectionOfTravel()
	goUpToShelfAndBack()
	#print("just went to 1st shelf spot and back, facing south")
	faceDegree(shelfDirectionOfTravel)
	#print("now facing degree of travel")
	moveOneForward()
	goUpToShelfAndBack()
	#print("just went to 2nd shelf spot and back, facing south")
	#print(currX, currY,  currRotation, getCurrShelf(), getCurrShelfPos())
	faceDegree(shelfDirectionOfTravel)
	#print("face Direction of Travel")
	#print(currX, currY,  currRotation, getCurrShelf(), getCurrShelfPos())
	moveOneForward()
	goUpToShelfAndBack()
	#print("just went to 3rd shelf spot and back, facing south")
	#print(currX, currY,  currRotation, getCurrShelf(), getCurrShelfPos())

def getShelfandPosition(itemID): #get the shelf and position indices in tasks list
	l = sum(tasks, [])
	index = l.index(itemID)
	shelf = index // len(l)
	shelfPosition = index % 3
	return shelf, shelfPosition

def calculateShelfYPosition(desiredShelf): #coordinates on grid
	shelfY = 0;
	if desiredShelf == 0:
		shelfY = 0
	elif desiredShelf == 1:
		shelfY = 1
	elif desiredShelf == 2:
		shelfY = 4
	return shelfY

def calculateShelfXPosition(shelf, spot): # 0, 1, 2 in a shelf. coordinates on grid
	if shelf == 1 or shelf == 2:
		return spot
	elif shelf == 0:
		return 5 + spot

# given a shelf and shelfposition index, calculate its coordinates
def calculateShelfSpotCoordinates(desiredShelf, desiredSpot):
	return calculateShelfXPosition(desiredShelf, desiredSpot), calculateShelfYPosition(desiredShelf)

# get indices of itemID, go to that shelf
def findNextShelf():
	shelves = [0 for i in range(3)]
	for itemID in bins:
		if itemID:  # not false
			shelf, shelfPosition = getShelfandPosition(itemID)

			# l = sum(tasks, [])
			# index = l.index(itemID)
			# shelf = index // len(l)
			# shelfPosition = index % 3
			shelves[shelf] += 1

	# while True:
	# 	try:exec(input("DEBUG: "))
	# 	except Exception as E:print("ERROR:"+str(E))
	# 	except KeyboardInterrupt:break

	if shelves[2]:
		goToClosestEndOfDesiredShelf(2)
		faceDegree(180)
	elif shelves[1]:
		goToClosestEndOfDesiredShelf(1)
	elif shelves[0]:
		print("should go straight to stockroom")
		print(currX, currY)
		goToClosestEndOfDesiredShelf(0)

# Gives 0 or 1 whether we have to deposit something on a particular shelf
def getShelfPositions(shelfNo):
	shelfPositions = [0 for i in range(3)]
	for itemID in bins:
		shelf, shelfPosition = getShelfandPosition(itemID)
		if shelf == shelfNo:
			shelfPositions[shelfPosition] += 1
	return shelfPositions

#Given the Item's coordinates, move roomba to coordinates
def moveRoombaToItem(x, y):
	if getCurrShelf() == 0 or getCurrShelf == 1:
		goToPosition(x, y + 1)
	elif getCurrShelf() == 2:
		goToPosition(x, y - 1)

# go up to spot, deposit item, turn around, get back on intersection
def depositItem(shelf, position):
	x, y = calculateShelfSpotCoordinates(shelf, position)
	moveRoombaToItem(x, y)
	faceShelf()
	#move_until_bumpers()
	putOnShelf()
	rotateRoombaDegrees(180)
	# get back on intersection line

# Gives array of number of items left to deposit on each (all) shelves
def getShelves():
	shelves = [0 for i in range(3)]
	for itemID in bins:
		if itemID:  # not false
			shelf, shelfPosition = getShelfandPosition(itemID)
			shelves[shelf] += 1
	return shelves

def readTaskList():
	goToPosition(7, 4)
	rotateRoombaDegrees(270) # face east. since we start at bottom facing north, we only need to turn 90 degrees
	#Move arm to get into position to take picture?
	image = takePicUntilBarcode()
	taskListRead = decipherBarcode(image)
	if (taskListRead == 1):
		print("Task List Decoded Successfully.")
	else:
		print("Error Reading Task List!")

def start():
	# global shelfDirectionOfTravel
	# shelfDirectionOfTravel = 180
	readTaskList()
	goToClosestEndOfDesiredShelf(0) # goToStockRoom()
	print("before reading stockRoom")
	traverseShelf()
	print("before going to Shelf1")
	print(currX, currY,  currRotation, getCurrShelf(), getCurrShelfPos())
	goToClosestEndOfDesiredShelf(1)
	traverseShelf()
	print("before going to Shelf2")
	goToClosestEndOfDesiredShelf(2)
	traverseShelf() 	# ends the program after reading the last barcode

	# while True:
	# 	try:exec(input("DEBUG: "))
	# 	except KeyboardInterrupt:break
	# 	except Exception as E:print("ERROR:"+str(E))

	# # Second half allowing for optimizations
	# Im sorry Ryan I decided to do an ugly version to save time
	# if not allBinsEmpty():
	shelves = getShelves() # gets number of items per shelf left to deposit. NEW FUNCTION
	if shelves[2]:
		shelfPositions = getShelfPositions(2) # new function
		if shelfPositions[2]:
			depositItem(2, 2)
		if shelfPositions[1]:
			goToPosition(1, 3)
			depositItem(2, 1) 			# depositItem -  NEW FUNCTION
		if shelfPositions[0]:
			goToPosition(0, 3)
			depositItem(2, 0)
	if shelves[1]:
		goToClosestEndOfDesiredShelf(1)
		shelfPositions = getShelfPositions(1)
		if shelfPositions[0]:
			depositItem(1, 0)
		if shelfPositions[1]:
			goToPosition(1, 2) 		# might not need goToPosition since in depositItem there is "moveRoombaToItem"
			depositItem(1, 1)
		if shelfPositions[2]:
			goToPosition(2, 2)
			depositItem(2, 1)
	if shelves[0]:
		goToClosestEndOfDesiredShelf(0)
		shelfPositions = getShelfPositions(0)
		if shelfPositions[0]:
			depositItem(0, 0)
		if shelfPositions[1]:
			goToPosition(5, 1)
			depositItem(0, 1)
		if shelfPositions[2]:
			goToPosition(6, 1)
			depositItem(0, 2)

	goToPosition(6, 7) # put this inside findNextShelf() ?? if bins empty
	printPos()

# From top to bottom:
# Stockroom: Spots 0, 1, 2
# Shelf one: Spots 0, 1, 2
# Shelf two: Spots 0, 1, 2
itemPositions = [ [0, 0, 0] for i in range(3)]
shelfDirectionOfTravel = 0

currX = 7
currY = 7
currRotation = 0	 # 0 = facing east, 90 = facing north, 180 = facing west, 270 = facing south (-90) <-- BUT would be better to turn left 90
start()
