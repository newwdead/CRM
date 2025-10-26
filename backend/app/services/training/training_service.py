"""
Training Service
High-level service for model training orchestration
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from pathlib import Path

from ..base import BaseService
from .dataset_preparer import DatasetPreparer
from .model_trainer import ModelTrainer

logger = logging.getLogger(__name__)


class TrainingService(BaseService):
    """
    Training service for LayoutLMv3 model management
    
    Features:
    - Orchestrates training pipeline
    - Manages training data
    - Version control for models
    - Training metrics tracking
    """
    
    def __init__(
        self,
        db: Session,
        models_dir: str = "./models",
        datasets_dir: str = "./datasets"
    ):
        """
        Initialize training service
        
        Args:
            db: SQLAlchemy database session
            models_dir: Directory for model storage
            datasets_dir: Directory for dataset storage
        """
        super().__init__(db)
        self.models_dir = Path(models_dir)
        self.datasets_dir = Path(datasets_dir)
        self.dataset_preparer = DatasetPreparer()
        self.model_trainer = None
        
        # Create directories
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
    
    def prepare_training_data(
        self,
        annotations: List[Dict[str, Any]],
        images: List[bytes]
    ) -> Dict[str, Any]:
        """
        Prepare training data from Label Studio annotations
        
        Args:
            annotations: Label Studio annotations
            images: Business card images
        
        Returns:
            Dataset info dictionary
        """
        try:
            logger.info(f"📚 Preparing training data from {len(annotations)} samples...")
            
            # Convert annotations
            samples, labels = self.dataset_preparer.prepare_from_label_studio(
                annotations, images
            )
            
            # Split dataset
            train_samples, val_samples, test_samples = self.dataset_preparer.split_dataset(samples)
            
            # Save datasets
            self.dataset_preparer.save_dataset(
                train_samples,
                str(self.datasets_dir / "train.json")
            )
            self.dataset_preparer.save_dataset(
                val_samples,
                str(self.datasets_dir / "val.json")
            )
            self.dataset_preparer.save_dataset(
                test_samples,
                str(self.datasets_dir / "test.json")
            )
            
            dataset_info = {
                'total_samples': len(samples),
                'train_samples': len(train_samples),
                'val_samples': len(val_samples),
                'test_samples': len(test_samples),
                'unique_labels': len(set(labels)),
                'dataset_dir': str(self.datasets_dir),
            }
            
            logger.info(f"✅ Training data prepared: {dataset_info}")
            return dataset_info
            
        except Exception as e:
            logger.error(f"❌ Failed to prepare training data: {e}", exc_info=True)
            return {}
    
    def train_model(
        self,
        dataset_info: Dict[str, Any],
        model_version: str = "v1",
        epochs: int = 10,
        batch_size: int = 4,
        learning_rate: float = 5e-5
    ) -> Dict[str, Any]:
        """
        Train LayoutLMv3 model
        
        Args:
            dataset_info: Dataset information from prepare_training_data
            model_version: Model version identifier
            epochs: Number of training epochs
            batch_size: Batch size
            learning_rate: Learning rate
        
        Returns:
            Training results
        """
        try:
            logger.info(f"🎯 Starting model training (version: {model_version})...")
            
            # Load datasets
            import json
            with open(self.datasets_dir / "train.json") as f:
                train_samples = json.load(f)
            with open(self.datasets_dir / "val.json") as f:
                val_samples = json.load(f)
            
            # Initialize trainer
            output_dir = self.models_dir / f"layoutlmv3-bizcard-{model_version}"
            self.model_trainer = ModelTrainer(
                output_dir=str(output_dir),
                num_labels=12  # Number of business card fields + OTHER
            )
            
            # Train
            metrics = self.model_trainer.train(
                train_samples=train_samples,
                val_samples=val_samples,
                epochs=epochs,
                batch_size=batch_size,
                learning_rate=learning_rate
            )
            
            # Save training info
            training_info = {
                'model_version': model_version,
                'model_path': str(output_dir),
                'dataset_info': dataset_info,
                'training_params': {
                    'epochs': epochs,
                    'batch_size': batch_size,
                    'learning_rate': learning_rate,
                },
                'metrics': metrics,
            }
            
            # Save training info
            with open(output_dir / "training_info.json", 'w') as f:
                json.dump(training_info, f, indent=2)
            
            logger.info(f"✅ Model training complete: {model_version}")
            return training_info
            
        except Exception as e:
            logger.error(f"❌ Model training failed: {e}", exc_info=True)
            return {}
    
    def evaluate_model(
        self,
        model_version: str
    ) -> Dict[str, float]:
        """
        Evaluate trained model on test set
        
        Args:
            model_version: Model version to evaluate
        
        Returns:
            Evaluation metrics
        """
        try:
            logger.info(f"📊 Evaluating model: {model_version}...")
            
            # Load test dataset
            import json
            with open(self.datasets_dir / "test.json") as f:
                test_samples = json.load(f)
            
            # Load model
            model_path = self.models_dir / f"layoutlmv3-bizcard-{model_version}"
            if not model_path.exists():
                logger.error(f"❌ Model not found: {model_path}")
                return {}
            
            self.model_trainer = ModelTrainer()
            self.model_trainer.load_model(str(model_path / "final"))
            
            # Evaluate
            metrics = self.model_trainer.evaluate(test_samples)
            
            logger.info(f"✅ Evaluation complete: {metrics}")
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Evaluation failed: {e}", exc_info=True)
            return {}
    
    def list_models(self) -> List[Dict[str, Any]]:
        """
        List all trained models
        
        Returns:
            List of model info dictionaries
        """
        models = []
        
        for model_dir in self.models_dir.glob("layoutlmv3-bizcard-*"):
            if model_dir.is_dir():
                info_file = model_dir / "training_info.json"
                if info_file.exists():
                    import json
                    with open(info_file) as f:
                        info = json.load(f)
                        models.append(info)
        
        return models
    
    def get_best_model_path(self) -> Optional[str]:
        """
        Get path to best trained model
        
        Returns:
            Path to best model or None
        """
        models = self.list_models()
        if not models:
            return None
        
        # Sort by eval loss (lower is better)
        best_model = min(
            models,
            key=lambda m: m.get('metrics', {}).get('eval_loss', float('inf'))
        )
        
        return best_model.get('model_path')

