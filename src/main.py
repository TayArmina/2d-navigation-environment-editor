from pathlib import Path

import PyQt6.QtCore
from PyQt6.QtWidgets import *
from PyQt6.QtWidgets import QApplication,QWidget,QPushButton,QMainWindow,QLineEdit,QLabel,QVBoxLayout,QMenu,QHBoxLayout,QGridLayout,QStackedLayout,QScrollArea,QGroupBox,QSlider,QTabWidget,QAbstractSpinBox,QDialog,QDialogButtonBox,QMessageBox
from PyQt6.QtCore import QSize,QSizeF,Qt,QRectF,QPointF,QLineF,pyqtSignal,QTimer,QAbstractListModel
from PyQt6.QtGui import QPixmap,QAction,QPainter,QColor,QTransform
import sys
import PyQt6
from PyQt6.QtWidgets import ( QApplication, QCheckBox, QComboBox, QDateEdit, QDateTimeEdit, QDial, QDoubleSpinBox, QFontComboBox, QLabel, QLCDNumber, QLineEdit, QMainWindow, QProgressBar, QPushButton, QRadioButton, QSlider, QSpinBox, QTimeEdit, QVBoxLayout, QWidget)
import json
import PyQt6.QtWidgets

title = "2D Navigation Environment Editor"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
path = str(PROJECT_ROOT / "config") + "/"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.model = Model() #contains list of obstacles
        self.model.obstAddedEvent.connect(self.obstCreated) #when an obstacle is created on the canvas, a corresponding menu is created
        self.model.goalAddedEvent.connect(self.goalCreated) #when a goal is created on the canvas, a corresponding menu is created
        self.setWindowTitle(title)
        self.setGeometry(0,0,1100,410) #initial size of window, change later
        self.setCentralWidget(self.initWidgetLayot()) #call function to generate the initial window layout
        
    def initWidgetLayot(self): #generate central widget layout
        mainLayout = QHBoxLayout()
        mainLayout.setContentsMargins(0,0,0,0) #makes sure the coordinates of a mouseclick align with the coordinates of the canvas
        
        leftSideLayout = QVBoxLayout()
        leftSideLayout.setContentsMargins(0,0,0,0) #makes sure the coordinates of a mouseclick align with the coordinates of the canvas
        leftSideLayout.addWidget(self.initPicture()) #initialize the widget where the obstacles will be drawn
        leftSideLayout.addWidget(self.initDocumentMenu()) #add the menu under the canvas
        leftSide = QWidget()
        leftSide.setLayout(leftSideLayout)

        rightSide = QTabWidget()
        rightSide.addTab(self.initObstacleMenu(),"Obstacle Menu") #creates a layout and widget that will hold the menu, once its generated
        '''placeholder tab'''
        rightSide.addTab(self.initPlaceHolderMenu(),"placeholder tab") #add the second tab, currently placeholder
        mainLayout.addWidget(leftSide)
        mainLayout.addWidget(rightSide) 
        mainWidget = QWidget()
        mainWidget.setLayout(mainLayout)

        return mainWidget
        
    def initPicture(self): #initialize the widget where the obstacles will be drawn
        self.pictureWidget = ObstacleCanvas(self.model) #the ObstacleCanvas shows the graphical representation
        return self.pictureWidget
    
    def initDocumentMenu(self):
        documentMenu = DocumentMenu(self.model)
        documentMenu.endProgrammEvent.connect(self.endProgramm)
        return documentMenu

    def initObstacleMenu(self): #creates a layout and widget that will hold the menu, once its generated
        self.obstMenuLayout = QVBoxLayout()
        
        obstMenuWidget = QWidget()
        obstMenuWidget.setLayout(self.obstMenuLayout)
        return obstMenuWidget
    
    def initPlaceHolderMenu(self): #creates a layout and widget that will hold the menu, once its generated
        '''initPlaceHolderMenu'''
        self.placeHolderMenuLayout = QVBoxLayout()
        obstMenuWidget = QWidget()
        obstMenuWidget.setLayout(self.placeHolderMenuLayout)
        return obstMenuWidget
        
    # Menu management
    
    def obstCreated(self, obstIndex,active): #is called when a new obstacle is created by clicking on the canvas
        assert type(obstIndex) == int
        obstacleMenuItem = ObstacleMenuItem(self.model,obstIndex) #creates a new menu for the new obst
        obstacleMenuItem.setMaximumSize(1440,250)
        obstacleMenuItem.setMinimumSize(500,250)
        obstacleMenuItem.selfDestroyEvent.connect(lambda index:self.removeWidgetFromObstMenu(obstacleMenuItem)) #removes the menu on the right when an obstacle is deleted
        self.addWidgetToObstMenu(obstacleMenuItem) #adds it to the layout
        ''' TmazeMenuItem'''
        if obstIndex == 1:
            tmazeMenuItem = TmazeMenuItem(self.model,obstIndex) #creates a new menu for the new obst
            tmazeMenuItem.selfDestroyEvent.connect(lambda index:self.removeWidgetFromObstMenu(tmazeMenuItem)) #removes the menu on the right when an obstacle is deleted
            self.addWidgetToObstMenu2(tmazeMenuItem) #adds it to the layout

    def goalCreated(self):
        goalMenuItem = GoalMenuItem(self.model)
        goalMenuItem.setMaximumSize(1440,300)
        goalMenuItem.setMinimumSize(500,300)
        goalMenuItem.selfDestroyEvent.connect(lambda index:self.removeWidgetFromObstMenu(goalMenuItem)) #removes the menu on the right when an obstacle is deleted
        self.obstMenuLayout.insertWidget(0,goalMenuItem)
 
    def addWidgetToObstMenu(self,widget): #adds a new obstMenuItem to the menu layout

        assert type(widget)== ObstacleMenuItem #makes sure only valid widgets are added
        self.obstMenuLayout.addWidget(widget)    
        
        
    def addWidgetToObstMenu2(self,widget): #adds a new obstMenuItem to the menu layout
        assert type(widget)== TmazeMenuItem #makes sure only valid widgets are added
        self.placeHolderMenuLayout.addWidget(widget)    
    def removeWidgetFromObstMenu(self,widget): #removes the specified obstacleMenuItem from the layout on the right side
       self.obstMenuLayout.removeWidget(widget)

    def endProgramm(self):
        self.close()


class Model(QAbstractListModel): #holds list of obstacles
    obstAddedEvent = pyqtSignal(int,bool) #this event can be emitted to inform the canvas and main window of a new obstacle
    dataChangedEvent = pyqtSignal(int) #this event can be emitted to inform the canvas that the data has changed and it should redraw
    obstRemovedEvent = pyqtSignal(int) #this event can be emitted to inform the ObstacleMenuItem that it should delete itself

    goalAddedEvent = pyqtSignal()
    goalRemovedEvent = pyqtSignal()

    sizeChangedEvent = pyqtSignal(QSizeF)

    def __init__(self):
        super().__init__()
        self.modelSize = QSizeF(100,100) #determines the coordinate system of the model, should be changed dynamically later        
        self.createObstLists() #create the lists where the data is stored
        # self.tMaze()
    def createObstLists(self): #create the lists where the data is stored
        self.obstacles = {"flag":False,"centers":[],"vert_lengths":[],"horiz_lengths":[]} #data structure similar to the one in the json files
        self.drawableObstList = [] #list of obstacles as QRectF that can be drawn by the ObstacleCanvas. It should contain the same as self.obstacles at all times
        self.highlightList = [] #list of obstacles that should be highlighted
        self.openfield =  {"ymax_position": self.modelSize.height()/2, "xmax_position": self.modelSize.width()/2, "ymin_position": -self.modelSize.height()/2, "xmin_position": -self.modelSize.width()/2}

        self.goal = None
        self.drawableGoal = None
    
    '''tMaze'''
    def tMaze(self):
        self.addObst(10,10,10,10)
        self.addObst(-10,-10,10,10)
    # Manage openfield parameters
    
    def setModelSize(self,width,height):
        self.removeAll()
        self.modelSize = QSizeF(width,height)
        self.openfield["ymax_position"] = self.modelSize.height()/2
        self.openfield["xmax_position"] = self.modelSize.width()/2
        self.openfield["ymin_position"] = -self.modelSize.height()/2
        self.openfield["xmin_position"] = -self.modelSize.width()/2
        self.sizeChangedEvent.emit(self.modelSize)

    def getModelSize(self):
        return self.modelSize
    

    # Manage obstacles


    def addObst(self,xCenter,yCenter,width,height): #adds a new obstacle to both lists
        assert len(self.obstacles["centers"]) == len(self.obstacles["vert_lengths"]) == len(self.obstacles["horiz_lengths"]) == len(self.drawableObstList)
        #makes sure all lists have the same length
        if len(self.drawableObstList)==0:
            xCenter,yCenter = (self.modelSize.width()-width)/2 ,-((self.modelSize.height()-height)/2)
        elif len(self.drawableObstList)==1:
            xCenter,yCenter = -((self.modelSize.width()-width)/2) ,-((self.modelSize.height()-height)/2)

        #add the obstacle information to the lists
        self.obstacles["centers"].append([xCenter,yCenter])
        self.obstacles["horiz_lengths"].append(width)
        self.obstacles["vert_lengths"].append(height)
        #create an easily drawable obstacle and store it in a lists
        rectCorner = QPointF(xCenter-width/2,yCenter-height/2) #determines the position of the upper left corner
        self.drawableObstList.append(QRectF(rectCorner,QSizeF(width,height))) #creates the drawable rectangle
        self.highlightList.append(False) #obstacles are not highlighted by default
        index = len(self.drawableObstList)-1
        self.obstAddedEvent.emit(index,True) #infrom the MainWindow and ObstacleCanvas, that a new obstacle has been created
        return index #returns the index of the new obstacle
    
            
    def moveObst(self,index,xCenter=None,yCenter=None,width=None,height=None): #moves the specified obstacle to the specified coordinate
        if xCenter == None: xCenter = self.obstacles["centers"][index][0]       # for all coordinates that were not specified, 
        if yCenter == None: yCenter = self.obstacles["centers"][index][1]       # it is assumed they stay the same
        if width == None: width = self.obstacles["horiz_lengths"][index]          # they are set to their previous value
        if height == None: height = self.obstacles["vert_lengths"][index]       

        self.obstacles["centers"][index] = [xCenter,yCenter] #updates the saved values
        self.obstacles["horiz_lengths"][index] = width
        self.obstacles["vert_lengths"][index] = height

        self.drawableObstList[index].setWidth(width)
        self.drawableObstList[index].setHeight(height)
        self.drawableObstList[index].moveCenter(QPointF(xCenter,yCenter)) #updates the drawable list

        self.dataChangedEvent.emit(index) #inform the ObstacleCanvas of the change in data

    def removeObst(self,index):
        #makes sure all lists have the same length
        assert len(self.obstacles["centers"]) == len(self.obstacles["vert_lengths"]) == len(self.obstacles["horiz_lengths"]) == len(self.drawableObstList)
        
        #remove the obstacle information from the lists
        self.obstacles["centers"].pop(index)
        self.obstacles["vert_lengths"].pop(index)
        self.obstacles["horiz_lengths"].pop(index)

        self.drawableObstList.pop(index)

        self.highlightList.pop(index)
        
        self.obstRemovedEvent.emit(index) #infrom the ObstacleMenuItem and ObstacleCanvas, that an obstacle has been removed

    def removeAll(self): #removes all obstacles
        self.createObstLists()
        self.obstRemovedEvent.emit(-1)

    def getDrawableObst(self,index):
        if type(index)== str:
            return self.getDrawableGoal()[0]
        else:
            return self.drawableObstList[index]
    
    def getDrawableObstList(self):
        return self.drawableObstList

    def highlight(self,index,highlighted): #changes wether or not the obstacle at the given index is highlighted
        self.highlightList[index] = highlighted
        self.dataChangedEvent.emit(index) #inform the ObstacleCanvas of the change in data

    def getHighlightList(self): #returns the list of booleans that indicates, which obstacles are highlighted
        return self.highlightList


    # Manage the goal

    def addGoal(self,shape,x,y,size1,size2):
        if self.drawableGoal:
            self.dataChangedEvent.emit(-1)
            notPossibleMessage = QMessageBox()
            notPossibleMessage.setWindowTitle("Only one goal allowed!")
            notPossibleMessage.setText("There already is a goal")
            notPossibleMessage.exec()
            return
        
        self.goal = {"goal_shape":[shape],"goal_size1":[size1],"goal_size2":[size2],"goal_x":[x],"goal_y":[y]}

        self.drawableGoal = QRectF(QPointF(0,0),QSizeF(size1,size2)) #creates the drawable rectangle
        self.updateDrawableGoal()
        self.goalAddedEvent.emit()

    def removeGoal(self):
        self.goal = None
        self.drawableGoal = None
        self.goalRemovedEvent.emit()

    def moveGoal(self,xCenter=None,yCenter=None,width=None,height=None):
        if xCenter == None: xCenter = self.goal["goal_x"][0]      # for all coordinates that were not specified, 
        if yCenter == None: yCenter = self.goal["goal_y"][0]       # it is assumed they stay the same
        if width == None: width = self.goal["goal_size1"][0]          # they are set to their previous value
        if height == None: height = self.goal["goal_size2"][0]       
        if abs(xCenter)+width<= 100:
            self.goal["goal_x"] = [xCenter]
            self.goal["goal_size1"] = [width]
        if abs(yCenter*2)+height <= 100:
            self.goal["goal_y"] = [yCenter]
            self.goal["goal_size2"] = [height]

        self.updateDrawableGoal()

        self.dataChangedEvent.emit(-1) #inform the ObstacleCanvas of the change in data

    def setGoalShape(self,shape):
        self.goal["goal_shape"] = [shape]
        self.updateDrawableGoal()
        self.dataChangedEvent.emit(-1)

    def updateDrawableGoal(self):
        self.updateDrawableGoalSides()
        self.updateDrawableGoalCenter()

    def updateDrawableGoalCenter(self):
        xCenter = self.goal["goal_x"][0]
        yCenter = self.goal["goal_y"][0]
        self.drawableGoal.moveCenter(QPointF(xCenter,yCenter)) #updates the drawable goal

    def updateDrawableGoalSides(self):
        if self.goal["goal_shape"][0] == "round":
            self.drawableGoal.setWidth(self.goal["goal_size1"][0])
            self.drawableGoal.setHeight(self.goal["goal_size1"][0])
        else:
            self.drawableGoal.setWidth(self.goal["goal_size1"][0])
            self.drawableGoal.setHeight(self.goal["goal_size2"][0])    
    
    def getDrawableGoal(self):
        if self.drawableGoal:
            return (self.drawableGoal,self.goal["goal_shape"])
        else:
            return False
    

    # Save and Load

    def loadJSON(self,path): #deletes all previous data and loads the data from the specified JSON file
        self.removeAll()

        env_params, sim_params = self.loadDocs(path)

        xmax = env_params["environment"]["openfield"]["xmax_position"]
        ymax = env_params["environment"]["openfield"]["ymax_position"]
        self.setModelSize(xmax*2,ymax*2)

        if sim_params["trial_params"]["goal_shape"]:
            trial_params = sim_params["trial_params"]
            self.addGoal(trial_params["goal_shape"][0],trial_params["goal_x"][0],trial_params["goal_y"][0],trial_params["goal_size1"][0],trial_params["goal_size2"][0])

        for index,center in enumerate(env_params["environment"]["obstacles"]["centers"]): #adds all objects specified in the JSON file
            width = env_params["environment"]["obstacles"]["horiz_lengths"][index]
            height = env_params["environment"]["obstacles"]["vert_lengths"][index]
            newObstIndex = self.addObst(center[0],center[1],width,height)
            self.dataChangedEvent.emit(newObstIndex)


    def saveJSON(self,path):
        env_params, sim_params = self.loadDocs(path)

        env_params["environment"]["openfield"] = self.openfield

        env_params["environment"]["obstacles"] = self.obstacles

        if self.goal:
            for key in self.goal.keys():
                
                sim_params["trial_params"][key] = self.goal[key]


        self.saveDocs(path,env_params,sim_params)

    def loadDocs(self,path):
        with open(path+"env_params.json","r") as json_file:
            env_params = json.load(json_file)

        with open(path+"sim_params.json","r") as json_file:
            sim_params = json.load(json_file)

        return env_params,sim_params
    
    def saveDocs(self,path,env_params,sim_params):
        with open(path+"env_params.json","w") as json_file:
            json.dump(env_params,json_file,indent=2)

        with open(path+"sim_params.json","w") as json_file:
            json.dump(sim_params,json_file,indent=2)

    
class ObstacleCanvas(QLabel): #draws the obstacles and makes them visible
    def __init__(self,model):
        super().__init__()

        self.model = model #reference to the model that it will draw
        #whenever the unerlying data is changed, a redraw is triggered
        self.model.dataChangedEvent.connect(self.reDraw)
        self.model.obstRemovedEvent.connect(self.reDraw)
        self.model.obstAddedEvent.connect(self.reDraw)
        self.model.goalAddedEvent.connect(self.reDraw)
        self.model.goalRemovedEvent.connect(self.reDraw)
        self.model.sizeChangedEvent.connect(self.modelSizeChanged)

        self.pixmapSize = QSize(600,400) #TODO should be changed dynamically later
        self.createTransform(self.model.getModelSize()) #transform the model coordinates to canvas coordinates
        canvas = QPixmap(self.pixmapSize) #creates a QPixmap of the specified size
        canvas.fill(Qt.GlobalColor.white) #makes the canvas white
        self.setPixmap(canvas) #makes the widget display the canvas QPixmap

        self.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.reDraw()


    # Manage changes to the openfield

    def modelSizeChanged(self,newSize):
        self.createTransform(newSize)
        self.reDraw()

    def createTransform(self,modelSize): #transform the model coordinates to canvas coordinates
        self.transformToCanvas = QTransform()
        self.transformToCanvas.translate(self.pixmapSize.width()/2,self.pixmapSize.height()/2) #place (0,0) in the middle of the canvas

        #widthFactor = self.pixmapSize.width()/modelSize.width() 
        #heightFactor = -self.pixmapSize.height()/modelSize.height() #negative to make up positive and down negative
        self.pixmapSize.scaled
        maxSize = modelSize.scaled(QSizeF(self.pixmapSize),Qt.AspectRatioMode.KeepAspectRatio)
        widthFactor = maxSize.width()/modelSize.width()
        heightFactor = maxSize.height()/modelSize.height()

        self.transformToCanvas.scale(widthFactor,-heightFactor) 

        self.transformToModel,invertible = self.transformToCanvas.inverted() #inverted transform transforms canvas coords to model coords
        assert invertible


    # Drawing functions

    def reDraw(self): #redraws the canvas and all obstacles
        canvas = QPixmap(self.pixmapSize) #creates a new canvas
        canvas.fill(Qt.GlobalColor.white)
        painter = QPainter(canvas)
        highlightList = self.model.getHighlightList()
        for index,obst in enumerate(self.model.getDrawableObstList()): #iterates through obstacles and draws them
            self.drawObst(obst,painter,"rect",highlightList[index])

        goal = self.model.getDrawableGoal()
        if goal:
            painter.setPen(QColor(255,0,0))
            self.drawObst(goal[0],painter,goal[1][0],False)

        self.drawPerimeter(painter)
        
        painter.end()
        self.setPixmap(canvas) #sets the updated canvas

    def drawObst(self,obst,painter,shape,highlighted): #draws the given obst to the canvas
        if highlighted: #if the obsacle is highlighted, it is drawn in green
            painter.setPen(QColor(0,255,0))

        if shape == "rect":
            transformedObst = self.transformToCanvas.mapRect(obst) #transforms the model coordinates to canvas coords
            painter.drawRect(transformedObst)
        elif shape == "round":
            circle = obst.adjusted(0,0,0,0)
            transformedObst = self.transformToCanvas.mapRect(circle) #transforms the model coordinates to canvas coords
            painter.drawEllipse(transformedObst)
        elif shape == "line" :
            transformedObst = self.transformToCanvas.map(obst)
            painter.drawLine(transformedObst)
        
        painter.setPen(QColor(0,0,0))

    def drawPerimeter(self,painter):
        perimeter = QRectF(QPointF(0,0),self.model.getModelSize())
        perimeter.moveCenter(QPointF(0,0))
        painter.setPen(QColor(120,120,120))
        self.drawObst(perimeter,painter,"rect",False)

    def addTempDrawing(self,obst): #draws something to the canvas that will be removed on the next redraw
        canvas = self.pixmap() #gets the current canvas
        painter = QPainter(canvas)
        self.drawObst(obst,painter,"line",False)
        painter.end()
        self.setPixmap(canvas) #sets the updated canvas
    
    def drawFirstClickMarker(self,point): #draws a cross at the firstClickPoint
        width = self.model.getModelSize().width()/50
        height = width
        self.addTempDrawing(QLineF(point.x()-width,point.y(),point.x()+width,point.y()))
        self.addTempDrawing(QLineF(point.x(),point.y()-height,point.x(),point.y()+height))

    
    # Handle mouse clicks on the canvas

    def mousePressEvent(self, ev): #triggered by clicking the canvas
        self.firstClickPoint = self.transformToModel.map(QPointF(ev.pos())) #saves the click position
        if ev.button()==Qt.MouseButton.LeftButton:
         self.firstClickSide="Left"
        else:
         self.firstClickSide="Right"   
        self.drawFirstClickMarker(self.firstClickPoint) #draws a cross at the firstClickPoint
        return super().mousePressEvent(ev)
    
    def mouseReleaseEvent(self, ev):
        if self.firstClickPoint == None:
            return
        
        releasePoint = self.transformToModel.map(QPointF(ev.pos())) #saves the mouse position where the button was released
        if self.firstClickPoint == releasePoint: #if the mouse did not move, no rectangle is created
            self.reDraw()
            return
        
        width = releasePoint.x()-self.firstClickPoint.x() #determine obst size from click positions 
        height = releasePoint.y()-self.firstClickPoint.y()
        xCenter = self.firstClickPoint.x()+width/2
        yCenter = self.firstClickPoint.y()+height/2
        width = abs(width) #width and height can not be negative
        height = abs(height)

        if self.firstClickSide == "Left":
            self.model.addObst(xCenter,yCenter,width,height) #calls function to create obst
        else:
            self.model.addGoal("round",xCenter,yCenter,width,height)

        self.firstClickPoint = None #resets the first click position
        self.firstClickSide = None
        return super().mouseReleaseEvent(ev) #passes the eventhandling on
    

class ObstacleMenuItem(QGroupBox): #contains the UI to change the obstacle it is associated with
    selfDestroyEvent = pyqtSignal(int)
    def __init__(self, model, obstIndex): #is executed whenever an obstacle is created. creates a menu for the specific obstacle
        super().__init__()
        self.obstIndex = obstIndex #the index of the obstacle this menu is associated with
        self.model = model #a reference to the model that saves the object information
        self.model.obstRemovedEvent.connect(self.selfDestroyChecker)
        self.obstData = self.model.getDrawableObst(obstIndex) #get obstacle data from the model
        self.maxValues = [self.model.getModelSize().width()/2,self.model.getModelSize().height()/2] #make sure the obstacles can't leave the canvas
        obstMenuLayout = QVBoxLayout()
        
        obstMenuLayout.addWidget(self.initButtons())
        obstMenuLayout.addWidget(self.initSpinBox(obstIndex)) #adds boxes that allow user to change object position and size
        obstMenuLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.setLayout(obstMenuLayout)
        self.obstMenuLayout = obstMenuLayout

    def initButtons(self):
        buttonLayout = QHBoxLayout()
        deleteButton = QPushButton("Delete")
        deleteButton.clicked.connect(self.deleteObst)
        highlightButton = QPushButton("highlight")
        highlightButton.setCheckable(True)
        highlightButton.toggled.connect(self.highlight)

        buttonLayout.addWidget(deleteButton)
        buttonLayout.addWidget(highlightButton)
        buttonWidget = QWidget()
        buttonWidget.setLayout(buttonLayout)
        return buttonWidget
        
    def initSpinBox(self,obstIndex): #Initialize the Spinboxes that allow changing an objects position and size
        obstData = self.model.getDrawableObst(obstIndex) #get obstacle data from the model
        if abs(obstData.center().x()*2)+self.obstData.width() <= 100:
            # maxValues = [(self.model.getModelSize().width()-obstData.width())/2,(self.model.getModelSize().height()-obstData.height())/2] #make sure the obstacles can't leave the canvas
            maxDimensions = [self.model.getModelSize().width(),self.model.getModelSize().height()] #make sure the obstacle can't be larger than the canvas

            
            #add the spinboxes to the layout
            spinBoxLayout = QHBoxLayout()
        
            #creates the spinbox for the obstacles X-coordinate
            spinBoxLayout.addWidget(self.createSpinbox("X-Coordinate", -self.maxValues[0], self.maxValues[0], obstData.center().x(), self.moveObstX))
            #creates the spinbox for the obstacles Y-coordinate
            spinBoxLayout.addWidget(self.createSpinbox("Y-Coordinate", -self.maxValues[1], self.maxValues[1], obstData.center().y(), self.moveObstY))
            #creates the spinbox for the obstacles Width
            spinBoxLayout.addWidget(self.createSpinbox("width", 0, maxDimensions[0], obstData.width(), self.moveObstWidth))
            #creates the spinbox for the obstacles Height
            spinBoxLayout.addWidget(self.createSpinbox("height", 0, maxDimensions[1], obstData.height(), self.moveObstHeight))
            
            spinBoxLayout.setAlignment(Qt.AlignmentFlag.AlignRight)
            spinBoxLayout.addSpacing(3)
            # spinBoxLayout
            
            spinBoxHolderWidget = QWidget()
            spinBoxHolderWidget.setLayout(spinBoxLayout)

            return spinBoxHolderWidget
        else: 
            return 
    
    def createSpinbox(self,labelText,minValue,maxValue,initVal,callback):
        layout = QVBoxLayout()
        # layout.minimumHeightForWidth(250)
        spinBoxlabel = QLabel(labelText)
        
        
        spinBox = QDoubleSpinBox()
        
        spinBox.setMinimum(minValue)
        spinBox.setMaximum(maxValue)
        spinBox.setValue(initVal) #sets the starting value to the value in the model
        spinBox.valueChanged.connect(callback) #changing the value of the spinBox also changes the position of the obst accordingly
        if labelText in ['height','Y-Coordinate']:
            slider = QSlider(Qt.Orientation.Vertical, self)   # adjust a slider named zoom-slider
            slider.setTickPosition(QSlider.TickPosition.TicksLeft)    # adjust ticks below the slider line
        else:
            slider = QSlider(Qt.Orientation.Horizontal, self)   # adjust a slider named zoom-slider
            slider.setTickPosition(QSlider.TickPosition.TicksBelow)    # adjust ticks below the slider line
        slider.setMinimum(int(minValue*100))
        slider.setMaximum(int(maxValue*100))
        slider.setValue(int(initVal*100))                           # Initial value corresponding to 20% canvas size
        slider.setTickInterval(int((maxValue-minValue)*50))                                 # the distance between each tick
        slider.sliderMoved.connect(lambda value: spinBox.setValue(value/100))           # connect the slider to a the function zoomObst
        spinBox.valueChanged.connect(lambda value: slider.setValue(int(value*100)))
        # if labelText not in ['height','Y-Coordinate']:
        layout.addWidget(spinBoxlabel)
        layout.addStretch(10) 
        layout.addWidget(slider)
        layout.addStretch(10) 
        layout.addWidget(spinBox)
        # layout.addStretch(10)
        holderWidget = QWidget()
        holderWidget.setLayout(layout)

        if callback == self.moveObstHeight:
            self.heightSpinBox = spinBox
            self.heightSlider = slider

        return holderWidget
        
    # def changeMaX
    # Make changes to the obstacle
    ''' changed '''
    def moveObstX(self,newX): #move the obst to the new coordinate and redaw the canvas
        if abs(newX*2)+self.obstData.width() <= 100:
            self.model.moveObst(self.obstIndex,xCenter=newX)

    def moveObstY(self,newY): #move the obst to the new coordinate and redaw the canvas
        if abs(newY*2)+self.obstData.height() <= 100:
            self.model.moveObst(self.obstIndex,yCenter=newY)
        
    def moveObstWidth(self,newW): #move the obst to the new widht and redaw the canvas
        if abs(self.obstData.center().x())+(self.obstData.width()/2) >= 50:
            if self.obstData.center().x()<0:
                self.model.moveObst(self.obstIndex,xCenter=self.obstData.center().x()+1)
            else:
                self.model.moveObst(self.obstIndex,xCenter=self.obstData.center().x()-1)
        self.model.moveObst(self.obstIndex,width=newW)

    def moveObstHeight(self,newH): #move the obst to the new height and redaw the canvas
        if abs(self.obstData.center().y())+(self.obstData.height()/2) >= 50:
            if self.obstData.center().y()<0:
                self.model.moveObst(self.obstIndex,yCenter=self.obstData.center().y()+1)
            else:
                self.model.moveObst(self.obstIndex,yCenter=self.obstData.center().y()-1)
        self.model.moveObst(self.obstIndex,height=newH)

    def highlight(self,highlighted):
        self.model.highlight(self.obstIndex,highlighted)

    def deleteObst(self):
        self.model.removeObst(self.obstIndex)


    # Handle signals

    def selfDestroyChecker(self,index): #checks if the index of the detroyed obstacle mathces its own. -1 signifies the destruction of all obstacles
        if index == self.obstIndex or index == -1: self.selfDestroy()
        elif index < self.obstIndex: self.obstIndex -= 1 #if an obstacle with a lower index is removed, everything behind it has its index shifted

    def selfDestroy(self):
        self.selfDestroyEvent.emit(self.obstIndex)
        self.deleteLater()

class GoalMenuItem(ObstacleMenuItem):
    def __init__(self, model):
        super().__init__(model, "goal")
        self.obstMenuLayout.insertWidget(1,self.initRadioButtons())
        self.model.goalRemovedEvent.connect(self.selfDestroy)

    def initRadioButtons(self): #creates radio Buttons to select shape of the goal

        radioButton1 = QRadioButton()
        radioButton1.clicked.connect(lambda x:self.model.setGoalShape("round")) 
        radioButton1.setChecked(True)
        self.toggleHeightSpinbox(False)

        button1label = QLabel("Round")

        radioButton2 = QRadioButton() 
        radioButton2.toggled.connect(self.toggleHeightSpinbox)
        radioButton2.clicked.connect(lambda x:self.model.setGoalShape("rect")) 

        button2label = QLabel("Rectangle")

        radioBLayout = QHBoxLayout()
        radioBLayout.addWidget(radioButton1)
        radioBLayout.addWidget(button1label)
        radioBLayout.addWidget(radioButton2)
        radioBLayout.addWidget(button2label)
        radioBWidget = QWidget()
        radioBWidget.setLayout(radioBLayout)
        radioBLayout.setAlignment(Qt.AlignmentFlag.AlignRight)

        return radioBWidget
    

    # Make changes to the goal
    
    def moveObstX(self,newX): #move the obst to the new coordinate and redaw the canvas
        self.model.moveGoal(xCenter=newX)

    def moveObstY(self,newY): #move the obst to the new coordinate and redaw the canvas
        self.model.moveGoal(yCenter=newY)

    def moveObstWidth(self,newW): #move the obst to the new widht and redaw the canvas
        self.model.moveGoal(width=newW)

    def moveObstHeight(self,newH): #move the obst to the new height and redaw the canvas
        self.model.moveGoal(height=newH)

    def highlight(self, highlighted):
        pass


    # Handle signals

    def toggleHeightSpinbox(self,state):
        self.heightSpinBox.setEnabled(state)
        self.heightSlider.setEnabled(state)

    def selfDestroyChecker(self, index):
        if index == -1: self.selfDestroy()

    def deleteObst(self):
        self.model.removeGoal()



class DocumentMenu(QGroupBox): #the button menu below the canvas
    endProgrammEvent = pyqtSignal()
    def __init__(self,model):
        super().__init__()
        self.model = model

        layout = QGridLayout()
        layout.addWidget(self.initAddObstButton(),0,0)
        layout.addWidget(self.initGoalButton(),0,1)
        layout.addWidget(self.initSaveButton(),1,0)
        layout.addWidget(self.initLoadButton(),1,1)
        layout.addWidget(self.initExitButton(),2,0)
        layout.addWidget(self.initModelSizeButton(),2,1)
        self.setLayout(layout)

    def initAddObstButton(self):
        addObstButton = QPushButton("Add obstacle")
        addObstButton.clicked.connect(self.addObst)
        
        return addObstButton
    
    def initGoalButton(self):
        addGoalButton = QPushButton("Add target")
        addGoalButton.clicked.connect(self.addGoal)

        return addGoalButton

    def initSaveButton(self):
        saveButton = QPushButton("save")
        saveButton.clicked.connect(self.save)

        return saveButton
    
    def initLoadButton(self):
        loadButton = QPushButton("load")
        loadButton.clicked.connect(self.load)

        return loadButton
    
    def initExitButton(self):
        exitButton = QPushButton("exit")
        exitButton.clicked.connect(self.exit)

        return exitButton
    
    def initModelSizeButton(self):
        popUp = ChangeModelSizePopup(self.model)

        ModelSizeButton = QPushButton("change model size")
        ModelSizeButton.clicked.connect(lambda x:popUp.exec())
        return ModelSizeButton
    

    # Functions called by the buttons
    
    def addObst(self):
        if len(self.model.obstacles['centers']) <= 1:
            # self.model.tMaze()
            self.model.addObst(1,1,10,10)
        else:
            
            height = self.model.modelSize.height()/10
            width = self.model.modelSize.width()/10
            size_of_obstacles_list = len(self.model.obstacles['centers'])-2
            
            if height*width >= size_of_obstacles_list:
                    y=45-((size_of_obstacles_list//width)*10)
                    x=-45+((size_of_obstacles_list%width)*10)
                    self.model.addObst(x,y,10,10)
            

    def addGoal(self):
        self.model.addGoal("round", 0, 0, 5, 5)
        
    def save(self):
        self.model.saveJSON(path)

    def load(self):
        self.model.loadJSON(path)

    def exit(self):
        self.endProgrammEvent.emit()


class ChangeModelSizePopup(QDialog):
    def __init__(self,model):
        super().__init__()
        self.setWindowTitle("Change Model Size")
        self.model = model
        layout = QGridLayout()
        layout.addWidget(QLabel("width"),0,0)
        layout.addWidget(QLabel("height"),0,1)

        self.widthBox = QDoubleSpinBox()
        self.widthBox.setMaximum(1000)
        self.widthBox.setValue(self.model.getModelSize().width())

        self.heightBox = QDoubleSpinBox()
        self.heightBox.setMaximum(1000)
        self.heightBox.setValue(self.model.getModelSize().height())

        layout.addWidget(self.widthBox,1,0)
        layout.addWidget(self.heightBox,1,1)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.accepted.connect(self.apply)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)

    def apply(self):
        width = self.widthBox.value()
        height = self.heightBox.value()
        self.model.setModelSize(width,height)
        self.accept()

'''new'''
class TmazeMenuItem(QGroupBox): #contains the UI to change the obstacle it is associated with
    selfDestroyEvent = pyqtSignal(int)
    def __init__(self, model, obstIndex): #is executed whenever an obstacle is created. creates a menu for the specific obstacle
        super().__init__()
        self.obstIndex = obstIndex #the index of the obstacle this menu is associated with
        self.model = model #a reference to the model that saves the object information
        self.model.obstRemovedEvent.connect(self.selfDestroyChecker)
        self.obstData0 = self.model.getDrawableObst(0) #get obstacle data from the model
        self.obstData1 = self.model.getDrawableObst(1) #get obstacle data from the model
        self.maxValues = [self.model.getModelSize().width()/2,self.model.getModelSize().height()/2] #make sure the obstacles can't leave the canvas
        obstMenuLayout = QVBoxLayout()
        
        obstMenuLayout.addWidget(self.initSpinBox(obstIndex)) #adds boxes that allow user to change object position and size
        obstMenuLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.setLayout(obstMenuLayout)
        self.obstMenuLayout = obstMenuLayout

    
    def initSpinBox(self,obstIndex): #Initialize the Spinboxes that allow changing an objects position and size
        maxDimensions = [self.model.getModelSize().width(),self.model.getModelSize().height()] #make sure the obstacle can't be larger than the canvas

        
        #add the spinboxes to the layout
        spinBoxLayout = QHBoxLayout()
        #creates the spinbox for the obstacles Width
        spinBoxLayout.addWidget(self.createSpinbox("width", 0, maxDimensions[0], self.model.modelSize.width()-(self.obstData0.width()+self.obstData1.width()), self.moveObstWidth))
        #creates the spinbox for the obstacles Height
        spinBoxLayout.addWidget(self.createSpinbox("height", 0, maxDimensions[1], self.model.modelSize.height()-(self.obstData0.height()+self.obstData1.height()), self.moveObstHeight))
        
        spinBoxLayout.setAlignment(Qt.AlignmentFlag.AlignRight)
        # spinBoxLayout
        
        spinBoxHolderWidget = QWidget()
        spinBoxHolderWidget.setLayout(spinBoxLayout)

        return spinBoxHolderWidget
        
    def createSpinbox(self,labelText,minValue,maxValue,initVal,callback):
        layout = QVBoxLayout()

        spinBoxlabel = QLabel(labelText)

        spinBox = QDoubleSpinBox()
        spinBox.setMinimum(minValue)
        spinBox.setMaximum(maxValue)
        spinBox.setValue(initVal) #sets the starting value to the value in the model
        spinBox.valueChanged.connect(callback) #changing the value of the spinBox also changes the position of the obst accordingly

        slider = QSlider(Qt.Orientation.Horizontal, self)   # adjust a slider named zoom-slider
        slider.setMinimum(int(minValue*100))
        slider.setMaximum(int(maxValue*100))
        slider.setValue(int(initVal*100))                           # Initial value corresponding to 20% canvas size
        slider.setTickPosition(QSlider.TickPosition.TicksBelow)    # adjust ticks below the slider line
        slider.setTickInterval(int((maxValue-minValue)*50))                                 # the distance between each tick
        slider.sliderMoved.connect(lambda value: spinBox.setValue(value/100))           # connect the slider to a the function zoomObst
        spinBox.valueChanged.connect(lambda value: slider.setValue(int(value*100)))

        layout.addWidget(spinBoxlabel)
        layout.addWidget(spinBox)
        layout.addWidget(slider)

        holderWidget = QWidget()
        holderWidget.setLayout(layout)

        if callback == self.moveObstHeight:
            self.heightSpinBox = spinBox
            self.heightSlider = slider

        return holderWidget
    
    
    # Make changes to the obstacle
    def moveObstWidth(self,newW): #move the obst to the new widht and redaw the canvas
        width_change = (((self.model.modelSize.width()-(self.obstData0.width()+self.obstData1.width())))-newW)/2
        self.model.moveObst(0,width=self.obstData0.width()+width_change)
        self.model.moveObst(1,width=self.obstData1.width()+width_change)
        self.model.moveObst(0,xCenter=((self.model.modelSize.width()-(self.obstData0.width()))/2))
        self.model.moveObst(1,xCenter=-((self.model.modelSize.width()-(self.obstData1.width()))/2))
    
    def moveObstHeight(self,newH): #move the obst to the new height and redaw the canvas
        height_change = (((self.model.modelSize.height()-(max(self.obstData0.height(),self.obstData1.height()))))-newH)
        self.model.moveObst(0,height=self.obstData0.height()+height_change)
        self.model.moveObst(1,height=self.obstData1.height()+height_change)
        self.model.moveObst(0,yCenter=-((self.model.modelSize.height()-(self.obstData0.height()))/2))
        self.model.moveObst(1,yCenter=-((self.model.modelSize.height()-(self.obstData1.height()))/2))
        




    # Handle signals

    def selfDestroyChecker(self,index): #checks if the index of the detroyed obstacle mathces its own. -1 signifies the destruction of all obstacles
        if index == self.obstIndex or index == -1: self.selfDestroy()
        elif index < self.obstIndex: self.obstIndex -= 1 #if an obstacle with a lower index is removed, everything behind it has its index shifted

    def selfDestroy(self):
        self.selfDestroyEvent.emit(self.obstIndex)
        self.deleteLater()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    styles = PyQt6.QtWidgets.QStyleFactory.keys()
    app.setStyle(styles[1])
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())