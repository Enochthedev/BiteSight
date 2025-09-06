"""
Training pipeline for Nigerian food recognition model.
Implements training loop with proper validation and model checkpointing.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
import logging
import time
from dataclasses import dataclass
import json

# Optional tensorboard import
try:
    from torch.utils.tensorboard import SummaryWriter
    TENSORBOARD_AVAILABLE = True
except ImportError:
    TENSORBOARD_AVAILABLE = False
    SummaryWriter = None

logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """Configuration for model training."""
    epochs: int = 50
    learning_rate: float = 0.001
    batch_size: int = 32
    weight_decay: float = 1e-4
    momentum: float = 0.9
    scheduler_step_size: int = 10
    scheduler_gamma: float = 0.1
    early_stopping_patience: int = 10
    save_best_only: bool = True
    checkpoint_dir: str = "checkpoints"
    log_dir: str = "logs"
    device: str = "auto"  # "auto", "cpu", "cuda"
    mixed_precision: bool = True
    gradient_clip_norm: Optional[float] = 1.0


@dataclass
class TrainingMetrics:
    """Training metrics for one epoch."""
    epoch: int
    train_loss: float
    train_accuracy: float
    val_loss: float
    val_accuracy: float
    learning_rate: float
    epoch_time: float


class FoodModelTrainer:
    """
    Trainer class for Nigerian food recognition models.
    Handles training loop, validation, checkpointing, and logging.
    """

    def __init__(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        val_loader: DataLoader,
        config: TrainingConfig,
        class_names: Optional[List[str]] = None
    ):
        """
        Initialize trainer.

        Args:
            model: PyTorch model to train
            train_loader: Training data loader
            val_loader: Validation data loader
            config: Training configuration
            class_names: List of class names for logging
        """
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.config = config
        self.class_names = class_names or [
            f"class_{i}" for i in range(model.num_classes)]

        # Setup device
        if config.device == "auto":
            self.device = torch.device(
                "cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(config.device)

        self.model.to(self.device)

        # Setup optimizer and scheduler
        self.optimizer = optim.SGD(
            self.model.parameters(),
            lr=config.learning_rate,
            momentum=config.momentum,
            weight_decay=config.weight_decay
        )

        self.scheduler = optim.lr_scheduler.StepLR(
            self.optimizer,
            step_size=config.scheduler_step_size,
            gamma=config.scheduler_gamma
        )

        # Loss function
        self.criterion = nn.CrossEntropyLoss()

        # Mixed precision training
        self.scaler = torch.cuda.amp.GradScaler() if config.mixed_precision else None

        # Setup directories
        self.checkpoint_dir = Path(config.checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)

        self.log_dir = Path(config.log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Setup tensorboard (optional)
        self.writer = SummaryWriter(
            self.log_dir) if TENSORBOARD_AVAILABLE else None

        # Training state
        self.current_epoch = 0
        self.best_val_accuracy = 0.0
        self.best_val_loss = float('inf')
        self.epochs_without_improvement = 0
        self.training_history: List[TrainingMetrics] = []

        logger.info(f"Trainer initialized on device: {self.device}")
        logger.info(
            f"Model has {sum(p.numel() for p in model.parameters())} parameters")

    def train_epoch(self) -> Tuple[float, float]:
        """
        Train for one epoch.

        Returns:
            Tuple of (average_loss, accuracy)
        """
        self.model.train()
        total_loss = 0.0
        correct_predictions = 0
        total_samples = 0

        for batch_idx, (images, targets) in enumerate(self.train_loader):
            images, targets = images.to(self.device), targets.to(self.device)

            self.optimizer.zero_grad()

            # Forward pass with mixed precision
            if self.scaler:
                with torch.cuda.amp.autocast():
                    outputs = self.model(images)
                    loss = self.criterion(outputs, targets)

                # Backward pass
                self.scaler.scale(loss).backward()

                # Gradient clipping
                if self.config.gradient_clip_norm:
                    self.scaler.unscale_(self.optimizer)
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(),
                        self.config.gradient_clip_norm
                    )

                self.scaler.step(self.optimizer)
                self.scaler.update()
            else:
                outputs = self.model(images)
                loss = self.criterion(outputs, targets)
                loss.backward()

                # Gradient clipping
                if self.config.gradient_clip_norm:
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(),
                        self.config.gradient_clip_norm
                    )

                self.optimizer.step()

            # Statistics
            total_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            correct_predictions += (predicted == targets).sum().item()
            total_samples += targets.size(0)

            # Log batch progress
            if batch_idx % 50 == 0:
                logger.debug(
                    f"Epoch {self.current_epoch}, Batch {batch_idx}/{len(self.train_loader)}, "
                    f"Loss: {loss.item():.4f}"
                )

        avg_loss = total_loss / len(self.train_loader)
        accuracy = 100.0 * correct_predictions / total_samples

        return avg_loss, accuracy

    def validate_epoch(self) -> Tuple[float, float]:
        """
        Validate for one epoch.

        Returns:
            Tuple of (average_loss, accuracy)
        """
        self.model.eval()
        total_loss = 0.0
        correct_predictions = 0
        total_samples = 0

        with torch.no_grad():
            for images, targets in self.val_loader:
                images, targets = images.to(
                    self.device), targets.to(self.device)

                outputs = self.model(images)
                loss = self.criterion(outputs, targets)

                total_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                correct_predictions += (predicted == targets).sum().item()
                total_samples += targets.size(0)

        avg_loss = total_loss / len(self.val_loader)
        accuracy = 100.0 * correct_predictions / total_samples

        return avg_loss, accuracy

    def save_checkpoint(
        self,
        epoch: int,
        is_best: bool = False,
        additional_info: Optional[Dict] = None
    ):
        """Save model checkpoint."""
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'best_val_accuracy': self.best_val_accuracy,
            'best_val_loss': self.best_val_loss,
            'config': self.config,
            'class_names': self.class_names
        }

        if additional_info:
            checkpoint.update(additional_info)

        # Save regular checkpoint
        checkpoint_path = self.checkpoint_dir / f"checkpoint_epoch_{epoch}.pth"
        torch.save(checkpoint, checkpoint_path)

        # Save best model
        if is_best:
            best_path = self.checkpoint_dir / "best_model.pth"
            torch.save(checkpoint, best_path)
            logger.info(
                f"Saved best model with validation accuracy: {self.best_val_accuracy:.2f}%")

    def load_checkpoint(self, checkpoint_path: str) -> int:
        """
        Load checkpoint and resume training.

        Args:
            checkpoint_path: Path to checkpoint file

        Returns:
            Epoch number to resume from
        """
        checkpoint = torch.load(checkpoint_path, map_location=self.device)

        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])

        self.best_val_accuracy = checkpoint.get('best_val_accuracy', 0.0)
        self.best_val_loss = checkpoint.get('best_val_loss', float('inf'))

        epoch = checkpoint['epoch']
        logger.info(f"Resumed training from epoch {epoch}")

        return epoch

    def train(self, resume_from: Optional[str] = None) -> List[TrainingMetrics]:
        """
        Main training loop.

        Args:
            resume_from: Path to checkpoint to resume from

        Returns:
            List of training metrics for each epoch
        """
        start_epoch = 0

        if resume_from:
            start_epoch = self.load_checkpoint(resume_from) + 1

        logger.info(f"Starting training for {self.config.epochs} epochs")
        logger.info(f"Training samples: {len(self.train_loader.dataset)}")
        logger.info(f"Validation samples: {len(self.val_loader.dataset)}")

        for epoch in range(start_epoch, self.config.epochs):
            self.current_epoch = epoch
            epoch_start_time = time.time()

            # Training phase
            train_loss, train_accuracy = self.train_epoch()

            # Validation phase
            val_loss, val_accuracy = self.validate_epoch()

            # Update scheduler
            self.scheduler.step()

            # Calculate epoch time
            epoch_time = time.time() - epoch_start_time

            # Create metrics
            metrics = TrainingMetrics(
                epoch=epoch,
                train_loss=train_loss,
                train_accuracy=train_accuracy,
                val_loss=val_loss,
                val_accuracy=val_accuracy,
                learning_rate=self.optimizer.param_groups[0]['lr'],
                epoch_time=epoch_time
            )

            self.training_history.append(metrics)

            # Log metrics (if tensorboard available)
            if self.writer:
                self.writer.add_scalar('Loss/Train', train_loss, epoch)
                self.writer.add_scalar('Loss/Validation', val_loss, epoch)
                self.writer.add_scalar('Accuracy/Train', train_accuracy, epoch)
                self.writer.add_scalar(
                    'Accuracy/Validation', val_accuracy, epoch)
                self.writer.add_scalar(
                    'Learning_Rate', metrics.learning_rate, epoch)

            # Check for improvement
            is_best = val_accuracy > self.best_val_accuracy
            if is_best:
                self.best_val_accuracy = val_accuracy
                self.best_val_loss = val_loss
                self.epochs_without_improvement = 0
            else:
                self.epochs_without_improvement += 1

            # Save checkpoint
            if self.config.save_best_only:
                if is_best:
                    self.save_checkpoint(epoch, is_best=True)
            else:
                self.save_checkpoint(epoch, is_best=is_best)

            # Log progress
            logger.info(
                f"Epoch {epoch:3d}/{self.config.epochs}: "
                f"Train Loss: {train_loss:.4f}, Train Acc: {train_accuracy:.2f}%, "
                f"Val Loss: {val_loss:.4f}, Val Acc: {val_accuracy:.2f}%, "
                f"LR: {metrics.learning_rate:.6f}, Time: {epoch_time:.1f}s"
            )

            # Early stopping
            if self.epochs_without_improvement >= self.config.early_stopping_patience:
                logger.info(
                    f"Early stopping triggered after {self.config.early_stopping_patience} "
                    f"epochs without improvement"
                )
                break

        # Save final training history
        self.save_training_history()

        logger.info(
            f"Training completed. Best validation accuracy: {self.best_val_accuracy:.2f}%")

        return self.training_history

    def save_training_history(self):
        """Save training history to JSON file."""
        history_data = []
        for metrics in self.training_history:
            history_data.append({
                'epoch': metrics.epoch,
                'train_loss': metrics.train_loss,
                'train_accuracy': metrics.train_accuracy,
                'val_loss': metrics.val_loss,
                'val_accuracy': metrics.val_accuracy,
                'learning_rate': metrics.learning_rate,
                'epoch_time': metrics.epoch_time
            })

        history_path = self.log_dir / "training_history.json"
        with open(history_path, 'w') as f:
            json.dump(history_data, f, indent=2)

        logger.info(f"Training history saved to {history_path}")

    def evaluate_model(self, test_loader: DataLoader) -> Dict[str, float]:
        """
        Evaluate model on test set.

        Args:
            test_loader: Test data loader

        Returns:
            Dictionary with evaluation metrics
        """
        self.model.eval()

        all_predictions = []
        all_targets = []
        total_loss = 0.0

        with torch.no_grad():
            for images, targets in test_loader:
                images, targets = images.to(
                    self.device), targets.to(self.device)

                outputs = self.model(images)
                loss = self.criterion(outputs, targets)

                total_loss += loss.item()

                _, predicted = torch.max(outputs, 1)
                all_predictions.extend(predicted.cpu().numpy())
                all_targets.extend(targets.cpu().numpy())

        # Calculate metrics
        all_predictions = np.array(all_predictions)
        all_targets = np.array(all_targets)

        accuracy = 100.0 * np.sum(all_predictions ==
                                  all_targets) / len(all_targets)
        avg_loss = total_loss / len(test_loader)

        # Per-class accuracy
        class_accuracies = {}
        for i, class_name in enumerate(self.class_names):
            class_mask = all_targets == i
            if np.sum(class_mask) > 0:
                class_acc = 100.0 * np.sum(
                    all_predictions[class_mask] == all_targets[class_mask]
                ) / np.sum(class_mask)
                class_accuracies[class_name] = class_acc

        results = {
            'test_accuracy': accuracy,
            'test_loss': avg_loss,
            'class_accuracies': class_accuracies,
            'total_samples': len(all_targets)
        }

        logger.info(
            f"Test Results: Accuracy: {accuracy:.2f}%, Loss: {avg_loss:.4f}")

        return results


def create_trainer(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    config: Optional[TrainingConfig] = None,
    **kwargs
) -> FoodModelTrainer:
    """
    Factory function to create a trainer.

    Args:
        model: Model to train
        train_loader: Training data loader
        val_loader: Validation data loader
        config: Training configuration
        **kwargs: Additional arguments for trainer

    Returns:
        Initialized trainer
    """
    if config is None:
        config = TrainingConfig()

    return FoodModelTrainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        config=config,
        **kwargs
    )
