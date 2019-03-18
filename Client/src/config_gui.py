# TODO
from pprint import pprint
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from layout_gui import Layout, LayoutMode
from data_handler import *


class Config(QWidget):
    def __init__(self, app, dataLoader):
        QWidget.__init__(self)
       # self.setMinimumSize(QSize(1280, 800))

        layout = QHBoxLayout()
        data = dataLoader.getConfigData()

        drawSpace = Layout(app, data, [LayoutMode.VIEW, LayoutMode.EDIT], self)

        drawSpace.painter.setMinimumSize(800, 800)

        drawSpace.painter.setSizePolicy(QSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Fixed))
        
        drawSpace.controls.setSizePolicy(QSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Fixed))


        self.levelMenu = LevelMenu(data, drawSpace)
        self.cameraMenu = CameraMenu(data, drawSpace)

        layout.addWidget(self.levelMenu)
        layout.addWidget(self.cameraMenu)

        layout.addWidget(drawSpace)

        self.setLayout(layout)


class LevelMenu(QScrollArea):
    def __init__(self, data, drawSpace):
        QScrollArea.__init__(self)
        self.drawSpace = drawSpace
        self.setSizePolicy(QSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Minimum))
        self.update(data)

    def update(self, data):
        self.layout = QVBoxLayout()

        data[0].sort(key=lambda level: level.levelID)

        for level in data[0]:
            disp = LevelDisplay(level, self.drawSpace)
            self.layout.addWidget(disp, Qt.AlignCenter)

        self.mainWidget = QFrame()
        self.mainWidget.setFrameStyle(QFrame.Box)
        self.mainWidget.setLayout(self.layout)
        self.setWidget(self.mainWidget)


class LevelDisplay(QLabel):
    def __init__(self, level, drawSpace):
        QLabel.__init__(self)
        self.setFrameStyle(QFrame.Box)
        self.drawSpace = drawSpace
        self.level = level
        pmap = getLabelledPixmap(
            256, 144, "Level " + str(self.level.levelID), self.level.drawPath)
        self.setPixmap(pmap)

    def mousePressEvent(self, event):
        self.drawSpace.controls.setLevel(self.level.levelID)


class CameraMenu(QWidget):
    def __init__(self, data, drawSpace):
        QWidget.__init__(self)
        self.data = data
        self.drawSpace = drawSpace
        self.setSizePolicy(QSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Minimum))
        self.update(data)


    def update(self, data):
        outerLayout = QVBoxLayout()

        assignedScroll = QScrollArea()
        assigned = QWidget()
        assignedLayout = QVBoxLayout()

        # already assigned cameras
        for level in data[0]:
            for camera in level.cameras:
                disp = CameraDisplay(camera, self.drawSpace)
                assignedLayout.addWidget(disp, Qt.AlignCenter)

        assigned.setLayout(assignedLayout)
        assignedScroll.setWidget(assigned)

        unassigned = QTabWidget()

        cameraScroll = QScrollArea()
        cameras = QWidget()
        cameraLayout = QVBoxLayout()

        # unassignedCameras
        for camera in data[1]:
            disp = CameraDisplay(camera, self.drawSpace)
            cameraLayout.addWidget(disp, Qt.AlignCenter)

        cameras.setLayout(cameraLayout)
        cameraScroll.setWidget(cameras)

        unassigned.addTab(cameraScroll, "Cameras")

        videoScroll = QScrollArea()
        videos = QWidget()
        videoLayout = QVBoxLayout()

        if len(data) == 3:
            for camera in data[2]:
                disp = CameraDisplay(camera, self.drawSpace)
                videoLayout.addWidget(disp)

        videos.setLayout(videoLayout)
        videoScroll.setWidget(videos)

        unassigned.addTab(videoScroll, "Videos")

        assTitle = QLabel('Assigned Feeds')
        font = QFont('Helvetica', 13)
        assTitle.setFont(font)
        assTitle.setAlignment(Qt.AlignCenter)
        outerLayout.addWidget(assTitle)
        outerLayout.addWidget(assignedScroll)

        unassTitle = QLabel('Unassigned Feeds')
        unassTitle.setFont(font)
        unassTitle.setAlignment(Qt.AlignCenter)
        outerLayout.addWidget(unassTitle)
        outerLayout.addWidget(unassigned)

        tempWidget = QWidget()
        tempWidget.setLayout(self.layout())

        self.setLayout(outerLayout)


class CameraDisplay(QLabel):
    def __init__(self, camera, drawSpace):
        QLabel.__init__(self)
        self.setFrameStyle(QFrame.Box)
        self.drawSpace = drawSpace
        self.camera = camera

        # print(self.camera.camID)
        pmap = camera.getPreview(256, 144)
        self.setPixmap(pmap)

    def mousePressEvent(self, event):
        self.drawSpace.controls.setMainFeedID(self.camera)

        if not self.camera.assigned:
            self.drawSpace.controls.setPlacing(True, self.camera.camID)
        else:
            self.drawSpace.controls.setPlacing(False, self.camera.camID)
