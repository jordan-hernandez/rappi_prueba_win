# 🛵 Rappi Analytics Chat - Streamlit App

Interfaz de chat interactiva para consultar las métricas de Rappi usando lenguaje natural.

## 🚀 Instalación

```bash
# Instalar dependencias
pip install -r requirements.txt
```

## ▶️ Ejecutar la aplicación

```bash
streamlit run rappi_sql_chat.py
```

La aplicación se abrirá en tu navegador en `http://localhost:8501`

## 💬 Características

- **Chat interactivo**: Pregunta en lenguaje natural sobre las métricas de Rappi
- **Text-to-SQL**: Convierte automáticamente tus preguntas en queries SQL
- **Visualizaciones automáticas**: Gráficos generados con Plotly
- **Scores de calidad**: Evaluación del valor de negocio de cada query
- **Historial de chat**: Mantiene el contexto de la conversación
- **Datos tabulares**: Visualiza los resultados en tablas interactivas
- **SQL Queries**: Inspecciona las queries generadas

## 📊 Ejemplos de preguntas

- ¿Cuál es el país con mejor Perfect Orders?
- Muestra la evolución de Gross Profit UE en México
- ¿Qué zonas tienen mejor Lead Penetration?
- Compara Pro Adoption entre países
- Top 5 ciudades por órdenes

## 🔧 Configuración

El webhook de N8N está configurado en:
```
https://sswebhookss.gaussiana.io/webhook/rappi-analytics
```

Para cambiar el webhook, edita la variable `WEBHOOK_URL` en [rappi_sql_chat.py](rappi_sql_chat.py#L13)

## 🎯 Arquitectura

```
User Input (Streamlit)
    ↓
N8N Webhook
    ↓
AI Agent (SQL Generator) → OpenAI GPT-4o-mini
    ↓
PostgreSQL Execution
    ↓
Evaluator Agent (Quality Check)
    ↓
Answer Generator + Visualization
    ↓
Response to Streamlit
```
