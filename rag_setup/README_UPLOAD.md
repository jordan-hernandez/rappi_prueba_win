# Subir Contexto de Negocio a Qdrant Cloud

Este script sube 17 contextos de negocio de Rappi a tu instancia de Qdrant Cloud.

## Contenido que se sube

### Métricas (13)
- % PRO Users Who Breakeven
- % Restaurants Sessions With Optimal Assortment
- Gross Profit UE
- Lead Penetration
- MLTV Top Verticals Adoption
- Non-Pro PTC > OP
- Perfect Orders
- Pro Adoption
- Restaurants Markdowns / GMV
- Restaurants SS > ATC CVR
- Restaurants SST > SS CVR
- Retail SST > SS CVR
- Turbo Adoption

### Geografía (2)
- Zone Segmentation (Wealthy vs Non Wealthy)
- Zone Prioritization (High Priority, Prioritized, Not Prioritized)

### Estructura de Datos (1)
- Time Series Data (L8W hasta L0W)
- Countries (9 países: AR, BR, CL, CO, CR, EC, MX, PE, UY)

## Configuración

### 1. Crear archivo `.env`

Copia el archivo `.env.example` a `.env` en la carpeta `n8n_workflows/`:

```bash
cd n8n_workflows
cp .env.example .env
```

### 2. Editar `.env` con tus credenciales

```env
# Qdrant Cloud Configuration
QDRANT_URL=https://tu-cluster.qdrant.io
QDRANT_API_KEY=tu-api-key-aqui

# OpenAI Configuration
OPENAI_API_KEY=tu-openai-api-key-aqui
```

## Uso

```bash
cd n8n_workflows/rag_setup
python upload_to_qdrant_cloud.py
```

## Qué hace el script

1. **Carga variables** desde `.env`
2. **Crea la colección** `rappi_business_context` si no existe
3. **Genera embeddings** para cada contexto usando OpenAI `text-embedding-3-small`
4. **Sube 17 puntos** a Qdrant Cloud
5. **Verifica** que se subieron correctamente
6. **Prueba búsqueda** con "Perfect Orders" como ejemplo

## Estructura de cada punto

```json
{
  "id": "uuid-generado",
  "vector": [1536 dimensiones],
  "payload": {
    "title": "Perfect Orders",
    "content": "Órdenes sin cancelaciones...",
    "category": "metrics",
    "type": "business_context"
  }
}
```

## Categorías

- `metrics`: Métricas de negocio
- `geography`: Información geográfica y segmentación
- `data_structure`: Estructura de datos y países

## Búsqueda desde N8N

Para buscar contexto relevante en N8N, usa:

```javascript
// En N8N Code Node
const query = "¿Qué es Perfect Orders?";

// Generar embedding del query
const embeddingResponse = await fetch('https://api.openai.com/v1/embeddings', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'text-embedding-3-small',
    input: query
  })
});

const embedding = await embeddingResponse.json();

// Buscar en Qdrant
const qdrantResponse = await fetch(`${process.env.QDRANT_URL}/collections/rappi_business_context/points/search`, {
  method: 'POST',
  headers: {
    'api-key': process.env.QDRANT_API_KEY,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    vector: embedding.data[0].embedding,
    limit: 3,
    with_payload: true
  })
});

const results = await qdrantResponse.json();
// results contiene los 3 contextos más relevantes
```

## Troubleshooting

### Error: "QDRANT_URL not set"
Asegúrate de haber creado el archivo `.env` en `n8n_workflows/.env`

### Error: "Failed to establish a new connection"
Verifica que tu URL de Qdrant Cloud sea correcta y que tu IP esté en la whitelist

### Error: "Authentication failed"
Verifica que tu `QDRANT_API_KEY` sea correcta

### Error: "OpenAI API key invalid"
Verifica que tu `OPENAI_API_KEY` sea correcta
