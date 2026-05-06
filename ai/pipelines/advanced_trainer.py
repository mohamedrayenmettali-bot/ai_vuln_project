import argparse
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import optuna
from optuna.pruners import MedianPruner
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error,
    r2_score, classification_report,
)
from sklearn.feature_selection import SelectFromModel
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.neighbors import KNeighborsRegressor

from ai.config import (
    FEATURE_COLS, TARGET_COL, MODEL_PATH, FEATURES_PATH,
    RANDOM_STATE, CV_FOLDS, SCORE_THRESHOLDS, DEFECTDOJO_CSV,
)
from ai.pipelines.data_loader import load_cvefixes, load_defectdojo, summarize

warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)

_base         = Path(MODEL_PATH).parent
SELECTOR_PATH = _base / "feature_selector.pkl"
PCA_PATH      = _base / "pca_reducer.pkl"
SCALER_PATH   = _base / "feature_scaler.pkl"
STUDIES_DIR   = _base / "optuna_studies"


from ai.utils.ml_utils import encode_chunked, score_to_severity, weighted_mae
from ai.pipelines.optimizer import run_study, objective_xgb, objective_lgbm, objective_cat, objective_mlp, objective_knn



def train_advanced(
    df: pd.DataFrame,
    nlp_model: str  = "cisco-ai/SecureBERT2.0-biencoder",
    tune: bool      = False,
    n_trials: int   = 50,
    tune_timeout: int = 600,
    pca_components: int = 64,
) -> dict:
    import lightgbm as lgb
    
    feature_cols = [c for c in FEATURE_COLS if c in df.columns]
    X_num        = df[feature_cols].fillna(0)
    y            = df[TARGET_COL]

    all_idx = df.index
    sev_labels = y.apply(score_to_severity)

    (idx_train, idx_test,
     y_train,   y_test,
     sev_train, sev_test) = train_test_split(
        all_idx, y, sev_labels,
        test_size=0.2, random_state=RANDOM_STATE,
        stratify=sev_labels
    )
    
    class_counts = sev_train.value_counts()
    total_samples = len(y_train)
    num_classes = len(class_counts)
    
    def get_weight(c):
        return total_samples / (num_classes * class_counts.get(c, 1))
        
    inv_weights_train = sev_train.map(get_weight)
    inv_weights_test = sev_test.map(get_weight)
    
    inv_weights_train = np.sqrt(inv_weights_train).clip(lower=0.5, upper=3.0)
    inv_weights_test = np.sqrt(inv_weights_test).clip(lower=0.5, upper=3.0)
    
    weights_full = pd.concat([inv_weights_train, inv_weights_test])
    
    if "sample_weight" in df.columns:
        print("[AdvancedTrainer] Combining inverse class frequency weights with existing sample_weight.")
        weights = weights_full * df["sample_weight"]
    else:
        print("[AdvancedTrainer] Using inverse class frequency weights for class imbalance.")
        weights = weights_full

    weights = pd.Series(weights, index=df.index)
    w_train = weights.loc[idx_train]
    w_test  = weights.loc[idx_test]

    pca_fitted = None

    if "description" in df.columns:
        print(f"[AdvancedTrainer] Generating NLP embeddings ({nlp_model})...")
        encoder      = SentenceTransformer(nlp_model)
        descriptions = df["description"].fillna("").astype(str).tolist()
        embeddings   = encode_chunked(encoder, descriptions)

        print(f"[AdvancedTrainer] Reducing embeddings: "
              f"{embeddings.shape[1]}d → {pca_components}d via PCA...")
        train_mask    = df.index.isin(idx_train)
        pca_fitted    = PCA(n_components=pca_components, random_state=RANDOM_STATE)
        pca_fitted.fit(embeddings[train_mask])
        embeddings_r  = pca_fitted.transform(embeddings)

        embedding_cols = [f"pca_emb_{i}" for i in range(pca_components)]
        df_emb         = pd.DataFrame(embeddings_r, columns=embedding_cols, index=df.index)
    else:
        print("[AdvancedTrainer] Warning: 'description' column not found — skipping NLP.")
        df_emb            = pd.DataFrame(index=df.index)
        embedding_cols    = []

    full_feature_cols = feature_cols + embedding_cols

    X_num_train = X_num.loc[idx_train]
    X_num_test  = X_num.loc[idx_test]

    print("[AdvancedTrainer] Performing feature selection on structured features...")
    selector_model = XGBRegressor(n_estimators=100, random_state=RANDOM_STATE, verbosity=0)
    selector_model.fit(X_num_train, y_train, sample_weight=w_train)
    selector = SelectFromModel(selector_model, threshold="0.5*mean", prefit=True)

    selected_numeric = [feature_cols[i] for i in selector.get_support(indices=True)]
    print(f"[AdvancedTrainer] Structured Features selected: {len(selected_numeric)} / {len(feature_cols)}")
    
    X_num_train_sel = pd.DataFrame(selector.transform(X_num_train), columns=selected_numeric, index=X_num_train.index)
    X_num_test_sel  = pd.DataFrame(selector.transform(X_num_test), columns=selected_numeric, index=X_num_test.index)
    
    if not df_emb.empty:
        X_train_sel = pd.concat([X_num_train_sel, df_emb.loc[idx_train]], axis=1)
        X_test_sel  = pd.concat([X_num_test_sel, df_emb.loc[idx_test]], axis=1)
    else:
        X_train_sel = X_num_train_sel
        X_test_sel  = X_num_test_sel

    selected_features = X_train_sel.columns.tolist()

    X_train_sel = X_train_sel.reset_index(drop=True)
    X_test_sel  = X_test_sel.reset_index(drop=True)
    y_train = y_train.reset_index(drop=True)
    y_test  = y_test.reset_index(drop=True)
    w_train = w_train.reset_index(drop=True)
    w_test  = w_test.reset_index(drop=True)
    sev_train = sev_train.reset_index(drop=True)

    print(f"\n[AdvancedTrainer] Train / Test : {len(X_train_sel):,} / {len(X_test_sel):,}")

    xgb_params  = {
        "n_estimators": 500, "max_depth": 6, "learning_rate": 0.05,
        "subsample": 0.8, "colsample_bytree": 0.8,
        "random_state": RANDOM_STATE, "verbosity": 0,
    }
    lgbm_params = {
        "n_estimators": 500, "max_depth": 6, "learning_rate": 0.05,
        "num_leaves": 63, "random_state": RANDOM_STATE, "verbosity": -1,
    }
    cat_params  = {
        "iterations": 500, "depth": 6, "learning_rate": 0.05,
        "random_seed": RANDOM_STATE, "verbose": False,
    }
    mlp_params = {
        "hidden_layer_sizes": (64, 32), "learning_rate_init": 0.005,
        "max_iter": 300, "random_state": RANDOM_STATE,
    }
    knn_params = {
        "n_neighbors": 5, "weights": "distance",
    }

    if tune:
        print(f"\n[AdvancedTrainer] Tuning with Optuna "
              f"({n_trials} trials / {tune_timeout}s timeout each)...")

        best_xgb  = run_study("xgb",  objective_xgb,  X_train_sel, y_train, w_train, sev_train, n_trials, tune_timeout, STUDIES_DIR)
        best_lgbm = run_study("lgbm", objective_lgbm, X_train_sel, y_train, w_train, sev_train, n_trials, tune_timeout, STUDIES_DIR)
        best_cat  = run_study("cat",  objective_cat,  X_train_sel, y_train, w_train, sev_train, n_trials, tune_timeout, STUDIES_DIR)
        best_mlp  = run_study("mlp",  objective_mlp,  X_train_sel, y_train, w_train, sev_train, n_trials, tune_timeout, STUDIES_DIR)
        best_knn  = run_study("knn",  objective_knn,  X_train_sel, y_train, w_train, sev_train, n_trials, tune_timeout, STUDIES_DIR)

        xgb_params.update(best_xgb)
        lgbm_params.update(best_lgbm)
        cat_params.update(best_cat)
        mlp_params.update(best_mlp)
        knn_params.update(best_knn)

    print("\n[AdvancedTrainer] Generating Out-Of-Fold (OOF) predictions for Stacking (5 Base Models)...")
    kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    oof_xgb  = np.zeros(len(X_train_sel))
    oof_lgbm = np.zeros(len(X_train_sel))
    oof_cat  = np.zeros(len(X_train_sel))
    oof_mlp  = np.zeros(len(X_train_sel))
    oof_knn  = np.zeros(len(X_train_sel))
    
    for train_idx, val_idx in kf.split(X_train_sel, sev_train):
        X_t, X_v = X_train_sel.iloc[train_idx], X_train_sel.iloc[val_idx]
        y_t, y_v = y_train.iloc[train_idx], y_train.iloc[val_idx]
        w_t      = w_train.iloc[train_idx]
        
        # Scaling specifically for distance/gradient based architectures
        scaler = StandardScaler()
        X_t_scaled = pd.DataFrame(scaler.fit_transform(X_t), index=X_t.index, columns=X_t.columns)
        X_v_scaled = pd.DataFrame(scaler.transform(X_v), index=X_v.index, columns=X_v.columns)

        # TREE ALGORITHMS (Scale-Invariant)
        try:
            m_lgbm = LGBMRegressor(**lgbm_params).fit(
                X_t, y_t, sample_weight=w_t, eval_set=[(X_v, y_v)],
                callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)]
            )
        except Exception:
            m_lgbm = LGBMRegressor(**lgbm_params).fit(X_t, y_t, sample_weight=w_t)
            
        m_xgb  = XGBRegressor(**xgb_params, early_stopping_rounds=50).fit(
            X_t, y_t, sample_weight=w_t, eval_set=[(X_v, y_v)], verbose=False
        )
        m_cat  = CatBoostRegressor(**cat_params).fit(
            X_t, y_t, sample_weight=w_t, eval_set=[(X_v, y_v)], early_stopping_rounds=50, verbose=False
        )
        
        # NEURAL & SPATIAL ALGORITHMS (Scale-Dependent)
        m_mlp  = MLPRegressor(**mlp_params).fit(X_t_scaled, y_t)
        m_knn  = KNeighborsRegressor(**knn_params).fit(X_t_scaled, y_t)
        
        # Prediction Aggregation
        oof_xgb[val_idx]  = m_xgb.predict(X_v)
        oof_lgbm[val_idx] = m_lgbm.predict(X_v)
        oof_cat[val_idx]  = m_cat.predict(X_v)
        oof_mlp[val_idx]  = m_mlp.predict(X_v_scaled)
        oof_knn[val_idx]  = m_knn.predict(X_v_scaled)

    print("[AdvancedTrainer] Training base models on full train split...")
    xgb_model = XGBRegressor(**xgb_params).fit(X_train_sel, y_train, sample_weight=w_train)
    lgbm_model = LGBMRegressor(**lgbm_params).fit(X_train_sel, y_train, sample_weight=w_train)
    cat_model = CatBoostRegressor(**cat_params).fit(X_train_sel, y_train, sample_weight=w_train)

    # Train master scaler on entire training subset
    scaler_full = StandardScaler()
    X_train_scaled = pd.DataFrame(scaler_full.fit_transform(X_train_sel), index=X_train_sel.index, columns=X_train_sel.columns)
    X_test_scaled  = pd.DataFrame(scaler_full.transform(X_test_sel), index=X_test_sel.index, columns=X_test_sel.columns)

    mlp_model = MLPRegressor(**mlp_params).fit(X_train_scaled, y_train)
    knn_model = KNeighborsRegressor(**knn_params).fit(X_train_scaled, y_train)

    from sklearn.linear_model import Ridge
    print("[AdvancedTrainer] Training Stacking Meta-Learner (Ridge) on OOF predictions...")
    oof_features = pd.DataFrame({
        "xgb": oof_xgb,
        "lgbm": oof_lgbm,
        "cat": oof_cat,
        "mlp": oof_mlp,
        "knn": oof_knn
    })
    meta_model = Ridge(alpha=100.0, random_state=RANDOM_STATE)
    meta_model.fit(oof_features, y_train, sample_weight=w_train)

    test_preds_xgb  = xgb_model.predict(X_test_sel)
    test_preds_lgbm = lgbm_model.predict(X_test_sel)
    test_preds_cat  = cat_model.predict(X_test_sel)
    # Neural and KNN predict specifically on the SCALED test distributions
    test_preds_mlp  = mlp_model.predict(X_test_scaled)
    test_preds_knn  = knn_model.predict(X_test_scaled)
    
    res_xgb  = y_test - test_preds_xgb
    res_lgbm = y_test - test_preds_lgbm
    res_cat  = y_test - test_preds_cat
    res_mlp  = y_test - test_preds_mlp
    res_knn  = y_test - test_preds_knn
    
    print(f"\n[AdvancedTrainer] Residual Pearson Correlations (XGB Baseline vs Rest):")
    print(f"  XGB vs LGBM : {np.corrcoef(res_xgb, res_lgbm)[0, 1]:.4f}")
    print(f"  XGB vs CAT  : {np.corrcoef(res_xgb, res_cat)[0, 1]:.4f}")
    print(f"  XGB vs MLP  : {np.corrcoef(res_xgb, res_mlp)[0, 1]:.4f}  (Diverse Target!)")
    print(f"  XGB vs KNN  : {np.corrcoef(res_xgb, res_knn)[0, 1]:.4f}  (Diverse Target!)")

    test_features = pd.DataFrame({
        "xgb": test_preds_xgb,
        "lgbm": test_preds_lgbm,
        "cat": test_preds_cat,
        "mlp": test_preds_mlp,
        "knn": test_preds_knn
    })
    y_pred = np.clip(meta_model.predict(test_features), 0.0, 10.0)

    mae  = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2   = r2_score(y_test, y_pred)
    w_mae = weighted_mae(y_test, y_pred, w_test)

    pred_sev = [score_to_severity(s) for s in y_pred]
    true_sev = [score_to_severity(s) for s in y_test]

    print(f"\n{'='*50}")
    print(f"  MAE          : {mae:.4f}")
    print(f"  Weighted MAE : {w_mae:.4f}")
    print(f"  RMSE         : {rmse:.4f}")
    print(f"  R²           : {r2:.4f}")
    print(f"{'='*50}")
    print("\n[AdvancedTrainer] Severity Classification Report:")
    print(classification_report(true_sev, pred_sev, zero_division=0))

    gain_dict = xgb_model.get_booster().get_score(importance_type="gain")
    importance = pd.DataFrame({
        "feature":    selected_features,
        "importance": xgb_model.feature_importances_,
        "gain":       [gain_dict.get(f, 0.0) for f in selected_features],
    }).sort_values("importance", ascending=False)

    return {
        "models": {
            "xgb":  xgb_model,
            "lgbm": lgbm_model,
            "cat":  cat_model,
            "mlp":  mlp_model,
            "knn":  knn_model,
            "meta": meta_model,
        },
        "nlp_model":        nlp_model,
        "scaler":           scaler_full,
        "feature_cols":     selected_features,
        "selector":         selector,
        "pca":              pca_fitted,
        "X_train": X_train_sel, "X_test": X_test_sel,
        "y_train": y_train,     "y_test": y_test,
        "y_pred":  y_pred,
        "metrics": {
            "mae": mae, "weighted_mae": w_mae,
            "rmse": rmse, "r2": r2,
        },
        "feature_importance":      importance,
        "classification_report":   classification_report(
            true_sev, pred_sev, zero_division=0, output_dict=True
        ),
        "pred_sev": pred_sev,
        "true_sev": true_sev,
    }


def save_artifacts(results: dict) -> None:
    """Persist all artifacts needed for inference."""
    Path(MODEL_PATH).parent.mkdir(parents=True, exist_ok=True)

    # Save all models and nlp_model name as a dict
    joblib.dump(
        {
            "models": results["models"],
            "nlp_model": results.get("nlp_model", "cisco-ai/SecureBERT2.0-biencoder")
        },
        MODEL_PATH,
    )
    joblib.dump(results["feature_cols"], FEATURES_PATH)
    joblib.dump(results["selector"],     SELECTOR_PATH)
    joblib.dump(results["scaler"],       SCALER_PATH)

    if results["pca"] is not None:
        joblib.dump(results["pca"], PCA_PATH)
        print(f"[AdvancedTrainer] PCA saved         → {PCA_PATH}")

    print(f"[AdvancedTrainer] Models saved      → {MODEL_PATH}")
    print(f"[AdvancedTrainer] Features saved    → {FEATURES_PATH}")
    print(f"[AdvancedTrainer] Scaler saved      → {SCALER_PATH}")
    print(f"[AdvancedTrainer] Selector saved    → {SELECTOR_PATH}")


def load_artifacts():
    """Load all inference artifacts. Returns (models_dict, feature_cols, selector, pca|None, nlp_model, scaler)."""
    bundle   = joblib.load(MODEL_PATH)
    features = joblib.load(FEATURES_PATH)
    selector = joblib.load(SELECTOR_PATH)
    scaler   = joblib.load(SCALER_PATH)
    pca      = joblib.load(PCA_PATH) if PCA_PATH.exists() else None
    
    # Retrieve nlp_model or fallback safely
    nlp_model = bundle.get("nlp_model", "cisco-ai/SecureBERT2.0-biencoder")
    return bundle["models"], features, selector, pca, nlp_model, scaler


def predict(descriptions: list[str],
            structured_df: pd.DataFrame,
            nlp_model_override: str = None) -> np.ndarray:
    """
    Inference helper — mirrors the exact preprocessing pipeline used during training.
    """
    models, feature_cols, selector, pca, trained_nlp_model, scaler = load_artifacts()
    
    nlp_model = nlp_model_override if nlp_model_override else trained_nlp_model

    # 1. Align structured features (ensure all training cols exist, even if 0)
    from ai.config import FEATURE_COLS as ALL_STRUCTURED
    X_num = pd.DataFrame(index=structured_df.index)
    for col in ALL_STRUCTURED:
        X_num[col] = structured_df[col] if col in structured_df.columns else 0.0
    X_num = X_num.fillna(0)

    # 2. Handle Text / PCA
    if pca is not None:
        encoder    = SentenceTransformer(nlp_model)
        descriptions = [str(d) for d in descriptions]
        embeddings = encode_chunked(encoder, descriptions)
        emb_r      = pca.transform(embeddings)
        emb_cols   = [f"pca_emb_{i}" for i in range(emb_r.shape[1])]
    else:
        emb_r = None

    # 3. Apply Selector (Must happen on full structured set)
    X_sel_num = pd.DataFrame(
        selector.transform(X_num), 
        columns=[c for c in feature_cols if not c.startswith('pca_emb')],
        index=X_num.index
    )

    # 4. Combine with PCA embeddings if they exist
    if emb_r is not None:
        X_sel = pd.concat([X_sel_num, pd.DataFrame(emb_r, columns=emb_cols, index=X_num.index)], axis=1)
    else:
        X_sel = X_sel_num
    # 5. Reorder columns just in case to match feature_cols exactly
    X_sel = X_sel[feature_cols]

    # 6. Pre-scale exactly how training happened!
    X_sel_scaled = pd.DataFrame(scaler.transform(X_sel), index=X_sel.index, columns=X_sel.columns)

    base_preds = pd.DataFrame({
        "xgb": models["xgb"].predict(X_sel),
        "lgbm": models["lgbm"].predict(X_sel),
        "cat": models["cat"].predict(X_sel),
        "mlp": models["mlp"].predict(X_sel_scaled),
        "knn": models["knn"].predict(X_sel_scaled)
    }, index=X_sel.index)
    preds = models["meta"].predict(base_preds)
    
    return np.clip(preds, 0.0, 10.0)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Advanced AI Risk Model Trainer")
    parser.add_argument("--source",    choices=["cvefixes", "defectdojo"], default="cvefixes")
    parser.add_argument("--db",        type=str, default="data/CVEfixes.db",
                        help="Path to CVEfixes SQLite DB (--source cvefixes only)")
    parser.add_argument("--nlp-model", type=str, default="cisco-ai/SecureBERT2.0-biencoder")
    parser.add_argument("--tune",      action="store_true",
                        help="Run Optuna hyperparameter search")
    parser.add_argument("--n-trials",  type=int, default=50,
                        help="Optuna trials per model")
    parser.add_argument("--timeout",   type=int, default=600,
                        help="Max seconds per Optuna study")
    parser.add_argument("--pca-components", type=int, default=64,
                        help="Embedding dimensions after PCA")
    args = parser.parse_args()

    if args.source == "cvefixes":
        if not args.db:
            raise ValueError("--db required when --source=cvefixes")
        df = load_cvefixes(args.db)
    else:
        df = load_defectdojo(str(DEFECTDOJO_CSV))

    summarize(df, args.source.upper())

    results = train_advanced(
        df,
        nlp_model      = args.nlp_model,
        tune           = args.tune,
        n_trials       = args.n_trials,
        tune_timeout   = args.timeout,
        pca_components = args.pca_components,
    )
    save_artifacts(results)