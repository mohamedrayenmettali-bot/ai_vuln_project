import optuna
from optuna.pruners import MedianPruner
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.neighbors import KNeighborsRegressor

from ai.config import RANDOM_STATE
from ai.utils.ml_utils import weighted_mae

def _cv_mae(model, X: pd.DataFrame, y: pd.Series,
            weights: pd.Series, stratify_labels: pd.Series, 
            n_splits: int = 3, scale_data: bool = False) -> float:
    """K-fold weighted MAE — shared by all Optuna objectives."""
    kf   = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
    maes = []
    for train_idx, val_idx in kf.split(X, stratify_labels):
        X_t = X.iloc[train_idx];  X_v = X.iloc[val_idx]
        y_t = y.iloc[train_idx];  y_v = y.iloc[val_idx]
        w_t = weights.iloc[train_idx]; w_v = weights.iloc[val_idx]
        
        
        if scale_data:
            scaler = StandardScaler()
            X_t = pd.DataFrame(scaler.fit_transform(X_t), index=X_t.index, columns=X_t.columns)
            X_v = pd.DataFrame(scaler.transform(X_v), index=X_v.index, columns=X_v.columns)
            
        try:
            model.fit(X_t, y_t, sample_weight=w_t)
        except TypeError:
            model.fit(X_t, y_t)
            
        maes.append(weighted_mae(y_v, model.predict(X_v), w_v))
    return float(np.mean(maes))


def objective_xgb(trial, X, y, weights, stratify_labels):
    params = {
        "n_estimators":    trial.suggest_int("n_estimators", 100, 1000),
        "max_depth":       trial.suggest_int("max_depth", 3, 10),
        "learning_rate":   trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "subsample":       trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree":trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "reg_alpha":       trial.suggest_float("reg_alpha", 1e-4, 10.0, log=True),
        "reg_lambda":      trial.suggest_float("reg_lambda", 1e-4, 10.0, log=True),
        "random_state":    RANDOM_STATE,
        "verbosity":       0,
    }
    return _cv_mae(XGBRegressor(**params), X, y, weights, stratify_labels, scale_data=False)


def objective_lgbm(trial, X, y, weights, stratify_labels):
    params = {
        "n_estimators":  trial.suggest_int("n_estimators", 100, 1000),
        "max_depth":     trial.suggest_int("max_depth", 3, 15),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "num_leaves":    trial.suggest_int("num_leaves", 20, 150),
        "reg_alpha":     trial.suggest_float("reg_alpha", 1e-4, 10.0, log=True),
        "reg_lambda":    trial.suggest_float("reg_lambda", 1e-4, 10.0, log=True),
        "random_state":  RANDOM_STATE,
        "verbosity":     -1,
    }
    return _cv_mae(LGBMRegressor(**params), X, y, weights, stratify_labels, scale_data=False)


def objective_cat(trial, X, y, weights, stratify_labels):
    params = {
        "iterations":    trial.suggest_int("iterations", 100, 1000),
        "depth":         trial.suggest_int("depth", 4, 10),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "l2_leaf_reg":   trial.suggest_float("l2_leaf_reg", 1e-4, 10.0, log=True),
        "random_seed":   RANDOM_STATE,
        "verbose":       False,
    }
    return _cv_mae(CatBoostRegressor(**params), X, y, weights, stratify_labels, scale_data=False)


def objective_mlp(trial, X, y, weights, stratify_labels):
    params = {
        "hidden_layer_sizes": trial.suggest_categorical("hidden_layer_sizes", [(128, 64), (64, 32), (64,)]),
        "alpha":              trial.suggest_float("alpha", 1e-4, 0.5, log=True),
        "learning_rate_init": trial.suggest_float("learning_rate_init", 1e-4, 0.05, log=True),
        "max_iter":           trial.suggest_int("max_iter", 100, 400),
        "random_state":       RANDOM_STATE,
    }
    return _cv_mae(MLPRegressor(**params), X, y, weights, stratify_labels, scale_data=True)


def objective_knn(trial, X, y, weights, stratify_labels):
    params = {
        "n_neighbors": trial.suggest_int("n_neighbors", 3, 30),
        "weights":     trial.suggest_categorical("weights", ["uniform", "distance"]),
        "p":           trial.suggest_int("p", 1, 2)
    }
    return _cv_mae(KNeighborsRegressor(**params), X, y, weights, stratify_labels, scale_data=True)


def run_study(name: str, objective, X, y, weights, stratify_labels,
              n_trials: int = 50, timeout: int = 600, studies_dir = None) -> dict:
    """Create, run, and optionally save an Optuna study. Returns best params."""
    study = optuna.create_study(
        direction="minimize",
        study_name=name,
        pruner=MedianPruner(n_warmup_steps=5),
    )
    study.optimize(
        lambda trial: objective(trial, X, y, weights, stratify_labels),
        n_trials=n_trials,
        timeout=timeout,
        show_progress_bar=False,
    )
    print(f"  [{name}] best MAE = {study.best_value:.4f} "
          f"after {len(study.trials)} trials")

    if studies_dir:
        studies_dir.mkdir(parents=True, exist_ok=True)
        study.trials_dataframe().to_csv(studies_dir / f"{name}.csv", index=False)

    return study.best_params
