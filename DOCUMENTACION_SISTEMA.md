# 🛵 Rappi Analytics Agent - Documentación Técnica Completa

## 📋 Índice

1. [Visión General del Sistema](#visión-general-del-sistema)
2. [Arquitectura de Contexto Completo](#arquitectura-de-contexto-completo)
3. [Implementación RAG (Retrieval-Augmented Generation)](#implementación-rag)
4. [Workflow de N8N y Agentes](#workflow-de-n8n-y-agentes)
5. [Sistema de Evaluación y Feedback](#sistema-de-evaluación-y-feedback)
6. [Interfaz de Usuario (Streamlit)](#interfaz-de-usuario-streamlit)
7. [Mejoras Futuras: Múltiples Agentes en Paralelo](#mejoras-futuras)
8. [Configuración y Despliegue](#configuración-y-despliegue)

---

## 🎯 Visión General del Sistema

El **Rappi Analytics Agent** es un sistema de inteligencia artificial que convierte preguntas en lenguaje natural sobre métricas de negocio de Rappi en consultas SQL ejecutables, proporcionando respuestas contextualizadas y visualizaciones automáticas.

### Objetivo Principal
Proporcionar a los equipos de Growth de Rappi una herramienta que les permita:
- Hacer preguntas en lenguaje natural sobre métricas de negocio
- Obtener respuestas basadas en datos reales de la base de datos
- Visualizar automáticamente los resultados
- Evaluar la calidad de las consultas generadas

### Stack Tecnológico
- **Frontend**: Streamlit (interfaz de chat)
- **Orquestación**: N8N (workflow automation)
- **IA**: OpenAI GPT-4o-mini (generación de SQL y respuestas)
- **Base de Datos**: PostgreSQL/Supabase (datos de métricas)
- **Vector Store**: Qdrant Cloud (contexto de negocio)
- **Visualización**: Plotly (gráficos interactivos)

---

## 🧠 Arquitectura de Contexto Completo

### Filosofía: Contexto Completo para Mejores Resultados

El sistema implementa una arquitectura de **contexto completo** que proporciona al modelo de IA toda la información necesaria para generar consultas SQL precisas y relevantes. Esta aproximación se basa en tres pilares fundamentales:

### 1. 📊 Documentación de Métricas de Negocio

**Ubicación**: Vector Store (Qdrant Cloud) - Colección `rappi_business_context`

**Contenido**:
- **13 métricas principales** con definiciones detalladas
- **Cálculos y fórmulas** específicas
- **Valores típicos** y rangos esperados
- **Casos de uso** y ejemplos de aplicación
- **Insights de negocio** y correlaciones

**Métricas incluidas**:
```
- Perfect Orders (0-1 scale)
- Lead Penetration (penetración de mercado)
- Gross Profit UE (ganancia bruta por orden)
- Pro Adoption (adopción de Rappi Prime)
- Order Frequency (frecuencia de órdenes)
- AOV (Average Order Value)
- Active Users (usuarios activos)
- New Users (usuarios nuevos)
- Retention Rate (tasa de retención)
- Churn Rate (tasa de abandono)
- CAC (Customer Acquisition Cost)
- LTV (Lifetime Value)
- Revenue (ingresos)
```

**Ejemplo de documentación**:
```markdown
Perfect Orders es una métrica pre-calculada (0-1 scale) que mide la calidad del servicio.

**Cálculo**: Órdenes entregadas a tiempo, sin cancelaciones, sin defectos / Total órdenes

**Valores**:
- 1.0 = 100% de órdenes perfectas
- 0.8 = 80% de órdenes perfectas
- < 0.7 = Requiere atención inmediata

**Uso en SQL**:
```sql
SELECT zone, l0w_value as perfect_order_rate
FROM metrics_input
WHERE metric = 'Perfect Orders'
ORDER BY l0w_value DESC;
```
```

### 2. 🗄️ DDL Schemas (Esquemas de Base de Datos)

**Ubicación**: Vector Store (Qdrant Cloud) - Colección `rappi_business_context`

**Contenido**:
- **Estructura completa** de las tablas
- **Tipos de datos** y restricciones
- **Índices** y optimizaciones
- **Reglas críticas** de uso
- **Ejemplos de datos** de muestra

**Tablas documentadas**:

#### `metrics_input` (Todas las métricas de negocio)
```sql
CREATE TABLE metrics_input (
    id BIGSERIAL PRIMARY KEY,
    country VARCHAR(10),        -- MX, CO, BR, CL, AR, PE, EC, CR, UY
    city VARCHAR(100),          -- Ciudad
    zone VARCHAR(200),          -- Zona
    zone_type VARCHAR(50),      -- Clasificación de zona
    metric VARCHAR(100),        -- ⚠️ CRÍTICO: Nombre de métrica
    l0w_value NUMERIC(10,4),    -- Semana actual
    l1w_value NUMERIC(10,4),    -- 1 semana atrás
    l2w_value NUMERIC(10,4),    -- 2 semanas atrás
    -- ... hasta l8w_value (8 semanas atrás)
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### `orders` (Solo conteos de órdenes)
```sql
CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    country VARCHAR(10),
    city VARCHAR(100),
    zone VARCHAR(200),
    l0w INTEGER,                -- Órdenes semana actual
    l1w INTEGER,                -- 1 semana atrás
    -- ... hasta l8w (8 semanas atrás)
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Reglas críticas documentadas**:
- ⚠️ **TODAS las métricas** están en `metrics_input`
- ⚠️ **SIEMPRE filtrar** por `metric = 'Nombre Exacto'`
- ⚠️ **Para tendencias** usar `l0w_value`, `l1w_value`, etc.
- ⚠️ **Para agregaciones** usar `AVG()`, `MIN()`, `MAX()`, `COUNT()`

### 3. 🏆 Gold Queries (Consultas Validadas)

**Ubicación**: Vector Store (Qdrant Cloud) - Colección `rappi_business_context`

**Contenido**:
- **Preguntas frecuentes** con sus consultas SQL correspondientes
- **Scores de calidad** (1-5 estrellas)
- **Patrones de consulta** validados
- **Ejemplos de mejores prácticas**

**Ejemplos de Gold Queries**:

```sql
-- Pregunta: "Top 5 zonas con mejor Perfect Order"
SELECT zone, country, city, l0w_value as perfect_order_rate
FROM metrics_input
WHERE metric = 'Perfect Orders'
  AND l0w_value IS NOT NULL
ORDER BY l0w_value DESC
LIMIT 5;

-- Pregunta: "Compara Perfect Order entre México y Colombia"
SELECT
    country,
    AVG(l0w_value) as avg_perfect_order,
    MIN(l0w_value) as min_perfect_order,
    MAX(l0w_value) as max_perfect_order,
    COUNT(*) as num_zones
FROM metrics_input
WHERE metric = 'Perfect Orders'
  AND country IN ('MX', 'CO')
GROUP BY country
ORDER BY avg_perfect_order DESC;
```

---

## 🔍 Implementación RAG (Retrieval-Augmented Generation)

### Arquitectura RAG

El sistema implementa un **RAG híbrido** que combina:

1. **Búsqueda semántica** en el vector store
2. **Contexto estructurado** de métricas y esquemas
3. **Ejemplos validados** de consultas SQL

### Flujo de Búsqueda de Contexto

```mermaid
graph TD
    A[Pregunta del Usuario] --> B[Generar Embedding]
    B --> C[Buscar en Qdrant]
    C --> D[Obtener Top 5 Contextos]
    D --> E[Filtrar por Relevancia]
    E --> F[Combinar Contextos]
    F --> G[Enriquecer Prompt del Agente]
```

### Configuración de Qdrant

**Colección**: `rappi_business_context`
**Embeddings**: OpenAI `text-embedding-3-small` (1536 dimensiones)
**Top-K**: 5 contextos más relevantes
**Filtros**: Por categoría (metrics, ddl, queries)

### Categorías de Contexto

```python
CONTEXT_CATEGORIES = {
    "business_metric": "Documentación de métricas de negocio",
    "ddl_schema": "Esquemas de base de datos",
    "validated_query": "Consultas SQL validadas",
    "geography": "Información geográfica",
    "data_structure": "Estructura de datos"
}
```

### Proceso de Enriquecimiento

1. **Búsqueda semántica**: Encuentra contextos relacionados con la pregunta
2. **Filtrado por relevancia**: Score > 0.7
3. **Combinación inteligente**: Mezcla métricas, DDL y ejemplos
4. **Formateo para prompt**: Estructura el contexto para el agente

---

## 🤖 Workflow de N8N y Agentes

### Arquitectura del Workflow

```mermaid
graph TD
    A[Webhook] --> B[AI Agent - SQL Generator]
    B --> C[Extract SQL]
    C --> D[Execute SQL Query]
    D --> E[Evaluator Agent]
    E --> F{Should Reject?}
    F -->|Yes| G[Prepare Regeneration]
    G --> B
    F -->|No| H[Answer Generator]
    H --> I[Detect Visualization]
    I --> J[Generate Chart]
    J --> K[Compile Response]
    K --> L[Respond to Webhook]
```

### Componentes del Workflow

#### 1. **AI Agent - SQL Generator**
- **Modelo**: GPT-4o-mini
- **Temperatura**: 0.1 (consistencia)
- **Max Tokens**: 500
- **Contexto**: Vector Store + DDL + Gold Queries
- **Memoria**: PostgreSQL Chat Memory

**Prompt del Sistema**:
```
You are an expert SQL analyst for Rappi's analytics database with access to business context and query validation tools.

**YOUR TOOLS:**
1. **Vector Store Search**: Use this FIRST to find business context, metric definitions, and examples for the metrics mentioned in the question.
2. **SQL Executor**: You can test queries before returning them (optional for validation).

**WORKFLOW:**
1. First, search the vector store for business context about the metrics/KPIs mentioned
2. Generate SQL query based on schema and context found
3. Return the final SQL query

**DATABASE SCHEMA:**
[DDL completo incluido aquí]

**IMPORTANT RULES:**
1. ALL metrics are in metrics_input table
2. Always filter: WHERE metric = 'Exact Metric Name'
3. Use aggregations (AVG, MIN, MAX, COUNT) when grouping
4. For comparisons, use GROUP BY country/zone
5. For trends, select l0w_value, l1w_value, l2w_value, etc.
6. Check NULL values with IS NOT NULL
```

#### 2. **Evaluator Agent**
- **Modelo**: GPT-4o-mini
- **Temperatura**: 0.2
- **Max Tokens**: 800
- **Propósito**: Evaluar calidad de la consulta SQL

**Criterios de Evaluación**:
```json
{
  "strategic_value": "Relevancia para Growth Manager (0-10)",
  "query_correctness": "Corrección lógica y estructura (0-10)",
  "efficiency_gain": "Ahorro de tiempo vs análisis manual (0-10)",
  "overall_score": "Promedio de los 3 criterios",
  "should_reject": "true si overall_score < 6.5 o query_correctness < 5",
  "feedback": "Feedback consolidado con sugerencias"
}
```

#### 3. **Answer Generator Agent**
- **Modelo**: GPT-4o-mini
- **Temperatura**: 0.3
- **Max Tokens**: 400
- **Propósito**: Generar respuesta en lenguaje natural

**Formato de Respuesta**:
- 2-4 oraciones concisas
- Números clave e insights
- Implicaciones de negocio
- Lenguaje no técnico

### Sistema de Iteraciones

El sistema implementa un **mecanismo de iteración** con feedback:

1. **Máximo 3 iteraciones** por consulta
2. **Feedback automático** del evaluador
3. **Regeneración** con contexto mejorado
4. **Aceptación forzada** después de 3 intentos

---

## 📊 Sistema de Evaluación y Feedback

### Evaluación Automática

#### Criterios de Calidad (0-10)

1. **Strategic Value** (Valor Estratégico)
   - Relevancia para Growth Manager
   - Accionabilidad de los resultados
   - Potencial de adopción

2. **Query Correctness** (Corrección de Consulta)
   - Estructura lógica correcta
   - Sintaxis SQL válida
   - Coherencia con la pregunta

3. **Efficiency Gain** (Ganancia de Eficiencia)
   - Ahorro de tiempo vs análisis manual
   - Automatización de tareas repetitivas
   - Reducción de errores humanos

#### Umbrales de Decisión

```python
EVALUATION_THRESHOLDS = {
    "accept": 6.5,           # Score mínimo para aceptar
    "reject": 5.0,           # Score mínimo de corrección
    "max_iterations": 3,     # Máximo de iteraciones
    "high_quality": 8.0      # Score de alta calidad
}
```

### Sistema de Feedback de Usuario

#### Componente de Feedback (Streamlit)

**Funcionalidades**:
- **Escala de 1-5 estrellas** para calificar respuestas
- **Comentarios opcionales** para feedback detallado
- **Almacenamiento automático** en vector DB para consultas de alta calidad (4+ estrellas)
- **Integración con webhook** de N8N

#### Flujo de Feedback

```mermaid
graph TD
    A[Usuario Califica Respuesta] --> B{Score >= 4?}
    B -->|Yes| C[Almacenar en Vector DB]
    B -->|No| D[Solo Registrar Feedback]
    C --> E[Usar para Aprendizaje Futuro]
    D --> F[Análisis de Mejoras]
```

#### Almacenamiento de Gold Queries

Las consultas con **4+ estrellas** se almacenan automáticamente como "Gold Queries" para:
- Mejorar futuras generaciones
- Crear patrones de consulta validados
- Entrenar el sistema con ejemplos de alta calidad

---

## 🖥️ Interfaz de Usuario (Streamlit)

### Características Principales

#### 1. **Chat Interactivo**
- Interfaz de chat moderna y responsive
- Historial de conversación persistente
- Indicadores de carga y estado

#### 2. **Visualización Automática**
- **Detección inteligente** del tipo de gráfico
- **Gráficos de barras** para comparaciones
- **Gráficos de línea** para tendencias
- **Gráficos de pie** para distribuciones
- **Preprocesamiento** de datos complejos

#### 3. **Mostrar Datos Tabulares**
- **Tablas interactivas** con pandas
- **Filtrado y ordenamiento** automático
- **Paginación** para grandes datasets
- **Formateo** de números y fechas

#### 4. **Sistema de Métricas**
- **Scores de calidad** en tiempo real
- **Tiempo ahorrado** estimado
- **Número de iteraciones** realizadas
- **Detalles de evaluación** expandibles

### Componentes Técnicos

#### Preprocesamiento de Visualizaciones

```python
def preprocess_chart_data(viz_data):
    """
    Preprocesa datos complejos donde X e Y son objetos JSON.
    Maneja casos como:
    - Objetos con múltiples métricas
    - Datos anidados de zona/ciudad/país
    - Conversión de escalas (0-1 a porcentajes)
    """
```

#### Extracción de Tablas

```python
def extract_data_table_from_chart(viz_data):
    """
    Extrae tablas de datos del JSON de visualización.
    Convierte objetos complejos en DataFrames de pandas.
    """
```

### Configuración de Webhook

```python
WEBHOOK_URL = "https://sswebhookss.gaussiana.io/webhook/604b1f14-eacb-4f33-91c7-60a914831b3c"
```

---

## 🚀 Mejoras Futuras: Múltiples Agentes en Paralelo

### Visión: Arquitectura de Agentes Paralelos

Basándose en el diagrama proporcionado, el sistema futuro implementará:

#### 1. **Clasificación de Complejidad**
```mermaid
graph TD
    A[Pregunta del Usuario] --> B[Clasificador de Complejidad]
    B --> C[Question Complexity]
    B --> D[Schema Complexity]
    B --> E[SQL Complexity]
    B --> F[Business Context Matching]
```

#### 2. **Agentes Especializados en Paralelo**

**Agente de Consultas Simples**:
- Preguntas directas sobre métricas
- Consultas de una sola tabla
- Agregaciones básicas

**Agente de Consultas Complejas**:
- Joins entre múltiples tablas
- Consultas con subconsultas
- Análisis de tendencias complejas

**Agente de Análisis de Negocio**:
- Correlaciones entre métricas
- Insights de crecimiento
- Análisis de segmentación

**Agente de Optimización**:
- Consultas eficientes
- Índices recomendados
- Mejores prácticas SQL

#### 3. **Sistema de Síntesis**

```mermaid
graph TD
    A[Agente 1] --> E[Síntesis]
    B[Agente 2] --> E
    C[Agente 3] --> E
    D[Agente N] --> E
    E --> F[Mejor Consulta SQL]
    E --> G[Interpretación de Pregunta]
```

#### 4. **Evaluación Comparativa**

- **Score de cada agente** por consulta
- **Selección del mejor resultado**
- **Aprendizaje** de patrones exitosos
- **Mejora continua** de especialización

### Implementación Técnica

#### Estructura de Agentes Paralelos

```python
class ParallelAgentSystem:
    def __init__(self):
        self.agents = {
            "simple_queries": SimpleQueryAgent(),
            "complex_queries": ComplexQueryAgent(),
            "business_analysis": BusinessAnalysisAgent(),
            "optimization": OptimizationAgent()
        }
        self.synthesizer = QuerySynthesizer()
        self.evaluator = ComparativeEvaluator()
    
    async def process_query(self, question: str):
        # Ejecutar todos los agentes en paralelo
        results = await asyncio.gather(*[
            agent.generate_sql(question) 
            for agent in self.agents.values()
        ])
        
        # Sintetizar el mejor resultado
        best_query = self.synthesizer.synthesize(results)
        
        return best_query
```

#### Ventajas de la Arquitectura Paralela

1. **Mayor Precisión**: Especialización por tipo de consulta
2. **Redundancia**: Múltiples enfoques para la misma pregunta
3. **Escalabilidad**: Fácil agregar nuevos agentes
4. **Robustez**: Fallback automático entre agentes
5. **Aprendizaje**: Mejora continua basada en resultados

---

## ⚙️ Configuración y Despliegue

### Requisitos del Sistema

#### Dependencias Python
```txt
streamlit>=1.28.0
requests>=2.31.0
plotly>=5.17.0
pandas>=2.1.0
qdrant-client>=1.6.0
openai>=1.3.0
python-dotenv>=1.0.0
```

#### Servicios Externos
- **OpenAI API**: Para embeddings y generación de texto
- **Qdrant Cloud**: Para vector store
- **PostgreSQL/Supabase**: Para base de datos de métricas
- **N8N**: Para orquestación de workflows

### Configuración de Variables de Entorno

```env
# OpenAI Configuration
OPENAI_API_KEY=tu-openai-api-key

# Qdrant Cloud Configuration
QDRANT_URL=https://tu-cluster.qdrant.io
QDRANT_API_KEY=tu-qdrant-api-key

# Database Configuration
DATABASE_URL=postgresql://user:pass@host:port/db
# O para Supabase:
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-supabase-key

# N8N Webhook
WEBHOOK_URL=https://sswebhookss.gaussiana.io/webhook/tu-webhook-id
```

### Proceso de Despliegue

#### 1. **Configurar Base de Datos**
```bash
# Ejecutar schema SQL
psql -h host -U user -d database -f supabase_schema.sql
```

#### 2. **Inicializar Vector Store**
```bash
cd rag_setup
python upload_to_qdrant_cloud.py
```

#### 3. **Configurar N8N Workflow**
- Importar `Agente_rappi.json`
- Configurar credenciales de OpenAI
- Configurar conexión a base de datos
- Configurar webhook URL

#### 4. **Ejecutar Aplicación Streamlit**
```bash
cd streamlit_app
streamlit run rappi_sql_chat.py
```

### Monitoreo y Mantenimiento

#### Métricas Clave
- **Tiempo de respuesta** promedio
- **Tasa de éxito** de consultas (score > 6.5)
- **Número de iteraciones** por consulta
- **Feedback de usuarios** (1-5 estrellas)
- **Uso de contexto** del vector store

#### Alertas Recomendadas
- Tiempo de respuesta > 30 segundos
- Tasa de éxito < 70%
- Errores de conexión a servicios externos
- Uso de API > 80% del límite

---

## 📈 Conclusiones

El **Rappi Analytics Agent** representa una implementación avanzada de RAG (Retrieval-Augmented Generation) que combina:

1. **Contexto completo** con métricas, DDL y gold queries
2. **Evaluación automática** de calidad de consultas
3. **Feedback loop** para mejora continua
4. **Visualización automática** de resultados
5. **Arquitectura escalable** hacia múltiples agentes paralelos

### Beneficios Clave

- **Democratización del acceso a datos** para equipos no técnicos
- **Reducción del tiempo** de análisis de horas a minutos
- **Consistencia** en la interpretación de métricas
- **Escalabilidad** para múltiples equipos y países
- **Aprendizaje continuo** basado en feedback

### Próximos Pasos

1. **Implementar agentes paralelos** para mayor precisión
2. **Expandir métricas** y contextos de negocio
3. **Integrar más fuentes de datos** (APIs externas)
4. **Desarrollar dashboards** automáticos
5. **Implementar alertas** basadas en métricas

---

*Documentación generada para Rappi Analytics Agent v1.0*
*Última actualización: Diciembre 2024*
