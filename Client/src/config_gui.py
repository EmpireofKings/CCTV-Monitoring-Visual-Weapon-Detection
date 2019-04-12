# Ben Ryan C15507277

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from data_handler import *
from layout_gui import Layout, LayoutMode


class Config(QWidget):
    def __init__(self, app, dataLoader):
        QWidget.__init__(self)

        layout = QHBoxLayout()
        data = dataLoader.getConfigData()
        self.levelMenu = None

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

        if len(data[0]) == 0:
            temp = Level("data will appear here", '../data/placeholder.png', [])
            disp = LevelDisplay(temp, self.drawSpace)
            disp.setStyleSheet("border: 3px solid black")
            self.layout.addWidget(disp, Qt.AlignCenter)

        for level in data[0]:
            disp = LevelDisplay(level, self.drawSpace)

            if level.levelID == self.drawSpace.painter.currentLevel:
                disp.setStyleSheet("border: 3px solid blue")
            else:
                disp.setStyleSheet("border: 3px solid black")

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

        self.curTabIndex = 0
        self.unassigned = None
        self.update(data)

    def update(self, data):
        if self.unassigned is not None:
            self.curTabIndex = self.unassigned.currentIndex()

        outerLayout = QVBoxLayout()

        assignedScroll = QScrollArea()
        assigned = QWidget()
        assignedLayout = QVBoxLayout()
        selectedCam = self.drawSpace.controls.getSelectedCamera()

        # already assigned cameras
        for level in data[0]:
            for camera in level.cameras:
                disp = CameraDisplay(camera, self.drawSpace)

                if selectedCam is not None:
                    if selectedCam.camID == camera.camID:
                        disp.setStyleSheet("border: 3px solid blue")
                    else:
                        disp.setStyleSheet("border: 3px solid black")
                else:
                    disp.setStyleSheet("border: 3px solid black")

                assignedLayout.addWidget(disp, Qt.AlignCenter)

        assigned.setLayout(assignedLayout)
        assignedScroll.setWidget(assigned)

        self.unassigned = QTabWidget()

        cameraScroll = QScrollArea()
        cameras = QWidget()
        cameraLayout = QVBoxLayout()

        # unassignedCameras
        for camera in data[1]:
            disp = CameraDisplay(camera, self.drawSpace)

            if selectedCam is not None:
                if selectedCam.camID == camera.camID:
                    disp.setStyleSheet("border: 3px solid blue")
                else:
                    disp.setStyleSheet("border: 3px solid black")
            else:
                disp.setStyleSheet("border: 3px solid black")

            cameraLayout.addWidget(disp, Qt.AlignCenter)

        cameras.setLayout(cameraLayout)
        cameraScroll.setWidget(cameras)

        self.unassigned.addTab(cameraScroll, "Cameras")

        videoScroll = QScrollArea()
        videos = QWidget()
        videoLayout = QVBoxLayout()

        if len(data) == 3:
            for camera in data[2]:
                disp = CameraDisplay(camera, self.drawSpace)
                if selectedCam is not None:
                    if selectedCam.camID == camera.camID:
                        disp.setStyleSheet("border: 3px solid blue")
                    else:
                        disp.setStyleSheet("border: 3px solid black")
                else:
                    disp.setStyleSheet("border: 3px solid black")

                videoLayout.addWidget(disp)

        videos.setLayout(videoLayout)
        videoScroll.setWidget(videos)

        self.unassigned.addTab(videoScroll, "Videos")
        self.unassigned.setCurrentIndex(self.curTabIndex)

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
        outerLayout.addWidget(self.unassigned)

        tempWidget = QWidget()
        tempWidget.setLayout(self.layout())

        self.setLayout(outerLayout)


class CameraDisplay(QLabel):
    def __init__(self, camera, drawSpace):
        QLabel.__init__(self)
        self.setFrameStyle(QFrame.Box)
        self.drawSpace = drawSpace
        self.camera = camera

        pmap = camera.getPreview(256, 144)
        self.setPixmap(pmap)

    def mousePressEvent(self, event):
        if not self.camera.assigned:
            self.drawSpace.controls.setPlacing(True, self.camera.camID)
            self.drawSpace.controls.setMainFeedID(self.camera, placing=True)
        else:
            self.drawSpace.controls.setPlacing(False, self.camera.camID)
            self.drawSpace.controls.setMainFeedID(self.camera)
