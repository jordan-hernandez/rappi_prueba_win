# Guía de Migración a Supabase

## ✨ Características principales

### 1. ✅ UPSERT automático (evita duplicados)
- Si ejecutas el script múltiples veces, **no se crearán duplicados**
- Los datos se actualizan en lugar de duplicarse
- Usa constraint único en `country + zone + metric` para `metrics_input`
- Usa constraint único en `country + zone` para `orders`

### 2. 🧹 Limpieza de datos
El script maneja automáticamente:
- ❌ Strings vacíos `""` → convertidos a `NULL`
- ❌ Valores `"NaN"`, `"null"`, `"none"`, `"N/A"`, `"#N/A"` → `NULL`
- ❌ Valores infinitos o inválidos → `NULL`
- ✅ Conversión automática de strings a números
- ✅ Conversión de decimales a enteros para órdenes

### 3. 📊 Detección inteligente de columnas
El script detecta automáticamente diferentes formatos de Excel:
- `Perfect_Orders_l0w`, `Perfect_Orders_l1w`, etc.
- `l0w_Perfect_Orders`, `l1w_Perfect_Orders`, etc.
- `Perfect_Orders` (valor único para L0W)

## 🚀 Uso rápido

```bash
# 1. Ejecutar el SQL en Supabase
# Copia y pega supabase_schema.sql en Supabase SQL Editor

# 2. Configurar .env
cd n8n_workflows
# Editar .env con SUPABASE_URL, SUPABASE_KEY, EXCEL_FILE

# 3. Ejecutar migración
cd rag_setup
python migrate_to_supabase.py
```

## 📋 Pasos detallados

### Paso 1: Crear tablas en Supabase

1. Abre tu proyecto en [Supabase](https://supabase.com)
2. Ve a **SQL Editor**
3. Copia y ejecuta todo el contenido de [`supabase_schema.sql`](supabase_schema.sql)
4. Verifica que se crearon las tablas:
   ```sql
   SELECT table_name FROM information_schema.tables
   WHERE table_schema = 'public';
   ```

### Paso 2: Configurar credenciales

Edita `n8n_workflows/.env`:

```env
# Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-service-role-key

# Excel
EXCEL_FILE=../../rappi_data.xlsx
```

**⚠️ Importante**: Usa el `service_role` key (no el `anon` key) para tener permisos de escritura.

### Paso 3: Ejecutar migración

```bash
cd n8n_workflows/rag_setup
python migrate_to_supabase.py
```

El script te preguntará si quieres continuar antes de subir datos.

## 🔄 UPSERT vs INSERT

El script usa **UPSERT por defecto**, lo que significa:

```python
# Primera ejecución
upload_to_supabase('metrics_input', data)  # Inserta 1000 registros

# Segunda ejecución (mismo Excel)
upload_to_supabase('metrics_input', data)  # Actualiza los 1000 registros existentes
                                            # NO crea duplicados ✅
```

### ¿Cómo funciona?

El UPSERT se basa en **unique constraints**:

**Para `metrics_input`:**
- Combinación única: `(country, zone, metric)`
- Si existe un registro con la misma combinación → **actualiza**
- Si no existe → **inserta nuevo**

**Para `orders`:**
- Combinación única: `(country, zone)`
- Si existe → **actualiza**
- Si no existe → **inserta nuevo**

## 🧪 Ejemplo de datos limpios

### Antes (en Excel)
```
country | zone    | Perfect Orders | Lead Penetration
MX      | Polanco | "0.87"        | ""
CO      |         | NaN           | "123.4"
BR      | Centro  | 0.92          | N/A
```

### Después (en Supabase)
```sql
country | zone    | metric            | l0w_value
--------|---------|-------------------|----------
MX      | Polanco | Perfect Orders    | 0.87
MX      | Polanco | Lead Penetration  | NULL
CO      | NULL    | Perfect Orders    | NULL
CO      | NULL    | Lead Penetration  | 123.4
BR      | Centro  | Perfect Orders    | 0.92
BR      | Centro  | Lead Penetration  | NULL
```

## 📊 Estructura de datos

### Tabla `metrics_input`

```sql
CREATE TABLE metrics_input (
    id BIGSERIAL PRIMARY KEY,
    country VARCHAR(10),      -- MX, CO, BR, etc.
    city VARCHAR(100),
    zone VARCHAR(200),
    zone_type VARCHAR(50),
    metric VARCHAR(100),      -- Perfect Orders, Lead Penetration, etc.
    l0w_value NUMERIC(10,4),  -- Semana actual
    l1w_value NUMERIC(10,4),  -- 1 semana atrás
    ...
    l8w_value NUMERIC(10,4),  -- 8 semanas atrás
    created_at TIMESTAMP
);

-- Unique constraint
UNIQUE (country, zone, metric);
```

### Tabla `orders`

```sql
CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    country VARCHAR(10),
    city VARCHAR(100),
    zone VARCHAR(200),
    l0w INTEGER,              -- Órdenes semana actual
    l1w INTEGER,              -- 1 semana atrás
    ...
    l8w INTEGER,              -- 8 semanas atrás
    created_at TIMESTAMP
);

-- Unique constraint
UNIQUE (country, zone);
```

## 🔍 Verificación

Después de la migración, verifica en Supabase:

```sql
-- Contar registros
SELECT COUNT(*) FROM metrics_input;
SELECT COUNT(*) FROM orders;

-- Ver métricas disponibles
SELECT DISTINCT metric FROM metrics_input ORDER BY metric;

-- Top 5 zonas por Perfect Orders
SELECT zone, country, l0w_value
FROM metrics_input
WHERE metric = 'Perfect Orders'
  AND l0w_value IS NOT NULL
ORDER BY l0w_value DESC
LIMIT 5;

-- Verificar que no hay duplicados
SELECT country, zone, metric, COUNT(*)
FROM metrics_input
GROUP BY country, zone, metric
HAVING COUNT(*) > 1;
-- Debería retornar 0 filas ✅
```

## ⚠️ Solución de problemas

### Error: "duplicate key value violates unique constraint"

**Causa**: Intentas hacer INSERT en lugar de UPSERT y ya existen los datos.

**Solución**:
```python
# Opción 1: Usar UPSERT (recomendado)
upload_to_supabase('metrics_input', data, use_upsert=True)

# Opción 2: Limpiar tabla antes
clear_table('metrics_input')
upload_to_supabase('metrics_input', data, use_upsert=False)
```

### Error: "invalid input syntax for type double precision"

**Causa**: Hay strings vacíos `""` en columnas numéricas.

**Solución**: ✅ Ya está manejado en el script con `clean_numeric_value()` y `clean_integer_value()`

### Error: "permission denied for table metrics_input"

**Causa**: Estás usando `anon key` en lugar de `service_role key`.

**Solución**: En Supabase → Settings → API → Copia el **service_role key**

### Excel no encontrado

**Solución**: El script busca en:
1. La ruta en `EXCEL_FILE` del `.env`
2. `../../rappi_data.xlsx`
3. `../../data/raw/rappi_data.xlsx`

Verifica que tu Excel esté en alguna de estas rutas.

## 🔄 Re-ejecutar la migración

Puedes ejecutar el script múltiples veces sin problema:

```bash
# Primera vez: inserta todos los datos
python migrate_to_supabase.py

# Segunda vez: actualiza los datos existentes (NO duplica)
python migrate_to_supabase.py

# Tercera vez: actualiza nuevamente
python migrate_to_supabase.py
```

Cada ejecución **actualiza** los registros existentes con los nuevos valores del Excel.

## 📝 Notas importantes

1. **UPSERT está habilitado por defecto** - No se crearán duplicados
2. **Los valores vacíos se convierten a NULL** - No habrá errores de tipo
3. **Las constraints únicas están definidas en el SQL** - Asegúrate de ejecutar `supabase_schema.sql` primero
4. **El script es idempotente** - Puedes ejecutarlo cuantas veces quieras

## 🎯 Siguiente paso

Una vez migrados los datos, actualiza tu API de N8N para conectar con Supabase:

```python
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Query metrics
response = supabase.table('metrics_input')\
    .select('zone, country, l0w_value')\
    .eq('metric', 'Perfect Orders')\
    .order('l0w_value', desc=True)\
    .limit(5)\
    .execute()

results = response.data
```
