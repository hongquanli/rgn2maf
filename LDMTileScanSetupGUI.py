# set QT_API environment variable
import os 
os.environ["QT_API"] = "pyqt5"
import qtpy

# qt libraries
from qtpy.QtCore import *
from qtpy.QtWidgets import *
from qtpy.QtGui import *

import math
import numpy as np
import xml.etree.ElementTree as ET
import MAFtool

import matplotlib.pyplot as plt
from shapely.geometry import Polygon

DEBUG = False

# DESKTOP_DIR = 'C:\\Users\\Wang Lab\\Desktop'
DESKTOP_DIR = os.path.expanduser("~/Desktop")

# microscope defination
FOV = 11.6*1e-3 # in meter
OVERLAP = 0.15
OFFSET = 0 # offset of the center of the FOV from the coordinate read from the RGN file
MAGNIFICATIONS = [10,25,40]

class tileScanSetupGUI(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # variables
        self.loaded_MAFfile = None
        self.XYZStagePointDefinitionList = MAFtool.XYZStagePointDefinitionList()
        self.XYTilescoordinates = []
        
        # entry boxes and buttons
        self.entry_AFCOffset = QLabel()
        self.entry_AFCOffset.setNum(0)
        self.entry_AFCOffset.setFixedWidth(60)
        self.entry_AFCOffset.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.entry_ZPosition = QLabel()
        self.entry_ZPosition.setNum(0)
        self.entry_ZPosition.setFixedWidth(90)
        self.entry_ZPosition.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.button_loadAFCOffsetandZPosition = QPushButton("Load from file")
        self.button_loadAFCOffsetandZPosition.clicked.connect(self.loadAFCOffsetandZPositionFromFile)

        self.dropdown_Magnification = QComboBox()
        self.dropdown_Magnification.addItems([str(M)+'x' for M in MAGNIFICATIONS])
        
        self.regionlist = QListWidget()

        self.button_addTileRegion = QPushButton("Add Tile Region from file")
        self.button_addTileRegion.clicked.connect(self.addTileRegion)
        
        self.lineEdit_MAFFileName = QLineEdit()
        self.button_generateLDMMAFFile = QPushButton("Generate LDM MAF file")
        self.button_generateLDMMAFFile.clicked.connect(self.generateLDMMAFFile)

        # set properties of entry box
        #self.entry_AFCOffset.setMinimum(AFC_MIN) 
        #self.entry_AFCOffset.setMaximum(AFC_MAX) 
        #self.entry_AFCOffset.setValue(0)

        # arrange entry boxes and buttons
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel('Objective Magnification'))
        hbox.addWidget(self.dropdown_Magnification)
        
        frame_1 = QFrame()
        frame_1.setLayout(hbox)
        frame_1.setFrameStyle(QFrame.Panel | QFrame.Raised)
        frame_1.setSizePolicy(QSizePolicy.Minimum,QSizePolicy.Minimum)

        vbox = QVBoxLayout()
        vbox.addWidget(self.regionlist)
        vbox.addWidget(self.button_addTileRegion)

        frame_2 = QFrame()
        frame_2.setLayout(vbox)
        frame_2.setFrameStyle(QFrame.Panel | QFrame.Raised)
        frame_2.setSizePolicy(QSizePolicy.Minimum,QSizePolicy.Minimum)

        hbox = QHBoxLayout()
        hbox.addWidget(QLabel('AFC Offset'))
        hbox.addWidget(self.entry_AFCOffset)
        hbox.addWidget(QLabel('Z Position'))
        hbox.addWidget(self.entry_ZPosition)
        hbox.addWidget(self.button_loadAFCOffsetandZPosition)
        self.button_loadAFCOffsetandZPosition.setEnabled(False) # disable this for now

        frame_3 = QFrame()
        frame_3.setLayout(hbox)
        frame_3.setFrameStyle(QFrame.Panel | QFrame.Raised)
        frame_3.setSizePolicy(QSizePolicy.Minimum,QSizePolicy.Minimum)

        hbox = QHBoxLayout()
        hbox.addWidget(self.lineEdit_MAFFileName)
        hbox.addWidget(self.button_generateLDMMAFFile)

        frame_4 = QFrame()
        frame_4.setLayout(hbox)
        frame_4.setFrameStyle(QFrame.Panel | QFrame.Raised)
        frame_4.setSizePolicy(QSizePolicy.Minimum,QSizePolicy.Minimum)

        # set up the central widget
        layout = QGridLayout()
        layout.addWidget(frame_1,0,0)
        layout.addWidget(frame_2,1,0)
        layout.addWidget(frame_3,2,0)
        layout.addWidget(frame_4,3,0)
        self.centralWidget = QWidget()
        self.centralWidget.setLayout(layout)
        self.setCentralWidget(self.centralWidget)

    def closeEvent(self, event):
        event.accept()

    def loadAFCOffsetandZPositionFromFile(self):
        dialog = QFileDialog()
        MAFfile, _filter = dialog.getOpenFileName(None,'Open File',DESKTOP_DIR,'XML files (*.maf)')
        if MAFfile != '':
            AFCOffset,ZPosition = MAFtool.read_AFCOffset_and_ZPosition_from_MAF_file(MAFfile)
            self.entry_AFCOffset.setNum(AFCOffset)
            self.entry_ZPosition.setNum(ZPosition)
            self.loaded_MAFfile = MAFfile

    def addTileRegion(self):
        
        dialog = QFileDialog()
        RGNfile, _filter = dialog.getOpenFileName(None,'Open File',DESKTOP_DIR,'XML files (*.rgn)')
        
        if RGNfile != '':
            # parse the RGN file
            # top(stageoverviewregions) -> regions -> shapelist -> items -> [itemX] -> verticies -> items -> [itemX] -> x,y,z
            regions_tree = ET.parse(RGNfile)
            regions_root = regions_tree.getroot()
            regions = regions_root.find('Regions')
            shapeList = regions.find('ShapeList')
            regions = shapeList.find('Items')

            # update FOV
            magnification = int(self.dropdown_Magnification.currentText()[:-1])
            FOV_object = FOV/magnification
            d = FOV_object*(1-OVERLAP)

            # iterate through tile regions and populate the MAFtree
            for region in regions:
                region_type = region.find('Type')

                # Rectangle
                if region_type.text == 'Rectangle':
                    self.regionlist.addItem(RGNfile)
                    verticies = region.find('Verticies')
                    items = verticies.find('Items')
                    point_bottom_left = items.find('Item0')
                    x0 = float(point_bottom_left.find('X').text)
                    y0 = float(point_bottom_left.find('Y').text)
                    point_top_right = items.find('Item3')
                    x1 = float(point_top_right.find('X').text)
                    y1 = float(point_top_right.find('Y').text)

                    '''
                    nx = math.ceil((x1-x0)/d)
                    ny = math.ceil((y1-y0)/d)
                    if DEBUG:
                        print(nx)
                        print(ny)
                    x_dir = 0
                    for i in range(ny):
                        x_dir = 1 - x_dir
                        y = y0 + d*(i) + OFFSET
                        for j in range(nx):
                            if x_dir == 1:
                                x = x0 + j*d
                            else:
                                x = x0 + (nx-1-j)*d
                            self.XYZStagePointDefinitionList.add_point(str(x),str(y),self.entry_AFCOffset.text(),self.entry_ZPosition.text())
                    '''

                    # create the rectangle
                    polygon = Polygon([[x0,y0],[x0,y1],[x1,y1],[x1,y0]])
                    x,y = polygon.exterior.xy
                    plt.clf()
                    plt.close()
                    plt.plot(x,y)
                    # plt.show()
            
                    # expand the rectangle
                    x0 = x0 - FOV_object*OVERLAP
                    y0 = y0 - FOV_object*OVERLAP
                    x1 = x1 + FOV_object*OVERLAP
                    y1 = y1 + FOV_object*OVERLAP
                    # calculate the number of FOVs needed
                    nx = math.ceil((x1-FOV_object-x0)/d) + 1
                    ny = math.ceil((y1-FOV_object-y0)/d) + 1
                    # update x1 and y1 coordinate
                    x1 = x0 + (nx-1)*d
                    y1 = y0 + (ny-1)*d
                    # show the rectangle
                    rectangle = Polygon([[x0,y0],[x0,y1+FOV_object],[x1+FOV_object,y1+FOV_object],[x1+FOV_object,y0]])
                    x,y = rectangle.exterior.xy
                    plt.plot(x,y,'--')
            
                    # go through individual tiles
                    x_dir = 0
                    for i in range(ny):
                        x_dir = 1 - x_dir
                        y = y0 + d*(i) + OFFSET
                        for j in range(nx):
                            if x_dir == 1:
                                x = x0 + j*d
                            else:
                                x = x0 + (nx-1-j)*d
                            fov = Polygon([[x,y],[x,y+FOV_object],[x+FOV_object,y+FOV_object],[x+FOV_object,y]])
                            # add the FOV if it is within or intersects the polygon
                            if fov.intersects(polygon):
                                xi,yi = fov.exterior.xy
                                plt.plot(xi,yi,'r')
                                self.XYZStagePointDefinitionList.add_point(str(x+FOV_object/2),str(y+FOV_object/2),self.entry_AFCOffset.text(),self.entry_ZPosition.text())
                                self.XYTilescoordinates.append([x,y])

                    plt.axis('equal')
                    plt.show()

                # AreaLine
                if region_type.text == 'AreaLine':

                    print('parsing an AreaLine rgn file')
                    # add the filename to the displayed list
                    self.regionlist.addItem(RGNfile)

                    # extract the vertices
                    verticies = region.find('Verticies')
                    items = verticies.find('Items')
                    coordinates_verticies_list = []
                    for item in items:
                        # print(item.tag)
                        x = float(item.find('X').text)
                        y = float(item.find('Y').text)
                        coordinates_verticies_list.append([x,y])                    
                    coordinates_verticies_list_np = np.array(coordinates_verticies_list)
                    # np.savetxt("rgn vertices.csv", coordinates_verticies_list_np, delimiter=",")

                    # create the polygon
                    polygon = Polygon(coordinates_verticies_list)
                    x,y = polygon.exterior.xy
                    plt.clf()
                    plt.close()
                    plt.plot(x,y)
                    # plt.show()

                    # start with a rectagular area that contains the polygon
                    [x0,y0] = np.min(coordinates_verticies_list_np,0)
                    [x1,y1] = np.max(coordinates_verticies_list_np,0)
                    # expand the rectangle
                    x0 = x0 - FOV_object*OVERLAP
                    y0 = y0 - FOV_object*OVERLAP
                    x1 = x1 + FOV_object*OVERLAP
                    y1 = y1 + FOV_object*OVERLAP
                    # calculate the number of FOVs needed
                    nx = math.ceil((x1-FOV_object-x0)/d) + 1
                    ny = math.ceil((y1-FOV_object-y0)/d) + 1
                    # update x1 and y1 coordinate
                    x1 = x0 + (nx-1)*d
                    y1 = y0 + (ny-1)*d
                    # show the rectangle
                    rectangle = Polygon([[x0,y0],[x0,y1+FOV_object],[x1+FOV_object,y1+FOV_object],[x1+FOV_object,y0]])
                    x,y = rectangle.exterior.xy
                    plt.plot(x,y,'--')
            
                    # go through individual tiles
                    x_dir = 0
                    for i in range(ny):
                        x_dir = 1 - x_dir
                        y = y0 + d*(i) + OFFSET
                        for j in range(nx):
                            if x_dir == 1:
                                x = x0 + j*d
                            else:
                                x = x0 + (nx-1-j)*d
                            fov = Polygon([[x,y],[x,y+FOV_object],[x+FOV_object,y+FOV_object],[x+FOV_object,y]])
                            # add the FOV if it is within or intersects the polygon
                            if fov.intersects(polygon):
                                xi,yi = fov.exterior.xy
                                plt.plot(xi,yi,'r')
                                self.XYZStagePointDefinitionList.add_point(str(x+FOV_object/2),str(y+FOV_object/2),self.entry_AFCOffset.text(),self.entry_ZPosition.text())
                                self.XYTilescoordinates.append([x,y])
                    plt.axis('equal')
                    plt.show()

                # CircleDiameter
                if region_type.text == 'CircleDiameter':
                    pass

                # Ellipse
                if region_type.text == 'Ellipse':
                    pass

            
    def generateLDMMAFFile(self):
        self.XYZStagePointDefinitionList.export(os.path.join(DESKTOP_DIR,self.lineEdit_MAFFileName.text() + '.maf'))
        if DEBUG:
            print(os.path.join(DESKTOP_DIR,self.lineEdit_MAFFileName.text() + '.maf'))
        # show the tiles
        plt.clf()
        plt.close()
        magnification = int(self.dropdown_Magnification.currentText()[:-1])
        FOV_object = FOV/magnification
        d = FOV_object*(1-OVERLAP)
        for x,y in self.XYTilescoordinates:
            fov = Polygon([[x,y],[x,y+FOV_object],[x+FOV_object,y+FOV_object],[x+FOV_object,y]])
            xi,yi = fov.exterior.xy
            plt.plot(xi,yi,'r')
        plt.axis('equal')
        plt.show()
        # empty the list
        self.XYZStagePointDefinitionList = MAFtool.XYZStagePointDefinitionList()
        self.XYTilescoordinates = []
        self.regionlist.clear()
        #plt.clf()

# start the gui
if __name__ == "__main__":

    app = QApplication([])
    win = tileScanSetupGUI()
    win.show()
    app.exec_() #sys.exit(app.exec_())
