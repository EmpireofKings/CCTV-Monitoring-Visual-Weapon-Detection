from enum import Enum
import math
import sys

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from data_handler import *
from gtts import gTTS
import logging


class LayoutMode(Enum):
    VIEW = 1
    EDIT = 2


class Layout(QFrame):
    def __init__(self, app, data, modes, config):
        QFrame.__init__(self)
        self.data = data
        self.setFrameStyle(QFrame.Box)

        self.painter = LayoutPainter(app, data, modes, config)
        self.controls = LayoutControls(app, data, modes, self.painter, config)

        layout = QVBoxLayout()
        layout.addWidget(self.painter)
        layout.addWidget(self.controls)
        layout.setAlignment(Qt.AlignCenter)

        self.setLayout(layout)


class LayoutPainter(QFrame):
    def __init__(self, app, data, modes, config):
        QFrame.__init__(self)
        self.data = data
        self.currentLevel = 0
        self.mainFeedID = '0'
        self.placing = False
        self.lastMousePos = None
        self.config = config
        self.pulseRadiusMultiplier = 0.9

        self.levelIDs = []

        for level in self.data[0]:
            self.levelIDs.append(level.levelID)

        self.tooltip = QToolTip()

        self.setMouseTracking(True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.data[0] != []:
            self.levelIDs.sort()
            index = self.levelIDs.index(int(self.currentLevel))
            self.level = self.data[0][index]

            self.currentpmap = getPixmap(
                self.width(), self.height(), self.level.drawPath)

            #check where pmap should draw to be centered
            pmapDrawX = (self.width() - self.currentpmap.width()) / 2

            painter.drawPixmap(QPoint(pmapDrawX, 0), self.currentpmap)

            for camera in self.level.cameras:
                # map coordinates
                camX = self.range2range(
                    camera.position.x(), 0, 500, 0, self.currentpmap.width() + pmapDrawX)

                camY = self.range2range(
                    camera.position.y(), 0, 500, 0, self.currentpmap.height())

                # set color to red if on alert
                if camera.alert:
                    color = QColor(255, 0, 0)
                else:
                    color = camera.color

                painter.setPen(color)
                painter.setBrush(QBrush(color, Qt.SolidPattern))

                # draw main circle
                painter.drawEllipse(QPoint(camX, camY),
                                    camera.size, camera.size)

                # calculate arrow coordinates
                radius = camera.size * 2
                arrowX = int(
                    (radius * math.sin(math.radians(camera.angle)))) + camX
                arrowY = int(
                    (radius * math.cos(math.radians(camera.angle)))) + camY
                arrowPoint = QPoint(arrowX, arrowY)

                # alter brush and pen
                painter.setBrush(Qt.NoBrush)
                pen = painter.pen()
                pen.setWidth(int(camera.size / 5))
                painter.setPen(pen)

                # draw arrow line
                painter.drawLine(QPoint(camX, camY), arrowPoint)

                # get rect for drawing arc
                rect = QRectF(
                    camX - (camera.size * 2),
                    camY - (camera.size * 2),
                    camera.size * 4,
                    camera.size * 4)

                # draw arc
                painter.drawArc(
                    rect,
                    int((camera.angle - 112.5) * 16),
                    int((45) * 16))

                # draw green circle around cam if selected
                if camera.camID == self.mainFeedID:
                    painter.setBrush(Qt.NoBrush)
                    pen = QPen(QColor(0, 255, 0))
                    pen.setWidth(3)
                    painter.setPen(pen)
                    painter.drawEllipse(QPoint(camX, camY),
                                        camera.size, camera.size)

                # if on alert pulse
                if camera.alert:
                    painter.setBrush(Qt.NoBrush)
                    pen = QPen(QColor(255, 0, 0))
                    pen.setWidth(2)
                    painter.setPen(pen)
                    painter.drawEllipse(
                        QPoint(camX, camY), 
                        self.pulseRadiusMultiplier * camera.size,
                        self.pulseRadiusMultiplier * camera.size)

            # control pulse radius multiplier
            if self.pulseRadiusMultiplier < 2.0:
                self.pulseRadiusMultiplier += 0.1
            else:
                self.pulseRadiusMultiplier = 0.0

            if self.placing is True:
                painter.setPen(QPen(QColor(255, 0, 0)))
                painter.setBrush(QBrush(QColor(255, 0, 0)))
                painter.drawEllipse(self.lastMousePos, 10, 10)

    def findCamByID(self, camID):
        print(camID)
        for level in self.data[0]:
            for camera in level.cameras:
                print(camera.camID)
                if camera.camID == camID:
                    return camera
        
        return False

    def mousePressEvent(self, event):
        if self.data[0] != []:
            camID = self.getCloseCam(event.x(), event.y())

            if camID is not None:
                camera = self.findCamByID(camID)
                if camera is not False:
                    self.controls.setMainFeedID(camera)
                    self.update()
                else:
                    logging.error("Camera not found")

            if self.placing is True:
                cameraDialog = self.CameraDialog(
                    self.mainFeedID, self.currentLevel)

                name, location, angle, color, size, staticBackground = (
                    cameraDialog.getCameraInfo())

                rawX = self.lastMousePos.x()
                rawY = self.lastMousePos.y()
                mappedX = self.range2range(rawX, 0, self.width(), 0, 500)
                mappedY = self.range2range(rawY, 0, self.height(), 0, 500)
                newCamera = Camera(
                    camID=self.mainFeedID, levelID=self.currentLevel,
                    location=location, position=QPoint(mappedX, mappedY),
                    angle=angle, color=color, size=size, assigned=True)

                index = self.levelIDs.index(int(self.currentLevel))
                self.level = self.data[0][index]
                self.level.cameras.append(newCamera)
                self.config.cameraMenu.update(self.data)

                self.placing = False

    class CameraDialog(QDialog):
        def __init__(self, id, levelID):
            QDialog.__init__(self)

            ids = QLabel("Level " + str(levelID) + " : Camera " + str(id))

            self.locationInput = QLineEdit()
            self.locationInput.setPlaceholderText("Location Name")

            self.angleInput = QSpinBox()
            self.angleInput.setRange(0, 360)
            self.angleInput.setSuffix('°')
            self.angleInput.setSpecialValueText("Camera Angle(0-360°)")

            self.colorLayout = QHBoxLayout()
            self.colorButton = QPushButton("Change Color")
            self.colorButton.clicked.connect(self.getColor)
            self.colorPreview = self.ColorPreview()
            self.colorLayout.addWidget(self.colorButton)
            self.colorLayout.addWidget(self.colorPreview)

            self.submitButton = QPushButton("Submit")
            self.submitButton.clicked.connect(self.submitted)

            self.sizeInput = QSpinBox()
            self.sizeInput.setRange(5, 40)
            self.sizeInput.setSuffix('Px')
            self.sizeInput.setSpecialValueText("Camera Size (5-40 Pixels)")

            self.layout = QVBoxLayout()
            self.layout.addWidget(ids)
            self.layout.addWidget(self.locationInput)
            self.layout.addWidget(self.angleInput)
            self.layout.addLayout(self.colorLayout)
            self.layout.addWidget(self.sizeInput)
            self.layout.addWidget(self.submitButton)

            self.setLayout(self.layout)

        def getColor(self):
            prompt = QColorDialog()
            result = prompt.getColor()

            if result.isValid():
                self.colorPreview.color = result

        class ColorPreview(QLabel):
            def __init__(self):
                QLabel.__init__(self)
                self.color = QColor(0, 0, 0)
                self.setMinimumSize(QSize(30, 30))
                self.setMaximumSize(QSize(30, 30))

            def paintEvent(self, event):
                painter = QPainter(self)

                painter.setPen(self.color)
                painter.setBrush(self.color)

                painter.drawRect(QRect(0, 0, 30, 30))

        def submitted(self):
            location = self.locationInput.displayText()
            angle = self.angleInput.text()
            color = self.colorPreview.color
            size = self.sizeInput.text()

            self.result = [
                location, int(angle[:len(angle) - 1]),
                color, int(size[:len(size) - 2])]

            self.accept()

        def getCameraInfo(self):
            self.exec()
            return self.result

    def mouseMoveEvent(self, event):
        if self.data[0] != []:
            pos = event.globalPos()
            self.lastMousePos = event.localPos()
            id = self.getCloseCam(event.x(), event.y())

            if id is not None:
                self.tooltip.showText(pos, str(id))

            if self.placing is True:
                self.update()

    def getCloseCam(self, x1, y1):
        if self.level.cameras != []:
            dists = {}

            for camera in self.level.cameras:
                x2 = self.range2range(
                    camera.position.x(), 0, 500, 0, self.currentpmap.width())
                y2 = self.range2range(
                    camera.position.y(), 0, 500, 0, self.currentpmap.height())

                dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

                dists[camera.camID] = dist

            location = min(dists, key=dists.get)
            closestDist = dists.get(location)

            if closestDist < camera.size * 2:
                return location
            else:
                return None
        else:
            return None

    def range2range(self, value, oldMin, oldMax, newMin, newMax):
        return ((value - oldMin) / (oldMax - oldMin)) * (newMax - newMin) + newMin


class LayoutControls(QFrame):
    def __init__(self, app, data, modes, painter, config):
        QFrame.__init__(self)
        self.setFrameStyle(QFrame.Box)
        self.config = config
        self.data = data
        self.painter = painter
        self.painter.controls = self
        outerLayout = QVBoxLayout()

        if LayoutMode.VIEW in modes:
            self.upLevelButton = QPushButton("Up")
            self.downLevelButton = QPushButton("Down")

            self.upLevelButton.clicked.connect(self.changeLevel)
            self.downLevelButton.clicked.connect(self.changeLevel)

            self.dropdown = QComboBox()
            self.dropdown.currentIndexChanged.connect(self.indexChanged)

            for i in range(len(data[0])):
                self.dropdown.addItem("Level " + str(data[0][i].levelID))

            viewLayout = QHBoxLayout()
            viewControlBox = QWidget()
            viewLayout.addWidget(self.upLevelButton)
            viewLayout.addWidget(self.downLevelButton)
            viewLayout.addWidget(self.dropdown)

            viewControlBox.setLayout(viewLayout)
            outerLayout.addWidget(viewControlBox, Qt.AlignCenter)

        if LayoutMode.EDIT in modes:
            addLevelButton = QPushButton("Add Level")
            addLevelButton.clicked.connect(self.addLevel)

            deleteLevelButton = QPushButton("Delete Level")
            deleteLevelButton.clicked.connect(self.deleteLevel)

            simulateButton = QPushButton("Simulate Cameras")
            simulateButton.clicked.connect(self.simulateCameras)

            colorButton = QPushButton("Color")
            colorButton.clicked.connect(self.getColor)

            sizeButton = QPushButton("Size")
            sizeButton.clicked.connect(self.setSize)

            saveButton = QPushButton("Save")
            saveButton.clicked.connect(self.saveConfig)

            resetButton = QPushButton("Reset")
            resetButton.clicked.connect(self.resetConfig)

            editLayout = QHBoxLayout()
            editLayout.addWidget(addLevelButton)
            editLayout.addWidget(deleteLevelButton)
            editLayout.addWidget(simulateButton)
            editLayout.addWidget(colorButton)
            editLayout.addWidget(sizeButton)
            editLayout.addWidget(saveButton)
            editLayout.addWidget(resetButton)

            outerLayout.addLayout(editLayout)

        self.setLayout(outerLayout)

    def changeLevel(self):
        if self.data[0] != []:
            currentLevel = int(self.dropdown.currentText()[len("Level "):])

            if self.sender() is self.upLevelButton:
                nextLevel = currentLevel + 1
            elif self.sender() is self.downLevelButton:
                nextLevel = currentLevel - 1
            else:
                print("Unknown Caller: LayoutControls.changeLevel()")

            text = "Level " + str(nextLevel)
            index = self.dropdown.findText(text)

            if index != -1:
                self.dropdown.setCurrentIndex(index)  # triggers indexChanged

    def indexChanged(self):
        level = int(self.dropdown.currentText()[len("Level "):])
        self.painter.currentLevel = level
        self.painter.update()

    def setLevel(self, level):
        text = "Level " + str(level)
        index = self.dropdown.findText(text)

        if index != -1:
            self.dropdown.setCurrentIndex(index)  # triggers indexChanged

    def setMainFeedID(self, camera):
        self.painter.mainFeedID = camera.camID
        self.setLevel(camera.levelID)
        self.painter.update()

    def addLevel(self):
        dialog = QInputDialog()
        id, check = dialog.getInt(self, "Level Setup", "Level Number")

        if check:
            dialog = QFileDialog()
            path, check = dialog.getOpenFileName()

            if check:
                level = Level(id, path, [])
                self.data[0].append(level)
                self.painter.levelIDs.append(id)
                self.dropdown.addItem("Level " + str(id))
                self.painter.update()
                self.config.levelMenu.update(self.data)

    def deleteLevel(self):
        print("delete level called")

# TODO IGNORE DUPLICATES
    def simulateCameras(self):
        dialog = QFileDialog()
        paths, check = dialog.getOpenFileNames()

        if check:
            simCams = []
            for id in paths:
                parts = id.split('/')
                name = parts[len(parts) - 1]
                camera = Camera(id, name)
                simCams.append(camera)

            if len(self.data) < 3:
                self.data.append(simCams)
            else:
                for cam in simCams:
                    self.data[2].append(cam)
            self.config.cameraMenu.update(self.data)

    def getColor(self):
        if self.data[0] != []:
            prompt = QColorDialog()
            result = prompt.getColor()

            if result.isValid():
                self.setColor(result.getRgb()[:3])
        else:
            msgBox = QMessageBox()
            msgBox.setText(
                "You must select a placed camera before you can edit its color")
            msgBox.exec()

    def setColor(self, color):
        newColor = QColor(color[0], color[1], color[2])
        camera = self.getSelectedCamera()
        camera.color = newColor
        self.painter.update()

    def saveConfig(self):
        if self.data[0] != []:
            msgBox = QMessageBox()
            msgBox.setText(
                    """A restart will be required to begin live analysis with 
				the new configuration data, do you wish to continue?""")

            msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
            result = msgBox.exec()

            if result == QMessageBox.Yes:
                dataLoader = DataLoader()
                dataLoader.saveConfigData(self.data[0])

                msgBox = QMessageBox()
                msgBox.setText(
                    "Configuration data saved successfully. Program will now restart.")
                msgBox.exec()

                program = sys.executable
                os.execl(program, program, * sys.argv)
        else:
            msgBox = QMessageBox()
            msgBox.setText("Nothing to save.")
            msgBox.exec()

    def setSize(self):
        if self.data[0] != []:
            dialog = QInputDialog()
            camera = self.getSelectedCamera()
            result = dialog.getInt(
                self, "Set Camera Size", "Label", camera.size, 5, 30, 1)
            if result[1]:
                camera.size = result[0]
                self.painter.update()
        else:
            msgBox = QMessageBox()
            msgBox.setText(
                "You must select a placed camera before you can edit its size")
            msgBox.exec()

    def setPlacing(self, bool, id):
        self.painter.placing = bool
        self.painter.mainFeedID = id
        self.painter.update()

    def getSelectedCamera(self):
        for level in self.data[0]:
            for camera in level.cameras:
                if camera.camID == self.painter.mainFeedID:
                    return camera

    def resetConfig(self):
        dialog = QMessageBox()
        dialog.setText("Are you sure?")
        dialog.setInformativeText(
            "The configuration data will be permanently deleted.")
        dialog.setStandardButtons(QMessageBox.Reset | QMessageBox.Cancel)
        dialog.setDefaultButton(QMessageBox.Reset)
        result = dialog.exec()

        if result == QMessageBox.Reset:
            dataLoader = DataLoader()
            dataLoader.saveConfigData([])
            self.painter.data[0] = []
            self.config.levelMenu.update(self.painter.data)
            msgBox = QMessageBox()
            msgBox.setText("Configuration data reset successfully.")
            msgBox.exec()
