import cv2
import numpy as np

# 棋盘格参数
pattern_size = (8, 10)  # 角点数

# 拍一张照片
img = cv2.imread('G:/Manipulator_Recognition/chessboard_roi.jpg')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
ret, corners = cv2.findChessboardCorners(gray, pattern_size, None)
if not ret:
    print("角点检测失败！")
    exit()

# 精确化角点
corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1),
                                   criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))

# 选择4个角点（左上、右上、左下、右下）
indices = [0, 7, 72, 79]  # 8x10角点，索引：0(左上), 7(右上), 72(左下), 79(右下)
pixel_coords = corners_refined[indices].reshape(-1, 2)

# 手动输入机械臂坐标
robot_coords = np.zeros((4, 2), dtype=np.float32)
for i, idx in enumerate(indices):
    print(f"请将机械臂移动到角点 {idx}（像素坐标: {pixel_coords[i]}），输入坐标 (x, y):")
    x, y = map(float, input().split())  # 示例：100 200
    robot_coords[i] = [x, y]

# 计算单应性矩阵
H, _ = cv2.findHomography(pixel_coords, robot_coords)

# 保存
np.save('G:/Manipulator_Recognition/homography.npy', H)
print("单应性矩阵:\n", H)