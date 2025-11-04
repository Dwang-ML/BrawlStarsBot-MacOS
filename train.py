import time
import torch
import torchvision.transforms as T
from torch.utils.data import DataLoader
from dataset import CustomDataset
from model import create_model
from tqdm import tqdm

# Device
device = torch.device("cpu")
print(f"Using device: {device}")

# Config
NUM_CLASSES = 11
BATCH_SIZE = 2
EPOCHS = 75

# Dataset
train_dataset = CustomDataset("data/images/train", "data/labels/train", transforms=T.ToTensor())
print(f"Dataset length: {len(train_dataset)}")  # Debug: total images

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    collate_fn=lambda batch: tuple(zip(*[b for b in batch if b is not None]))
)

# Model + optimizer
model = create_model(NUM_CLASSES).to(device)
optimizer = torch.optim.SGD(
    [p for p in model.parameters() if p.requires_grad],
    lr=0.005,
    momentum=0.9,
    weight_decay=0.0005
)

# Training loop
for epoch in range(EPOCHS):
    print(f"\n=== Epoch {epoch+1}/{EPOCHS} ===")
    model.train()
    epoch_loss = 0

    for batch_idx, (imgs, targets) in enumerate(tqdm(train_loader, desc=f"Epoch {epoch+1}/{EPOCHS}")):
        print(f"\nBatch {batch_idx+1}: {len(imgs)} images")  # Debug: batch size

        image_times = []
        for i, t in enumerate(targets):
            num_boxes = t['boxes'].shape[0]
            print(f"  Image {i}: {num_boxes} boxes")
            if num_boxes == 0:
                print(f"    WARNING: Image {i} has no valid boxes!")

        imgs = list(img.to(device) for img in imgs)
        targets = [{k: v.to(device) for k, v in t.items()} for t in targets]

        batch_start = time.time()
        try:
            loss_dict = model(imgs, targets)
            losses = sum(loss for loss in loss_dict.values())
        except Exception as e:
            print(f"Error during forward pass: {e}")
            continue
        forward_time = time.time() - batch_start
        print(f"  Forward pass took {forward_time:.2f}s")

        optimizer.zero_grad()
        backward_start = time.time()
        losses.backward()
        optimizer.step()
        backward_time = time.time() - backward_start
        print(f"  Backward + optimizer step took {backward_time:.2f}s")

        epoch_loss += losses.item()

    print(f"Epoch {epoch+1} loss: {epoch_loss/len(train_loader):.4f}")

torch.save(model.state_dict(), "object_detector.pth")
print("Training complete, weights saved to object_detector.pth")
