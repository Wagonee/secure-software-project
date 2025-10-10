# Data Flow Diagram для Workout Log API

Диаграмма потоков данных (DFD) с обозначенными границами доверия и потоками для сервиса отслеживания тренировок. Отражает требования безопасности из NFR-02 (защита данных) и NFR-05 (защита от DoS).

```mermaid
flowchart LR
  Client[Browser / Mobile App] -->|F1: HTTPS POST /workouts/, /exercises/| GW[FastAPI Gateway]

  subgraph Edge[Trust Boundary: Edge]
    GW -->|F2: Rate-limited requests| SVC[Workout Service]
  end

  subgraph Core[Trust Boundary: Core]
    SVC -->|F3: In-memory storage operations| DB[(DB: Lists<br>db_workouts<br>db_exercises)]
    SVC -->|F4: Pydantic validation| VAL[Input Validation]
  end

  subgraph Data[Trust Boundary: Data]
    DB -->|F5: Future: Persistence| STORAGE[(Persistent Storage)]
  end

  style GW stroke-width:2px,stroke:#f66
  style SVC stroke-width:2px
  style DB stroke-width:2px,stroke:#66f

  %% F1 - NFR-02 (AuthN/AuthZ)
  %% F2 - NFR-05 (Rate limiting)
  %% F3 - NFR-03 (Data validation)
  %% F4 - NFR-03 (Pydantic models)
  %% F5 - NFR-02 (Data protection)

```