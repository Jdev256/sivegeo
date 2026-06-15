# 🧭 Grafo de Execução do Pipeline de Dados (Macro DATAFLOW)

Este documento descreve a topologia macro do pipeline de dados do **SIVEGEO**. O fluxo opera como um Grafo Direcionado Acíclico (DAG) baseado em **Lazy Evaluation** (Avaliação Preguiçosa) via Polars, onde o processamento real e a alocação de memória física ocorrem apenas no nó terminal de computação.

## DATAFLOW
LOAD
  ↓
CLEAN
  ↓
PARSE
  ↓
TRANSFORM
  ↓
FILTER
  ↓
SELECT
  ↓
AGGREGATE
  ↓
JOIN COM IBGE
  ↓
JOIN SINAN ↔ SIM
  ↓
KPIs / TAXAS / MODELAGEM


[FTP DATASUS]                [FTP DATASUS]                [APIs IBGE]
         │                            │                           │
(A) Stream SINAN             (B) Stream SIM              (C) Stream População
         │                            │                           │
  ┌──────┴──────┐              ┌──────┴──────┐             ┌──────┴──────┐
  │   CLEAN     │              │   CLEAN     │             │   CLEAN     │
  │ (Upper Cols)│              │ (Upper Cols)│             │ (Upper Cols)│
  └──────┬──────┘              └──────┬──────┘             └──────┬──────┘
         │                            │                           │
  ┌──────┴──────┐              ┌──────┴──────┐             ┌──────┴──────┐
  │   PARSE     │              │   PARSE     │             │   PARSE     │
  │(Dates/IDs/UF│              │(Causa/Idade)│             │(Cast Pop/UF)│
  └──────┬──────┘              └──────┬──────┘             └──────┬──────┘
         │                            │                           │
         ▼                            ▼                           ▼
  [PREDICATE PUSHDOWN]         [PREDICATE PUSHDOWN]        [PREDICATE PUSHDOWN]
(UI Filters: UF/Ano/Sexo)    (UI Filters: UF/Ano/Sexo)    (UI Filters: UF/Ano)
         │                            │                           │
         ▼                            ▼                           ▼
  ┌─────────────┐              ┌─────────────┐                    │
  │  AGGREGATE  │              │  AGGREGATE  │                    │
  │(TOTAL_CASES)│              │(TOTAL_DEATHS│                    │
  └──────┬──────┘              └──────┬──────┘                    │
         │                            │                           │
         └─────────────┬──────────────┘                           │
                       │                                          │
                       ▼ (Left Lazy Join)                         │
             [SINAN ↔ SIM por Geo-Keys]                           │
                       │                                          │
                       └──────────────────────┬───────────────────┘
                                              │
                                              ▼ (Full Lazy Join)
                                  [Unificação com Base IBGE]
                                              │
                                              ▼
                                  ┌───────────────────────┐
                                  │ MÓDULO KPIs VETORIAIS │
                                  │ (Incidência, Mort.)   │
                                  └──────────┬────────────┘
                                              │
                                              ▼ Nó Terminal
                                         [.collect()]
                                              │ (DataFrame em Memória)
                                   ┌──────────┴──────────┐
                                   ▼                     ▼
                             [Streamlit UI]       [Prophet Model]
                            (Renderização)       (Time Series Forecast)


## 🔍 Descrição Comportamental dos Nós

1. **Camada de Origem e Extração (A, B, C):** O `PySUS` e o `geobr` realizam o I/O dos arquivos brutos (`.dbc`/`.parquet`/`.shp`). Eles entram no motor do Polars como ponteiros de arquivos, instanciando `LazyFrames`. Nenhum dado é carregado na RAM aqui.
2. **Transformações Estritas (Clean & Parse):** Padronização de strings e parsing de tipos (ex: conversão de data de string para `Date`, e fatiamento vetorial de códigos de municípios para compatibilização).
3. **Otimização Crítica (Predicate Pushdown):** Os filtros selecionados pelo usuário na UI do Streamlit (Ano, Sexo, Faixa Etária, UF) são injetados diretamente na base do grafo. O Polars filtra as linhas *antes* de realizar qualquer agregação ou join, reduzindo drasticamente o volume de dados trafegados.
4. **Agregações Intermediárias:** Redução volumétrica das tabelas de microdados a nível de granularidade espaço-temporal (`ANO`, `UF`, `COD_MUN`, `SEXO`). O volume cai de milhões de registros para poucas linhas agrupadas.
5. **Junções Preguiçosas (Lazy Joins):** Fusão das tabelas utilizando chaves geo-temporais homogêneas (`COD_MUN` + `ANO`).
6. **Nó de Resolução Terminal (`.collect()`):** O gatilho que força o Polars a otimizar a query, disparar as threads em paralelo na CPU, processar os dados in-memory e descarregar o resultado final como um `pl.DataFrame` limpo para consumo imediato da UI e das engines estatísticas (Prophet).