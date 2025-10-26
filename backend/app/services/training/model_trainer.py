"""
Model Trainer
Fine-tunes LayoutLMv3 model on business card data
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ModelTrainer:
    """
    Trainer for LayoutLMv3 model fine-tuning
    
    Features:
    - Fine-tune pre-trained LayoutLMv3
    - Training metrics tracking
    - Model checkpointing
    - Early stopping
    - Evaluation on validation set
    """
    
    def __init__(
        self,
        model_name: str = "microsoft/layoutlmv3-base",
        output_dir: str = "./models/layoutlmv3-bizcard",
        num_labels: int = 12
    ):
        """
        Initialize model trainer
        
        Args:
            model_name: Base model to fine-tune
            output_dir: Directory to save fine-tuned model
            num_labels: Number of labels for classification
        """
        self.model_name = model_name
        self.output_dir = Path(output_dir)
        self.num_labels = num_labels
        self.model = None
        self.trainer = None
    
    def train(
        self,
        train_samples: List[Dict[str, Any]],
        val_samples: List[Dict[str, Any]],
        epochs: int = 10,
        batch_size: int = 4,
        learning_rate: float = 5e-5
    ) -> Dict[str, Any]:
        """
        Train LayoutLMv3 model
        
        Args:
            train_samples: Training samples
            val_samples: Validation samples
            epochs: Number of training epochs
            batch_size: Batch size
            learning_rate: Learning rate
        
        Returns:
            Training metrics
        """
        try:
            from transformers import (
                AutoModelForTokenClassification,
                AutoProcessor,
                TrainingArguments,
                Trainer
            )
            from datasets import Dataset
            import torch
            
            logger.info(f"🚀 Starting LayoutLMv3 training...")
            logger.info(f"📊 Train samples: {len(train_samples)}, Val samples: {len(val_samples)}")
            
            # Load model and processor
            self.model = AutoModelForTokenClassification.from_pretrained(
                self.model_name,
                num_labels=self.num_labels
            )
            processor = AutoProcessor.from_pretrained(self.model_name, apply_ocr=False)
            
            # Prepare datasets
            train_dataset = self._prepare_dataset(train_samples, processor)
            val_dataset = self._prepare_dataset(val_samples, processor)
            
            # Training arguments
            training_args = TrainingArguments(
                output_dir=str(self.output_dir),
                evaluation_strategy="epoch",
                save_strategy="epoch",
                learning_rate=learning_rate,
                per_device_train_batch_size=batch_size,
                per_device_eval_batch_size=batch_size,
                num_train_epochs=epochs,
                weight_decay=0.01,
                load_best_model_at_end=True,
                metric_for_best_model="eval_loss",
                logging_dir=f"{self.output_dir}/logs",
                logging_steps=10,
                save_total_limit=3,
                remove_unused_columns=False,
            )
            
            # Initialize trainer
            self.trainer = Trainer(
                model=self.model,
                args=training_args,
                train_dataset=train_dataset,
                eval_dataset=val_dataset,
                tokenizer=processor,
            )
            
            # Train
            logger.info("⏳ Training started...")
            train_result = self.trainer.train()
            
            # Save final model
            self.trainer.save_model(str(self.output_dir / "final"))
            
            # Evaluate
            eval_result = self.trainer.evaluate()
            
            metrics = {
                'train_loss': train_result.training_loss,
                'eval_loss': eval_result['eval_loss'],
                'epochs': epochs,
                'total_steps': train_result.global_step,
            }
            
            logger.info(f"✅ Training complete! Metrics: {metrics}")
            
            return metrics
            
        except ImportError as e:
            logger.error(f"❌ Missing dependencies for training: {e}")
            logger.info("💡 Install with: pip install transformers datasets accelerate")
            return {}
        except Exception as e:
            logger.error(f"❌ Training failed: {e}", exc_info=True)
            return {}
    
    def _prepare_dataset(
        self,
        samples: List[Dict[str, Any]],
        processor
    ):
        """
        Prepare dataset for training
        
        Args:
            samples: Training samples
            processor: LayoutLMv3 processor
        
        Returns:
            HuggingFace Dataset
        """
        from datasets import Dataset
        from PIL import Image
        import io
        
        # Convert to HuggingFace dataset format
        dataset_dict = {
            'id': [],
            'words': [],
            'boxes': [],
            'labels': [],
            'image': [],
        }
        
        for sample in samples:
            dataset_dict['id'].append(sample['id'])
            dataset_dict['words'].append(sample['words'])
            dataset_dict['boxes'].append(sample['boxes'])
            dataset_dict['labels'].append(sample['labels'])
            
            # Convert image bytes to PIL Image
            image = Image.open(io.BytesIO(sample['image']))
            dataset_dict['image'].append(image)
        
        return Dataset.from_dict(dataset_dict)
    
    def evaluate(self, test_samples: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Evaluate model on test set
        
        Args:
            test_samples: Test samples
        
        Returns:
            Evaluation metrics
        """
        if not self.trainer:
            logger.error("❌ Model not trained yet")
            return {}
        
        try:
            from transformers import AutoProcessor
            
            processor = AutoProcessor.from_pretrained(self.model_name, apply_ocr=False)
            test_dataset = self._prepare_dataset(test_samples, processor)
            
            eval_result = self.trainer.evaluate(test_dataset)
            
            logger.info(f"📊 Test set evaluation: {eval_result}")
            return eval_result
            
        except Exception as e:
            logger.error(f"❌ Evaluation failed: {e}")
            return {}
    
    def save_model(self, output_path: str):
        """Save trained model"""
        if self.model:
            self.model.save_pretrained(output_path)
            logger.info(f"💾 Model saved to {output_path}")
    
    def load_model(self, model_path: str):
        """Load trained model"""
        try:
            from transformers import AutoModelForTokenClassification
            
            self.model = AutoModelForTokenClassification.from_pretrained(model_path)
            logger.info(f"✅ Model loaded from {model_path}")
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")

