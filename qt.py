import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton,
                             QVBoxLayout, QHBoxLayout, QFileDialog,QComboBox,QDialog,
                             QRadioButton,QSlider,QLineEdit)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen
from PyQt5.QtCore import Qt, QPoint, QRect

def process_roi(roi_image, channel='r', threshold_type=None, low_thresh=0, high_thresh=33, min_area=3000):
    b, g, r = cv2.split(roi_image)
    if channel == 'r':
        gray = r
    elif channel == 'g':
        gray = g
    elif channel == 'b':
        gray = b
    else:
        gray = r

    if threshold_type is None:
        processed_image = cv2.merge([gray, gray, gray])
        return processed_image

    if threshold_type == 'auto':
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        # 手动二值化：只标记像素值在 low_thresh 到 high_thresh 之间的区域
        _, binary = cv2.threshold(gray, low_thresh, high_thresh, cv2.THRESH_BINARY)
        print(f"手动二值化: 低 {low_thresh}, 高 {high_thresh}")

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    processed_image = roi_image.copy()

    for contour in contours:
        area = cv2.contourArea(contour)
        if area >= min_area:
            cv2.drawContours(processed_image, [contour], -1, (0, 255, 0), thickness=2)  # 绿点标记
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(processed_image, (x, y), (x + w, y + h), (0, 255, 0), 2)  # 外接矩形

    return processed_image

class ImageViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.original_image = None
        self.pristine_image = None
        self.display_image = None
        self.roi_rect = None
        self.resizing = False
        self.moving = False
        self.resize_handle = None
        self.threshold_type = 'auto'
        self.low_thresh = 0
        self.high_thresh = 33
        self.min_area = 3000
        self.channel_combo = None
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

        btn_process = QPushButton("提取通道",self)
        btn_process.clicked.connect(self.processROI)

        #添加下拉菜单选择通道
        self.channel_combo = QComboBox(self)
        self.channel_combo.addItems(["Red", "Green", "Blue"])
        #创建一个水平布局（QHBoxLayout），并将多个控件（如按钮和下拉框）添加到这个布局中
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_load)
        btn_layout.addWidget(btn_roi)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_process)
        btn_layout.addWidget(self.channel_combo)

        btn_params = QPushButton("参数设置", self)
        btn_params.clicked.connect(self.showParamsDialog)
        btn_layout.addWidget(btn_params)


        main_layout = QVBoxLayout()
        main_layout.addLayout(btn_layout)
        main_layout.addWidget(self.image_label)
        self.setLayout(main_layout)

        self.setWindowTitle('PyQt5')
        self.show()

    def setThresholdType(self, type):
        self.threshold_type = type
        print(f"设置阈值类型: {type}")

    def setLowThresh(self, value):
        self.low_thresh = value
        print(f"设置低阈值: {value}")

    def setHighThresh(self, value):
        self.high_thresh = value
        print(f"设置高阈值: {value}")

    def setMinArea(self, text):
        try:
            self.min_area = int(text)
            print(f"设置最小面积: {self.min_area}")
        except ValueError:
            self.min_area = 3000
            print("面积输入无效，使用默认值 3000")

    def applyThreshold(self):
        if self.roi_rect and self.original_image is not None:
            print("开始应用阈值...")
            x1, y1 = self.roi_rect.left(), self.roi_rect.top()
            x2, y2 = self.roi_rect.right(), self.roi_rect.bottom()
            roi = self.original_image[y1:y2, x1:x2]
            if roi.size > 0:
                channel = self.channel_combo.currentText().lower()[0]
                processed_roi = process_roi(roi, channel, self.threshold_type,
                                            self.low_thresh, self.high_thresh, self.min_area)
                new_image = self.original_image.copy()
                new_image[y1:y2, x1:x2] = processed_roi
                self.original_image = new_image
                self.updateDisplay()
                print("阈值应用完成")
            else:
                print("错误：选择的区域无效")

    def loadImage(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "Image Files (*.png *.jpg *.jpeg)")
        if filename:
            self.original_image = cv2.imread(filename)
            if self.original_image is not None:
                self.pristine_image = self.original_image.copy()  # 保存原始副本
                self.roi_rect = None
                self.updateDisplay()

    def showParamsDialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("参数设置")
        layout = QVBoxLayout()

        auto_radio = QRadioButton("自动二值化", dialog)
        manual_radio = QRadioButton("手动二值化", dialog)
        auto_radio.setChecked(self.threshold_type == 'auto')
        manual_radio.setChecked(self.threshold_type == 'manual')
        auto_radio.toggled.connect(lambda checked: self.setThresholdType('auto') if checked else None)
        manual_radio.toggled.connect(lambda checked: self.setThresholdType('manual') if checked else None)
        layout.addWidget(auto_radio)
        layout.addWidget(manual_radio)

        low_slider = QSlider(Qt.Horizontal, dialog)
        low_slider.setRange(0, 100)  # 保持 0-100，但后面映射到 0-255
        low_slider.setValue(self.low_thresh)
        low_slider.valueChanged.connect(self.setLowThresh)
        layout.addWidget(QLabel("低阈值:"))
        layout.addWidget(low_slider)

        high_slider = QSlider(Qt.Horizontal, dialog)
        high_slider.setRange(0, 300)  # 示例要 0-300
        high_slider.setValue(self.high_thresh)
        high_slider.valueChanged.connect(self.setHighThresh)
        layout.addWidget(QLabel("高阈值:"))
        layout.addWidget(high_slider)

        area_input = QLineEdit(str(self.min_area), dialog)
        area_input.textChanged.connect(self.setMinArea)
        layout.addWidget(QLabel("最小面积:"))
        layout.addWidget(area_input)

        ok_btn = QPushButton("确定", dialog)
        ok_btn.clicked.connect(lambda checked: [dialog.accept(), self.applyThreshold()])
        layout.addWidget(ok_btn)

        dialog.setLayout(layout)
        print("对话框初始化完成")
        dialog.exec_()

    def onAutoToggled(self, checked):
        if checked:
            self.setThresholdType('auto')

    def onManualToggled(self, checked):
        if checked:
            self.setThresholdType('manual')

    def onDialogAccept(self, dialog):
        dialog.accept()
        self.applyThreshold()

    def updateDisplay(self):
        if self.original_image is None:
            return
        h, w, ch = self.original_image.shape  # 用 original_image
        bytes_per_line = ch * w
        image_rgb = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)  # 从 original_image 转换
        q_img = QImage(image_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.display_image = QPixmap.fromImage(q_img)  # 生成 QPixmap
        pixmap = self.display_image.copy()
        if self.roi_rect:
            self.drawROI(pixmap)  # 绘制 ROI 框
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.update()  # 确保刷新

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
        handle_size = 16
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
            # print(f"ROI 坐标: 左上角 ({self.roi_rect.left()}, {self.roi_rect.top()}), "
            #       f"右下角 ({self.roi_rect.right()}, {self.roi_rect.bottom()})")

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

    def processROI(self):
        if self.roi_rect and self.pristine_image is not None:
            x1, y1 = self.roi_rect.left(), self.roi_rect.top()
            x2, y2 = self.roi_rect.right(), self.roi_rect.bottom()
            roi = self.pristine_image[y1:y2, x1:x2]  # 从原始图像取 ROI
            if roi.size > 0:
                channel = self.channel_combo.currentText().lower()[0]
                processed_roi = process_roi(roi, channel, threshold_type=None)
                new_image = self.pristine_image.copy()  # 从原始图像复制
                new_image[y1:y2, x1:x2] = processed_roi
                self.original_image = new_image  # 更新当前图像
                self.updateDisplay()
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