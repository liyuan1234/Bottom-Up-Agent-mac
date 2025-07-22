from transformers import pipeline
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt

# 1) 用 image-segmentation 任务加载 SegFormer
segmenter = pipeline(
    task="image-segmentation",
    model="nvidia/segformer-b5-finetuned-ade-640-640",
    device=0
)  # 该管道支持语义分割模型 :contentReference[oaicite:2]{index=2}

# 2) 读取游戏界面截图
image = Image.open("./scripts/images/1.jpg").convert("RGB")
img_np = np.array(image)
h, w, _ = img_np.shape

# 3) 执行分割推理
#    返回格式: List[{"label": str, "mask": PIL.Image(mode='L')}]
results = segmenter(image)

# 4) 定义固定调色板（示例 5 种高对比颜色）
palette = [
    (255,   0,   0),  # 红
    (  0, 255,   0),  # 绿
    (  0,   0, 255),  # 蓝
    (255, 255,   0),  # 黄
    (255,   0, 255),  # 品红
]  # 循环使用保证一致性:contentReference[oaicite:4]{index=4}

# 5) 为每个 mask 创建固体覆盖
overlay = img_np.copy()
for idx, inst in enumerate(results):
    # 转为布尔数组：True 表示掩码内像素
    mask = np.array(inst["mask"], dtype=bool)
    color = palette[idx % len(palette)]
    # 直接替换掩码区域像素为指定颜色
    overlay[mask] = color  # solid overlay，无透明度:contentReference[oaicite:5]{index=5}

# 6) 可视化展示
plt.figure(figsize=(12, 8))
plt.imshow(overlay)
plt.axis('off')
plt.title("Game UI Segmentation – One Mask One Color")
plt.show()  # 清晰展示每个掩码的固有颜色:contentReference[oaicite:6]{index=6}