# ADR-0001 · Arquitectura hexagonal + DDD táctico

- **Estado:** aceptado · en migración incremental (strangler fig)
- **Contexto:** el backend crecía con la lógica de dominio modelada con `dict`, sin capa de casos
  de uso, con acceso al singleton de configuración esparcido y factorías globales. Se busca
  testabilidad, límites claros y capacidad de sustituir infraestructura (Ollama/Qdrant/memoria)
  sin tocar la lógica.

## Decisión
Adoptar **arquitectura hexagonal (ports & adapters)** con **DDD táctico**, como **monolito modular**
(un solo despliegue). Capas y regla de dependencias (hacia adentro):

```
presentation (http, mcp)  ─┐
application (casos de uso) ─┼─► domain (modelos + puertos)
infrastructure (adapters) ─┘
```

- **domain/**: value objects (`Fuente`, `Veredicto`, `SearchResult`) y **puertos** (`Protocol`):
  `LlmPort`, `EmbeddingsPort`, `VectorStorePort`, `RetrieverPort`, `MemoryPort`, `DocumentLoaderPort`.
  Sin framework ni infraestructura.
- **application/**: casos de uso (`ResponderConsulta`, `EvaluarCumplimiento`, `EjecutarAgente`,
  `Ingestar`) que dependen de puertos, no de implementaciones.
- **infrastructure/ (hoy `services/`)**: adaptadores concretos (Ollama, Qdrant, FastEmbed, memoria).
- **presentation/ (hoy `api/`, `mcp/`)**: routers/tools finos que llaman a casos de uso.

## Decisiones pragmáticas (aceptadas)
- **Pydantic para los value objects**: doblan como contrato interno y DTO de la API (evita mapeos
  redundantes en un monolito). La presentación depende del dominio (dirección permitida).
- **`Document` (langchain-core) como contenedor de datos neutro** en firmas de puertos y en
  `SearchResult`, para no re-envolver cada fragmento. Es un DTO ligero, no lógica.
- **Sin CQRS, event sourcing ni buses de eventos** salvo necesidad real.

## Plan de migración (strangler, sin romper; `ruff`+`pytest`+`eval`+CI verdes en cada paso)
- **C1 · Puertos** — interfaces `Protocol` (hecho). Los módulos actuales son los adaptadores.
- **C2 · Modelos de dominio** — `Fuente`/`Veredicto`/`SearchResult` (hecho a nivel de contrato;
  la adopción interna completa —`to_source` devolviendo `Fuente`— es un incremento posterior).
- **C3 · Casos de uso** — mover la orquestación de `chain/compliance/agent` a `application/`.
- **C4 · Inyección de dependencias** — `composition_root` que construye adaptadores e inyecta;
  eliminar el `get_settings()` esparcido.
- **C5 · Reorganización** a `contexts/{documentacion,cumplimiento,ingesta}` con presentación fina.
- **C6 · Memoria como puerto** — `InProcessMemory` (LRU acotado, hecho) → Redis por DI, sin tocar
  aplicación.

## Consecuencias
- (+) Testabilidad (dominio y casos de uso con fakes de puertos, sin red), límites claros,
  infraestructura sustituible, deuda de memoria cerrada.
- (−) Más ceremonia/indirección; migración por fases (estado híbrido temporal, esperado).
