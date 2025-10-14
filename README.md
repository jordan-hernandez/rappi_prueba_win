# 🛵 Rappi Analytics Agent

> **Sistema de IA para consultas de métricas de negocio en lenguaje natural**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-green.svg)](https://openai.com)
[![N8N](https://img.shields.io/badge/N8N-Workflow-orange.svg)](https://n8n.io)

## 🎯 Descripción

El **Rappi Analytics Agent** es un sistema de inteligencia artificial que permite a los equipos de Growth de Rappi hacer preguntas en lenguaje natural sobre métricas de negocio y obtener respuestas basadas en datos reales, con visualizaciones automáticas y evaluación de calidad.

### ✨ Características Principales

- 🤖 **Generación automática de SQL** a partir de preguntas en lenguaje natural
- 📊 **Visualizaciones automáticas** con Plotly (barras, líneas, pie charts)
- 🧠 **Contexto completo** con métricas, DDL y consultas validadas
- ⭐ **Sistema de evaluación** automática de calidad de consultas
- 🔄 **Feedback loop** para mejora continua
- 📈 **Métricas de negocio** de 9 países de Latinoamérica

## 🏗️ Arquitectura

### Stack Tecnológico

```
Frontend: Streamlit + Plotly + Pandas
Orquestación: N8N Workflows
IA: OpenAI GPT-4o-mini + Embeddings
Vector Store: Qdrant Cloud
Base de Datos: PostgreSQL/Supabase
```

### Flujo de Procesamiento

1. **Usuario** hace pregunta en Streamlit
2. **N8N** recibe pregunta vía webhook
3. **Vector Store** busca contexto relevante
4. **AI Agent** genera SQL con contexto completo
5. **Base de datos** ejecuta consulta
6. **Evaluador** califica calidad de la consulta
7. **Generador de respuestas** crea explicación en lenguaje natural
8. **Visualizador** genera gráficos automáticamente
9. **Usuario** recibe respuesta completa con visualización

## 🚀 Instalación Rápida

### Prerrequisitos

- Python 3.8+
- Cuenta de OpenAI
- Cuenta de Qdrant Cloud
- Base de datos PostgreSQL o Supabase
- N8N (local o cloud)

### 1. Clonar Repositorio

```bash
git clone <repository-url>
cd n8n_workflows
```

### 2. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno

#### Opción A: Archivo .env (Recomendado para desarrollo)

```bash
# Copiar template de configuración
cp config.example .env

# Editar .env con tus credenciales
```

Configurar las variables en `.env`:

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
```

#### Opción B: Streamlit Secrets (Para producción)

Crear archivo `streamlit_app/secrets.toml`:

```toml
[webhook]
url = "https://sswebhookss.gaussiana.io/webhook/tu-webhook-id"

[openai]
api_key = "sk-tu-openai-api-key"

[database]
url = "postgresql://user:pass@host:port/db"

[qdrant]
url = "https://tu-cluster.qdrant.io"
api_key = "tu-qdrant-api-key"
```

**Nota**: Copia `secrets.toml.example` a `secrets.toml` y configura tus valores.

### 4. Configurar Base de Datos

```bash
# Ejecutar schema SQL
psql -h host -U user -d database -f rag_setup/supabase_schema.sql
```

### 5. Inicializar Vector Store

```bash
cd rag_setup
python upload_to_qdrant_cloud.py
```

### 6. Configurar N8N

1. Importar `Agente_rappi.json` en N8N
2. Configurar credenciales de OpenAI
3. Configurar conexión a base de datos
4. Activar workflow

### 7. Configurar Streamlit Secrets

```bash
# Copiar template de secrets
cd streamlit_app
cp secrets.toml.example secrets.toml

# Editar secrets.toml con tus configuraciones
# Especialmente el webhook URL de N8N
```

### 8. Ejecutar Aplicación

```bash
cd streamlit_app
streamlit run rappi_sql_chat.py
```

## 📊 Métricas Soportadas

### Métricas de Calidad
- **Perfect Orders** (0-1): Calidad del servicio
- **Lead Penetration**: Penetración de mercado
- **Gross Profit UE**: Ganancia bruta por orden
- **Pro Adoption** (0-1): Adopción de Rappi Prime

### Métricas de Usuario
- **Order Frequency**: Frecuencia de órdenes
- **AOV**: Valor promedio de orden
- **Active Users**: Usuarios activos
- **New Users**: Usuarios nuevos
- **Retention Rate**: Tasa de retención
- **Churn Rate**: Tasa de abandono

### Métricas Financieras
- **CAC**: Costo de adquisición de cliente
- **LTV**: Valor de vida del cliente
- **Revenue**: Ingresos

### Países Soportados
🇦🇷 Argentina | 🇧🇷 Brasil | 🇨🇱 Chile | 🇨🇴 Colombia | 🇨🇷 Costa Rica | 🇪🇨 Ecuador | 🇲🇽 México | 🇵🇪 Perú | 🇺🇾 Uruguay

## 💡 Ejemplos de Uso

### Preguntas Simples
- "¿Cuál es el país con mejor Perfect Orders?"
- "Muestra las top 5 zonas por Lead Penetration"
- "¿Qué ciudades tienen Pro Adoption mayor al 50%?"

### Preguntas de Tendencias
- "Evolución de Gross Profit UE en México en las últimas 4 semanas"
- "Compara Perfect Orders entre Colombia y Brasil"
- "Tendencia de órdenes en las zonas prioritarias"

### Preguntas de Análisis
- "¿Qué zonas tienen alto Lead Penetration pero bajo Perfect Order?"
- "Correlación entre Pro Adoption y Order Frequency por país"
- "Análisis de segmentación por tipo de zona"

## 🔧 Configuración Avanzada

### Personalizar Métricas

Editar `rag_setup/init_rag.py` para agregar nuevas métricas:

```python
METRICS_DOCUMENTATION = [
    {
        "title": "Nueva Métrica",
        "content": "Descripción detallada...",
        "category": "business_metric"
    }
]
```

### Configurar Visualizaciones

Modificar `streamlit_app/rappi_sql_chat.py` para personalizar tipos de gráficos:

```python
def detect_chart_type(question, data):
    # Lógica personalizada para detectar tipo de gráfico
    pass
```

### Ajustar Evaluación

Modificar criterios en `Agente_rappi.json`:

```json
{
  "strategic_value": "Relevancia para Growth Manager (0-10)",
  "query_correctness": "Corrección lógica (0-10)",
  "efficiency_gain": "Ahorro de tiempo (0-10)"
}
```

## 📈 Monitoreo y Métricas

### Métricas Técnicas
- **Tiempo de respuesta**: Target < 30 segundos
- **Tasa de éxito**: Target > 70% (score > 6.5)
- **Iteraciones promedio**: Target < 2 por consulta

### Métricas de Negocio
- **Feedback de usuarios**: Target > 4⭐ promedio
- **Consultas almacenadas**: Gold queries para aprendizaje
- **Uso de contexto**: Hits en vector store

### Alertas Recomendadas
- Timeout > 30 segundos
- Error rate > 30%
- API usage > 80% del límite

## 🚀 Roadmap

### Fase 1 (Actual) ✅
- [x] Contexto completo con RAG
- [x] Evaluación automática de calidad
- [x] Feedback loop para mejora continua
- [x] Visualizaciones automáticas

### Fase 2 (Próxima) 🔄
- [ ] Múltiples agentes en paralelo
- [ ] Síntesis inteligente de resultados
- [ ] Optimización automática de consultas
- [ ] Dashboard de métricas del sistema

### Fase 3 (Futuro) 🔮
- [ ] Soporte multi-modal (imágenes, documentos)
- [ ] Streaming de datos en tiempo real
- [ ] Auto-scaling basado en demanda
- [ ] Integración con más fuentes de datos

## 📚 Documentación

- **[Documentación Técnica Completa](DOCUMENTACION_SISTEMA.md)**: Arquitectura detallada y implementación
- **[Diagramas de Arquitectura](DIAGRAMAS_ARQUITECTURA.md)**: Visualizaciones del sistema
- **[Guía de Migración a Supabase](rag_setup/README_SUPABASE.md)**: Configuración de base de datos
- **[Guía de Upload a Qdrant](rag_setup/README_UPLOAD.md)**: Configuración del vector store

## 🤝 Contribuir

1. Fork el proyecto
2. Crear branch para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 👥 Equipo

- **Desarrollo**: Equipo de Data Science de Rappi
- **Arquitectura**: Implementación de RAG con contexto completo
- **IA**: OpenAI GPT-4o-mini para generación de SQL

## 📞 Soporte

Para soporte técnico o preguntas:
- Crear un issue en GitHub
- Contactar al equipo de Data Science
- Revisar la documentación técnica

---

**🛵 Rappi Analytics Agent** - Democratizando el acceso a datos de negocio a través de IA

*Última actualización: Diciembre 2024*
