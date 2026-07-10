# Changelog

Todos os marcos relevantes do projeto serão documentados aqui.


---

# [1.0.2] - 2026-07-09
### Correctins
  - schema returns
  - joins 1:1 product cartesian to return

### Added
  - StdoutRedirector Real Time console log interface

### Views
- HeatMap change indicators to kpis

# [1.0.1] - 2026-06-20 / 2026-06-27

### Corrections
  - Erros de Sintaxe e Logica
  - Tratamento de retorno padrao com schema nulo contra falha de dados vazios

### Added
  - Teste de conexao HeathCheck antecipadamente
  - Caixa de logs de processamento e execucao
  - Consulta Geral - Recurso de Teste, analise e verificacao da base original
---

## [1.0.0] - 2026-06-10

### Added
 #### Core
  - Pipeline Lazy
  - Integraco SIM
  - Integracao SINAN
  - Processador de limpesa, parseamento, normalizacao e padronizacao.
  - Integração com `geobr`.
  - Integração com `geopandas`.

  #### Dimensao Analitica:
    ##### Indicadores
      - TOTAL_CASES
      - TOTAL_DEATHS
    ##### KPIS
      - Incidência
      - Mortalidade
      - Letalidade

 #### Vizualizacoes
  - previsão temporal com Prophet.
  - Radar para comparação entre agravos.
  - Heatmap para intensidade de casos.
  - Gauge Evolucao Hitorica