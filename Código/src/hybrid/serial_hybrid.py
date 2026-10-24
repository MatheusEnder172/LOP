"""Módulo do Orquestrador Híbrido Serial (DDM -> PBM) em Batelada (t > 0, 3 Inputs, RRB ÷ D³).

Implementa a classe `SerialHybridModel`, responsável por acoplar o modelo cinético orientado
por dados (Data-Driven Model - DDM, por padrão o MLP campeão da Etapa 3.2)
ao modelo fenomenológico de Balanço Populacional em Batelada (`BatchPBMSolver` com RRB ÷ D³).

Princípios Físico-Químicos e Garantias:
1. Condição Inicial Física Hardcodada em t = 0:
   Em t = 0, a conversão é fisicamente conhecida e exata:
   X_Zn(0) = 0,0, δ(0) = 0,0 µm, C_Af(0) = C_A0.
   O ponto t = 0 é excluído dos conjuntos de treino/validação/teste e métricas estatísticas,
   e o modelo Black-Box opera estritamente sobre t > 0 com 3 variáveis cinéticas ativas [C_A0, η, t].
2. Conservação Rigorosa de Massa:
   A taxa de encolhimento interfacial v(t) = dD/dt é estritamente não-positiva (v <= 0),
   garantindo que a conversão mássica de zinco X_Zn(t) pertença estritamente ao intervalo [0, 1]
   e que a concentração de ácido residual C_Af(t) seja estritamente não-negativa (C_Af >= 0).
3. Interoperabilidade Modular:
   Suporte transparente a qualquer modelo da Etapa 3.2 (MLP Campeão, Random Forest, XGBoost, SVR).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
import torch

# Definição e importação de módulos do projeto
CURRENT_DIR = Path(__file__).resolve().parent
SRC_DIR = CURRENT_DIR.parent
CODIGO_DIR = SRC_DIR.parent
BASE_DIR = CODIGO_DIR.parent

ETAPA_3_2_DIR = CODIGO_DIR / "etapas" / "etapa_3_2"
for sub in [
    "subetapa_3_2_1_mlp",
    "subetapa_3_2_2_random_forest",
    "subetapa_3_2_3_svr",
    "subetapa_3_2_4_xgboost",
    "subetapa_3_2_5_comparacao_campeao",
]:
    p = str(ETAPA_3_2_DIR / sub)
    if p not in sys.path:
        sys.path.insert(0, p)

if str(CODIGO_DIR) not in sys.path:
    sys.path.insert(0, str(CODIGO_DIR))

from src.physics.pbm_batch import BatchPBMSolver
from modelo_mlp import KineticsMLP
from modelo_rf import KineticsRandomForest
from modelo_svr import KineticsSVR
from modelo_xgb import KineticsXGBoost


class SerialHybridModel:
    """Orquestrador do Modelo Híbrido Serial (DDM -> PBM) em Batelada (t > 0, 3 Inputs).

    Acopla um regressor supervisionado |v(t)| = f_ML(CA0, eta, t) (t > 0) ao resolvedor
    de Balanço Populacional BatchPBMSolver (RRB ÷ D³, α = 0) com condição inicial hardcodada em t = 0.
    """

    def __init__(
        self,
        ddm_model: Optional[Any] = None,
        model_type: str = "champion",
        solver: Optional[BatchPBMSolver] = None,
        scaler_X: Optional[Any] = None,
        models_dir: Optional[Union[str, Path]] = None,
    ) -> None:
        self.models_dir = Path(models_dir) if models_dir else CODIGO_DIR / "outputs" / "models_saved"
        self.solver = solver if solver is not None else BatchPBMSolver()
        self.scaler_X = scaler_X

        if ddm_model is not None:
            self.model = ddm_model
            self.model_type = model_type if model_type != "champion" else self._detect_model_type(ddm_model)
            self.model_name = type(ddm_model).__name__
        else:
            self.model, self.model_type, self.model_name = self._load_model_by_type(model_type)

        if self.model_type == "mlp" and self.scaler_X is None:
            scaler_path = BASE_DIR / "Base de dados" / "processed" / "splits" / "scalers.joblib"
            if scaler_path.exists():
                sc_dict = joblib.load(scaler_path)
                self.scaler_X = sc_dict.get("scaler_X")

    def _detect_model_type(self, model: Any) -> str:
        """Identifica a família do modelo a partir de sua classe."""
        name = type(model).__name__
        if "RandomForest" in name:
            return "random_forest"
        elif "MLP" in name:
            return "mlp"
        elif "XGB" in name:
            return "xgboost"
        elif "SVR" in name:
            return "svr"
        return "custom"

    def _load_model_by_type(self, model_type: str) -> Tuple[Any, str, str]:
        """Carrega o checkpoint correspondente ao tipo requisitado."""
        t_lower = model_type.strip().lower()

        if t_lower in ("champion", "campeao"):
            info_file = self.models_dir / "modelo_campeao_info.json"
            if not info_file.exists():
                raise FileNotFoundError(f"Arquivo de metadados do campeão não encontrado: {info_file}")

            with open(info_file, "r", encoding="utf-8") as f:
                info = json.load(f)

            nome_campeao = info.get("modelo_campeao", "MLP")
            ckpt_rel = info["arquivos_acoplamento_etapa_4"]["checkpoint_relativo"]
            ckpt_path = self.models_dir / ckpt_rel

            if "Random Forest" in nome_campeao:
                model = KineticsRandomForest.load(ckpt_path)
                return model, "random_forest", f"Campeão: {nome_campeao}"
            elif "MLP" in nome_campeao:
                return self._load_mlp(ckpt_path), "mlp", f"Campeão: {nome_campeao}"
            elif "XGBoost" in nome_campeao:
                model = KineticsXGBoost.load(ckpt_path)
                return model, "xgboost", f"Campeão: {nome_campeao}"
            elif "SVR" in nome_campeao:
                model = KineticsSVR.load(ckpt_path)
                return model, "svr", f"Campeão: {nome_campeao}"
            else:
                raise ValueError(f"Modelo campeão não reconhecido: {nome_campeao}")

        elif t_lower in ("random_forest", "rf"):
            ckpt_path = self.models_dir / "random_forest" / "rf_kinetics_v1.joblib"
            model = KineticsRandomForest.load(ckpt_path)
            return model, "random_forest", "Random Forest Regressor"

        elif t_lower in ("mlp", "neural"):
            ckpt_path = self.models_dir / "mlp" / "mlp_kinetics_v1.pt"
            return self._load_mlp(ckpt_path), "mlp", "KineticsMLP (PyTorch C∞)"

        elif t_lower in ("xgboost", "xgb"):
            ckpt_path = self.models_dir / "xgboost" / "xgb_kinetics_v1.joblib"
            model = KineticsXGBoost.load(ckpt_path)
            return model, "xgboost", "XGBoost Regressor"

        elif t_lower == "svr":
            ckpt_path = self.models_dir / "svr" / "svr_kinetics_v1.joblib"
            model = KineticsSVR.load(ckpt_path)
            return model, "svr", "Support Vector Regression"

        else:
            raise ValueError(f"Tipo de modelo inválido: {model_type}. Opções: champion, random_forest, mlp, xgboost, svr")

    def _load_mlp(self, ckpt_path: Path) -> KineticsMLP:
        """Carrega e instancia a rede neural MLP em PyTorch com input_dim = 3."""
        config_path = ckpt_path.parent / "mlp_config.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            input_dim = int(cfg.get("input_dim", 3))
            hidden_dims = cfg.get("hidden_dims", [64, 32])
            use_ln = bool(cfg.get("use_layer_norm", True))
            activation = str(cfg.get("activation", "gelu"))
            use_res = bool(cfg.get("use_residual", False))
        else:
            input_dim = 3
            hidden_dims = [64, 32]
            use_ln = True
            activation = "gelu"
            use_res = False

        mlp = KineticsMLP(
            input_dim=input_dim,
            hidden_dims=hidden_dims,
            dropout_rate=0.0,
            use_layer_norm=use_ln,
            activation=activation,
            use_residual=use_res,
        )
        mlp.load_state_dict(torch.load(ckpt_path, weights_only=True))
        mlp.eval()
        return mlp

    def predict_rate(
        self,
        T: float = 40.0,
        ca0: float = 0.50,
        eta: float = 1.0,
        t_eval: Optional[Union[List[float], np.ndarray]] = None,
    ) -> np.ndarray:
        """Prediz a taxa de retração interfacial |v(t)| usando as 3 entradas ativas [CA0, eta, t > 0]."""
        if t_eval is None:
            t_arr = np.linspace(0.25, 15.0, 60, dtype=np.float64)
        else:
            t_arr = np.atleast_1d(np.asarray(t_eval, dtype=np.float64)).ravel()

        if ca0 <= 0.0:
            raise ValueError(f"CA0 deve ser estritamente positivo, recebido: {ca0}")
        if eta <= 0.0:
            raise ValueError(f"eta deve ser estritamente positivo, recebido: {eta}")

        # Garante avaliação estritamente no domínio positivo de treinamento (t >= 0.25 min)
        t_pos = np.maximum(t_arr, 0.25)
        n_pts = len(t_pos)

        # Matriz de 3 features ativas: [CA0_mol_L, razao_molar_eta, t_min]
        X_raw = np.column_stack([
            np.full(n_pts, float(ca0), dtype=np.float64),
            np.full(n_pts, float(eta), dtype=np.float64),
            t_pos,
        ])

        if self.model_type == "mlp":
            if self.scaler_X is None:
                raise RuntimeError("scaler_X não foi fornecido para inferência com o modelo MLP.")
            X_scaled = self.scaler_X.transform(X_raw)
            with torch.no_grad():
                x_ten = torch.tensor(X_scaled, dtype=torch.float32)
                preds_ten = self.model.forward(x_ten)
                preds = preds_ten.cpu().numpy().ravel()
        elif self.model_type in ("random_forest", "xgboost", "svr"):
            preds = self.model.predict(X_raw)
        else:
            preds = self.model.predict(X_raw)

        abs_v = np.maximum(0.0, np.asarray(preds, dtype=np.float64))
        return abs_v

    def simulate(
        self,
        T: float = 40.0,
        ca0: float = 0.50,
        eta: float = 1.0,
        t_eval: Optional[Union[List[float], np.ndarray]] = None,
    ) -> Dict[str, Any]:
        """Simula a dinâmica de lixiviação acoplando o DDM (t > 0) ao Balanço Populacional em Batelada.

        Condição inicial física hardcodada em t = 0:
            X_Zn(0) = 0.0, δ(0) = 0.0 µm, C_Af(0) = C_A0.
        """
        if t_eval is None:
            t_arr = np.linspace(0.0, 15.0, 61, dtype=np.float64)
        else:
            t_arr = np.asarray(t_eval, dtype=np.float64)

        if len(t_arr) > 1 and not np.all(np.diff(t_arr) >= 0):
            raise ValueError("O vetor t_eval deve ser monotonicamente crescente.")

        # 1. Malha canônica positiva consistente com a geração dos alvos na Etapa 2.1 (Δt = 0.25 min)
        t_max = float(max(np.max(t_arr) if len(t_arr) > 0 else 15.0, 15.0))
        n_canon = max(60, int(round(t_max / 0.25)))
        t_canon = np.linspace(0.25, t_max, n_canon, dtype=np.float64)

        # 2. Predição da taxa interfacial |v(t)| via DDM estritamente em t > 0
        abs_v_canon = self.predict_rate(T=T, ca0=ca0, eta=eta, t_eval=t_canon)

        # 3. Resolução do Balanço Populacional a partir de δ(0) = 0 hardcodado
        pbm_res = self.solver.simulate_with_v_profile(
            t_eval=t_canon,
            v_profile=-abs_v_canon,
        )

        # Concatenar condição inicial exata hardcodada em t = 0
        t_internal = np.concatenate([[0.0], t_canon])
        delta_internal = np.concatenate([[0.0], pbm_res["delta"].copy()])
        xzn_raw = np.concatenate([[0.0], pbm_res["XZn"].copy()])
        abs_v_internal = np.concatenate([[abs_v_canon[0]], abs_v_canon.copy()])

        # Limite físico estequiométrico rigoroso: X_Zn <= min(1.0, eta)
        max_xzn = min(1.0, float(eta))
        xzn_raw = np.maximum.accumulate(xzn_raw)
        xzn_internal = np.clip(xzn_raw, 0.0, max_xzn)

        idx_exhaust = np.where(xzn_raw >= max_xzn - 1e-7)[0]
        if len(idx_exhaust) > 0 and max_xzn < 1.0:
            first_exhaust = idx_exhaust[0]
            delta_internal[first_exhaust:] = delta_internal[first_exhaust]
            abs_v_internal[first_exhaust:] = 0.0

        caf_internal = np.maximum(0.0, ca0 * (1.0 - (xzn_internal / eta)))

        # Reamostragem nos pontos solicitados em t_arr e imposição estrita em t == 0
        delta_final = np.interp(np.maximum(0.0, t_arr), t_internal, delta_internal)
        xzn_final = np.interp(np.maximum(0.0, t_arr), t_internal, xzn_internal)
        caf_final = np.interp(np.maximum(0.0, t_arr), t_internal, caf_internal)
        abs_v_final = np.interp(np.maximum(0.0, t_arr), t_internal, abs_v_internal)

        # Hardcode absoluto para t <= 0
        mask_zero = t_arr <= 0.0
        delta_final[mask_zero] = 0.0
        xzn_final[mask_zero] = 0.0
        caf_final[mask_zero] = float(ca0)

        if len(t_arr) > 1:
            delta_final = np.maximum.accumulate(delta_final)
            xzn_final = np.clip(np.maximum.accumulate(xzn_final), 0.0, max_xzn)
            caf_final = np.maximum(0.0, ca0 * (1.0 - (xzn_final / eta)))

        v_final = -abs_v_final

        return {
            "t": t_arr,
            "t_min": t_arr,
            "delta": delta_final,
            "delta_um": delta_final,
            "XZn": xzn_final,
            "X_Zn": xzn_final,
            "CAf": caf_final,
            "C_Af": caf_final,
            "abs_v": abs_v_final,
            "abs_v_um_min": abs_v_final,
            "v": v_final,
            "T": float(T),
            "CA0": float(ca0),
            "eta": float(eta),
            "model_type": self.model_type,
            "model_name": self.model_name,
        }

    def simulate_experiment(
        self,
        ensaio_id: int,
        t_eval: Optional[Union[List[float], np.ndarray]] = None,
        use_experimental_timepoints_only: bool = False,
    ) -> Dict[str, Any]:
        """Simula diretamente um dos 16 ensaios de bancada de Bortot Coelho (2017).

        Os pontos experimentais avaliados (t_exp, XZn_exp) correspondem estritamente
        aos 7 instantes ativos t > 0 (excluindo o ponto trivial t = 0).
        """
        raw_meta = BASE_DIR / "Base de dados" / "raw" / "bancada_batelada_A1_1.csv"
        raw_series = BASE_DIR / "Base de dados" / "raw" / "cinetica_batelada_A1_4.csv"

        if not raw_meta.exists() or not raw_series.exists():
            raise FileNotFoundError("Bases brutas de bancada não encontradas em Base de dados/raw/.")

        df_meta = pd.read_csv(raw_meta)
        df_series = pd.read_csv(raw_series)

        match_meta = df_meta[df_meta["ensaio"] == ensaio_id]
        if match_meta.empty:
            raise ValueError(f"Ensaio {ensaio_id} não encontrado na base de dados de bancada.")

        ca0 = float(match_meta["CA0_mol_L"].iloc[0])
        eta = float(match_meta["razao_molar_eta"].iloc[0])
        T = 40.0

        # Filtragem estrita t > 0 nos pontos experimentais
        sub_series = df_series[(df_series["ensaio"] == ensaio_id) & (df_series["t_min"] > 0.0)].sort_values("t_min")
        t_exp = sub_series["t_min"].values
        xzn_exp = sub_series["XZn"].values

        if use_experimental_timepoints_only:
            t_grid = t_exp
        elif t_eval is not None:
            t_grid = np.asarray(t_eval, dtype=np.float64)
        else:
            t_grid = np.linspace(0.0, 15.0, 61, dtype=np.float64)

        sim_res = self.simulate(T=T, ca0=ca0, eta=eta, t_eval=t_grid)
        sim_res["ensaio"] = ensaio_id
        sim_res["t_exp"] = t_exp
        sim_res["XZn_exp"] = xzn_exp

        if use_experimental_timepoints_only:
            sim_res["residuos_XZn"] = xzn_exp - sim_res["XZn"]

        return sim_res

    def simulate_batch(
        self,
        ensaios_list: Optional[List[int]] = None,
        use_experimental_timepoints_only: bool = True,
    ) -> pd.DataFrame:
        """Simula uma lista de ensaios gerando um DataFrame consolidado (estritamente t > 0 quando experimental)."""
        if ensaios_list is None:
            ensaios_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]

        records: List[Dict[str, Any]] = []
        for ens in sorted(ensaios_list):
            res = self.simulate_experiment(
                ensaio_id=ens,
                use_experimental_timepoints_only=use_experimental_timepoints_only,
            )
            t_pts = res["t"]
            xzn_pts = res["XZn"]
            caf_pts = res["CAf"]
            v_pts = res["abs_v"]
            delta_pts = res["delta"]

            has_exp = len(t_pts) == len(res["t_exp"]) and np.allclose(t_pts, res["t_exp"])

            for idx in range(len(t_pts)):
                row = {
                    "ensaio": ens,
                    "t_min": t_pts[idx],
                    "XZn_pred": xzn_pts[idx],
                    "CAf_pred": caf_pts[idx],
                    "abs_v_pred": v_pts[idx],
                    "delta_pred": delta_pts[idx],
                    "CA0_mol_L": res["CA0"],
                    "razao_molar_eta": res["eta"],
                    "temperatura_C": res["T"],
                    "modelo": res["model_name"],
                }
                if has_exp:
                    row["XZn_exp"] = res["XZn_exp"][idx]
                    row["residuo_XZn"] = res["XZn_exp"][idx] - xzn_pts[idx]
                records.append(row)

        return pd.DataFrame(records)
