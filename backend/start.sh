#!/bin/bash
set -e

echo "==> Pre-caching HuggingFace embedding model (all-MiniLM-L6-v2)..."
python -c "
from langchain_huggingface import HuggingFaceEmbeddings
HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')
print('Model cached successfully.')
"

echo "==> Starting Gunicorn..."
exec gunicorn app:app --bind "0.0.0.0:${PORT:-10000}" --workers 1 --timeout 120
