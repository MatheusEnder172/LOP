"""Módulo do Orquestrador Híbrido Serial (DDM -> PBM) em Batelada.

Implementa a classe `SerialHybridModel`, responsável por acoplar o modelo cinético orientado
por dados (Data-Driven Model - DDM, por padrão o Random Forest campeão da Etapa 3.2)
ao modelo fenomenológico de Balanço Populacional em Batelada (`BatchPBMSolver`).

Princípios Físico-Químicos e Garantias:
1. Conservação Rigorosa de Massa:
   A taxa de encolhimento interfacial v(t) = dD/dt é estritamente não-positiva (v <= 0),
   garantindo que a conversão mássica de zinco X_Zn(t) pertença estritamente ao intervalo [0, 1]
   e que a concentração de ácido residual C_Af(t) seja estritamente não-negativa (C_Af >= 0).
2. Interoperabilidade Modular:
   Suporte transparente a qualquer modelo da Etapa 3.2 (Random Forest, MLP, XGBoost, SVR).
3. Resolução Integrada:
   Integração cumulativa da retração diametral delta(t) e deformação da distribuição
   granulométrica inicial Rosin-Rammler-Bennet (RRB).

Referências:
- Herbst, J. A. (1979). Rate Processes of Extractive Metallurgy.
- Bortot Coelho, F. E. (2017). Dissertação de Mestrado, PPGEM/UFMG.
- von Stosch, M. et al. (2014). Hybrid modeling in biochemical engineering.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
import torch

# Definição e importação de módulos do projeto
CURRENT_DIR = Path(__file__).resolve().parent
SRC_DIR = CURRENT_DIR.parent
CODIGO_DIR = SRC_DIR.parent
BASE_DIR = CODIGO_DIR.parent

# Inclusão de subetapas no sys.path para carregamento de modelos serializados
ETAPA_3_2_DIR = CODIGO_DIR / "etapas" / "etapa_3_2"
if not ETAPA_3_2_DIR.exists():
    ETAPA_3_2_DIR = CODIGO_DIR / "etapas" / "etapa_3_2_modelos_blackbox"

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

from src.physics.pbm_batch import BatchPBMSolver
from modelo_mlp import KineticsMLP
from modelo_rf import KineticsRandomForest
from modelo_svr import KineticsSVR
from modelo_xgb import KineticsXGBoost


class SerialHybridModel:
    """Orquestrador do Modelo Híbrido Serial (DDM -> PBM) em Batelada.

    Acopla um regressor supervisionado |v(t)| = f_ML(T, CA0, eta, t) ao resolvedor
    de Balanço Populacional BatchPBMSolver para reconstituir a cinética de dissolução.

    Attributes:
        model_type: Tipo do regressor utilizado ('random_forest', 'mlp', 'xgboost', 'svr').
        model: Instância do modelo de machine learning carregado.
        solver: Instância de BatchPBMSolver para integração populacional e estequiométrica.
        scaler_X: Scaler de features (necessário para MLP).
        model_name: Nome legível do modelo selecionado.
    """

    def __init__(
        self,
        ddm_model: Optional[Any] = None,
        model_type: str = "champion",
        solver: Optional[BatchPBMSolver] = None,
        scaler_X: Optional[Any] = None,
        models_dir: Optional[Union[str, Path]] = None,
    ) -> None:
        """Inicializa o modelo híbrido serial.

        Args:
            ddm_model: Instância pré-carregada do regressor (opcional).
            model_type: Tipo de modelo ('champion', 'random_forest', 'mlp', 'xgboost', 'svr').
            solver: Instância de BatchPBMSolver. Se None, instancia automaticamente.
            scaler_X: StandardScaler de features para modelos que requerem normalização.
            models_dir: Diretório raiz onde os modelos salvos estão localizados.
        """
        self.models_dir = Path(models_dir) if models_dir else CODIGO_DIR / "outputs" / "models_saved"
        self.solver = solver if solver is not None else BatchPBMSolver()
        self.scaler_X = scaler_X

        if ddm_model is not None:
            self.model = ddm_model
            self.model_type = model_type if model_type != "champion" else self._detect_model_type(ddm_model)
            self.model_name = type(ddm_model).__name__
        else:
            self.model, self.model_type, self.model_name = self._load_model_by_type(model_type)

        # Se for MLP e o scaler não foi passado, tenta carregar o scaler padrão
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
        t_lower = model_type.lower()

        if t_lower == "champion":
            info_file = self.models_dir / "modelo_campeao_info.json"
            if not info_file.exists():
                raise FileNotFoundError(f"Arquivo de metadados do campeão não encontrado: {info_file}")

            with open(info_file, "r", encoding="utf-8") as f:
                info = json.load(f)

            nome_campeao = info.get("modelo_campeao", "Random Forest")
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

        elif t_lower == "mlp":
            ckpt_path = self.models_dir / "mlp" / "mlp_kinetics_v1.pt"
            return self._load_mlp(ckpt_path), "mlp", "KineticsMLP (PyTorch)"

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
        """Carrega e instancia a rede neural MLP em PyTorch."""
        config_path = ckpt_path.parent / "mlp_config.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            hidden_dims = cfg.get("hidden_dims", [128, 64, 32])
        else:
            hidden_dims = [128, 64, 32]

        mlp = KineticsMLP(
            input_dim=4,
            hidden_dims=hidden_dims,
            dropout_rate=0.0,
            use_layer_norm=True,
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
        """Prediz a taxa de retração interfacial |v(t)| para condições operacionais fixas.

        Args:
            T: Temperatura reacional (°C). Padrão: 40,0 °C.
            ca0: Concentração inicial de ácido livre (mol/L).
            eta: Razão molar estequiométrica H2SO4/ZnO (-).
            t_eval: Vetor de tempos de reação (min). Se None, usa malha fina [0, 15 min] (61 nós).

        Returns:
            Vetor float64 de taxas de retração interfacial |v(t)| estritamente >= 0 (µm/min).
        """
        if t_eval is None:
            t_arr = np.linspace(0.0, 15.0, 61, dtype=np.float64)
        else:
            t_arr = np.asarray(t_eval, dtype=np.float64)

        if ca0 <= 0.0:
            raise ValueError(f"CA0 deve ser estritamente positivo, recebido: {ca0}")
        if eta <= 0.0:
            raise ValueError(f"eta deve ser estritamente positivo, recebido: {eta}")

        n_pts = len(t_arr)
        # Matriz de features: [T, CA0, eta, t]
        X_raw = np.column_stack([
            np.full(n_pts, float(T), dtype=np.float64),
            np.full(n_pts, float(ca0), dtype=np.float64),
            np.full(n_pts, float(eta), dtype=np.float64),
            t_arr,
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

        # Projeção inegociável de não-negatividade (conservação de massa)
        abs_v = np.maximum(0.0, np.asarray(preds, dtype=np.float64))
        return abs_v

    def simulate(
        self,
        T: float = 40.0,
        ca0: float = 0.50,
        eta: float = 1.0,
        t_eval: Optional[Union[List[float], np.ndarray]] = None,
    ) -> Dict[str, Any]:
        """Simula a dinâmica de lixiviação acoplando o DDM ao Balanço Populacional em Batelada.

        Args:
            T: Temperatura operacional (°C).
            ca0: Concentração inicial de ácido livre (mol/L).
            eta: Razão molar estequiométrica H2SO4/ZnO (-).
            t_eval: Vetor de tempos de reação (min). Se None, usa malha fina padrão.

        Returns:
            Dicionário com séries temporais e variáveis físicas calculadas:
                - 't': Vetor de tempos (min)
                - 'delta': Retração diametral acumulada (µm)
                - 'XZn': Conversão mássica de zinco X_Zn(t) ∈ [0, 1] (-)
                - 'CAf': Concentração de ácido livre residual C_Af(t) >= 0 (mol/L)
                - 'abs_v': Módulo da taxa interfacial |v(t)| >= 0 (µm/min)
                - 'v': Taxa de retração diametral v(t) = -|v| <= 0 (µm/min)
                - 'T': Temperatura (°C)
                - 'CA0': Concentração inicial (mol/L)
                - 'eta': Razão molar (-)
                - 'model_type': Identificador do modelo DDM utilizado
                - 'model_name': Nome legível do modelo
        """
        if t_eval is None:
            t_arr = np.linspace(0.0, 15.0, 61, dtype=np.float64)
        else:
            t_arr = np.asarray(t_eval, dtype=np.float64)

        if not np.all(np.diff(t_arr) >= 0):
            raise ValueError("O vetor t_eval deve ser monotonicamente crescente.")

        # 1. Construção de malha interna fina para integração precisa do pulso inicial
        # Evita superestimação por discretização trapezoidal em malhas temporais esparsas
        if len(t_arr) < 200 or np.max(np.diff(t_arr)) > 0.05:
            n_internal = max(500, len(t_arr))
            t_internal = np.unique(
                np.concatenate([t_arr, np.linspace(float(t_arr[0]), float(t_arr[-1]), n_internal)])
            )
            is_subsampled = True
        else:
            t_internal = t_arr
            is_subsampled = False

        # 2. Predição da taxa interfacial |v(t)| via DDM na malha de integração
        abs_v_internal = self.predict_rate(T=T, ca0=ca0, eta=eta, t_eval=t_internal)
        v_profile_internal = -abs_v_internal

        # 3. Resolução do Balanço Populacional pelo método das características
        pbm_res = self.solver.simulate_with_v_profile(t_eval=t_internal, v_profile=v_profile_internal)
        delta_internal = pbm_res["delta"].copy()
        
        # Limite físico estequiométrico rigoroso: X_Zn <= min(1.0, eta)
        max_xzn = min(1.0, float(eta))
        xzn_raw = np.maximum.accumulate(pbm_res["XZn"])
        xzn_internal = np.clip(xzn_raw, 0.0, max_xzn)
        
        # Se a conversão atingir o teto estequiométrico (ácido esgotado), congela delta e zera v
        idx_exhaust = np.where(xzn_raw >= max_xzn - 1e-7)[0]
        if len(idx_exhaust) > 0 and max_xzn < 1.0:
            first_exhaust = idx_exhaust[0]
            delta_internal[first_exhaust:] = delta_internal[first_exhaust]
            abs_v_internal[first_exhaust:] = 0.0

        caf_internal = np.maximum(0.0, ca0 * (1.0 - (xzn_internal / eta)))

        if is_subsampled:
            # Reamostragem exata nos pontos solicitados em t_arr
            delta_final = np.interp(t_arr, t_internal, delta_internal)
            xzn_final = np.interp(t_arr, t_internal, xzn_internal)
            caf_final = np.interp(t_arr, t_internal, caf_internal)
            abs_v_final = np.interp(t_arr, t_internal, abs_v_internal)
            v_final = -abs_v_final
        else:
            delta_final = delta_internal
            xzn_final = xzn_internal
            caf_final = caf_internal
            abs_v_final = abs_v_internal
            v_final = v_profile_internal

        return {
            "t": t_arr,
            "delta": delta_final,
            "XZn": xzn_final,
            "CAf": caf_final,
            "abs_v": abs_v_final,
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

        Args:
            ensaio_id: Número do ensaio (1 a 16).
            t_eval: Vetor de tempos de avaliação. Se None e use_experimental_timepoints_only=False,
                    utiliza malha fina de 61 nós.
            use_experimental_timepoints_only: Se True, simula estritamente nos 8 pontos experimentais.

        Returns:
            Dicionário com a simulação do ensaio e medições experimentais reais correspondentes.
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
        T = 40.0  # Temperatura constante de bancada

        sub_series = df_series[df_series["ensaio"] == ensaio_id].sort_values("t_min")
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

        # Se a malha incluir os pontos experimentais exatos, calcula resíduos pontuais
        if use_experimental_timepoints_only:
            sim_res["residuos_XZn"] = xzn_exp - sim_res["XZn"]

        return sim_res

    def simulate_batch(
        self,
        ensaios_list: Optional[List[int]] = None,
        use_experimental_timepoints_only: bool = True,
    ) -> pd.DataFrame:
        """Simula uma lista de ensaios gerando um DataFrame consolidado no formato tidy long.

        Args:
            ensaios_list: Lista de identificadores de ensaios (padrão: todos os 16 ensaios).
            use_experimental_timepoints_only: Se True, simula nos instantes experimentais reais.

        Returns:
            DataFrame com predições tabuladas para cada ensaio e ponto de tempo.
        """
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
