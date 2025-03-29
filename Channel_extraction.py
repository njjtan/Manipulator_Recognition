# roi_processor.py
import cv2
import numpy as np
def process_roi(roi_image, channel='r'):
    """
    处理 ROI 区域，提取指定通道并转为灰度图像
    参数:
        roi_image: ROI 区域的图像 (numpy 数组)
        channel: 通道选择，'r'、'g' 或 'b'
    返回:
        processed_image: 处理后的图像 (numpy 数组)
    """
    # 分离通道
    b, g, r = cv2.split(roi_image)

    # 根据选择的通道返回灰度图像
    if channel == 'r':
        gray = r
    elif channel == 'g':
        gray = g
    elif channel == 'b':
        gray = b
    else:
        gray = r  # 默认红色通道

    # 将单通道灰度图转回三通道，以便后续显示
    processed_image = cv2.merge([gray, gray, gray])
    return processed_image