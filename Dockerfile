FROM python:3.10-slim as builder

# 1. Instala dependencias de compilación
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# 2. Instala dependencias GRPC
RUN pip install --upgrade pip && \
    pip install grpcio-tools==1.59.3 protobuf==4.24.4

# 3. Crea el directorio destino primero
RUN mkdir -p /app/proto

# 4. Copia el archivo proto
COPY proto/chat.proto /tmp/

# 5. Genera los archivos protobuf
RUN python -m grpc_tools.protoc \
    -I/tmp \
    --python_out=/app/proto \
    --grpc_python_out=/app/proto \
    /tmp/chat.proto

# --- Fase final ---
FROM python:3.10-slim

# 6. Crea el directorio proto
RUN mkdir -p /app/proto

# 7. Copia los archivos generados
COPY --from=builder /app/proto/ /app/proto/

# Corrige las importaciones
RUN sed -i 's/import chat_pb2 as chat__pb2/from proto import chat_pb2 as chat__pb2/' /app/proto/chat_pb2_grpc.py

# 8. Instala dependencias
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 9. Copia el resto de la aplicación
COPY . .

# 10. Configura entorno
ENV PYTHONPATH="${PYTHONPATH}:/app"

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]