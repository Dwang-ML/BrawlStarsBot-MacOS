from PIL import ImageDraw

def draw_boxes(image, boxes, labels=None, scores=None):
    """
    Draw bounding boxes on an image.
    image: PIL Image
    boxes: [[x1, y1, x2, y2], ...]
    labels: list of class names or IDs
    scores: list of confidences
    """
    draw = ImageDraw.Draw(image)
    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = box
        draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
        if labels:
            label = str(labels[i])
            if scores:
                label += f" ({scores[i]:.2f})"
            draw.text((x1, y1 - 10), label, fill="red")
    return image
