import numpy as np
# 测试一个新点
u, v = 320, 240  # 图像中心点
pixel = np.array([[u, v, 1]], dtype=np.float32).T
# 读取单应性矩阵
# 从.npy读取
H_loaded_npy = np.load('G:/Manipulator_Recognition/homography.npy')
# 用.npy读取的矩阵映射
robot = H_loaded_npy @ pixel
robot = robot / robot[2]  # 归一化
x, y = robot[0, 0], robot[1, 0]
z = 0.1  # 已知高度

print(f"\n使用.npy读取的矩阵，测试点 ({u}, {v}) 映射到机械臂坐标: ({x:.3f}, {y:.3f}, {z})")