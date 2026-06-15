# 🛠️ Stack Tecnológica (Tech Stack) - SIVEGEO

Este documento especifica a infraestrutura de software, bibliotecas e ecossistema de execução que compõem o **SIVEGEO**. A escolha dos componentes baseia-se estritamente no paradigma **Stateless** e **In-Memory**, priorizando a eliminação de latência de I/O de banco de dados tradicional em favor de computação paralela baseada em vetores.

---

## 💻 Core Runtime & Mecanismo de Execução

* **Python 3.11+:** Runtime principal do sistema, aproveitando as melhorias de performance e tipagem estática avançada.
* **Polars (LazyFrames & Expressions):** O motor central de processamento. Substitui o Pandas tradicional e os bancos de dados relacionais (SQL). É utilizado no modo *Lazy Evaluation*, permitindo a otimização de consultas (*Predicate Pushdown*) e execução paralela em nível de CPU via RUST engine.

---

## 🧬 Engenharia de Dados & Extração Pública

* **PySUS:** Biblioteca especializada para comunicação e extração automatizada de microdados diretamente dos servidores FTP do DATASUS (SINAN e SIM) e download de estruturas demográficas.
* **GeoBR & GeoPandas:** Ferramentas de engenharia geoespacial utilizadas para baixar, manipular e cachear as malhas cartográficas dos municípios brasileiros (IBGE) para posterior acoplamento ao pipeline analítico.

---

## 📊 Modelagem Estatística & Inferência Temporal

* **Prophet (Meta):** Modelo aditivo para previsão de dados de séries temporais não lineares. Utilizado no core científico para detecção de tendências de agravos epidemiológicos, capturando sazonalidades anuais, semanais e efeitos de feriados com bandas de incerteza estatística (95%).
* **Numpy / SciPy:** Suporte matemático subjacente para operações algébricas vetoriais e transformações lineares pesadas antes da renderização.

---

## 🎨 Camada de Apresentação & UI Reativa

* **Streamlit:** Framework de interface de usuário. Gerencia o ciclo de renderização síncrono e reativo através do estado em memória (`st.session_state`), eliminando a necessidade de servidores web pesados (como Flask/Gunicorn) e bancos de sessões (como Redis).
* **Plotly Charts (Graph Objects):** Engine de visualização declarativa de alta performance. Utilizada para renderizar gráficos polares (Radar), matrizes de densidade (Heatmaps), dispersão histórica e curvas de projeção preditiva de forma interativa.

---

## ⚙️ Ambiente de Desenvolvimento & Ferramentas

* **Miniconda / Conda:** Gerenciador de ambientes virtuais e dependências binárias complexas (garantindo a compilação correta do Prophet e dependências C++/Rust do Polars de forma isolada).
* **Linux Environment (i3wm / Ranger):** Ambiente nativo de desenvolvimento focado em eficiência operacional e automação via CLI.
* **JetBrains DataGrip & CLion:** Ferramentas utilizadas no ambiente integrado para depuração e inspeção profunda de esquemas de dados brutos e performance.