import cv2
import numpy as np

# 读取图像并转为灰度图
img = cv2.imread("roi_result.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# 定义像素阈值（0-33灰度范围）
low_thresh = 0
high_thresh = 33

# 生成初始掩膜
mask = cv2.inRange(gray, low_thresh, high_thresh)

# 寻找连通区域
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# 面积阈值设置
min_area = 3000  # 最小保留面积

# 创建过滤后的掩膜
filtered_mask = np.zeros_like(mask)

for cnt in contours:
    area = cv2.contourArea(cnt)
    if area >= min_area:
        # 绘制到过滤掩膜
        cv2.drawContours(filtered_mask, [cnt], -1, 255, -1)

        # 计算最小外接矩形
        rect = cv2.minAreaRect(cnt)
        box = cv2.boxPoints(rect)  # 获取矩形顶点
        box = np.int0(box)  # 坐标转换为整数

        # 在原图上绘制红色矩形框
        cv2.drawContours(img, [box], 0, (0, 0, 255), 2)  # 红色，线宽2像素

# 将符合要求的区域填充为绿色
img[filtered_mask == 255] = [0, 255, 0]

# 显示并保存结果
cv2.imshow('Result with Bounding Boxes', img)
cv2.waitKey(0)
cv2.destroyAllWindows()
cv2.imwrite('result_with_boxes.jpg', img)