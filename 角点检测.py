import cv2
import numpy as np

img = cv2.imread('3.jpg')  # 替换为你的照片路径
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
pattern_size = (7, 9)  # 你的棋盘格内角点数（列，行）
ret, corners = cv2.findChessboardCorners(gray, pattern_size, None)

if ret:
    print("角点检测成功！")
    cv2.drawChessboardCorners(img, pattern_size, corners, ret)
    cv2.imshow('Corners', img)
    cv2.waitKey(0)
else:
    print("角点检测失败，检查棋盘格是否平整或背景是否干扰。")
cv2.destroyAllWindows()