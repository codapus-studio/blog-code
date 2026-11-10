FROM python:3.12.12-slim@sha256:f3fa41d74a768c2fce8016b98c191ae8c1bacd8f1152870a3f9f87d350920b7c
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HOME=/opt/hf TOKENIZERS_PARALLELISM=false
RUN pip install --no-cache-dir torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
WORKDIR /app
COPY requirements.lock /app/
RUN pip install --no-cache-dir --no-deps -r requirements.lock && pip check
COPY download_model.py /app/
RUN python download_model.py && pip freeze > /opt/packages.txt
COPY baseline/ /app/baseline/
COPY recorded-results/ /app/recorded-results/
COPY cases.json experiment.py verify_results.py /app/
ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
CMD ["sh", "-c", "python experiment.py && python verify_results.py --reference /app/recorded-results"]
