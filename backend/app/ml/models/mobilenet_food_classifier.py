"""
MobileNetV2-based classifier for Nigerian food recognition.

The backbone is torchvision's MobileNetV2 feature extractor (optionally with
ImageNet weights for transfer learning); the head is a small MLP. The head is
an ``nn.Sequential`` whose index 3 is the final ``Linear`` layer, which the
predictor relies on (``classifier.3.weight``) to infer the class count from a
checkpoint.
"""

from typing import Dict, List, Optional, Sequence, Tuple, Union

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models

MOBILENET_V2_FEATURE_DIM = 1280


class FoodClassificationHead(nn.Module):
    """Configurable MLP head mapping backbone features to food classes."""

    def __init__(
        self,
        input_dim: int,
        num_classes: int,
        hidden_dims: Optional[Sequence[int]] = None,
        dropout_rate: float = 0.2,
    ):
        super().__init__()
        layers: List[nn.Module] = []
        prev_dim = input_dim
        for hidden_dim in hidden_dims or []:
            layers += [
                nn.Dropout(dropout_rate),
                nn.Linear(prev_dim, hidden_dim),
                nn.ReLU(inplace=True),
            ]
            prev_dim = hidden_dim
        layers.append(nn.Linear(prev_dim, num_classes))
        self.classifier = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(x)


class MobileNetV2FoodClassifier(nn.Module):
    """MobileNetV2 backbone + classification head for food images (224x224 RGB)."""

    def __init__(
        self,
        num_classes: int,
        pretrained: bool = True,
        dropout: float = 0.2,
        hidden_dim: int = 512,
    ):
        super().__init__()
        self.num_classes = num_classes
        self.feature_dim = MOBILENET_V2_FEATURE_DIM
        self.pretrained = pretrained

        weights = models.MobileNet_V2_Weights.IMAGENET1K_V1 if pretrained else None
        self.backbone = models.mobilenet_v2(weights=weights).features

        # Index 3 must stay the final Linear layer (see module docstring).
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(self.feature_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, num_classes),
        )

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """Return pooled backbone features of shape (batch, feature_dim)."""
        x = self.backbone(x)
        x = F.adaptive_avg_pool2d(x, 1)
        return torch.flatten(x, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.extract_features(x))

    @torch.no_grad()
    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        return F.softmax(self.forward(x), dim=1)

    @torch.no_grad()
    def predict_top_k(
        self, x: torch.Tensor, k: int = 5
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        probs = self.predict_proba(x)
        return torch.topk(probs, k=min(k, self.num_classes), dim=1)

    def freeze_backbone(self) -> None:
        """Train only the head (stage 1 of transfer learning)."""
        for param in self.backbone.parameters():
            param.requires_grad = False

    def unfreeze_backbone(self) -> None:
        """Fine-tune the whole network (stage 2 of transfer learning)."""
        for param in self.backbone.parameters():
            param.requires_grad = True

    def get_model_info(self) -> Dict[str, Union[str, int, bool]]:
        total, trainable = count_parameters(self)
        return {
            "model_name": "MobileNetV2FoodClassifier",
            "num_classes": self.num_classes,
            "feature_dim": self.feature_dim,
            "pretrained": self.pretrained,
            "total_parameters": total,
            "trainable_parameters": trainable,
        }


class EnsembleFoodClassifier(nn.Module):
    """Averages the logits (or probabilities) of several classifiers."""

    def __init__(self, models_list: Sequence[MobileNetV2FoodClassifier]):
        super().__init__()
        if not models_list:
            raise ValueError("Ensemble needs at least one model")
        num_classes = {m.num_classes for m in models_list}
        if len(num_classes) != 1:
            raise ValueError("All ensemble members must have the same num_classes")
        self.models = nn.ModuleList(models_list)
        self.num_classes = num_classes.pop()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.stack([m(x) for m in self.models]).mean(dim=0)

    @torch.no_grad()
    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        return torch.stack([F.softmax(m(x), dim=1) for m in self.models]).mean(dim=0)


def create_mobilenet_food_classifier(
    num_classes: int, pretrained: bool = True, dropout: float = 0.2
) -> MobileNetV2FoodClassifier:
    """Factory used by training scripts."""
    return MobileNetV2FoodClassifier(
        num_classes=num_classes, pretrained=pretrained, dropout=dropout
    )


def count_parameters(model: nn.Module) -> Tuple[int, int]:
    """Return (total, trainable) parameter counts."""
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return int(total), int(trainable)


def load_pretrained_model(
    model_path: str, device: Union[str, torch.device] = "cpu"
) -> Tuple[MobileNetV2FoodClassifier, dict]:
    """Load a checkpoint saved by the trainer or scripts/create_mock_model.py."""
    checkpoint = torch.load(model_path, map_location=device)
    state_dict = checkpoint.get("model_state_dict", checkpoint)
    num_classes = (
        checkpoint.get("num_classes") or state_dict["classifier.3.weight"].shape[0]
    )
    model = MobileNetV2FoodClassifier(num_classes=num_classes, pretrained=False)
    model.load_state_dict(state_dict)
    model.to(device).eval()
    return model, checkpoint
