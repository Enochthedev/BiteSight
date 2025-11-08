# Nigerian Food Dataset Organization

This directory contains the dataset for training the Nigerian food recognition model.

## Directory Structure

```
dataset/
├── images/
│   ├── train/          # Training images (70-80% of data)
│   │   ├── carbohydrates/
│   │   ├── protein/
│   │   ├── fats_oils/
│   │   ├── vitamins/
│   │   ├── water/
│   │   └── snacks/
│   ├── val/            # Validation images (10-15% of data)
│   │   ├── carbohydrates/
│   │   ├── protein/
│   │   ├── fats_oils/
│   │   ├── vitamins/
│   │   ├── water/
│   │   └── snacks/
│   └── test/           # Test images (10-15% of data)
│       ├── carbohydrates/
│       ├── protein/
│       ├── fats_oils/
│       ├── vitamins/
│       ├── water/
│       └── snacks/
└── metadata/
    └── nigerian_foods.json  # Food class mappings and nutritional info
```

## Image Collection Guidelines

### Recommended Images per Food Class

**For MVP (Minimum Viable Product):**
- **Minimum:** 30-50 images per food class
- **Recommended:** 100+ images per food class
- **Ideal:** 200+ images per food class

**Priority Foods to Collect First (Top 20):**
1. Jollof Rice
2. Fried Rice
3. White Rice
4. Eba
5. Amala
6. Pounded Yam
7. Fufu
8. Moimoi
9. Akara
10. Egusi Soup
11. Efo Riro (Vegetable Soup)
12. Fried Plantains
13. Boiled Eggs
14. Fried Chicken
15. Suya
16. Pepper Soup
17. Jollof & Stew
18. Beans Porridge
19. Yam Porridge
20. Pap (Ogi)

### Image Quality Requirements

**Technical Specifications:**
- **Format:** JPEG or PNG
- **Resolution:** Minimum 224x224 pixels (higher is better)
- **File Size:** 100KB - 5MB per image
- **Color:** RGB (no grayscale)

**Content Requirements:**
- Clear, well-lit images
- Food should occupy 50-80% of the frame
- Various angles (top-down, 45-degree, side view)
- Different lighting conditions (natural, indoor, outdoor)
- Various presentations (plate, bowl, wrap, etc.)
- Include garnishes and typical serving styles
- Show portion sizes (single serving, family size)

**Diversity Requirements:**
- Different preparation methods
- Various cooking stages (if applicable)
- Different restaurants/home cooking
- Regional variations
- Traditional and modern presentations

### Image Sources

**Free/Legal Sources:**
1. **Your Own Photos:**
   - Take photos at restaurants
   - Cook and photograph meals
   - Ask friends/family to contribute

2. **Creative Commons:**
   - Flickr (CC-licensed)
   - Wikimedia Commons
   - Unsplash (food category)
   - Pexels (food category)

3. **Nigerian Food Blogs/Websites:**
   - Contact bloggers for permission
   - Credit sources appropriately
   - Respect copyright

4. **Social Media:**
   - Instagram (with permission)
   - Pinterest (verify licensing)
   - Food delivery apps (with permission)

5. **Existing Datasets:**
   - Food-101 dataset (some overlap)
   - African Food Dataset (if available)
   - Custom web scraping (with permission)

### Data Collection Tools

**Automated Collection:**
```bash
# Use the provided script
python scripts/dataset_utils.py collect --food "Jollof Rice" --count 100

# Or use google-images-download
pip install google-images-download
googleimagesdownload --keywords "Nigerian Jollof Rice" --limit 100
```

**Manual Collection:**
- Use browser extensions (Download All Images)
- Mobile apps for bulk photo organization
- Cloud storage for team collaboration

### Image Naming Convention

```
{food_class}_{source}_{index}.jpg

Examples:
- jollof_rice_restaurant_001.jpg
- eba_homemade_042.jpg
- suya_street_015.jpg
```

### Data Augmentation

The training pipeline will automatically apply:
- Random rotation (±15 degrees)
- Random horizontal flip
- Random brightness/contrast adjustment
- Random crop and resize
- Color jittering

**You don't need to manually augment images.**

## Data Split Ratios

**Recommended Split:**
- Training: 70% (for learning patterns)
- Validation: 15% (for tuning hyperparameters)
- Test: 15% (for final evaluation)

**Example for 100 images:**
- Train: 70 images
- Val: 15 images
- Test: 15 images

## Quick Start: Collecting Your First Dataset

### Step 1: Start with Top 10 Foods
Focus on the most common Nigerian foods first:
1. Jollof Rice
2. Fried Rice
3. Eba
4. Moimoi
5. Fried Plantains
6. Egusi Soup
7. Pounded Yam
8. Suya
9. Akara
10. Boiled Eggs

### Step 2: Collect 50 Images Each
- 35 images → train/
- 8 images → val/
- 7 images → test/

### Step 3: Organize by Food Class
```bash
# Example for Jollof Rice (Carbohydrates category)
train/carbohydrates/jollof_rice_001.jpg
train/carbohydrates/jollof_rice_002.jpg
...
val/carbohydrates/jollof_rice_036.jpg
...
test/carbohydrates/jollof_rice_044.jpg
```

### Step 4: Verify Dataset
```bash
python scripts/dataset_utils.py verify
```

## Using Pre-trained Models (MVP Approach)

For quick MVP deployment, you can:

1. **Download Food-101 Pre-trained Model:**
   - Already trained on 101 food classes
   - Fine-tune on Nigerian foods
   - Faster than training from scratch

2. **Use Transfer Learning:**
   - Start with ImageNet weights
   - Train only on Nigerian food classes
   - Requires less data (30-50 images per class)

See `TRAINING_GUIDE.md` for detailed instructions.

## Data Privacy & Ethics

**Important Considerations:**
- Get permission before using others' photos
- Respect copyright and licensing
- Credit photographers when required
- Don't use images with identifiable people without consent
- Follow platform terms of service
- Consider cultural sensitivity

## Next Steps

1. **Read:** `TRAINING_GUIDE.md` for training instructions
2. **Collect:** Start with top 10 foods (50 images each)
3. **Organize:** Place images in correct directories
4. **Verify:** Run verification script
5. **Train:** Follow training guide to create your model

## Need Help?

- Check `TRAINING_GUIDE.md` for detailed training instructions
- See `scripts/dataset_utils.py` for automation tools
- Review `app/ml/dataset/` for data loading code

## Current Status

- [ ] Collected images for top 10 foods
- [ ] Organized images into train/val/test splits
- [ ] Created food mapping JSON
- [ ] Verified dataset quality
- [ ] Ready for training

**Target:** 500-1000 images total (50-100 per class for 10 classes)
**Timeline:** 1-2 days for collection, 4-8 hours for training
