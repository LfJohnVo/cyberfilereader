# SGI-Agent

Asistente conversacional empresarial con **RAG documental** y **núcleo 3D interactivo**.
Permite consultar por chat la documentación del Sistema de Gestión Integral (ISO, políticas,
procedimientos, manuales) con respuestas **fundamentadas solo en los documentos indexados**,
citas verificables y **filtrado por área/permiso**. Incluye además **verificación de
cumplimiento**: sube un documento y comprueba si cumple con las políticas/ISO del SGI.

## Stack

- **Frontend:** React 18 + TypeScript + Vite · React Three Fiber + drei · Tailwind CSS · Zustand
- **Backend:** Python 3.12 · FastAPI · LangChain
- **Infra:** Qdrant Cloud (vector DB) · Ollama (LLM y embeddings locales)
- **Orquestación:** Docker + Docker Compose

## Requisitos

- Python 3.12 · Node.js 20+ (recomendado 22+) · Docker Desktop / Engine + Compose v2
- Cuenta en [Qdrant Cloud](https://cloud.qdrant.io) (el cluster *Free* basta)
- [Ollama](https://ollama.com/download) instalado en el host, con:
  - `ollama pull qwen3:8b`
  - `ollama pull nomic-embed-text`

## Puesta en marcha

### Local (desarrollo)

```bash
# Backend
cd backend
py -3.12 -m venv .venv
.venv\Scripts\activate            # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload     # http://localhost:5001

# Ingesta de documentos (coloca los archivos en docs/<Área>/…)
python -m scripts.ingest

# Frontend
cd ../frontend
npm install
npm run dev                       # http://localhost:5173
```

### Docker

```bash
docker compose up --build -d      # app en http://localhost:5000
docker compose exec backend python -m scripts.ingest
```

> `docs/` (documentación de la empresa) es de **solo lectura** y **no se versiona**.
> `.env` **nunca** se versiona; créalo a partir de `.env.example`.

## Variables de entorno

Copia `.env.example` a `.env` y completa los valores reales.

| Variable | Por defecto | Descripción |
|----------|-------------|-------------|
| `ENV` | `dev` | Entorno de ejecución (`dev` / `prod`). |
| `LOG_LEVEL` | `INFO` | Nivel de logging. |
| `API_HOST` | `0.0.0.0` | Host de escucha de la API. |
| `API_PORT` | `5001` | Puerto de la API. |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | Lista blanca CORS separada por comas. |
| `DOCS_DIR` | `./docs` | Carpeta raíz de documentos (solo lectura). En Docker: `/data/docs`. |
| `DATA_DIR` | `./data` | Carpeta de estado generado (`manifest.json`). |
| `ALLOWED_EXTENSIONS` | `.pdf,.docx,.txt,.md,.xlsx,.csv` | Extensiones aceptadas en ingesta. |
| `MAX_FILE_MB` | `25` | Tamaño máximo de archivo a ingerir (MB). |
| `CHUNK_SIZE` | `1000` | Tamaño de chunk (caracteres). |
| `CHUNK_OVERLAP` | `150` | Solapamiento entre chunks. |
| `RETRIEVER_K` | `5` | Nº de fragmentos recuperados por consulta. |
| `SCORE_THRESHOLD` | `0.50` | Similitud coseno mínima para aceptar contexto (recalibrar por modelo de embeddings; ver `backend/tests/eval`). |
| `RERANK_ENABLED` | `false` | Reordena los candidatos densos con un cross-encoder (activar tras validar; descarga modelo ~1 GB). |
| `RERANK_MODEL` | `jinaai/jina-reranker-v2-base-multilingual` | Modelo cross-encoder (fastembed). Alternativa ligera: `Xenova/ms-marco-MiniLM-L-6-v2`. |
| `RERANK_CANDIDATES` | `20` | Nº de candidatos densos que pasan al reranker. |
| `HYBRID_ENABLED` | `false` | Búsqueda híbrida densa+BM25 (RRF). Requiere re-ingestar la colección con vectores nombrados. |
| `SPARSE_MODEL` | `Qdrant/bm25` | Modelo de embedding disperso (léxico) del modo híbrido. |
| `CONDENSE_ENABLED` | `true` | Reformula preguntas de seguimiento con el historial para recuperar mejor. |
| `CRAG_ENABLED` | `false` | Recuperación correctiva: evalúa el contexto y reintenta/`NO_INFO` si no basta (+1 llamada LLM). |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | URL de Ollama. En Docker: `http://host.docker.internal:11434`. |
| `OLLAMA_CHAT_MODEL` | `qwen3:8b` | Modelo de chat. |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Modelo de embeddings. |
| `OLLAMA_NUM_CTX` | `8192` | Ventana de contexto del LLM. |
| `LLM_TEMPERATURE` | `0.1` | Temperatura de generación (≤0.2 para respuestas documentales). |
| `QDRANT_URL` | — | URL del cluster Qdrant Cloud (incluye `:6333`). |
| `QDRANT_API_KEY` | — | API key de Qdrant Cloud. |
| `QDRANT_COLLECTION` | `sgi_docs` | Nombre de la colección de vectores. |
| `DATABASE_URL` | — | (prod) Cadena de conexión PostgreSQL. |
| `REDIS_URL` | — | (prod) Cadena de conexión Redis. |
| `JWT_SECRET` | `dev-only` | (prod) Secreto de firma JWT (usar 32+ bytes aleatorios). |
| `JWT_EXPIRE_MINUTES` | `480` | (prod) Expiración del token JWT. |
| `VITE_API_URL` | `http://localhost:5001` | (frontend) Base de la API; vacía en build Docker (proxy nginx). |

> Las variables `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` del `.env.example`
> las consume solo el contenedor `postgres` (perfil `prod`).

## Estructura

```
agentessgi/
├── backend/        # FastAPI + LangChain (app/, scripts/, tests/)
├── frontend/       # React + Vite + React Three Fiber
├── mcp/            # servidor MCP opcional
├── docs/           # documentos de la empresa (solo lectura, no versionado)
└── docs-proyecto/  # ADRs y planes
```

## Servidor MCP (opcional)

Expone la recuperación documental como herramientas [MCP](https://modelcontextprotocol.io),
reutilizando el mismo `retriever` que el chat (embeddings Ollama + filtro por área/estado), para
que un agente o cliente MCP (Cursor, el MCP Inspector u otros compatibles) consulte el SGI.

```bash
pip install -r mcp/requirements.txt
python mcp/server.py                                # stdio (clientes locales)
python mcp/server.py --transport http --port 8765   # red / agentes
```

Herramientas:
- **`sgi_buscar(query, areas?)`** — busca en la documentación vigente y devuelve fragmentos con su
  fuente. `areas` filtra por permiso (`null` / `["*"]` = acceso total).
- **`sgi_cumplimiento(ruta, areas?)`** — evalúa si un documento (PDF, DOCX, TXT, MD, XLSX, CSV)
  cumple con las normas del SGI/ISO: veredicto, informe con hallazgos y fuentes citadas.
  `sgi_cumplimiento_texto(documento, nombre, areas?)` hace lo mismo con el texto ya extraído.
- **`sgi_estado()`** — colección, nº de fragmentos y modelo de embeddings.

> El transporte `http` no lleva autenticación: expónlo solo en una red de confianza o detrás de un
> proxy con auth. El servidor lee `backend/.env` (mismos Qdrant/Ollama que la API).
