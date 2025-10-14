# Migración de Datos a Supabase

Este directorio contiene los scripts para migrar los datos del Excel a Supabase.

## Archivos

- **`supabase_schema.sql`** - DDL para crear las tablas en Supabase
- **`migrate_to_supabase.py`** - Script Python para migrar datos del Excel
- **`README_SUPABASE.md`** - Esta documentación

## Tablas que se crean

### 1. `metrics_input`
Contiene todas las métricas de negocio con series temporales (L0W a L8W):
- Perfect Orders
- Lead Penetration
- Gross Profit UE
- Pro Adoption
- Y todas las demás métricas del Excel

**Estructura:**
```sql
- country (VARCHAR)
- city (VARCHAR)
- zone (VARCHAR)
- zone_type (VARCHAR)
- metric (VARCHAR) -- Nombre de la métrica
- l0w_value (NUMERIC) -- Semana actual
- l1w_value...l8w_value (NUMERIC) -- 1-8 semanas atrás
```

### 2. `orders`
Contiene conteos de órdenes por zona con series temporales (L0W a L8W):

**Estructura:**
```sql
- country (VARCHAR)
- city (VARCHAR)
- zone (VARCHAR)
- l0w (INTEGER) -- Órdenes semana actual
- l1w...l8w (INTEGER) -- Órdenes 1-8 semanas atrás
```

## Configuración

### Paso 1: Configurar Supabase

1. Ve a tu proyecto en [Supabase](https://supabase.com)
2. Ve a **SQL Editor**
3. Copia y ejecuta el contenido de `supabase_schema.sql`
4. Verifica que las tablas se crearon correctamente

### Paso 2: Obtener credenciales

1. Ve a **Settings** → **API**
2. Copia:
   - **Project URL** (ejemplo: `https://abcdefgh.supabase.co`)
   - **anon/public key** o **service_role key** (recomendado service_role para insertar datos)

### Paso 3: Configurar `.env`

Edita el archivo `n8n_workflows/.env` y agrega:

```env
# Supabase Configuration
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-service-role-key-aqui

# Excel File Path
EXCEL_FILE=../../rappi_data.xlsx
```

### Paso 4: Instalar dependencias

```bash
cd n8n_workflows
pip install -r requirements.txt
```

## Ejecutar la migración

```bash
cd n8n_workflows/rag_setup
python migrate_to_supabase.py
```

El script:
1. ✅ Lee el archivo `.env`
2. 📂 Busca el archivo Excel en varias ubicaciones
3. 📊 Analiza las columnas y detecta métricas
4. 📋 Prepara los datos para ambas tablas
5. ⚠️ Te pide confirmación antes de subir
6. 📤 Sube los datos en batches de 100 registros
7. 🔍 Verifica que se subieron correctamente

## Estructura del Excel esperada

El script es flexible y detecta automáticamente las columnas. Puede manejar:

### Formato 1: Columnas separadas por métrica
```
country | city | zone | Perfect_Orders_l0w | Perfect_Orders_l1w | Lead_Penetration_l0w | ...
MX      | CDMX | Roma | 0.87              | 0.85              | 123.4               | ...
```

### Formato 2: Columnas con prefijo de tiempo
```
country | city | zone | l0w_Perfect_Orders | l1w_Perfect_Orders | l0w_Lead_Penetration | ...
MX      | CDMX | Roma | 0.87              | 0.85              | 123.4               | ...
```

### Formato 3: Una columna por métrica (valor actual)
```
country | city | zone | Perfect_Orders | Lead_Penetration | Gross_Profit_UE | ...
MX      | CDMX | Roma | 0.87          | 123.4           | 45.67          | ...
```

El script detecta automáticamente el formato y crea los registros correspondientes.

## Verificación

Después de la migración, puedes verificar en Supabase SQL Editor:

```sql
-- Contar registros
SELECT COUNT(*) FROM metrics_input;
SELECT COUNT(*) FROM orders;

-- Ver métricas disponibles
SELECT DISTINCT metric FROM metrics_input;

-- Top 5 zonas por Perfect Orders
SELECT zone, country, l0w_value
FROM metrics_input
WHERE metric = 'Perfect Orders'
ORDER BY l0w_value DESC
LIMIT 5;
```

## Conectar desde N8N

En tu workflow de N8N, usa el nodo **Supabase** o **Postgres**:

### Opción 1: Nodo Supabase
```
Host: tu-proyecto.supabase.co
Database: postgres
Port: 5432
User: postgres
Password: [tu password de Supabase]
SSL: Enabled
```

### Opción 2: HTTP Request a Supabase REST API
```javascript
// En N8N HTTP Request Node
const url = `${process.env.SUPABASE_URL}/rest/v1/metrics_input`;

const response = await fetch(url, {
  method: 'POST',
  headers: {
    'apikey': process.env.SUPABASE_KEY,
    'Authorization': `Bearer ${process.env.SUPABASE_KEY}`,
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
  },
  body: JSON.stringify({
    select: 'zone,country,l0w_value',
    metric: 'eq.Perfect Orders',
    order: 'l0w_value.desc',
    limit: 5
  })
});
```

## Troubleshooting

### Error: "SUPABASE_URL not set"
Verifica que el archivo `.env` existe en `n8n_workflows/.env` y tiene las credenciales correctas.

### Error: "Could not find Excel file"
El script busca en varias ubicaciones:
- `../../rappi_data.xlsx`
- `../../data/raw/rappi_data.xlsx`
- La ruta especificada en `EXCEL_FILE` del `.env`

Verifica que el archivo existe en alguna de estas ubicaciones.

### Error: "permission denied for table metrics_input"
Estás usando la `anon key` en lugar de la `service_role key`. Usa la service_role key para tener permisos de inserción.

### Error: "relation metrics_input does not exist"
No has ejecutado el SQL de `supabase_schema.sql`. Ve al SQL Editor de Supabase y ejecútalo.

## Próximos pasos

1. ✅ Migrar datos del Excel a Supabase
2. 🔗 Conectar N8N con Supabase
3. 🤖 Actualizar el agente para usar Supabase en lugar de PostgreSQL local
4. 📊 Configurar Streamlit para consultar Supabase

## Notas importantes

- **RLS (Row Level Security)** está habilitado por defecto
- Las políticas permiten acceso a usuarios autenticados
- Los índices están creados para queries rápidas en `country`, `zone`, y `metric`
- Los datos tienen timestamp automático en `created_at`
