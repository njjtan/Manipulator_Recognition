import cv2
import numpy as np

# 编造的点对
pixel_coords = np.array([
    [100, 100],  # 点1：左上
    [540, 100],  # 点2：右上
    [100, 380],  # 点3：左下
    [540, 380],  # 点4：右下
    [320, 100],  # 点5：上中
    [320, 380],  # 点6：下中
    [100, 240],  # 点7：左中
    [540, 240]   # 点8：右中
], dtype=np.float32)

robot_coords = np.array([
    [0.0, 0.0],   # 点1：左上
    [0.5, 0.0],   # 点2：右上
    [0.0, 0.4],   # 点3：左下
    [0.5, 0.4],   # 点4：右下
    [0.25, 0.0],  # 点5：上中
    [0.25, 0.4],  # 点6：下中
    [0.0, 0.2],   # 点7：左中
    [0.5, 0.2]    # 点8：右中
], dtype=np.float32)

# 计算单应性矩阵
H, _ = cv2.findHomography(pixel_coords, robot_coords)
print("单应性矩阵 H:\n", H)

# 存到文件（用.npy格式，推荐）
np.save('G:/Manipulator_Recognition/homography.npy', H)
print("已存到 G:/Manipulator_Recognition/homography.npy")



