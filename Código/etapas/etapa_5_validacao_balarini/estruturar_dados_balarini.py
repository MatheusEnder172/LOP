"""Módulo de Estruturação e Padronização dos Dados Cinéticos de Júlio Cezar Balarini (2009/2025).

Extrai e valida os 176 pontos experimentais de lixiviação ácida de calcina de zinco
a partir da planilha consolidada do projeto:
'C:/us trem/Doc/UFMG/9/Lop/Artigos base/Dataset_Lixiviacao_Zinco_Modelagem_Hibrida.xlsx'

Exporta os dados em formato tabular padronizado (tidy CSV) para:
'Base de dados/processed/balarini_2009_cinetica_bancada.csv'

Referências:
- Balarini, J. C. (2009). Tese de Doutorado, PPGEM/UFMG.
- Balarini, J. C. et al. (2025). Revista Observatorio de la Economía Latinoamericana.
"""

from pathlib import Path
import pandas as pd
import numpy as np


def extrair_e_padronizar_dados_balarini(
    excel_path: Path,
    output_csv_path: Path,
) -> pd.DataFrame:
    """Extrai e valida os dados de Balarini (2009) das abas da planilha Excel.

    Args:
        excel_path: Caminho completo para o arquivo Excel consolidado.
        output_csv_path: Caminho onde o arquivo CSV processado será salvo.

    Returns:
        pd.DataFrame com os 176 pontos experimentais padronizados.
    """
    if not excel_path.exists():
        raise FileNotFoundError(f"Arquivo Excel não encontrado em: {excel_path}")

    # Leitura da Aba 3 (Cinéticas de Bancada com detalhes de mesh e taxas)
    df3 = pd.read_excel(excel_path, sheet_name="3_Cineticas_Bancada_Balarini", header=3)
    
    # Padronização dos nomes de colunas da Aba 3
    # Ponto_ID, Série_Teste, Temperatura (°C), Malha Tyler (#), dp Médio (µm), Agitação (rpm), CA0 (g/L H2SO4), Tempo t (min), Conversão Zn (XZn)
    col_map_3 = {
        df3.columns[0]: "ponto_id",
        df3.columns[1]: "serie_teste",
        df3.columns[2]: "temperatura_c",
        df3.columns[3]: "malha_tyler",
        df3.columns[4]: "dp_medio_um",
        df3.columns[5]: "agitacao_rpm",
        df3.columns[6]: "ca0_g_l",
        df3.columns[7]: "tempo_min",
        df3.columns[8]: "conversao_zn_exp",
        df3.columns[9]: "termo_quimico_scm",
        df3.columns[10]: "termo_difusivo_scm",
    }
    df3 = df3.rename(columns=col_map_3)

    # Conversão de unidades físico-químicas
    # CA0: 4.0 g/L H2SO4 -> mol/L (M_H2SO4 = 98.079 g/mol)
    molar_mass_h2so4 = 98.079
    df3["ca0_mol_l"] = (df3["ca0_g_l"] / molar_mass_h2so4).round(4)
    
    # Condições operacionais do reator de bancada de Balarini
    df3["volume_l"] = 1.0
    df3["massa_solido_g"] = 5.0
    df3["razao_molar_eta"] = 1.5  # Razão molar estequiométrica H2SO4 / ZnO

    # Categorização do tipo de ensaio
    def classificar_ensaio(serie: str) -> str:
        if "Temp" in serie:
            return "efeito_temperatura"
        elif "Granulo" in serie:
            return "efeito_granulometria"
        elif "Agitacao" in serie:
            return "efeito_agitacao"
        return "outro"

    df3["categoria_efeito"] = df3["serie_teste"].apply(classificar_ensaio)

    # Verificação de integridade e consistência física
    assert len(df3) == 176, f"Esperado 176 pontos experimentais, obtido {len(df3)}"
    assert (df3["conversao_zn_exp"] >= 0.0).all(), "Conversão negativa detectada!"
    assert (df3["conversao_zn_exp"] <= 1.0).all(), "Conversão > 1.0 detectada!"
    assert (df3["tempo_min"] >= 0.0).all(), "Tempo negativo detectado!"

    # Ordenação canônica
    df3 = df3.sort_values(by=["serie_teste", "tempo_min"]).reset_index(drop=True)

    # Criação do diretório de destino se necessário
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    df3.to_csv(output_csv_path, index=False, float_format="%.5f")
    print(f"[OK] Dados de Balarini estruturados com sucesso: {output_csv_path} ({len(df3)} pontos, 16 séries).")
    
    return df3


if __name__ == "__main__":
    current_file = Path(__file__).resolve()
    codigo_v3_dir = current_file.parents[3]  # Codigo_v3
    lop_dir = codigo_v3_dir.parent           # Lop
    excel = lop_dir / "Artigos base" / "Dataset_Lixiviacao_Zinco_Modelagem_Hibrida.xlsx"
    out_csv = codigo_v3_dir / "Base de dados" / "processed" / "balarini_2009_cinetica_bancada.csv"
    extrair_e_padronizar_dados_balarini(excel, out_csv)
