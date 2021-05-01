from PySide6.QtCore import Qt,QRect, QEvent
from PySide6.QtWidgets import QMainWindow, QLabel,QWidget,QPushButton, QVBoxLayout,QHBoxLayout, QApplication, QGridLayout, QToolBar, QToolButton
from PySide6.QtGui import QIcon, QAction
from functools import partial
import random
import time
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        #Builds window
        super().__init__()
        self.difficultydata = {'Easy':[10,10,10],'Normal':[15,15,25],'Hard':[20,20,50]} #0: x, 1:y, 2:mines
        self.difficulty = 'Easy'
        stylesheet = self.readstylesheet()
        self.setStyleSheet(stylesheet)
        self.build_grid()
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        self.build_toolbar(toolbar)
        self.flaggedlist = []

    def build_grid(self):
        #Builds grid of fields.
        #The grid is stored as gridfield instances in a list of lists, the first list representing x coord, second the y coord.        
        #Note that Qt reverses coords, so (0,0) is the top left corner, and the x value is actually the row, not the column as would be expected.
        #The gridfields are represented in a QGridLayout. 
        #The holder widget contains the status label as well as the grid, and is used as the central widget of mainwindow.
        self.xlength = self.difficultydata[self.difficulty][0]
        self.ylength = self.difficultydata[self.difficulty][1]
        minegrid = QWidget()
        gridlayout = QGridLayout()
        self.grid = []
        #Creates instances for grid
        for x in range(self.xlength):
            self.ylist = []
            for y in range(self.ylength):
                coords = (x,y)
                self.ylist.append(gridfield((coords),self))
                self.ylist[-1].clicked.connect(partial(self.wasclicked,data=coords))
                gridlayout.addWidget(self.ylist[-1],x,y)
            self.grid.append(self.ylist)
        #Sets layout
        gridlayout.setSpacing(0)
        minegrid.setLayout(gridlayout)
        minegrid.setObjectName('thegrid')
        mainlayout = QVBoxLayout()
        mainlayout.setAlignment(Qt.AlignCenter)
        #Adds statustext
        self.statustext = QLabel()
        self.statustext.setAlignment(Qt.AlignCenter)
        difstring = 'Difficulty: ' + self.difficulty
        self.updatestatustext(difstring)
        #Adds widgets to holder
        mainlayout.addWidget(self.statustext)
        mainlayout.addWidget(minegrid)
        holder = QWidget()
        holder.setLayout(mainlayout)
        self.setCentralWidget(holder)
        self.setmines(self.difficultydata[self.difficulty][2])

    def build_toolbar(self,toolbar):
        #Toolbar with the options to reset the game, and to set another difficulty.
        resetgame = QAction('Reset',self)
        resetgame.triggered.connect(self._resetgame)
        toolbar.addAction(resetgame)
        toolbar.addSeparator()
        setdifficultyeasy = QAction('Easy',self)
        setdifficultynormal = QAction('Normal',self)
        setdifficultyhard = QAction('Hard',self)
        setdifficultyeasy.triggered.connect(self.seteasy)
        setdifficultynormal.triggered.connect(self.setnormal)
        setdifficultyhard.triggered.connect(self.sethard)
        toolbar.addAction(setdifficultyeasy)
        toolbar.addAction(setdifficultynormal)
        toolbar.addAction(setdifficultyhard)

    def seteasy(self):
        self.difficulty = 'Easy'
        self._resetgame()

    def setnormal(self):
        self.difficulty = 'Normal'
        self._resetgame()

    def sethard(self):
        self.difficulty = 'Hard'
        self._resetgame()

    def updatestatustext(self,text):
        self.statustext.setText(text)
        self.statustext.update()

    def _resetgame(self):
        print('reset!')
        print(self.difficulty)
        self.build_grid()

    def surroundingfields(self,coords):
        #Returns all the surrounding fields of a given coord, as long as the field is within bound of the grid.
        x,y = coords
        fields = []
        for xdif in range (-1,2):
            for ydif in range (-1,2):
                if (xdif,ydif) != (0,0):
                    newx = x+xdif
                    newy = y+ydif
                    #if newx >= 0 and newy >= 0:
                    if 0 <= newx <= self.xlength-1 and 0 <= newy <= self.ylength-1:
                        fields.append(self.grid[newx][newy])
        return fields

    def checksurrounding(self,thisgridfield):
        #Checks the surroundings of a field for mines. 
        #If there are no adjacent mines, recursively checks each surrounding field for adjacent mines, clearing out a chunk of the grid.
        coords = thisgridfield.pos
        fields = self.surroundingfields(coords)
        surroundingbombs = 0
        for field in fields:
            if field.hasmine:
                surroundingbombs += 1
        if surroundingbombs == 0:
            #Recursively checks surrounding fields for other clear fields, and reveals them.
            thisgridfield.isclicked = True
            thisgridfield.reveal()
            for field in fields:
                if not field.isclicked:
                    self.checksurrounding(field)
        else:
            #Reveals amount of surrounding mines
            thisgridfield.surroundingmines = surroundingbombs
            thisgridfield.isclicked = True
            thisgridfield.reveal()
        

    def wasclicked(self,data):
        #When gridfield is clicked. Data is coords (x,y).
        #Checks for victory and defeat, or reveal the field.
        self.checkforvictory()
        x,y = data
        thisgridfield = self.grid[x][y]
        if thisgridfield.hasmine == True:
            self.gamelost()
        else:
            self.checksurrounding(thisgridfield)


    def setmines(self,n):
        #n is amount of mines
        #find random fields:
        mines = []
        for m in range (n):
            mineloc = None
            while mineloc == None:
                (x,y) = (random.randint(0,self.xlength-1), random.randint(0,self.ylength-1))
                if (x,y) not in mines:
                    mineloc = (x,y)
            mines.append(mineloc)
        self.mines = mines
        #Update gridfield instance for each mine
        for mine in mines:
            x, y = mine
            self.grid[x][y].hasmine = True

    def readstylesheet(self):
        file = open('stylesheet.qss','r').read()
        return file

    def gamelost(self):
        #Reveals mines, updates statustext, and disables all gridfields
        for mine in self.mines:
            x,y = mine
            field = self.grid[x][y]
            field.setIcon(QIcon('bomb.png'))
        self.updatestatustext('Game lost!')
        for x in self.grid:
            for y in x:
                y.setEnabled(False)


    def checkforvictory(self):
        #If all mines are flagged, and no other fields are flagged, game is won. Disables fields and updates statustext.
        flags = self.flaggedlist
        flags.sort()
        mines = self.mines
        mines.sort()
        if flags == mines:
            self.updatestatustext('Game won!')
            for x in self.grid:
                for y in x:
                    y.setEnabled(False)


class gridfield(QPushButton):
    #Class for each individual field, as child of QPushButton.
    def __init__(self,data,window):
        super().__init__()
        self.pos = data
        self.isclicked = False
        self.surroundingmines = None
        self.flagged = False
        self.hasmine = False
        self.setGeometry(QRect(0,0,30,30))
        self.setFixedHeight(30)
        self.setFixedWidth(30)
        self.window = window
        #print('Jeg er blevet bygget! ',data)

    def reveal(self):
        #Shows surrounding mines if there are any. Disables field.
        if self.isclicked:
            self.setStyleSheet('background-color:white')
            if self.surroundingmines:
                self.setText(str(self.surroundingmines))
            self.setEnabled(False)

    def toggleflag(self):
        #Flags field. Displays icon and adds to list of flagged fields
        if not self.flagged:
            self.setIcon(QIcon('flag.png'))
            self.flagged = True
            self.window.flaggedlist.append(self.pos)
        else:
            self.setIcon(QIcon())
            self.flagged = False
            self.window.flaggedlist.remove(self.pos)
    
    def mousePressEvent(self,event):
        #Detects rightclick. If field is rightclicked, flag is toggled. Otherwise, the usual QPushButton event is called.
        if event.button() == Qt.RightButton:
            self.toggleflag()

        QPushButton.mousePressEvent(self,event)
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()