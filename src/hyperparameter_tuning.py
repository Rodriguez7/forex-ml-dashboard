# src/hyperparameter_tuning.py

import optuna
import lightgbm as lgb
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import roc_auc_score, accuracy_score
from typing import Dict
from .dataset import get_train_val_test_splits
from .models import train_lightgbm_model, evaluate_model, save_model


def objective(trial: optuna.Trial) -> float:
    """
    Optuna objective function for hyperparameter optimization.
    
    Args:
        trial: Optuna trial object
    
    Returns:
        ROC-AUC score on validation set
    """
    # Load data (cached after first call)
    if not hasattr(objective, 'data_loaded'):
        print("Loading dataset...")
        objective.X_train, objective.y_train, objective.X_val, objective.y_val, _, _ = get_train_val_test_splits()
        objective.data_loaded = True
    
    X_train = objective.X_train
    y_train = objective.y_train
    X_val = objective.X_val
    y_val = objective.y_val
    
    # Suggest hyperparameters
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 500),
        'max_depth': trial.suggest_int('max_depth', 3, 9),
        'num_leaves': trial.suggest_int('num_leaves', 15, 127),
        'min_child_samples': trial.suggest_int('min_child_samples', 10, 100),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
        'feature_fraction': trial.suggest_float('feature_fraction', 0.6, 0.95),
        'bagging_fraction': trial.suggest_float('bagging_fraction', 0.6, 0.95),
        'bagging_freq': trial.suggest_int('bagging_freq', 1, 7),
        'lambda_l1': trial.suggest_float('lambda_l1', 0.0, 2.0),
        'lambda_l2': trial.suggest_float('lambda_l2', 0.0, 2.0),
        'min_gain_to_split': trial.suggest_float('min_gain_to_split', 0.0, 1.0),
        'random_state': 42,
        'n_jobs': -1,
        'verbose': -1,
    }
    
    # Train model
    model = lgb.LGBMClassifier(**params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        eval_metric='binary_logloss',
        callbacks=[lgb.early_stopping(stopping_rounds=20, verbose=False)]
    )
    
    # Evaluate on validation set
    y_pred_proba = model.predict_proba(X_val)[:, 1]
    roc_auc = roc_auc_score(y_val, y_pred_proba)
    
    # Also track accuracy
    y_pred = model.predict(X_val)
    accuracy = accuracy_score(y_val, y_pred)
    
    # Report intermediate results
    trial.set_user_attr('accuracy', accuracy)
    
    return roc_auc


def tune_hyperparameters(
    n_trials: int = 100,
    timeout: int = None,
    study_name: str = "lgbm_forex_optimization"
) -> Dict:
    """
    Run hyperparameter optimization using Optuna.
    
    Args:
        n_trials: Number of optimization trials
        timeout: Timeout in seconds (None for no timeout)
        study_name: Name for the Optuna study
    
    Returns:
        Dict with best parameters and metrics
    """
    print("=" * 80)
    print("HYPERPARAMETER OPTIMIZATION WITH OPTUNA")
    print("=" * 80)
    print(f"\nOptimization settings:")
    print(f"  Number of trials: {n_trials}")
    print(f"  Timeout: {timeout if timeout else 'None'}")
    print(f"  Objective: ROC-AUC on validation set")
    print("\n" + "=" * 80 + "\n")
    
    # Create study
    study = optuna.create_study(
        direction="maximize",  # Maximize ROC-AUC
        study_name=study_name,
        sampler=optuna.samplers.TPESampler(seed=42),
    )
    
    # Optimize
    study.optimize(
        objective,
        n_trials=n_trials,
        timeout=timeout,
        show_progress_bar=True,
        callbacks=[
            lambda study, trial: print(
                f"Trial {trial.number}: "
                f"ROC-AUC={trial.value:.4f}, "
                f"Accuracy={trial.user_attrs.get('accuracy', 0):.4f}"
            )
        ]
    )
    
    print("\n" + "=" * 80)
    print("OPTIMIZATION COMPLETE!")
    print("=" * 80)
    
    # Best trial
    best_trial = study.best_trial
    print(f"\nBest trial: #{best_trial.number}")
    print(f"  ROC-AUC: {best_trial.value:.4f}")
    print(f"  Accuracy: {best_trial.user_attrs.get('accuracy', 0):.4f}")
    
    print("\nBest hyperparameters:")
    for key, value in best_trial.params.items():
        print(f"  {key:20s}: {value}")
    
    # Parameter importance
    try:
        importance = optuna.importance.get_param_importances(study)
        print("\nParameter Importance (top 10):")
        for i, (param, imp) in enumerate(sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10], 1):
            print(f"  {i:2d}. {param:20s}: {imp:.4f}")
    except:
        pass
    
    return {
        'best_params': best_trial.params,
        'best_roc_auc': best_trial.value,
        'best_accuracy': best_trial.user_attrs.get('accuracy', 0),
        'n_trials': len(study.trials),
        'study': study,
    }


def train_optimized_model(best_params: Dict, model_name: str = "lgbm_optimized"):
    """
    Train final model with optimized hyperparameters.
    
    Args:
        best_params: Best hyperparameters from Optuna
        model_name: Name for saved model
    """
    print("\n" + "=" * 80)
    print("TRAINING FINAL MODEL WITH OPTIMIZED PARAMETERS")
    print("=" * 80)
    
    # Load data
    X_train, y_train, X_val, y_val, X_test, y_test = get_train_val_test_splits()
    
    # Train model
    model = train_lightgbm_model(X_train, y_train, X_val, y_val, params=best_params)
    
    # Evaluate
    print("\nEvaluating optimized model...")
    train_metrics = evaluate_model(model, X_train, y_train, "Train")
    val_metrics = evaluate_model(model, X_val, y_val, "Validation")
    test_metrics = evaluate_model(model, X_test, y_test, "Test")
    
    # Save model
    from .models import get_feature_importance, analyze_probability_buckets
    
    bucket_df = analyze_probability_buckets(model, X_test, y_test)
    importance_df = get_feature_importance(model, X_train.columns.tolist(), top_n=20)
    
    metadata = {
        'train_metrics': train_metrics,
        'val_metrics': val_metrics,
        'test_metrics': test_metrics,
        'bucket_analysis': bucket_df,
        'feature_importance': importance_df,
        'params': best_params,
        'n_features': len(X_train.columns),
        'n_train': len(X_train),
        'n_val': len(X_val),
        'n_test': len(X_test),
        'optimization': 'optuna',
    }
    
    save_model(model, X_train.columns.tolist(), metadata, model_name)
    
    print("\n" + "=" * 80)
    print("✓ Optimized model training complete!")
    print("=" * 80)
    
    print("\n📊 Performance Comparison:")
    print(f"  Validation ROC-AUC: {val_metrics['roc_auc']:.4f}")
    print(f"  Test Accuracy: {test_metrics['accuracy']:.4f}")
    print(f"  Test ROC-AUC: {test_metrics['roc_auc']:.4f}")
    
    return model, metadata


if __name__ == "__main__":
    # Run optimization
    results = tune_hyperparameters(n_trials=100)
    
    # Train final model with best parameters
    model, metadata = train_optimized_model(results['best_params'])



