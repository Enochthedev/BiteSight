# Quick Guide: Adding Training Images

## Image Organization Structure

Training images must be organized by **category folders**, not individual food names:

```
backend/dataset/images/
├── train/
│   ├── carbohydrates/
│   ├── protein/
│   ├── fats_oils/
│   ├── vitamins/
│   ├── water/
│   └── snacks/
├── val/
│   ├── carbohydrates/
│   ├── protein/
│   ├── fats_oils/
│   ├── vitamins/
│   ├── water/
│   └── snacks/
└── test/
    ├── carbohydrates/
    ├── protein/
    ├── fats_oils/
    ├── vitamins/
    ├── water/
    └── snacks/
```

## File Naming Convention

Use this format: `{food_id}_{source}_{number}.jpg`

### Examples:

**Carbohydrates:**
- `jollof_&_concoction_rice_restaurant_001.jpg`
- `white_rice_homemade_042.jpg`
- `eba_street_015.jpg`
- `pounded_yam_party_023.jpg`

**Protein:**
- `boiled_egg_homemade_001.jpg`
- `suya_street_042.jpg`
- `fried_white_meat_chicken_restaurant_015.jpg`
- `beef_stew_homemade_023.jpg`

**Vitamins:**
- `orange_market_001.jpg`
- `ugu_fresh_042.jpg`
- `tomatoes_vendor_015.jpg`

**Snacks:**
- `puff-puff_street_001.jpg`
- `biscuits_store_042.jpg`

## Food ID Reference

Use the exact IDs from `class_names.txt`. Here are the categories:

### Carbohydrates (32 foods)
```
white_rice, ofada_rice, jollof_&_concoction_rice, boiled_rice_&_beans,
fried_rice, boiled_yam, porridge_yam, fried_yam, pounded_yam,
soaked_garri, eba, boiled_cocoyam, porridge_cocoyam, fufu, amala,
semo, white_pap, brown_pap, boiled_corn, roasted_corn, boiled_plantains,
kunu, porridge_plantains, boiled_sweet_potatoes, boiled_irish_potatoes,
boiled_beans, moimoi, boiled_spaghetti, boiled_macaroni, semolina,
semovita, oats
```

### Protein (29 foods)
```
boiled_red_meat_beef, boiled_red_meat_goat, boiled_white_meat_chicken,
boiled_white_meat_turkey, boiled_white_meat_pork, fried_red_meat_beef,
fried_red_meat_goat, grilled_red_meat_beef, grilled_red_meat_goat,
fried_white_meat_chicken, fried_white_meat_turkey, fried_white_meat_pork,
boiled_egg, beef_stew, chicken_stew, fish_stew, turkey_stew,
goat_meat_stew, fried_egg_stew, boiled_egg_stew, fried_egg, wara,
greek_yogurt_unsweetened, sweetened_yogurt, milk_sachet, glass_of_milk,
tea_with_milk, boiled_groundnut, suya, kilishi
```

### Vitamins (20 foods)
```
orange, mango, bananas, pawpaw, pineapple, watermelon, guava,
efo_tete, ugu, bitterleaf, okra, tomatoes, carrots, cabbage,
pepper_chilli, pepper_bell, pepper_habanero, zobo,
plain_stew_tomato-pepper_blend
```

### Snacks (8 foods)
```
biscuits, puff-puff, buns, doughnut, samosa, springroll,
soda_drinks, gala
```

### Water (3 foods)
```
pure_water, bottled_water, cup_of_water
```

### Fats & Oils (0 foods)
```
(Currently empty - oils are tracked as nutrients in other foods)
```

## Quick Steps to Add Images

### 1. Create Category Folders (if not exist)
```bash
cd backend/dataset/images

# For training set
mkdir -p train/carbohydrates train/protein train/vitamins train/snacks train/water train/fats_oils

# For validation set
mkdir -p val/carbohydrates val/protein val/vitamins val/snacks val/water val/fats_oils

# For test set
mkdir -p test/carbohydrates test/protein test/vitamins test/snacks test/water test/fats_oils
```

### 2. Add Your Images

Place images in the correct category folder:

```bash
# Example: Adding jollof rice images
cp jollof_rice_001.jpg train/carbohydrates/
cp jollof_rice_002.jpg train/carbohydrates/
cp jollof_rice_003.jpg val/carbohydrates/
cp jollof_rice_004.jpg test/carbohydrates/
```

### 3. Recommended Split Ratio

For every 100 images of a food:
- **70 images** → `train/` folder
- **15 images** → `val/` folder  
- **15 images** → `test/` folder

### 4. Minimum Images per Food

- **MVP:** 30-50 images per food
- **Recommended:** 100+ images per food
- **Production:** 200+ images per food

## Image Requirements

### Technical Specs
- **Format:** JPG or PNG
- **Size:** Minimum 224x224 pixels
- **File size:** 100KB - 5MB
- **Color:** RGB (no grayscale)

### Quality Guidelines
- Clear, well-lit photos
- Food occupies 50-80% of frame
- Various angles (top-down, 45°, side)
- Different lighting conditions
- Show typical serving presentations
- Include garnishes and accompaniments

## Example: Adding Jollof Rice Images

```bash
# 1. Collect 100 jollof rice images
# 2. Rename them with proper naming:
jollof_&_concoction_rice_restaurant_001.jpg
jollof_&_concoction_rice_restaurant_002.jpg
...
jollof_&_concoction_rice_homemade_070.jpg

# 3. Split them:
# - First 70 → train/carbohydrates/
# - Next 15 → val/carbohydrates/
# - Last 15 → test/carbohydrates/

# 4. Copy to folders:
cp jollof_*_001.jpg to jollof_*_070.jpg train/carbohydrates/
cp jollof_*_071.jpg to jollof_*_085.jpg val/carbohydrates/
cp jollof_*_086.jpg to jollof_*_100.jpg test/carbohydrates/
```

## Verify Your Dataset

After adding images, verify the structure:

```bash
# Check image counts
ls -1 train/carbohydrates/*.jpg | wc -l
ls -1 val/carbohydrates/*.jpg | wc -l
ls -1 test/carbohydrates/*.jpg | wc -l

# List all images for a category
ls train/carbohydrates/
```

## Common Mistakes to Avoid

❌ **Wrong:** Creating folders for each food
```
train/jollof_rice/
train/eba/
train/suya/
```

✅ **Correct:** Using category folders
```
train/carbohydrates/jollof_rice_*.jpg
train/carbohydrates/eba_*.jpg
train/protein/suya_*.jpg
```

❌ **Wrong:** Using spaces in filenames
```
jollof rice 001.jpg
```

✅ **Correct:** Using underscores
```
jollof_&_concoction_rice_001.jpg
```

❌ **Wrong:** Inconsistent food IDs
```
jollof_rice_001.jpg  (should be jollof_&_concoction_rice)
boiled_egg_white_001.jpg  (should be boiled_egg)
```

✅ **Correct:** Match exact IDs from class_names.txt
```
jollof_&_concoction_rice_001.jpg
boiled_egg_001.jpg
```

## Next Steps

1. Add images following this guide
2. Verify your dataset structure
3. See `TRAINING_GUIDE.md` to train the model
4. Check `README.md` for data collection tips

## Need More Help?

- See `class_names.txt` for exact food IDs
- Check `nigerian_foods.json` for food categories
- Read `TRAINING_GUIDE.md` for training instructions
