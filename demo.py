import cv2

# 全局变量
points = []          # 存储ROI的坐标
cropping = False     # 标记是否正在选择
scale_factor = 0.5   # 显示缩放比例（根据需求调整，例如0.5表示缩小到50%）

def mouse_callback(event, x, y, flags, param):
    global points, cropping, img_display

    # 计算缩放后的坐标需映射回原始图像坐标
    x_orig = int(x / scale_factor)
    y_orig = int(y / scale_factor)

    # 左键按下：记录左上角坐标
    if event == cv2.EVENT_LBUTTONDOWN:
        points = [(x_orig, y_orig)]
        cropping = True

    # 左键释放：记录右下角坐标
    elif event == cv2.EVENT_LBUTTONUP:
        points.append((x_orig, y_orig))
        cropping = False

        # 在原始图像上绘制矩形，然后更新显示图像
        img_copy = img.copy()
        cv2.rectangle(img_copy, points[0], points[1], (0, 255, 0), 2)
        img_display = cv2.resize(img_copy, (0, 0), fx=scale_factor, fy=scale_factor)
        cv2.imshow("Select ROI", img_display)

# 读取原始图像
img = cv2.imread("test.png")
if img is None:
    print("错误：无法加载图像，请检查路径")
    exit()

# 缩放图像用于显示
img_display = cv2.resize(img, (0, 0), fx=scale_factor, fy=scale_factor)

# 创建窗口并绑定鼠标事件
cv2.namedWindow("Select ROI", cv2.WINDOW_NORMAL)  # 允许调整窗口大小
cv2.resizeWindow("Select ROI", img_display.shape[1], img_display.shape[0])
cv2.setMouseCallback("Select ROI", mouse_callback)

while True:
    cv2.imshow("Select ROI", img_display)
    key = cv2.waitKey(1) & 0xFF

    # 按 'r' 重置选择
    if key == ord("r"):
        img_display = cv2.resize(img.copy(), (0, 0), fx=scale_factor, fy=scale_factor)
        points = []

    # 按 'c' 确认选择
    elif key == ord("c"):
        if len(points) == 2:
            break

# 关闭窗口
cv2.destroyAllWindows()

# 提取ROI（处理坐标顺序）
if len(points) == 2:
    (x1, y1), (x2, y2) = points
    x1, x2 = sorted([x1, x2])
    y1, y2 = sorted([y1, y2])
    roi = img[y1:y2, x1:x2]

    # 显示并保存结果
    if roi.size > 0:
        cv2.imwrite("roi_result.jpg", roi)
        print("ROI 已保存为 roi_result.jpg")
    else:
        print("错误：选择的区域无效")
else:
    print("未选择有效区域")