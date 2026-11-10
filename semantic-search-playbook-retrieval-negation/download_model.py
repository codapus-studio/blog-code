"""Download the exact public model revision used for the article during build."""
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer

name = 'sentence-transformers/all-MiniLM-L6-v2'
revision = '1110a243fdf4706b3f48f1d95db1a4f5529b4d41'
model = SentenceTransformer(name, revision=revision, device='cpu')
model.save('/opt/model', safe_serialization=True)
Path('/opt/model-source.json').write_text(json.dumps({'name': name, 'revision': revision}, indent=2))
