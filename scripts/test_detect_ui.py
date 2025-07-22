"""
游戏UI元素检测 - 使用Segment Anything Model (SAM)
该代码实现了基于SAM的游戏UI界面元素、可交互对象和文本选项的检测
"""

import os
import cv2
import numpy as np
import torch
import matplotlib.pyplot as plt
from PIL import Image
import time
from typing import List, Tuple, Dict, Any, Optional
import pytesseract
import scipy.ndimage as ndimage
from sklearn.cluster import DBSCAN
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator

# SAM模型下载与加载
def download_sam_model():
    if not os.path.exists("./weights/sam_vit_h_4b8939.pth"):
        print("正在下载SAM模型...")
        os.system("wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth")
    
    # 或者使用更轻量级的模型
    if not os.path.exists("./weights/sam_vit_b_01ec64.pth"):
        print("正在下载SAM轻量级模型...")
        os.system("wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth")

# 加载SAM模型
def load_sam_model(model_type="vit_h"):
    from segment_anything import sam_model_registry, SamPredictor
    
    # 根据可用资源选择合适的模型
    if model_type == "vit_h" and os.path.exists("./weights/sam_vit_h_4b8939.pth"):
        sam = sam_model_registry["vit_h"](checkpoint="./weights/sam_vit_h_4b8939.pth")
    else:
        # 默认使用更轻量级的模型
        sam = sam_model_registry["vit_b"](checkpoint="./weights/sam_vit_b_01ec64.pth")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    sam.to(device)
    
    return SamPredictor(sam)


import cv2
import numpy as np
import time
from typing import List, Dict, Any
from segment_anything import sam_model_registry, SamPredictor, SamAutomaticMaskGenerator


class RefinedGameUIDetector:
    def __init__(self):
        # 加载 SAM 模型
        self.predictor = load_sam_model()
        self.mask_generator = SamAutomaticMaskGenerator(
            model=self.predictor.model,
            points_per_side=32,
            pred_iou_thresh=0.86,
            stability_score_thresh=0.92,
            min_mask_region_area=100,
        )

    def compute_iou(self, boxA, boxB):
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        interArea = max(0, xB - xA) * max(0, yB - yA)
        if interArea == 0:
            return 0.0
        areaA = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        areaB = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        return interArea / float(areaA + areaB - interArea)

    def overlap_ratio_to_self(self, boxA, boxB):
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        interArea = max(0, xB - xA) * max(0, yB - yA)
        areaA = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        return interArea / areaA if areaA > 0 else 0.0

    def remove_redundant_masks(self, masks, cover_thresh=0.6):
        boxes = []
        for m in masks:
            x, y, w, h = m["bbox"]
            boxes.append([x, y, x + w, y + h])

        centers = np.array([[(b[0] + b[2]) // 2, (b[1] + b[3]) // 2] for b in boxes])
        clustering = DBSCAN(eps=35, min_samples=1).fit(centers)
        labels = clustering.labels_

        deduped = []
        for lbl in set(labels):
            group = [m for i, m in enumerate(masks) if labels[i] == lbl]
            group = sorted(group, key=lambda x: x["predicted_iou"], reverse=True)
            kept = []
            for m in group:
                x, y, w, h = m["bbox"]
                boxA = [x, y, x + w, y + h]
                if all(self.overlap_ratio_to_self(boxA, [fx, fy, fx + fw, fy + fh]) < cover_thresh
                       for fx, fy, fw, fh in [b["bbox"] for b in kept]):
                    kept.append(m)
            deduped.extend(kept[:1])  # 每个簇保留一个
        return deduped

    def refine_with_point_prompt(self, frame_rgb, filtered_masks):
        self.predictor.set_image(frame_rgb)
        refined = []
        for m in filtered_masks:
            x, y, w, h = m["bbox"]
            cx, cy = x + w // 2, y + h // 2
            point_coords = np.array([[cx, cy]])
            point_labels = np.array([1])
            try:
                masks, scores, _ = self.predictor.predict(
                    point_coords=point_coords,
                    point_labels=point_labels,
                    multimask_output=False
                )
                if scores[0] > 0.7:
                    refined.append({
                        "bbox": [x, y, x + w, y + h],
                        "mask": masks[0],
                        "score": float(scores[0])
                    })
            except Exception as e:
                print(f"Refinement error: {e}")
        return refined

    def final_deduplicate(self, refined_masks):
        results = []
        for m in sorted(refined_masks, key=lambda x: x["score"], reverse=True):
            boxA = m["bbox"]
            if all(self.overlap_ratio_to_self(boxA, f["bbox"]) < 0.5 for f in results):
                results.append(m)
        return results

    def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        start_time = time.time()

        if len(frame.shape) == 2:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
        elif frame.shape[2] == 4:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)
        elif frame.shape[2] == 3:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            raise ValueError("Unsupported image format")

        # Stage 1: 初步掩码生成
        initial_masks = self.mask_generator.generate(frame_rgb)
        filtered_initial = self.remove_redundant_masks(initial_masks)

        # Stage 2: 用点提示 refine 掩码
        refined_masks = self.refine_with_point_prompt(frame_rgb, filtered_initial)

        # Stage 3: 再次去重
        # final_elements = self.final_deduplicate(refined_masks)

        processing_time = time.time() - start_time
        return {
            "ui_elements": [{
                "bbox": e["bbox"],
                "mask": e["mask"],
                "confidence": e["score"]
            } for e in filtered_initial],
            "processing_time": processing_time
        }



    def visualize_results(self, frame: np.ndarray, ui_elements: List[Dict[str, Any]], output_path: Optional[str] = None):
        """可视化检测结果"""
        # 创建副本以进行绘图
        vis_image = frame.copy()
        
        for element in ui_elements:
            bbox = element["bbox"]
            
            # 获取元素颜色
            color = (0, 255, 0)
            
            # 绘制边界框
            cv2.rectangle(vis_image, 
                         (bbox[0], bbox[1]), 
                         (bbox[2], bbox[3]), 
                         color, 
                         2)
            
            
            # 如果有文本，则显示
            if "text" in element:
                text = element["text"]
                text = text.replace('\n', ' ')  # 替换换行符为空格
                if len(text) > 20:
                    text = text[:17] + "..."  # 截断长文本
                
                cv2.putText(vis_image, 
                           text, 
                           (bbox[0], bbox[3] + 15), 
                           cv2.FONT_HERSHEY_SIMPLEX, 
                           0.4, 
                           (255, 255, 255), 
                           1)
        
        # 显示图像
        plt.figure(figsize=(12, 8))
        plt.imshow(cv2.cvtColor(vis_image, cv2.COLOR_BGR2RGB))
        plt.axis('off')
        plt.title('Game UI Detection Results')
        
        # 保存结果
        if output_path:
            plt.savefig(output_path, bbox_inches='tight', dpi=300)
            print(f"结果已保存到 {output_path}")
        
        plt.show()
        
        return vis_image

    def process_image_file(self, image_path: str, output_path: Optional[str] = None):
        """处理图像文件"""
        # 加载图像
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"无法加载图像: {image_path}")
        
        # 处理图像
        results = self.process_frame(image)
        ui_elements = results["ui_elements"]
        processing_time = results["processing_time"]
        
        print(f"处理完成, 用时 {processing_time:.2f} 秒")
        print(f"检测到 {len(ui_elements)} 个UI元素")
        
        # 可视化结果
        self.visualize_results(image, ui_elements, output_path)
        
        return ui_elements

def main():
    # 创建检测器实例
    detector = RefinedGameUIDetector()
    
    # 处理示例图像
    # 使用你自己的游戏截图路径
    image_path = "./scripts/images/20.jpg"  # 替换为实际路径
    
    try:
        if os.path.exists(image_path):
            print(f"处理图像: {image_path}")
            detector.process_image_file(image_path, "detection_result.png")
        else:
            print(f"图像文件不存在: {image_path}")
            print("请提供有效的游戏截图路径")
    except Exception as e:
        print(f"处理过程中出错: {e}")
        
if __name__ == "__main__":
    main()