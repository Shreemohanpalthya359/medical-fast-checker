#!/bin/bash
set -e

echo "==> Pre-caching FastEmbed ONNX model (BAAI/bge-small-en-v1.5)..."
python -c "
from langchain_community.embeddings import FastEmbedEmbeddings
FastEmbedEmbeddings(model_name='BAAI/bge-small-en-v1.5')
print('Model cached successfully.')
"

echo "==> Starting Gunicorn..."
exec gunicorn app:app --bind "0.0.0.0:${PORT:-10000}" --workers 1 --timeout 120
