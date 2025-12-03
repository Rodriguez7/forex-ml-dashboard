# src/models.py

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
)
import pickle
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from .config import MODEL_DIR, CONFIDENCE_THRESHOLD
from .dataset import get_train_val_test_splits, get_feature_columns


def train_lightgbm_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    params: Optional[Dict] = None,
) -> lgb.LGBMClassifier:
    """
    Train LightGBM classifier with validation set.
    
    Args:
        X_train: Training features
        y_train: Training labels
        X_val: Validation features
        y_val: Validation labels
        params: Optional LightGBM parameters
    
    Returns:
        Trained LightGBM model
    """
    if params is None:
        params = {
            'n_estimators': 200,
            'max_depth': 5,
            'learning_rate': 0.05,
            'num_leaves': 31,
            'min_child_samples': 20,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'n_jobs': -1,
            'verbose': -1,
        }
    
    print("Training LightGBM model...")
    print(f"Parameters: {params}")
    
    model = lgb.LGBMClassifier(**params)
    
    # Train with validation set for early stopping
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        eval_metric='binary_logloss',
        callbacks=[lgb.early_stopping(stopping_rounds=20, verbose=False)]
    )
    
    print(f"✓ Model trained ({model.n_estimators} trees)")
    
    return model


def evaluate_model(
    model: lgb.LGBMClassifier,
    X: pd.DataFrame,
    y: pd.Series,
    set_name: str = "Test",
) -> Dict:
    """
    Evaluate model and return comprehensive metrics.
    
    Args:
        model: Trained model
        X: Features
        y: True labels
        set_name: Name of dataset (for display)
    
    Returns:
        Dict with evaluation metrics
    """
    # Predictions
    y_pred = model.predict(X)
    y_pred_proba = model.predict_proba(X)[:, 1]
    
    # Metrics
    metrics = {
        'accuracy': accuracy_score(y, y_pred),
        'precision': precision_score(y, y_pred, zero_division=0),
        'recall': recall_score(y, y_pred, zero_division=0),
        'f1': f1_score(y, y_pred, zero_division=0),
        'roc_auc': roc_auc_score(y, y_pred_proba),
    }
    
    print(f"\n{set_name} Set Metrics:")
    print(f"  Accuracy:  {metrics['accuracy']:.4f}")
    print(f"  Precision: {metrics['precision']:.4f}")
    print(f"  Recall:    {metrics['recall']:.4f}")
    print(f"  F1 Score:  {metrics['f1']:.4f}")
    print(f"  ROC AUC:   {metrics['roc_auc']:.4f}")
    
    return metrics


def analyze_probability_buckets(
    model: lgb.LGBMClassifier,
    X: pd.DataFrame,
    y: pd.Series,
    buckets: List[Tuple[float, float]] = None,
) -> pd.DataFrame:
    """
    Analyze win rate by probability bucket.
    
    This is crucial for confidence-based filtering:
    higher probability predictions should have higher win rates.
    
    Args:
        model: Trained model
        X: Features
        y: True labels
        buckets: List of (min_prob, max_prob) tuples
    
    Returns:
        DataFrame with bucket analysis
    """
    if buckets is None:
        buckets = [
            (0.0, 0.5),
            (0.5, 0.6),
            (0.6, 0.7),
            (0.7, 0.8),
            (0.8, 0.9),
            (0.9, 1.0),
        ]
    
    y_pred_proba = model.predict_proba(X)[:, 1]
    
    results = []
    for min_prob, max_prob in buckets:
        mask = (y_pred_proba >= min_prob) & (y_pred_proba < max_prob)
        
        if mask.sum() == 0:
            continue
        
        bucket_y = y[mask]
        win_rate = bucket_y.mean()
        
        results.append({
            'bucket': f'{min_prob:.1f}-{max_prob:.1f}',
            'min_prob': min_prob,
            'max_prob': max_prob,
            'count': mask.sum(),
            'win_rate': win_rate,
            'pct_of_total': mask.sum() / len(y) * 100,
        })
    
    df = pd.DataFrame(results)
    
    print("\nWin Rate by Probability Bucket:")
    print(df.to_string(index=False))
    
    return df


def get_feature_importance(
    model: lgb.LGBMClassifier,
    feature_names: List[str],
    top_n: int = 20,
) -> pd.DataFrame:
    """
    Get and display feature importance.
    
    Args:
        model: Trained model
        feature_names: List of feature names
        top_n: Number of top features to return
    
    Returns:
        DataFrame with feature importance
    """
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"\nTop {top_n} Most Important Features:")
    for i, row in importance_df.head(top_n).iterrows():
        print(f"  {row['feature']:30s}: {row['importance']:8.1f}")
    
    return importance_df


def save_model(
    model: lgb.LGBMClassifier,
    feature_names: List[str],
    metadata: Dict,
    model_name: str = "lgbm_baseline",
):
    """
    Save trained model, feature list, and metadata.
    
    Args:
        model: Trained model
        feature_names: List of feature names
        metadata: Dict with training metadata (metrics, params, etc.)
        model_name: Name for saved model
    """
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save model
    model_path = MODEL_DIR / f"{model_name}.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"\n✓ Model saved to {model_path}")
    
    # Save feature names
    features_path = MODEL_DIR / f"{model_name}_features.txt"
    with open(features_path, 'w') as f:
        f.write('\n'.join(feature_names))
    print(f"✓ Features saved to {features_path}")
    
    # Save metadata
    metadata_path = MODEL_DIR / f"{model_name}_metadata.pkl"
    with open(metadata_path, 'wb') as f:
        pickle.dump(metadata, f)
    print(f"✓ Metadata saved to {metadata_path}")


def load_model(model_name: str = "lgbm_baseline") -> Tuple[lgb.LGBMClassifier, List[str], Dict]:
    """
    Load trained model, feature list, and metadata.
    
    Args:
        model_name: Name of saved model
    
    Returns:
        Tuple of (model, feature_names, metadata)
    """
    # Load model
    model_path = MODEL_DIR / f"{model_name}.pkl"
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    # Load feature names
    features_path = MODEL_DIR / f"{model_name}_features.txt"
    with open(features_path, 'r') as f:
        feature_names = [line.strip() for line in f]
    
    # Load metadata
    metadata_path = MODEL_DIR / f"{model_name}_metadata.pkl"
    with open(metadata_path, 'rb') as f:
        metadata = pickle.load(f)
    
    print(f"✓ Model loaded from {model_path}")
    
    return model, feature_names, metadata


def train_and_evaluate_model(
    params: Optional[Dict] = None,
    model_name: str = "lgbm_baseline",
) -> Tuple[lgb.LGBMClassifier, Dict]:
    """
    Complete training pipeline: load data, train, evaluate, save.
    
    Args:
        params: Optional LightGBM parameters
        model_name: Name for saved model
    
    Returns:
        Tuple of (model, metrics_dict)
    """
    print("=" * 80)
    print("MODEL TRAINING PIPELINE")
    print("=" * 80)
    
    # Load data
    print("\n1. Loading data...")
    X_train, y_train, X_val, y_val, X_test, y_test = get_train_val_test_splits()
    
    print(f"   Train: {len(X_train):,} samples")
    print(f"   Val:   {len(X_val):,} samples")
    print(f"   Test:  {len(X_test):,} samples")
    print(f"   Features: {len(X_train.columns)}")
    
    # Train model
    print("\n2. Training model...")
    model = train_lightgbm_model(X_train, y_train, X_val, y_val, params)
    
    # Evaluate
    print("\n3. Evaluating model...")
    train_metrics = evaluate_model(model, X_train, y_train, "Train")
    val_metrics = evaluate_model(model, X_val, y_val, "Validation")
    test_metrics = evaluate_model(model, X_test, y_test, "Test")
    
    # Probability analysis (on test set)
    print("\n4. Analyzing probability buckets (Test set)...")
    bucket_df = analyze_probability_buckets(model, X_test, y_test)
    
    # Feature importance
    print("\n5. Analyzing feature importance...")
    importance_df = get_feature_importance(model, X_train.columns.tolist(), top_n=20)
    
    # Save model
    print("\n6. Saving model...")
    metadata = {
        'train_metrics': train_metrics,
        'val_metrics': val_metrics,
        'test_metrics': test_metrics,
        'bucket_analysis': bucket_df,
        'feature_importance': importance_df,
        'params': params or {},
        'n_features': len(X_train.columns),
        'n_train': len(X_train),
        'n_val': len(X_val),
        'n_test': len(X_test),
    }
    save_model(model, X_train.columns.tolist(), metadata, model_name)
    
    print("\n" + "=" * 80)
    print("✓ Training complete!")
    print("=" * 80)
    
    # Summary
    print("\n📊 Summary:")
    print(f"   Test Accuracy: {test_metrics['accuracy']:.4f}")
    print(f"   Test ROC AUC:  {test_metrics['roc_auc']:.4f}")
    
    # High confidence subset
    high_conf_bucket = bucket_df[bucket_df['min_prob'] >= CONFIDENCE_THRESHOLD]
    if len(high_conf_bucket) > 0:
        avg_high_conf_wr = high_conf_bucket['win_rate'].mean()
        high_conf_count = high_conf_bucket['count'].sum()
        print(f"\n   High-Confidence Trades (prob ≥ {CONFIDENCE_THRESHOLD}):")
        print(f"     Count:    {high_conf_count:,} ({high_conf_count/len(X_test)*100:.1f}% of test)")
        print(f"     Win Rate: {avg_high_conf_wr:.4f} ({avg_high_conf_wr*100:.1f}%)")
    
    return model, metadata


if __name__ == "__main__":
    # Train baseline model
    model, metrics = train_and_evaluate_model()




