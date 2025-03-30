import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton,
                             QVBoxLayout, QHBoxLayout, QFileDialog, QComboBox, QDialog,
                             QRadioButton, QSlider, QLineEdit, QSizePolicy)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen
from PyQt5.QtCore import Qt, QPoint, QRect, QTimer


def process_roi(roi_image, channel='r', threshold_type=None, low_thresh=0, high_thresh=33, min_area=3000, offset=(0, 0)):
    if low_thresh > high_thresh:
        low_thresh, high_thresh = high_thresh, low_thresh
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
        return processed_image, []

    if threshold_type == 'auto':
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        binary = cv2.inRange(gray, low_thresh, high_thresh)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    processed_image = roi_image.copy()
    rect_info = []
    x_offset, y_offset = offset  # ROI 偏移量

    for idx, contour in enumerate(contours, 1):  # 从 1 开始编号
        area = cv2.contourArea(contour)
        if area >= min_area:
            rect = cv2.minAreaRect(contour)
            box = cv2.boxPoints(rect)
            box = np.intp(box)

            # 计算中心点和方向
            center = rect[0]  # (center_x, center_y)
            # 加上 ROI 偏移量，转换为全局坐标
            center = (center[0] + x_offset, center[1] + y_offset)
            angle = rect[2]
            rect_info.append((idx, center, angle))

            # 绘制矩形（红色）
            cv2.drawContours(processed_image, [box], 0, (0, 0, 255), 2)

            # 填充区域（绿色）
            mask = np.zeros_like(gray)
            cv2.drawContours(mask, [contour], -1, 255, -1)
            processed_image[mask == 255] = [0, 255, 0]

            # 在矩形中心绘制编号（红色字体）
            font = cv2.FONT_HERSHEY_SIMPLEX
            text = str(idx)
            text_size = cv2.getTextSize(text, font, 1, 2)[0]
            text_x = int(center[0] - x_offset - text_size[0] / 2)  # 局部坐标
            text_y = int(center[1] - y_offset + text_size[1] / 2)
            cv2.putText(processed_image, text, (text_x, text_y), font, 1, (255, 0, 0), 2)

    return processed_image, rect_info

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
        self.low_slider = None
        self.high_slider = None
        self.low_value_label = None
        self.high_value_label = None
        self.area_input = None
        self.rect_info = []  # 初始化矩形信息列表
        self.initUI()

    def initUI(self):
        # 图像标签
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 按钮区域
        btn_load = QPushButton("加载图片", self)
        btn_load.clicked.connect(self.loadImage)

        btn_roi = QPushButton("选择ROI", self)
        btn_roi.clicked.connect(self.createROI)

        btn_save = QPushButton("保存ROI", self)
        btn_save.clicked.connect(self.saveROI)

        btn_process = QPushButton("提取通道", self)
        btn_process.clicked.connect(self.processROI)

        self.channel_combo = QComboBox(self)
        self.channel_combo.addItems(["Red", "Green", "Blue"])

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_load)
        btn_layout.addWidget(btn_roi)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_process)
        btn_layout.addWidget(self.channel_combo)

        btn_params = QPushButton("参数设置", self)
        btn_params.clicked.connect(self.showParamsPanel)  # 修改为显示侧边栏
        btn_layout.addWidget(btn_params)

        # 图像区域布局
        image_layout = QVBoxLayout()
        image_layout.addLayout(btn_layout)
        image_layout.addWidget(self.image_label, stretch=1)

        # 图像区域容器
        self.image_widget = QWidget()
        self.image_widget.setLayout(image_layout)

        # 参数设置面板（侧边栏）
        self.params_panel = QWidget()
        self.params_layout = QVBoxLayout()
        self.setupParamsPanel()  # 初始化参数面板
        self.params_panel.setLayout(self.params_layout)
        self.params_panel.hide()  # 默认隐藏

        # 主布局：左侧图像，右侧参数面板
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.image_widget, stretch=3)  # 图像占 3/4
        main_layout.addWidget(self.params_panel, stretch=1)  # 面板占 1/4
        self.setLayout(main_layout)

        self.setWindowTitle('PyQt5')
        self.show()
        self.setMinimumSize(800, 600)

    def forceRefresh(self):
        if self.roi_rect:
            self.applyThreshold()
            self.updateDisplay()

    def setupParamsPanel(self):
        #添加 setupParamsPanel 方法，初始化参数面板
        # 单选按钮：自动/手动二值化
        auto_radio = QRadioButton("自动二值化")
        manual_radio = QRadioButton("手动二值化")
        auto_radio.setChecked(self.threshold_type == 'auto')
        manual_radio.setChecked(self.threshold_type == 'manual')

        # 低阈值滑条 + 动态标签
        low_layout = QHBoxLayout()
        low_label = QLabel("低阈值:")
        self.low_slider = QSlider(Qt.Horizontal)
        self.low_slider.setRange(0, 255)
        self.low_slider.setValue(self.low_thresh)
        self.low_value_label = QLabel(f"{self.low_thresh}")
        self.low_value_label.setFixedWidth(30)
        self.low_slider.valueChanged.connect(
            lambda value: [self.setLowThresh(value), self.low_value_label.setText(f"{value}")])
        low_layout.addWidget(low_label)
        low_layout.addWidget(self.low_slider)
        low_layout.addWidget(self.low_value_label)

        # 高阈值滑条 + 动态标签
        high_layout = QHBoxLayout()
        high_label = QLabel("高阈值:")
        self.high_slider = QSlider(Qt.Horizontal)
        self.high_slider.setRange(0, 255)
        self.high_slider.setValue(self.high_thresh)
        self.high_value_label = QLabel(f"{self.high_thresh}")
        self.high_value_label.setFixedWidth(30)
        self.high_slider.valueChanged.connect(
            lambda value: [self.setHighThresh(value), self.high_value_label.setText(f"{value}")])
        high_layout.addWidget(high_label)
        high_layout.addWidget(self.high_slider)
        high_layout.addWidget(self.high_value_label)

        # 最小面积输入框
        area_layout = QHBoxLayout()
        area_label = QLabel("最小面积:")
        self.area_input = QLineEdit(str(self.min_area))
        self.area_input.textChanged.connect(self.setMinArea)
        area_layout.addWidget(area_label)
        area_layout.addWidget(self.area_input)

        # 根据初始状态设置滑条启用/禁用
        self.low_slider.setEnabled(self.threshold_type == 'manual')
        self.high_slider.setEnabled(self.threshold_type == 'manual')

        # 单选按钮切换逻辑
        auto_radio.toggled.connect(lambda checked: self.onThresholdTypeChanged(checked, 'auto'))
        manual_radio.toggled.connect(lambda checked: self.onThresholdTypeChanged(checked, 'manual'))

        self.params_layout.addWidget(auto_radio)
        self.params_layout.addWidget(manual_radio)
        self.params_layout.addLayout(low_layout)
        self.params_layout.addLayout(high_layout)
        self.params_layout.addLayout(area_layout)

        # 确定按钮
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.hideParamsPanel)
        self.params_layout.addWidget(ok_btn)

        # 添加伸缩项，确保控件靠上
        self.params_layout.addStretch()
    def setThresholdType(self, type):
        self.threshold_type = type
        print(f"设置阈值类型: {type}")

    def setMinArea(self, text):
        try:
            self.min_area = int(text)
            print(f"设置最小面积: {self.min_area}")
            QTimer.singleShot(500, self.applyThreshold)  # 延迟 500ms
        except ValueError:
            self.min_area = 3000
            print("面积输入无效，使用默认值 3000")
            QTimer.singleShot(500, self.applyThreshold)

    def applyThreshold(self):
        self.rect_info = []  # 清空，确保编号从头开始
        if self.roi_rect and self.pristine_image is not None:
            x1, y1 = self.roi_rect.left(), self.roi_rect.top()
            x2, y2 = self.roi_rect.right(), self.roi_rect.bottom()
            roi = self.pristine_image[y1:y2, x1:x2]
            if roi.size > 0:
                channel = self.channel_combo.currentText().lower()[0]
                gray_roi, _ = process_roi(roi, channel, threshold_type=None, offset=(x1, y1))
                processed_roi, self.rect_info = process_roi(gray_roi, channel, self.threshold_type,
                                                            self.low_thresh, self.high_thresh, self.min_area,
                                                            offset=(x1, y1))
                new_image = self.pristine_image.copy()
                new_image[y1:y2, x1:x2] = processed_roi
                self.original_image = new_image
                self.updateDisplay()
            else:
                print("错误：选择的区域无效")
                self.rect_info = []
        else:
            print("无 ROI 或原始图像未加载")
            self.rect_info = []

    def loadImage(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "Image Files (*.png *.jpg *.jpeg)")
        if filename:
            self.original_image = cv2.imread(filename)
            if self.original_image is not None:
                self.pristine_image = self.original_image.copy()  # 保存原始副本
                self.roi_rect = None
                self.updateDisplay()

    def resizeEvent(self, event):
        self.updateDisplay()  # 窗口大小变化时刷新图像
        super().resizeEvent(event)  # 调用父类的 resizeEvent

    def showParamsDialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("参数设置")
        layout = QVBoxLayout()

        # 单选按钮：自动/手动二值化
        auto_radio = QRadioButton("自动二值化", dialog)
        manual_radio = QRadioButton("手动二值化", dialog)
        auto_radio.setChecked(self.threshold_type == 'auto')
        manual_radio.setChecked(self.threshold_type == 'manual')

        # 低阈值滑条 + 动态标签
        low_layout = QHBoxLayout()
        low_label = QLabel("低阈值:", dialog)
        low_slider = QSlider(Qt.Horizontal, dialog)
        low_slider.setRange(0, 255)
        low_slider.setValue(self.low_thresh)
        low_value_label = QLabel(f"{self.low_thresh}", dialog)
        low_value_label.setFixedWidth(30)
        low_slider.valueChanged.connect(lambda value: [self.setLowThresh(value), low_value_label.setText(f"{value}")])
        low_layout.addWidget(low_label)
        low_layout.addWidget(low_slider)
        low_layout.addWidget(low_value_label)
        layout.addLayout(low_layout)

        # 高阈值滑条 + 动态标签
        high_layout = QHBoxLayout()
        high_label = QLabel("高阈值:", dialog)
        high_slider = QSlider(Qt.Horizontal, dialog)
        high_slider.setRange(0, 255)
        high_slider.setValue(self.high_thresh)
        high_value_label = QLabel(f"{self.high_thresh}", dialog)
        high_value_label.setFixedWidth(30)
        high_slider.valueChanged.connect(
            lambda value: [self.setHighThresh(value), high_value_label.setText(f"{value}")])
        high_layout.addWidget(high_label)
        high_layout.addWidget(high_slider)
        high_layout.addWidget(high_value_label)
        layout.addLayout(high_layout)

        # 最小面积输入框
        area_layout = QHBoxLayout()
        area_label = QLabel("最小面积:", dialog)
        area_input = QLineEdit(str(self.min_area), dialog)
        area_input.textChanged.connect(self.setMinArea)
        area_layout.addWidget(area_label)
        area_layout.addWidget(area_input)
        layout.addLayout(area_layout)

        # 根据初始状态设置滑条启用/禁用
        low_slider.setEnabled(self.threshold_type == 'manual')
        high_slider.setEnabled(self.threshold_type == 'manual')

        # 单选按钮切换逻辑
        auto_radio.toggled.connect(
            lambda checked: self.onThresholdTypeChanged(checked, 'auto', low_slider, high_slider))
        manual_radio.toggled.connect(
            lambda checked: self.onThresholdTypeChanged(checked, 'manual', low_slider, high_slider))

        layout.addWidget(auto_radio)
        layout.addWidget(manual_radio)

        # 确定按钮
        ok_btn = QPushButton("确定", dialog)
        ok_btn.clicked.connect(lambda: [self.applyThreshold(), dialog.accept()])
        layout.addWidget(ok_btn)

        dialog.setLayout(layout)
        dialog.exec_()

    def onThresholdTypeChanged(self, checked, threshold_type):
        if checked:
            self.threshold_type = threshold_type
            if threshold_type == 'auto':
                self.low_slider.setEnabled(False)#禁用滑条
                self.high_slider.setEnabled(False)
            else:
                self.low_slider.setEnabled(True)
                self.high_slider.setEnabled(True)
            self.applyThreshold()

    def showParamsPanel(self):
        self.params_panel.show()
        self.applyThreshold()  # 打开时刷新，确保显示最新状态

    def hideParamsPanel(self):
        self.params_panel.hide()
        self.applyThreshold()
        # 输出矩形信息
        if self.rect_info:
            print("最小外接矩形信息：")
            for idx, center, angle in self.rect_info:
                print(f"矩形 {idx}: 中心点 ({center[0]:.2f}, {center[1]:.2f}), 方向: {angle:.2f} 度")
        else:
            print("没有检测到最小外接矩形")

    def setLowThresh(self, value):
        self.low_thresh = min(int(value), 255)
        if self.low_thresh > self.high_thresh:
            self.low_thresh = self.high_thresh
        self.applyThreshold()  # 实时应用

    def setHighThresh(self, value):
        self.high_thresh = min(int(value), 255)
        if self.high_thresh < self.low_thresh:
            self.high_thresh = self.low_thresh
        self.applyThreshold()  # 实时应用

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
        h, w, ch = self.original_image.shape
        bytes_per_line = ch * w
        image_rgb = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)
        q_img = QImage(image_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.display_image = QPixmap.fromImage(q_img)

        pixmap = self.display_image.copy()
        if self.roi_rect:
            self.drawROI(pixmap)

        # 动态缩放到 image_label 的大小
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.update()

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
        self.rect_info = []  # 清空，确保编号从头开始
        if self.roi_rect and self.pristine_image is not None:
            x1, y1 = self.roi_rect.left(), self.roi_rect.top()
            x2, y2 = self.roi_rect.right(), self.roi_rect.bottom()
            roi = self.pristine_image[y1:y2, x1:x2]
            if roi.size > 0:
                channel = self.channel_combo.currentText().lower()[0]
                processed_roi, self.rect_info = process_roi(roi, channel, threshold_type=None, offset=(x1, y1))
                new_image = self.pristine_image.copy()
                new_image[y1:y2, x1:x2] = processed_roi
                self.original_image = new_image
                self.updateDisplay()
                # print("通道提取完成，ROI 区域已变灰")
            else:
                print("错误：选择的区域无效")
                self.rect_info = []
        else:
            print("无 ROI 或原始图像未加载")
            self.rect_info = []

    def getROICoordinates(self):
        if self.roi_rect:
            return (self.roi_rect.left(), self.roi_rect.top(),
                    self.roi_rect.right(), self.roi_rect.bottom())
        return None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageViewer()
    sys.exit(app.exec_())