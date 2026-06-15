#!/bin/bash

set -e

VEND_DIR=".venv"

if [ ! -d "VENV_DIR" ]: then
    echo "Criando ambiente"
    python3 -m venv "$VENV_DIR"
fi

echo "ativando"
source "$VENV_DIR/bin/activate"

echo "Atualizando"
pip install --upgrade pip
pip install -e .

echo "Iniciando Painel Streamlit"
Streamlit run src/app.py --server.port 8501