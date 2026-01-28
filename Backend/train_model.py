"""
Plant Disease Model Training Script
Uses PyTorch with a pretrained ResNet model for classification
"""

import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from PIL import Image
import json
from pathlib import Path

# Dataset paths
TRAIN_DIR = r"C:\Users\adith\Downloads\archive\PlantDisease416x416\PlantDisease416x416\train"
TEST_DIR = r"C:\Users\adith\Downloads\archive\PlantDisease416x416\PlantDisease416x416\test"
MODEL_OUTPUT = r"C:\Users\adith\OneDrive\Desktop\plant-disease\Backend\plant_disease_model.pth"
CLASSES_OUTPUT = r"C:\Users\adith\OneDrive\Desktop\plant-disease\Backend\classes.json"

# Standard PlantVillage disease classes (30 classes based on your dataset)
CLASS_NAMES = {
    0: "Apple_Scab",
    1: "Apple_Black_Rot",
    2: "Apple_Cedar_Rust",
    3: "Apple_Healthy",
    4: "Blueberry_Healthy",
    5: "Cherry_Powdery_Mildew",
    6: "Cherry_Healthy",
    7: "Corn_Cercospora_Leaf_Spot",
    8: "Corn_Common_Rust",
    9: "Corn_Northern_Leaf_Blight",
    10: "Corn_Healthy",
    11: "Grape_Black_Rot",
    12: "Grape_Esca_Black_Measles",
    13: "Grape_Leaf_Blight",
    14: "Grape_Healthy",
    15: "Orange_Citrus_Greening",
    16: "Peach_Bacterial_Spot",
    17: "Peach_Healthy",
    18: "Pepper_Bacterial_Spot",
    19: "Pepper_Healthy",
    20: "Potato_Early_Blight",
    21: "Potato_Late_Blight",
    22: "Potato_Healthy",
    23: "Raspberry_Healthy",
    24: "Soybean_Healthy",
    25: "Squash_Powdery_Mildew",
    26: "Strawberry_Leaf_Scorch",
    27: "Strawberry_Healthy",
    28: "Tomato_Bacterial_Spot",
    29: "Tomato_Early_Blight",
}

# Remedies for each disease
REMEDIES = {
    "Apple_Scab": "Apply fungicide sprays containing captan or myclobutanil. Remove fallen leaves.",
    "Apple_Black_Rot": "Prune dead or infected branches. Apply copper-based fungicide.",
    "Apple_Cedar_Rust": "Remove nearby juniper trees. Apply fungicide in spring.",
    "Apple_Healthy": "No treatment needed. Continue regular care and monitoring.",
    "Blueberry_Healthy": "No treatment needed. Maintain proper watering and mulching.",
    "Cherry_Powdery_Mildew": "Apply sulfur-based fungicide. Improve air circulation.",
    "Cherry_Healthy": "No treatment needed. Continue regular pruning and care.",
    "Corn_Cercospora_Leaf_Spot": "Use resistant varieties. Apply fungicide if severe.",
    "Corn_Common_Rust": "Plant resistant hybrids. Apply foliar fungicide if needed.",
    "Corn_Northern_Leaf_Blight": "Use resistant varieties. Rotate crops annually.",
    "Corn_Healthy": "No treatment needed. Maintain proper fertilization.",
    "Grape_Black_Rot": "Remove infected fruit. Apply fungicide before bloom.",
    "Grape_Esca_Black_Measles": "Prune infected wood. No effective chemical control.",
    "Grape_Leaf_Blight": "Apply fungicide sprays. Remove infected leaves.",
    "Grape_Healthy": "No treatment needed. Continue regular vineyard management.",
    "Orange_Citrus_Greening": "Remove infected trees. Control psyllid insects.",
    "Peach_Bacterial_Spot": "Apply copper sprays. Use resistant varieties.",
    "Peach_Healthy": "No treatment needed. Regular pruning recommended.",
    "Pepper_Bacterial_Spot": "Use disease-free seeds. Apply copper-based bactericide.",
    "Pepper_Healthy": "No treatment needed. Maintain proper spacing.",
    "Potato_Early_Blight": "Apply fungicide. Remove infected plant debris.",
    "Potato_Late_Blight": "Apply fungicide immediately. Destroy infected plants.",
    "Potato_Healthy": "No treatment needed. Hill soil around plants.",
    "Raspberry_Healthy": "No treatment needed. Prune old canes after harvest.",
    "Soybean_Healthy": "No treatment needed. Rotate crops for best results.",
    "Squash_Powdery_Mildew": "Apply neem oil or sulfur fungicide. Improve airflow.",
    "Strawberry_Leaf_Scorch": "Remove infected leaves. Apply fungicide.",
    "Strawberry_Healthy": "No treatment needed. Mulch and water properly.",
    "Tomato_Bacterial_Spot": "Use copper sprays. Avoid overhead watering.",
    "Tomato_Early_Blight": "Apply fungicide. Mulch around plants.",
}


class PlantDiseaseDataset(Dataset):
    """Custom dataset that reads YOLO format and extracts class labels"""
    
    def __init__(self, data_dir, transform=None):
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.samples = []
        
        # Find all jpg files and their corresponding txt files
        for img_path in self.data_dir.glob("*.jpg"):
            txt_path = img_path.with_suffix(".txt")
            if txt_path.exists():
                # Read class ID from txt file (first number)
                with open(txt_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        class_id = int(content.split()[0])
                        if class_id in CLASS_NAMES:
                            self.samples.append((str(img_path), class_id))
        
        print(f"Loaded {len(self.samples)} samples from {data_dir}")
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        img_path, class_id = self.samples[idx]
        image = Image.open(img_path).convert('RGB')
        
        if self.transform:
            image = self.transform(image)
        
        return image, class_id


def train_model():
    # Check for GPU
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Data transforms
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    test_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    # Load datasets
    print("Loading training data...")
    train_dataset = PlantDiseaseDataset(TRAIN_DIR, transform=train_transform)
    
    print("Loading test data...")
    test_dataset = PlantDiseaseDataset(TEST_DIR, transform=test_transform)
    
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False, num_workers=0)
    
    # Create model (using pretrained ResNet18 for speed)
    print("Creating model...")
    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    num_classes = len(CLASS_NAMES)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    model = model.to(device)
    
    # Loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.1)
    
    # Training
    num_epochs = 5  # Quick training - increase for better accuracy
    best_acc = 0.0
    
    print(f"\nStarting training for {num_epochs} epochs...")
    
    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        
        for batch_idx, (images, labels) in enumerate(train_loader):
            images, labels = images.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
            
            if (batch_idx + 1) % 20 == 0:
                print(f"Epoch [{epoch+1}/{num_epochs}], Batch [{batch_idx+1}/{len(train_loader)}], "
                      f"Loss: {loss.item():.4f}, Acc: {100.*correct/total:.2f}%")
        
        scheduler.step()
        
        # Validation
        model.eval()
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for images, labels in test_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, predicted = outputs.max(1)
                val_total += labels.size(0)
                val_correct += predicted.eq(labels).sum().item()
        
        val_acc = 100. * val_correct / val_total
        print(f"\nEpoch [{epoch+1}/{num_epochs}] - Validation Accuracy: {val_acc:.2f}%\n")
        
        # Save best model
        if val_acc > best_acc:
            best_acc = val_acc
            torch.save({
                'model_state_dict': model.state_dict(),
                'class_names': CLASS_NAMES,
                'num_classes': num_classes,
            }, MODEL_OUTPUT)
            print(f"Saved best model with accuracy: {best_acc:.2f}%")
    
    # Save class names and remedies
    classes_data = {
        'class_names': CLASS_NAMES,
        'remedies': REMEDIES
    }
    with open(CLASSES_OUTPUT, 'w') as f:
        json.dump(classes_data, f, indent=2)
    
    print(f"\n✅ Training complete!")
    print(f"   Model saved to: {MODEL_OUTPUT}")
    print(f"   Classes saved to: {CLASSES_OUTPUT}")
    print(f"   Best accuracy: {best_acc:.2f}%")


if __name__ == "__main__":
    train_model()
