import torch
import numpy as np
import cv2
from segment_anything import SamAutomaticMaskGenerator, sam_model_registry, SamPredictor
import clip
from PIL import Image
from typing import List, Dict

class CLIP:
    def __init__(self, model_name: str = "ViT-B/32", use_gpu: bool = True):

        self.device = torch.device("cuda" if torch.cuda.is_available() and use_gpu else "cpu")
        
        self.model, self.preprocess = clip.load(model_name, device=self.device)
        self.model.eval()
    
    def encode_text(self, text_query: str, max_length: int = 77) -> np.ndarray:
        text_query = text_query[:max_length]

        with torch.no_grad():
            text_tokens = clip.tokenize([text_query]).to(self.device)
            text_features = self.model.encode_text(text_tokens)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        
        text_features_np = text_features.cpu().numpy()
        return text_features_np
    
    def encode_image(self, img_cv) -> np.ndarray:
        pil_img = Image.fromarray(img_cv.astype('uint8'))
        image = self.preprocess(pil_img).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            features = self.model.encode_image(image)
            features = features / features.norm(dim=-1, keepdim=True)
        
        features_np = features.cpu().numpy()
        return features_np
    
class Detector:
    def __init__(self, config):
        self.type = config['detector']['sam_type']
        self.weights = config['detector']['sam_weights']
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        sam = sam_model_registry[self.type](checkpoint=self.weights)
        sam = sam.to(self.device)
        
        self.predictor = SamAutomaticMaskGenerator(
            model=sam,
            points_per_side=32,
            pred_iou_thresh=0.9,
            stability_score_thresh=0.92,
            min_mask_region_area=100,
        )
        self.area_threshold = 0.03  

        self.clip = CLIP(model_name=config['detector']['clip_model'], use_gpu=True)
    
    def encode_image(self, img_cv):

        return self.clip.encode_image(img_cv)

    def encode_text(self, text_query: str):
        return self.clip.encode_text(text_query)
        
    def extract_objects(self, image: np.ndarray) -> List[Dict]:
        height, width = image.shape[:2]
        image_area = height * width

        masks = self.predictor.generate(image)
        objects = []

        for mask in masks:
            bbox = mask['bbox']
            x, y, w, h = bbox
            x0, y0 = int(x), int(y)
            x1, y1 = int(x + w), int(y + h)
            area = w * h
            rel_area = area / image_area

            if rel_area > self.area_threshold or w <= 5 or h <= 5:
                continue

            cropped = image[y0:y1, x0:x1]
            resized = cv2.resize(cropped, (32, 32))

            gray = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)
            if np.std(gray) < 10: 
                continue

            hash_val = self._average_hash(resized)
            center_x = (x0 + x1) // 2
            center_y = (y0 + y1) // 2

            if center_y < 25:
                continue

            is_duplicate = False
            for prev_object in objects:
                px, py = prev_object['center']
                if abs(px - center_x) <= 6 and abs(py - center_y) <= 6:
                    is_duplicate = True
                    break

                hash_dist = self._hamming_distance(prev_object['hash'], hash_val)
                if hash_dist <= 5:  
                    is_duplicate = True
                    break

            if is_duplicate:
                continue

            objects.append({
                'id': None,
                'bbox': [x0, y0, w, h],
                'area': area,
                'hash': hash_val,
                'center': (center_x, center_y),
                'image': cropped
            })

        return objects
    
    def _average_hash(self, image: np.ndarray) -> str:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        resized = cv2.resize(gray, (8, 8))
        avg = resized.mean()
        return ''.join(['1' if pixel > avg else '0' for row in resized for pixel in row])

    def _hamming_distance(self, hash1: str, hash2: str) -> int:
        return sum(ch1 != ch2 for ch1, ch2 in zip(hash1, hash2))

    def objects_annotate(self, objects: List[Dict], existed_objects: List[Dict], area_tol=0.1, hash_threshold=15) -> List[Dict]:
        for object in objects:
            for existed_object in existed_objects:
                if abs(object['area'] - existed_object['area']) / existed_object['area'] > area_tol:
                    continue
                if self._hamming_distance(object['hash'], existed_object['hash']) <= hash_threshold:
                    object['id'] = existed_object['id']
                    break

    def update_objects(self, img, existed_objects):
        objects = self.extract_objects(img)
        self.objects_annotate(objects, existed_objects)
    
        return objects