# Nigerian Food Recognition Model Training Guide

Complete guide for training the MobileNetV2-based food recognition model.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start (MVP with Pre-trained Model)](#quick-start-mvp)
3. [Full Training from Scratch](#full-training)
4. [Fine-tuning Pre-trained Models](#fine-tuning)
5. [Model Evaluation](#model-evaluation)
6. [Deployment](#deployment)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Minimum (CPU Training):**
- 8GB RAM
- 20GB free disk space
- Python 3.8+
- 2-4 CPU cores

**Recommended (GPU Training):**
- 16GB+ RAM
- NVIDIA GPU with 6GB+ VRAM (GTX 1060 or better)
- 50GB free disk space
- CUDA 11.0+ and cuDNN

### Software Dependencies

```bash
# Install PyTorch (CPU version)
pip install torch torchvision torchaudio

# Or GPU version (if you have NVIDIA GPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install other dependencies
pip install -r requirements.txt
```

### Verify Installation

```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA Available: {torch.cuda.is_available()}')"
```

---

## Quick Start (MVP with Pre-trained Model)

**Best for:** Quick MVP, limited data, fast deployment

### Option 1: Use Food-101 Pre-trained Model

```bash
# 1. Download pre-trained Food-101 model
wget https://download.pytorch.org/models/mobilenet_v2-b0353104.pth -O models/mobilenet_v2_pretrained.pth

# 2. Create food mapping from your CSV
python scripts/create_food_mapping.py --csv data/Nigerianfood.csv --output dataset/metadata/nigerian_foods.json

# 3. Fine-tune on Nigerian foods (if you have some images)
python app/ml/training/trainer.py \
    --mode fine-tune \
    --pretrained models/mobilenet_v2_pretrained.pth \
    --data-dir dataset/images \
    --epochs 10 \
    --batch-size 16 \
    --learning-rate 0.001

# 4. Or use mock model for testing (no images needed)
python scripts/create_mock_model.py --output models/best_model.pth
```

### Option 2: Transfer Learning (Recommended)

```bash
# Train with ImageNet pre-trained weights
python app/ml/training/trainer.py \
    --mode transfer \
    --data-dir dataset/images \
    --epochs 20 \
    --batch-size 32 \
    --learning-rate 0.001 \
    --freeze-backbone \
    --output models/nigerian_food_model.pth
```

**Timeline:** 2-4 hours (with 500-1000 images)

---

## Full Training from Scratch

**Best for:** Maximum accuracy, large dataset, research

### Step 1: Prepare Dataset

```bash
# Verify dataset structure
python scripts/dataset_utils.py verify

# Expected output:
# ✓ Found 700 training images across 10 classes
# ✓ Found 150 validation images across 10 classes
# ✓ Found 150 test images across 10 classes
# ✓ All classes have minimum 30 images
```

### Step 2: Create Food Mapping

```bash
# Generate food mapping JSON from CSV
python scripts/create_food_mapping.py \
    --csv data/Nigerianfood.csv \
    --output dataset/metadata/nigerian_foods.json \
    --categories carbohydrates,protein,fats_oils,vitamins,water,snacks
```

### Step 3: Configure Training

Create `training_config.yaml`:

```yaml
# Training Configuration
model:
  architecture: mobilenet_v2
  num_classes: 10  # Adjust based on your dataset
  pretrained: true
  dropout: 0.2

data:
  train_dir: dataset/images/train
  val_dir: dataset/images/val
  test_dir: dataset/images/test
  batch_size: 32
  num_workers: 4
  image_size: 224

training:
  epochs: 50
  learning_rate: 0.001
  optimizer: adam
  scheduler: step
  step_size: 10
  gamma: 0.1
  early_stopping_patience: 10

augmentation:
  random_rotation: 15
  random_horizontal_flip: true
  color_jitter: true
  random_crop: true
  normalize: true

output:
  checkpoint_dir: checkpoints
  model_output: models/best_model.pth
  log_dir: logs
```

### Step 4: Start Training

```bash
# Full training from scratch
python app/ml/training/trainer.py \
    --config training_config.yaml \
    --mode full \
    --device cuda  # or 'cpu' if no GPU

# Monitor training
tensorboard --logdir logs
```

### Step 5: Monitor Progress

Training will output:
```
Epoch 1/50
Train Loss: 2.3456 | Train Acc: 45.2%
Val Loss: 2.1234 | Val Acc: 52.3%
Saved checkpoint: checkpoints/checkpoint_epoch_1.pth

Epoch 2/50
Train Loss: 1.8765 | Train Acc: 58.7%
Val Loss: 1.7654 | Val Acc: 61.2%
Saved checkpoint: checkpoints/checkpoint_epoch_2.pth
...

Best model saved: models/best_model.pth (Val Acc: 87.5%)
```

**Timeline:** 4-8 hours (with GPU), 24-48 hours (with CPU)

---

## Fine-tuning Pre-trained Models

**Best for:** Limited data, faster training, good accuracy

### Approach 1: Freeze Backbone (Fast)

```bash
# Only train the classifier head
python app/ml/training/trainer.py \
    --mode fine-tune \
    --pretrained models/mobilenet_v2_pretrained.pth \
    --freeze-backbone \
    --epochs 15 \
    --learning-rate 0.001
```

**Timeline:** 1-2 hours

### Approach 2: Gradual Unfreezing (Better Accuracy)

```bash
# Stage 1: Train classifier only (5 epochs)
python app/ml/training/trainer.py \
    --mode fine-tune \
    --freeze-backbone \
    --epochs 5 \
    --learning-rate 0.001

# Stage 2: Unfreeze and train all layers (15 epochs)
python app/ml/training/trainer.py \
    --mode fine-tune \
    --pretrained checkpoints/checkpoint_epoch_5.pth \
    --epochs 15 \
    --learning-rate 0.0001
```

**Timeline:** 2-3 hours

---

## Model Evaluation

### Evaluate on Test Set

```bash
# Run evaluation
python app/ml/training/trainer.py \
    --mode evaluate \
    --model models/best_model.pth \
    --data-dir dataset/images/test

# Output:
# Test Accuracy: 87.5%
# Test Loss: 0.4321
# 
# Per-Class Accuracy:
# Jollof Rice: 92.3%
# Fried Rice: 88.7%
# Eba: 85.2%
# ...
```

### Generate Confusion Matrix

```bash
python scripts/evaluate_model.py \
    --model models/best_model.pth \
    --data-dir dataset/images/test \
    --output evaluation_results.json \
    --plot-confusion-matrix
```

### Test on Single Image

```bash
python scripts/test_inference.py \
    --model models/best_model.pth \
    --image path/to/test_image.jpg \
    --top-k 5

# Output:
# Top 5 Predictions:
# 1. Jollof Rice (92.3%)
# 2. Fried Rice (5.2%)
# 3. White Rice (1.8%)
# 4. Ofada Rice (0.5%)
# 5. Concoction Rice (0.2%)
```

---

## Deployment

### Step 1: Optimize Model for Production

```bash
# Convert to TorchScript for faster inference
python scripts/optimize_model.py \
    --model models/best_model.pth \
    --output models/best_model_optimized.pt \
    --quantize  # Optional: reduce model size
```

### Step 2: Test Inference Speed

```bash
python scripts/benchmark_model.py \
    --model models/best_model.pth \
    --batch-sizes 1,8,16,32

# Output:
# Batch Size 1: 45ms per image (22 FPS)
# Batch Size 8: 12ms per image (83 FPS)
# Batch Size 16: 8ms per image (125 FPS)
# Batch Size 32: 6ms per image (166 FPS)
```

### Step 3: Deploy to Backend

```bash
# Copy model to backend
cp models/best_model.pth BiteSight/backend/models/

# Copy food mapping
cp dataset/metadata/nigerian_foods.json BiteSight/backend/dataset/metadata/

# Restart backend
# The model will be automatically loaded on startup
```

### Step 4: Test API Integration

```bash
# Test inference endpoint
curl -X POST http://localhost:8000/api/v1/meals/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test_meal.jpg"

# Response:
# {
#   "meal_id": "...",
#   "detected_foods": [
#     {"name": "Jollof Rice", "confidence": 0.92, "category": "carbohydrates"}
#   ],
#   "analysis_status": "completed"
# }
```

---

## Training Strategies

### Strategy 1: MVP with Minimal Data (1-2 days)

**Goal:** Get something working quickly

1. Collect 30-50 images for top 10 foods (300-500 total)
2. Use transfer learning with frozen backbone
3. Train for 10-15 epochs
4. Expected accuracy: 70-80%

```bash
python app/ml/training/trainer.py \
    --mode transfer \
    --freeze-backbone \
    --epochs 15 \
    --batch-size 16
```

### Strategy 2: Production Quality (1-2 weeks)

**Goal:** High accuracy for deployment

1. Collect 100-200 images for 20-30 foods (2000-6000 total)
2. Use transfer learning with gradual unfreezing
3. Train for 30-50 epochs with early stopping
4. Expected accuracy: 85-92%

```bash
# Stage 1: Freeze backbone
python app/ml/training/trainer.py \
    --mode transfer \
    --freeze-backbone \
    --epochs 10

# Stage 2: Unfreeze and fine-tune
python app/ml/training/trainer.py \
    --mode fine-tune \
    --pretrained checkpoints/checkpoint_epoch_10.pth \
    --epochs 40 \
    --learning-rate 0.0001
```

### Strategy 3: Research Grade (1-2 months)

**Goal:** Maximum accuracy, publication-ready

1. Collect 200+ images for 50+ foods (10,000+ total)
2. Train from scratch or use advanced architectures
3. Extensive hyperparameter tuning
4. Expected accuracy: 92-95%

---

## Troubleshooting

### Issue: Out of Memory (OOM)

**Solution:**
```bash
# Reduce batch size
--batch-size 8  # or even 4

# Reduce image size
--image-size 192  # instead of 224

# Use gradient accumulation
--gradient-accumulation-steps 4
```

### Issue: Model Not Learning (Loss Not Decreasing)

**Solutions:**
1. Check data quality and labels
2. Reduce learning rate: `--learning-rate 0.0001`
3. Use pre-trained weights: `--pretrained true`
4. Increase batch size: `--batch-size 64`

### Issue: Overfitting (Train Acc >> Val Acc)

**Solutions:**
```bash
# Increase dropout
--dropout 0.5

# Add data augmentation
--augmentation-strength high

# Reduce model complexity
--freeze-backbone

# Add more training data
```

### Issue: Training Too Slow

**Solutions:**
1. Use GPU instead of CPU
2. Increase batch size
3. Reduce image size
4. Use fewer workers: `--num-workers 2`
5. Use mixed precision training: `--mixed-precision`

### Issue: Poor Accuracy on Specific Classes

**Solutions:**
1. Collect more images for those classes
2. Check for mislabeled images
3. Use class weights: `--use-class-weights`
4. Increase augmentation for minority classes

---

## Advanced Topics

### Custom Data Augmentation

Edit `app/ml/dataset/augmentation.py`:

```python
def get_training_transforms():
    return transforms.Compose([
        transforms.RandomResizedCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        # Add custom transforms here
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                           std=[0.229, 0.224, 0.225])
    ])
```

### Hyperparameter Tuning

```bash
# Use grid search
python scripts/hyperparameter_search.py \
    --param learning_rate 0.001,0.0001,0.00001 \
    --param batch_size 16,32,64 \
    --param dropout 0.2,0.3,0.5
```

### Multi-GPU Training

```bash
# Use DataParallel
python app/ml/training/trainer.py \
    --multi-gpu \
    --gpu-ids 0,1,2,3
```

---

## Quick Reference Commands

```bash
# Create food mapping
python scripts/create_food_mapping.py --csv data/Nigerianfood.csv

# Verify dataset
python scripts/dataset_utils.py verify

# Train MVP model (fast)
python app/ml/training/trainer.py --mode transfer --freeze-backbone --epochs 15

# Train production model (accurate)
python app/ml/training/trainer.py --mode fine-tune --epochs 40

# Evaluate model
python app/ml/training/trainer.py --mode evaluate --model models/best_model.pth

# Test single image
python scripts/test_inference.py --model models/best_model.pth --image test.jpg

# Benchmark performance
python scripts/benchmark_model.py --model models/best_model.pth

# Deploy to backend
cp models/best_model.pth BiteSight/backend/models/
```

---

## Next Steps

1. **Collect Data:** Follow `dataset/README.md` to collect images
2. **Start Training:** Use MVP strategy for quick results
3. **Evaluate:** Test on validation set
4. **Deploy:** Copy model to backend
5. **Iterate:** Collect more data and retrain

## Resources

- [PyTorch Documentation](https://pytorch.org/docs/)
- [MobileNetV2 Paper](https://arxiv.org/abs/1801.04381)
- [Transfer Learning Guide](https://pytorch.org/tutorials/beginner/transfer_learning_tutorial.html)
- [Food-101 Dataset](https://data.vision.ee.ethz.ch/cvl/datasets_extra/food-101/)

## Support

For issues or questions:
1. Check this guide
2. Review `dataset/README.md`
3. Check logs in `logs/` directory
4. Review code in `app/ml/`
