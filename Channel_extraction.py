import cv2
# 读取ROI
img = cv2.imread("test.png")

# 分离通道
b, g, r = cv2.split(img)

# 创建全零矩阵，用于置零不需要的通道
zeros = np.zeros_like(b)

# 只保留R通道
r_only = cv2.merge([zeros, zeros, r])

# 只保留G通道
g_only = cv2.merge([zeros, g, zeros])

# 只保留B通道
b_only = cv2.merge([b, zeros, zeros])

# 显示图像
cv2.imshow("Red Channel", r_only)
cv2.imshow("Green Channel", g_only)
cv2.imshow("Blue Channel", b_only)

# 等待按键按下
cv2.waitKey(0)

# 关闭所有窗口
cv2.destroyAllWindows()
