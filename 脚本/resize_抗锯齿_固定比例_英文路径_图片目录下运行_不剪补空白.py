
# 定义缩放后的图片尺寸
new_width1 = int(input("宽"))
new_height1 = int(input("高"))

import cv2
import os
import numpy as np

# 定义缩放后的图片尺寸

# 创建一个新文件夹用于保存处理后的图片
output_folder = 'processed_images'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 遍历当前目录下所有的图片文件
for filename in os.listdir('.'):
    new_width = new_width1
    new_height = new_height1
    if filename.endswith('.jpg') or filename.endswith('.png') or filename.endswith('.jpeg'):
        # 读取原始图片
        img = cv2.imread(filename, cv2.IMREAD_UNCHANGED)
        
        # 获取原始图片的尺寸
        height, width, channels = img.shape
        
        # 计算宽高缩放比例，并取最小值
        scale_x = new_width / width
        scale_y = new_height / height
        scale = min(scale_x, scale_y)
        
        # 计算新的宽和高
        new_width = int(width * scale)
        new_height = int(height * scale)
        # print("width is: "+str(width))
        # print("height is: "+str(height))
        # print("new_width is: "+str(new_width))
        # print("new_height is: "+str(new_height))
        # 创建一个透明的黑色背景图像
        background = cv2.cvtColor(np.zeros((new_height1, new_width1, 4), np.uint8), cv2.COLOR_BGR2BGRA)

        # 计算图像在新背景中的位置
        x_offset = int((new_width - width*scale) / 2)
        y_offset = int((new_height - height*scale) / 2)
        
        # 缩放原始图片并将其复制到新背景上
        resized_img = cv2.resize(img, (new_width, new_height),interpolation=cv2.INTER_AREA)

        resized_img_rgba = cv2.cvtColor(resized_img, cv2.COLOR_RGB2RGBA)


        background[y_offset:y_offset+new_height, x_offset:x_offset+new_width] = resized_img_rgba

        # 将PNG图片保存到输出文件夹中

        # 保存处理后的图片到新文件夹中
        cv2.imwrite(os.path.join(output_folder, filename+".png"), background)

