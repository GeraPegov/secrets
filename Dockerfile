FROM python 

WORKDIR /app

COPY config.toml ./config.toml
COPY . .

RUN pip3 install --no-cache-dir -r requirements.txt
EXPOSE 8000

CMD ["uvicorn", "programm:app", "--host", "0.0.0.0", "--port", "8000"]