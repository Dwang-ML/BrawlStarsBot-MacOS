import torch, time
import torchvision.transforms as T
from PIL import Image, ImageDraw
from model import create_model

# Config
img_num = 1

# CPU mode
device = torch.device("cpu")

# Load model
NUM_CLASSES = 12
model = create_model(num_classes=NUM_CLASSES)
model.load_state_dict(torch.load("object_detector.pth", map_location=device))
model.eval().to(device)

# Class names
CLASS_NAMES = [
    "background",
    "Wall",
    "Bush",
    "Player",
    "Enemy",
    "Projectile",
    "Molly",
    "Gas",
    "Water",
    "Boxes",
    "PowerCube",
    "Text"
]

COLORS = [
    (0,0,0),         # background (not used)
    (255,0,0),       # Wall - red
    (0,255,0),       # Bush - green
    (0,0,255),       # Player - blue
    (255,255,0),     # Enemy - yellow
    (255,0,255),     # Projectile - magenta
    (0,255,255),     # Molly - cyan
    (128,0,128),     # Gas - purple
    (255,165,0),     # Water - orange
    (128,128,128),   # Boxes - gray
    (0,128,0),       # PowerCube - dark green
    (173, 216, 230)  # Text - light blue
]

# Load and transform image
transform = T.ToTensor()
img_path = "data/images/val/e{}.png".format(img_num)
img = Image.open(img_path).convert("RGB")
img_tensor = transform(img).unsqueeze(0).to(device)

# Run inference
start_time = time.time()
with torch.no_grad():
    preds = model(img_tensor)
end_time = time.time()

# Draw predictions
draw = ImageDraw.Draw(img)
print(f"Predictions for {img_path}:")
for i, (box, label, score) in enumerate(zip(preds[0]["boxes"], preds[0]["labels"], preds[0]["scores"])):
    x1, y1, x2, y2 = box.tolist()
    label_idx = label.item()
    class_name = CLASS_NAMES[label_idx] if label_idx < len(CLASS_NAMES) else "Unknown"
    color = COLORS[label_idx] if label_idx < len(COLORS) else (255,255,255)

    # Debug logs
    print(f"  Box {i}: Class={class_name}, Score={score:.3f}, Coordinates=({x1:.1f},{y1:.1f},{x2:.1f},{y2:.1f})")

    if score > 0.7:
        draw.rectangle([x1, y1, x2, y2], outline=color, width=6)
        draw.text((x1+15, y1+10), f"{class_name} {score:.2f}", fill=color)

print('Processed in ', round(end_time - start_time, 2), 'seconds')

# Show image
img.show()
