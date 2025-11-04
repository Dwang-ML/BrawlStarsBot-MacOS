import os
import torch
from PIL import Image

class CustomDataset(torch.utils.data.Dataset):
    def __init__(self, img_dir, label_dir, transforms=None):
        self.img_dir = img_dir
        self.label_dir = label_dir
        self.transforms = transforms
        # Include .png and .jpg, ignore hidden files eg .DS_Store
        self.images = [
            f for f in os.listdir(img_dir)
            if (f.endswith(".png") or f.endswith(".jpg")) and not f.startswith('.')
        ]

    def __getitem__(self, idx):
        img_name = self.images[idx]
        img_path = os.path.join(self.img_dir, img_name)
        label_path = os.path.join(self.label_dir, img_name.rsplit('.', 1)[0] + ".txt")

        img = Image.open(img_path).convert("RGB")

        boxes, labels = [], []

        if os.path.exists(label_path):
            with open(label_path) as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) != 5:
                        continue
                    cls, xmin, ymin, xmax, ymax = map(float, parts)
                    # Skip invalid boxes
                    boxes.append([xmin, ymin, xmax, ymax])
                    labels.append(int(cls))

        # Convert to tensors
        boxes = torch.as_tensor(boxes, dtype=torch.float32)
        labels = torch.as_tensor(labels, dtype=torch.int64)

        if boxes.numel() == 0:
            return None

        target = {"boxes": boxes, "labels": labels}

        if self.transforms:
            img = self.transforms(img)

        return img, target

    def __len__(self):
        return len(self.images)
