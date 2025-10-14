# 🏗️ Diagramas de Arquitectura - Rappi Analytics Agent

## 📊 Arquitectura General del Sistema

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[Streamlit Chat Interface]
        B[Feedback Component]
        C[Visualization Engine]
    end
    
    subgraph "Orchestration Layer"
        D[N8N Workflow Engine]
        E[Webhook Handler]
    end
    
    subgraph "AI Layer"
        F[SQL Generator Agent]
        G[Evaluator Agent]
        H[Answer Generator Agent]
        I[OpenAI GPT-4o-mini]
    end
    
    subgraph "Context Layer"
        J[Qdrant Vector Store]
        K[Metrics Documentation]
        L[DDL Schemas]
        M[Gold Queries]
    end
    
    subgraph "Data Layer"
        N[PostgreSQL/Supabase]
        O[Metrics Data]
        P[Orders Data]
    end
    
    A --> E
    E --> F
    F --> J
    J --> K
    J --> L
    J --> M
    F --> N
    N --> O
    N --> P
    F --> G
    G --> H
    H --> C
    C --> A
    B --> E
```

## 🔄 Flujo de Procesamiento de Consultas

```mermaid
sequenceDiagram
    participant U as Usuario
    participant S as Streamlit
    participant N as N8N
    participant V as Vector Store
    participant AI as AI Agent
    participant DB as Database
    participant E as Evaluator
    
    U->>S: Pregunta en lenguaje natural
    S->>N: POST /webhook
    N->>V: Buscar contexto relevante
    V-->>N: Top 5 contextos
    N->>AI: Generar SQL con contexto
    AI-->>N: Consulta SQL
    N->>DB: Ejecutar consulta
    DB-->>N: Resultados
    N->>E: Evaluar calidad
    E-->>N: Score y feedback
    alt Score < 6.5
        N->>AI: Regenerar con feedback
        AI-->>N: Nueva consulta SQL
        N->>DB: Ejecutar nueva consulta
        DB-->>N: Nuevos resultados
    end
    N->>S: Respuesta completa
    S->>U: Mostrar respuesta + visualización
```

## 🧠 Sistema de Contexto Completo

```mermaid
graph LR
    subgraph "Vector Store (Qdrant)"
        A[Metrics Documentation<br/>13 métricas de negocio]
        B[DDL Schemas<br/>Estructura de tablas]
        C[Gold Queries<br/>Consultas validadas]
        D[Geography Context<br/>Segmentación de zonas]
    end
    
    subgraph "Context Retrieval"
        E[Semantic Search]
        F[Relevance Filtering]
        G[Context Combination]
    end
    
    subgraph "AI Agent"
        H[Enhanced Prompt]
        I[SQL Generation]
    end
    
    A --> E
    B --> E
    C --> E
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
```

## 🔍 Proceso RAG (Retrieval-Augmented Generation)

```mermaid
flowchart TD
    A[Pregunta del Usuario] --> B[Generar Embedding]
    B --> C[Buscar en Qdrant]
    C --> D[Obtener Top 5 Contextos]
    D --> E[Filtrar por Relevancia > 0.7]
    E --> F[Combinar Contextos]
    F --> G[Enriquecer Prompt del Agente]
    G --> H[Generar SQL con Contexto]
    H --> I[Ejecutar Consulta]
    I --> J[Evaluar Resultado]
    J --> K{¿Calidad Suficiente?}
    K -->|No| L[Regenerar con Feedback]
    L --> H
    K -->|Sí| M[Generar Respuesta Final]
```

## 🤖 Arquitectura de Múltiples Agentes (Futuro)

```mermaid
graph TD
    A[Pregunta del Usuario] --> B[Clasificador de Complejidad]
    
    B --> C[Question Complexity]
    B --> D[Schema Complexity]
    B --> E[SQL Complexity]
    B --> F[Business Context Matching]
    
    C --> G[Agente Consultas Simples]
    D --> H[Agente Consultas Complejas]
    E --> I[Agente Análisis de Negocio]
    F --> J[Agente Optimización]
    
    G --> K[Síntesis de Resultados]
    H --> K
    I --> K
    J --> K
    
    K --> L[Evaluación Comparativa]
    L --> M[Mejor Consulta SQL]
    L --> N[Interpretación de Pregunta]
    
    M --> O[Respuesta Final]
    N --> O
```

## 📊 Sistema de Evaluación y Feedback

```mermaid
graph LR
    subgraph "Evaluación Automática"
        A[Strategic Value<br/>0-10]
        B[Query Correctness<br/>0-10]
        C[Efficiency Gain<br/>0-10]
    end
    
    subgraph "Decisión"
        D[Overall Score]
        E{Score >= 6.5?}
    end
    
    subgraph "Feedback Usuario"
        F[Calificación 1-5⭐]
        G[Comentarios Opcionales]
    end
    
    subgraph "Aprendizaje"
        H{Score >= 4⭐?}
        I[Almacenar en Vector DB]
        J[Gold Query]
    end
    
    A --> D
    B --> D
    C --> D
    D --> E
    E -->|No| K[Regenerar]
    E -->|Sí| L[Aceptar]
    F --> H
    G --> H
    H -->|Sí| I
    I --> J
```

## 🎯 Flujo de Visualización Automática

```mermaid
flowchart TD
    A[Resultados de Consulta] --> B[Detectar Tipo de Gráfico]
    B --> C{¿Tendencia?}
    C -->|Sí| D[Gráfico de Línea]
    C -->|No| E{¿Comparación?}
    E -->|Sí| F[Gráfico de Barras]
    E -->|No| G{¿Distribución?}
    G -->|Sí| H[Gráfico de Pie]
    G -->|No| I[Tabla de Datos]
    
    D --> J[Preprocesar Datos]
    F --> J
    H --> J
    I --> J
    
    J --> K[Generar Plotly Chart]
    K --> L[Renderizar en Streamlit]
    L --> M[Mostrar al Usuario]
```

## 🔧 Stack Tecnológico

```mermaid
graph TB
    subgraph "Frontend"
        A[Streamlit<br/>Chat Interface]
        B[Plotly<br/>Visualizaciones]
        C[Pandas<br/>Data Processing]
    end
    
    subgraph "Backend"
        D[N8N<br/>Workflow Engine]
        E[Python<br/>Scripts]
    end
    
    subgraph "AI/ML"
        F[OpenAI GPT-4o-mini<br/>Text Generation]
        G[OpenAI Embeddings<br/>Vector Search]
    end
    
    subgraph "Data Storage"
        H[Qdrant Cloud<br/>Vector Store]
        I[PostgreSQL/Supabase<br/>Relational DB]
    end
    
    subgraph "External APIs"
        J[OpenAI API]
        K[Qdrant API]
        L[Supabase API]
    end
    
    A --> D
    D --> F
    D --> G
    D --> H
    D --> I
    F --> J
    G --> J
    H --> K
    I --> L
```

## 📈 Métricas de Rendimiento

```mermaid
graph LR
    subgraph "Métricas Técnicas"
        A[Tiempo de Respuesta<br/>Target: < 30s]
        B[Tasa de Éxito<br/>Target: > 70%]
        C[Iteraciones Promedio<br/>Target: < 2]
    end
    
    subgraph "Métricas de Negocio"
        D[Feedback Usuario<br/>Target: > 4⭐]
        E[Consultas Almacenadas<br/>Gold Queries]
        F[Uso de Contexto<br/>Vector Store Hits]
    end
    
    subgraph "Alertas"
        G[Timeout > 30s]
        H[Error Rate > 30%]
        I[API Limit > 80%]
    end
    
    A --> G
    B --> H
    C --> I
    D --> E
    E --> F
```

## 🚀 Roadmap de Mejoras

```mermaid
timeline
    title Evolución del Sistema
    
    section Fase 1 (Actual)
        Contexto Completo : RAG con métricas, DDL, gold queries
        Evaluación Automática : 3 criterios de calidad
        Feedback Loop : Almacenamiento de consultas de alta calidad
    
    section Fase 2 (Próxima)
        Agentes Paralelos : Especialización por tipo de consulta
        Síntesis Inteligente : Mejor resultado de múltiples agentes
        Optimización : Consultas más eficientes
    
    section Fase 3 (Futuro)
        Multi-modal : Imágenes y documentos
        Real-time : Streaming de datos
        Auto-scaling : Escalado automático
```

---

*Diagramas generados para Rappi Analytics Agent v1.0*
*Última actualización: Diciembre 2024*
