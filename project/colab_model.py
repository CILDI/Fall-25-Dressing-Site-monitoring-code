import cv2
import numpy as np
import torch
import torch.nn as nn
import albumentations as A
from albumentations.pytorch import ToTensorV2
import open_clip
import os
"""
This is the script that interacts with our Pytorch model. 

The model has already been trained, so we are just calling it

POC: Kan Davis

"""

MODEL_PATH  = os.path.join(os.path.dirname(__file__), 'model.pt')
CLASSES     = ['Blood', 'Pus', 'Redness', 'Clean']
EXCLUDE     = {'Redness'}
THRESHOLDS  = {'Blood': 0.5, 'Pus': 0.5, 'Redness': 0.5, 'Clean': 0.5}
IMG_SIZE    = 224
BIOMED_MEAN = [0.48145466, 0.4578275,  0.40821073]
BIOMED_STD  = [0.26862954, 0.26130258, 0.27577711]

class WoundMedicalModel(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.backbone, _, _ = open_clip.create_model_and_transforms(
            'hf-hub:microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224'
        )
        self.backbone = self.backbone.visual
        self.classifier = nn.Sequential(
            nn.LayerNorm(512),
            nn.Dropout(p=0.4),
            nn.Linear(512, 256),
            nn.GELU(),
            nn.Dropout(p=0.3),
            nn.Linear(256, num_classes),
        )
    def forward(self, x):
        return self.classifier(self.backbone(x))

device = torch.device('cpu')
print(f'Loading wound model from {MODEL_PATH}...')
_model = WoundMedicalModel(num_classes=len(CLASSES)).to(device)
_model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
_model.eval()
print('Wound model loaded.')

_aug = A.Compose([
    A.Resize(IMG_SIZE, IMG_SIZE),
    A.Normalize(mean=BIOMED_MEAN, std=BIOMED_STD),
    ToTensorV2(),
])

def run_pytorch_inference(frame):
    success, buffer = cv2.imencode('.jpg', frame)
    if not success:
        raise RuntimeError('Failed to encode frame to JPEG')
    original_image_bytes = buffer.tobytes()

    img    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    tensor = _aug(image=img)['image'].unsqueeze(0).to(device)

    with torch.no_grad():
        probs_orig = torch.sigmoid(_model(tensor))
        probs_flip = torch.sigmoid(_model(torch.flip(tensor, dims=[3])))
        probs = ((probs_orig + probs_flip) / 2).cpu().numpy()[0]

    predictions = []
    for cls, prob in zip(CLASSES, probs):
        if cls in EXCLUDE:
            continue
        if prob > THRESHOLDS[cls]:
            predictions.append({
                'class':      cls,
                'class_id':   CLASSES.index(cls),
                'confidence': round(float(prob), 4),
            })

    if not predictions:
        predictions.append({
            'class':      'Clean',
            'class_id':   CLASSES.index('Clean'),
            'confidence': 1.0,
        })

    return predictions, None, original_image_bytes