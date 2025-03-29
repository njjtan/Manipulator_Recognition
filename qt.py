import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton,
                             QVBoxLayout, QHBoxLayout, QFileDialog)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen
from PyQt5.QtCore import Qt, QPoint, QRect


class ImageViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.original_image = None
        self.display_image = None
        self.roi_rect = None
        self.resizing = False
        self.moving = False
        self.resize_handle = None
        self.initUI()

    def initUI(self):
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(640, 480)

        btn_load = QPushButton("加载图片", self)
        btn_load.clicked.connect(self.loadImage)

        btn_roi = QPushButton("选择ROI", self)
        btn_roi.clicked.connect(self.createROI)

        btn_save = QPushButton("保存ROI", self)
        btn_save.clicked.connect(self.saveROI)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_load)
        btn_layout.addWidget(btn_roi)
        btn_layout.addWidget(btn_save)

        main_layout = QVBoxLayout()
        main_layout.addLayout(btn_layout)
        main_layout.addWidget(self.image_label)
        self.setLayout(main_layout)

        self.setWindowTitle('PyQt5 ROI选择器')
        self.show()

    def loadImage(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "Image Files (*.png *.jpg *.jpeg)")
        if filename:
            self.original_image = cv2.imread(filename)
            if self.original_image is not None:
                self.roi_rect = None
                self.updateDisplay()

    def updateDisplay(self):
        h, w, ch = self.original_image.shape
        bytes_per_line = ch * w
        image_rgb = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)
        q_img = QImage(image_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.display_image = QPixmap.fromImage(q_img)
        pixmap = self.display_image.copy()
        if self.roi_rect:
            self.drawROI(pixmap)
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)

    def createROI(self):
        if self.original_image is not None:
            img_h, img_w = self.original_image.shape[:2]
            center_x, center_y = img_w // 2, img_h // 2
            self.roi_rect = QRect(center_x - 100, center_y - 100, 200, 200)
            self.image_label.mousePressEvent = self.mousePress
            self.image_label.mouseMoveEvent = self.mouseMove
            self.image_label.mouseReleaseEvent = self.mouseRelease
            self.updateDisplay()

    def getImagePosition(self, pos):
        pixmap = self.image_label.pixmap()
        if pixmap:
            label_width = self.image_label.width()
            label_height = self.image_label.height()
            img_width = self.original_image.shape[1]
            img_height = self.original_image.shape[0]

            pixmap_width = pixmap.width()
            pixmap_height = pixmap.height()
            scale_w = img_width / pixmap_width
            scale_h = img_height / pixmap_height

            x_offset = (label_width - pixmap_width) / 2
            y_offset = (label_height - pixmap_height) / 2

            x = int((pos.x() - x_offset) * scale_w)
            y = int((pos.y() - y_offset) * scale_h)

            x = max(0, min(x, img_width - 1))
            y = max(0, min(y, img_height - 1))
            return QPoint(x, y)
        return QPoint(0, 0)

    def drawROI(self, pixmap):
        painter = QPainter(pixmap)
        painter.setPen(QPen(Qt.blue, 15, Qt.SolidLine))  # 线条加粗到 15
        painter.drawRect(self.roi_rect)

        # 绘制调整大小的控制点
        handle_size = 12
        painter.setPen(Qt.NoPen)  # 移除边框线
        painter.setBrush(Qt.red)  # 设置填充颜色为红色

        # 四个角的控制点
        painter.drawRect(self.roi_rect.topLeft().x() - handle_size // 2,
                         self.roi_rect.topLeft().y() - handle_size // 2,
                         handle_size, handle_size)  # 左上
        painter.drawRect(self.roi_rect.topRight().x() - handle_size // 2,
                         self.roi_rect.topRight().y() - handle_size // 2,
                         handle_size, handle_size)  # 右上
        painter.drawRect(self.roi_rect.bottomLeft().x() - handle_size // 2,
                         self.roi_rect.bottomLeft().y() - handle_size // 2,
                         handle_size, handle_size)  # 左下
        painter.drawRect(self.roi_rect.bottomRight().x() - handle_size // 2,
                         self.roi_rect.bottomRight().y() - handle_size // 2,
                         handle_size, handle_size)  # 右下

        # 添加四条边的中点控制点
        painter.drawRect(self.roi_rect.center().x() - handle_size // 2,  # 上边中点
                         self.roi_rect.top() - handle_size // 2,
                         handle_size, handle_size)
        painter.drawRect(self.roi_rect.center().x() - handle_size // 2,  # 下边中点
                         self.roi_rect.bottom() - handle_size // 2,
                         handle_size, handle_size)
        painter.drawRect(self.roi_rect.left() - handle_size // 2,  # 左边中点
                         self.roi_rect.center().y() - handle_size // 2,
                         handle_size, handle_size)
        painter.drawRect(self.roi_rect.right() - handle_size // 2,  # 右边中点
                         self.roi_rect.center().y() - handle_size // 2,
                         handle_size, handle_size)

        painter.end()

    def mousePress(self, event):
        #检查是否存在一个 ROI 矩形（self.roi_rect），并且用户按下的是鼠标左键。如果满足条件，则继续处理鼠标按下事件
        if self.roi_rect and event.button() == Qt.LeftButton:
            #获取鼠标在图像坐标系中的当前位置。event.pos() 返回鼠标在窗口中的坐标，
            # self.getImagePosition 将其转换为图像坐标系中的坐标。
            pos = self.getImagePosition(event.pos())
            #定义调整大小的“手柄”（handle）的大小。这里设置为 16像素，表示每个角落的可点击区域是一个 16x16 的正方形。
            handle_size = 16
            #检查鼠标是否点击了 ROI 矩形的 左上角。
            # 如果点击了左上角附近 16x16 的区域，则设置 resizing = True 和 resize_handle = "topLeft"。
            if QRect(self.roi_rect.topLeft().x() - handle_size // 2,
                     self.roi_rect.topLeft().y() - handle_size // 2,
                     handle_size, handle_size).contains(pos):
                self.resizing = True
                self.resize_handle = "topLeft"
            elif QRect(self.roi_rect.topRight().x() - handle_size // 2,
                       self.roi_rect.topRight().y() - handle_size // 2,
                       handle_size, handle_size).contains(pos):
                self.resizing = True
                self.resize_handle = "topRight"
            elif QRect(self.roi_rect.bottomLeft().x() - handle_size // 2,
                       self.roi_rect.bottomLeft().y() - handle_size // 2,
                       handle_size, handle_size).contains(pos):
                self.resizing = True
                self.resize_handle = "bottomLeft"
            elif QRect(self.roi_rect.bottomRight().x() - handle_size // 2,
                       self.roi_rect.bottomRight().y() - handle_size // 2,
                       handle_size, handle_size).contains(pos):
                self.resizing = True
                self.resize_handle = "bottomRight"
                # 检测是否点击了四条边中心点
            elif QRect(self.roi_rect.center().x() - handle_size // 2,
                        self.roi_rect.top() - handle_size // 2,
                        handle_size, handle_size).contains(pos):
                self.resizing = True
                self.resize_handle = "topCenter"
            elif QRect(self.roi_rect.center().x() - handle_size // 2,
                       self.roi_rect.bottom() - handle_size // 2,
                       handle_size, handle_size).contains(pos):
                self.resizing = True
                self.resize_handle = "bottomCenter"
            elif QRect(self.roi_rect.left() - handle_size // 2,
                       self.roi_rect.center().y() - handle_size // 2,
                       handle_size, handle_size).contains(pos):
                self.resizing = True
                self.resize_handle = "leftCenter"
            elif QRect(self.roi_rect.right() - handle_size // 2,
                       self.roi_rect.center().y() - handle_size // 2,
                       handle_size, handle_size).contains(pos):
                self.resizing = True
                self.resize_handle = "rightCenter"
            elif self.roi_rect.contains(pos):
                self.moving = True
                self.last_pos = pos
            #如果鼠标点击了 ROI 矩形的内部（非角落区域），则设置 moving = True，表示用户正在移动 ROI 矩形。
            elif self.roi_rect.contains(pos):
                self.moving = True
                #记录当前鼠标位置，用于后续计算移动的偏移量。
                self.last_pos = pos

    def mouseMove(self, event):
        if self.roi_rect:
            #获取鼠标在图像坐标系中的当前位置。
            # event.pos() 返回鼠标在窗口中的坐标，self.getImagePosition 将其转换为图像坐标系中的坐标。
            pos = self.getImagePosition(event.pos())
            #检查是否正在调整 ROI 矩形的大小。如果是，则进入调整大小的逻辑
            if self.resizing:
                if self.resize_handle == "topLeft":
                    self.roi_rect.setTopLeft(pos)
                elif self.resize_handle == "topRight":
                    self.roi_rect.setTopRight(pos)
                elif self.resize_handle == "bottomLeft":
                    self.roi_rect.setBottomLeft(pos)
                elif self.resize_handle == "bottomRight":
                    self.roi_rect.setBottomRight(pos)
                    # 拖动上边中心点
                elif self.resize_handle == "topCenter":
                    self.roi_rect.setTop(pos.y())
                # 拖动下边中心点
                elif self.resize_handle == "bottomCenter":
                    self.roi_rect.setBottom(pos.y())
                # 拖动左边中心点
                elif self.resize_handle == "leftCenter":
                    self.roi_rect.setLeft(pos.x())
                # 拖动右边中心点
                elif self.resize_handle == "rightCenter":
                    self.roi_rect.setRight(pos.x())
                self.updateDisplay()
            elif self.moving:
                delta = pos - self.last_pos
                #将 ROI 矩形平移 delta 的距离。
                self.roi_rect.translate(delta)
                self.last_pos = pos
                self.updateDisplay()

    def mouseRelease(self, event):
        if event.button() == Qt.LeftButton:
            self.resizing = False
            self.moving = False
            print(f"ROI 坐标: 左上角 ({self.roi_rect.left()}, {self.roi_rect.top()}), "
                  f"右下角 ({self.roi_rect.right()}, {self.roi_rect.bottom()})")

    def saveROI(self):
        if self.roi_rect and self.original_image is not None:
            x1, y1 = self.roi_rect.left(), self.roi_rect.top()
            x2, y2 = self.roi_rect.right(), self.roi_rect.bottom()
            roi = self.original_image[y1:y2, x1:x2]
            if roi.size > 0:
                cv2.imwrite("roi_result.jpg", roi)
                print(f"ROI 已保存为 roi_result.jpg，坐标: ({x1},{y1}) - ({x2},{y2})")
            else:
                print("错误：选择的区域无效")

    def getROICoordinates(self):
        if self.roi_rect:
            return (self.roi_rect.left(), self.roi_rect.top(),
                    self.roi_rect.right(), self.roi_rect.bottom())
        return None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageViewer()
    sys.exit(app.exec_())