import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton,
                             QVBoxLayout, QHBoxLayout, QFileDialog)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen
from PyQt5.QtCore import Qt, QPoint


class ImageViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.original_image = None
        self.display_image = None
        self.roi_start = None
        self.roi_end = None
        self.drawing = False
        self.initUI()

    def initUI(self):
        # 创建控件
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(640, 480)

        btn_load = QPushButton("加载图片", self)
        btn_load.clicked.connect(self.loadImage)

        btn_roi = QPushButton("选择ROI", self)
        btn_roi.clicked.connect(self.startROISelection)

        # 布局
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_load)
        btn_layout.addWidget(btn_roi)

        main_layout = QVBoxLayout()
        main_layout.addLayout(btn_layout)
        main_layout.addWidget(self.image_label)
        self.setLayout(main_layout)

        # 窗口设置
        self.setWindowTitle('PyQt5 ROI选择器')
        self.show()

    def loadImage(self):
        # 打开文件对话框
        filename, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "Image Files (*.png *.jpg *.jpeg)")
        if filename:
            # 用OpenCV读取图片
            self.original_image = cv2.imread(filename)
            if self.original_image is not None:
                self.updateDisplay()

    def updateDisplay(self):
        # 将OpenCV图像转换为Qt格式
        h, w, ch = self.original_image.shape
        bytes_per_line = ch * w
        image_rgb = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)
        q_img = QImage(image_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.display_image = QPixmap.fromImage(q_img)

        # 缩放显示
        scaled_pixmap = self.display_image.scaled(
            self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)

    def startROISelection(self):
        self.drawing = True
        self.image_label.mousePressEvent = self.mousePress
        self.image_label.mouseMoveEvent = self.mouseMove
        self.image_label.mouseReleaseEvent = self.mouseRelease

    def mousePress(self, event):
        if self.drawing and event.button() == Qt.LeftButton:
            # 获取相对于图像的坐标
            self.roi_start = self.getImagePosition(event.pos())
            self.roi_end = self.roi_start
            self.drawROI()

    def mouseMove(self, event):
        if self.drawing:
            self.roi_end = self.getImagePosition(event.pos())
            self.drawROI()

    def mouseRelease(self, event):
        if self.drawing and event.button() == Qt.LeftButton:
            self.roi_end = self.getImagePosition(event.pos())
            self.drawing = False
            self.cropAndSave()

    def getImagePosition(self, pos):
        # 将控件坐标转换为原始图像坐标
        pixmap = self.image_label.pixmap()
        if pixmap:
            img_width = pixmap.width()
            img_height = pixmap.height()
            label_width = self.image_label.width()
            label_height = self.image_label.height()

            # 计算缩放比例
            scale_w = img_width / label_width
            scale_h = img_height / label_height

            # 计算实际坐标
            x = int(pos.x() * scale_w)
            y = int(pos.y() * scale_h)
            return QPoint(x, y)
        return QPoint(0, 0)

    def drawROI(self):
        if self.roi_start and self.roi_end:
            # 在显示图像上绘制矩形
            pixmap = self.display_image.copy()
            painter = QPainter(pixmap)
            painter.setPen(QPen(Qt.green, 2, Qt.SolidLine))

            # 确保矩形坐标正确
            x1 = min(self.roi_start.x(), self.roi_end.x())
            y1 = min(self.roi_start.y(), self.roi_end.y())
            x2 = max(self.roi_start.x(), self.roi_end.x())
            y2 = max(self.roi_start.y(), self.roi_end.y())

            painter.drawRect(x1, y1, x2 - x1, y2 - y1)
            painter.end()

            # 缩放显示
            scaled_pixmap = pixmap.scaled(
                self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)

    def cropAndSave(self):
        if self.roi_start and self.roi_end:
            # 获取坐标
            x1 = min(self.roi_start.x(), self.roi_end.x())
            y1 = min(self.roi_start.y(), self.roi_end.y())
            x2 = max(self.roi_start.x(), self.roi_end.x())
            y2 = max(self.roi_start.y(), self.roi_end.y())

            # 截取ROI
            roi = self.original_image[y1:y2, x1:x2]
            if roi.size > 0:
                cv2.imwrite("roi_result.jpg", roi)
                print("ROI已保存为 roi_result.jpg")
                self.updateDisplay()  # 刷新显示原始图像
            else:
                print("错误：选择的区域无效")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageViewer()
    sys.exit(app.exec_())