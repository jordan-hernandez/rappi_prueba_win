"""
Initialize RAG System for N8N
==============================
Popula Qdrant con:
1. Documentación de métricas
2. DDL schemas
3. SQL queries validadas
"""
import sys
sys.path.append('../..')

from src.vector_store.qdrant_manager import qdrant_manager
from src.database.connection import db_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================
# 1. Business Metrics Documentation
# ==========================================

METRICS_DOCUMENTATION = [
    {
        "title": "Perfect Orders",
        "content": """Perfect Orders es una métrica pre-calculada (0-1 scale) que mide la calidad del servicio.

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

        **Insights**:
        - Comparar países para identificar best practices
        - Detectar zonas con bajo performance
        - Correlacionar con otras métricas (Lead Penetration, Gross Profit)""",
        "category": "business_metric"
    },
    {
        "title": "Lead Penetration",
        "content": """Lead Penetration mide la penetración de mercado de Rappi en cada zona.

        **Definición**: Número de usuarios activos / Población total de la zona

        **Valores típicos**:
        - 50-100: Buena penetración
        - 100-200: Alta penetración
        - >200: Saturación (puede indicar doble conteo)

        **Uso en SQL**:
        ```sql
        SELECT zone, country, l0w_value as lead_penetration
        FROM metrics_input
        WHERE metric = 'Lead Penetration'
          AND l0w_value > 50
        ORDER BY l0w_value DESC;
        ```

        **Insights**:
        - Identificar zonas con potencial de crecimiento
        - Comparar con competencia
        - Proyectar TAM (Total Addressable Market)""",
        "category": "business_metric"
    },
    {
        "title": "Gross Profit UE",
        "content": """Gross Profit per Unit Economics - Ganancia bruta por orden.

        **Definición**: (Revenue - COGS) / Número de órdenes

        **Valores típicos**:
        - Positivo: Zona rentable
        - Negativo: Zona en pérdida (requiere optimización)

        **Uso en SQL**:
        ```sql
        SELECT zone, country,
               l0w_value as current_gross_profit,
               l4w_value as 4weeks_ago,
               (l0w_value - l4w_value) as trend
        FROM metrics_input
        WHERE metric = 'Gross Profit UE'
        ORDER BY l0w_value DESC;
        ```

        **Insights**:
        - Detectar zonas no rentables
        - Analizar tendencias (mejorando o empeorando)
        - Correlacionar con Perfect Orders y Lead Penetration""",
        "category": "business_metric"
    },
    {
        "title": "Pro Adoption",
        "content": """Pro Adoption mide el % de usuarios que usan Rappi Prime/Pro.

        **Definición**: Usuarios Prime / Total usuarios activos

        **Valores** (0-1 scale):
        - 0.3 = 30% de usuarios son Pro
        - 0.5 = 50% (excelente)
        - < 0.2 = Bajo adoption (oportunidad)

        **Uso en SQL**:
        ```sql
        SELECT country,
               AVG(l0w_value) as avg_pro_adoption,
               COUNT(*) as num_zones
        FROM metrics_input
        WHERE metric = 'Pro Adoption'
        GROUP BY country
        ORDER BY avg_pro_adoption DESC;
        ```

        **Insights**:
        - Comparar países para replicar estrategias
        - Identificar zonas con bajo Pro adoption
        - Correlacionar con frecuencia de órdenes""",
        "category": "business_metric"
    },
]

# ==========================================
# 2. DDL Schemas
# ==========================================

DDL_SCHEMAS = [
    {
        "table_name": "metrics_input",
        "ddl": """-- Table: metrics_input (TODAS las métricas de negocio)

CREATE TABLE metrics_input (
    id SERIAL PRIMARY KEY,
    country VARCHAR(10),        -- Country code: MX, CO, BR, CL, AR, PE, EC, CR, UY
    city VARCHAR(100),          -- City name
    zone VARCHAR(200),          -- Zone name
    zone_type VARCHAR(50),      -- Zone classification
    metric VARCHAR(100),        -- ⚠️ CRITICAL: Metric name (MUST filter by this)
    l0w_value NUMERIC(10,4),    -- Current week value
    l1w_value NUMERIC(10,4),    -- 1 week ago
    l2w_value NUMERIC(10,4),    -- 2 weeks ago
    l3w_value NUMERIC(10,4),    -- 3 weeks ago
    l4w_value NUMERIC(10,4),    -- 4 weeks ago
    l5w_value NUMERIC(10,4),    -- 5 weeks ago
    l6w_value NUMERIC(10,4),    -- 6 weeks ago
    l7w_value NUMERIC(10,4),    -- 7 weeks ago
    l8w_value NUMERIC(10,4),    -- 8 weeks ago
    created_at TIMESTAMP DEFAULT NOW()
);

-- Available metrics (MUST use exact names):
-- 'Perfect Orders', 'Lead Penetration', 'Gross Profit UE', 'Pro Adoption',
-- 'Order Frequency', 'AOV', 'Active Users', 'New Users', 'Retention Rate',
-- 'Churn Rate', 'CAC', 'LTV', 'Revenue'

-- ⚠️ CRITICAL RULES:
-- 1. ALL metrics are in this table
-- 2. ALWAYS filter: WHERE metric = 'Exact Metric Name'
-- 3. For trends, use l0w_value, l1w_value, l2w_value, etc.
-- 4. For aggregations, use AVG(), MIN(), MAX(), COUNT()
-- 5. Check NULL: WHERE l0w_value IS NOT NULL

-- Sample data:
-- country | city      | zone          | metric          | l0w_value | l1w_value
-- MX      | Mexico DF | Polanco       | Perfect Orders  | 0.8765    | 0.8543
-- CO      | Bogota    | Chapinero     | Perfect Orders  | 0.8921    | 0.8876
-- MX      | Mexico DF | Polanco       | Lead Penetration| 87.3      | 85.1"""
    },
    {
        "table_name": "orders",
        "ddl": """-- Table: orders (ONLY order counts, NO other metrics)

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    country VARCHAR(10),        -- Country code
    city VARCHAR(100),          -- City name
    zone VARCHAR(200),          -- Zone name
    l0w INTEGER,                -- Current week order count
    l1w INTEGER,                -- 1 week ago order count
    l2w INTEGER,                -- 2 weeks ago
    l3w INTEGER,                -- 3 weeks ago
    l4w INTEGER,                -- 4 weeks ago
    l5w INTEGER,                -- 5 weeks ago
    l6w INTEGER,                -- 6 weeks ago
    l7w INTEGER,                -- 7 weeks ago
    l8w INTEGER,                -- 8 weeks ago
    created_at TIMESTAMP DEFAULT NOW()
);

-- ⚠️ CRITICAL: This table ONLY has order counts
-- For any OTHER metric, use metrics_input table

-- Use this table ONLY for:
-- - Total orders per zone/country
-- - Order volume trends
-- - Order count comparisons

-- Sample data:
-- country | city      | zone      | l0w  | l1w  | l2w
-- MX      | Mexico DF | Polanco   | 1250 | 1180 | 1220
-- CO      | Bogota    | Chapinero | 890  | 875  | 901"""
    }
]

# ==========================================
# 3. Validated SQL Queries (Examples)
# ==========================================

VALIDATED_QUERIES = [
    {
        "question": "Top 5 zonas con mejor Perfect Order",
        "sql": """SELECT zone, country, city, l0w_value as perfect_order_rate
FROM metrics_input
WHERE metric = 'Perfect Orders'
  AND l0w_value IS NOT NULL
ORDER BY l0w_value DESC
LIMIT 5;""",
        "score": 5
    },
    {
        "question": "Compara Perfect Order entre México y Colombia",
        "sql": """SELECT
    country,
    AVG(l0w_value) as avg_perfect_order,
    MIN(l0w_value) as min_perfect_order,
    MAX(l0w_value) as max_perfect_order,
    COUNT(*) as num_zones
FROM metrics_input
WHERE metric = 'Perfect Orders'
  AND country IN ('MX', 'CO')
GROUP BY country
ORDER BY avg_perfect_order DESC;""",
        "score": 5
    },
    {
        "question": "Evolución de Gross Profit UE en las últimas 4 semanas",
        "sql": """SELECT
    zone,
    country,
    l0w_value as week_0,
    l1w_value as week_1,
    l2w_value as week_2,
    l3w_value as week_3,
    (l0w_value - l3w_value) as trend
FROM metrics_input
WHERE metric = 'Gross Profit UE'
  AND l0w_value IS NOT NULL
ORDER BY l0w_value DESC
LIMIT 10;""",
        "score": 5
    },
    {
        "question": "Promedio de Pro Adoption por país",
        "sql": """SELECT
    country,
    AVG(l0w_value) as avg_pro_adoption,
    MIN(l0w_value) as min_pro_adoption,
    MAX(l0w_value) as max_pro_adoption,
    COUNT(DISTINCT zone) as num_zones
FROM metrics_input
WHERE metric = 'Pro Adoption'
  AND l0w_value IS NOT NULL
GROUP BY country
ORDER BY avg_pro_adoption DESC;""",
        "score": 5
    },
    {
        "question": "Zonas con Lead Penetration mayor a 100",
        "sql": """SELECT
    zone,
    country,
    city,
    l0w_value as lead_penetration
FROM metrics_input
WHERE metric = 'Lead Penetration'
  AND l0w_value > 100
ORDER BY l0w_value DESC;""",
        "score": 5
    },
    {
        "question": "Relación entre Perfect Order y Lead Penetration por zona",
        "sql": """SELECT
    m1.zone,
    m1.country,
    m1.l0w_value as perfect_order,
    m2.l0w_value as lead_penetration
FROM metrics_input m1
JOIN metrics_input m2 ON m1.zone = m2.zone AND m1.country = m2.country
WHERE m1.metric = 'Perfect Orders'
  AND m2.metric = 'Lead Penetration'
  AND m1.l0w_value IS NOT NULL
  AND m2.l0w_value IS NOT NULL
ORDER BY m1.l0w_value DESC
LIMIT 20;""",
        "score": 5
    },
]

# ==========================================
# Main Initialization
# ==========================================

def main():
    """Initialize RAG system"""
    print("=" * 70)
    print("Initializing RAG System for N8N Rappi Analytics")
    print("=" * 70)

    # 1. Add Metrics Documentation
    print("\n[Step 1] Adding metrics documentation...")
    for metric in METRICS_DOCUMENTATION:
        try:
            qdrant_manager.add_documentation(
                title=metric["title"],
                content=metric["content"],
                category=metric["category"]
            )
            print(f"✅ Added: {metric['title']}")
        except Exception as e:
            print(f"❌ Error adding {metric['title']}: {e}")

    # 2. Add DDL Schemas
    print("\n[Step 2] Adding DDL schemas...")
    for schema in DDL_SCHEMAS:
        try:
            qdrant_manager.add_ddl(
                ddl_text=schema["ddl"],
                table_name=schema["table_name"]
            )
            print(f"✅ Added DDL: {schema['table_name']}")
        except Exception as e:
            print(f"❌ Error adding DDL {schema['table_name']}: {e}")

    # 3. Add Validated Queries
    print("\n[Step 3] Adding validated SQL queries...")
    for query in VALIDATED_QUERIES:
        try:
            qdrant_manager.add_question_sql(
                question=query["question"],
                sql=query["sql"],
                score=query["score"]
            )
            print(f"✅ Added query: {query['question'][:60]}...")
        except Exception as e:
            print(f"❌ Error adding query: {e}")

    # 4. Verify
    print("\n[Step 4] Verification...")
    try:
        collection_info = qdrant_manager.client.get_collection(
            collection_name=qdrant_manager.collection_name
        )

        print(f"\n✅ RAG System initialized successfully!")
        print(f"   Collection: {qdrant_manager.collection_name}")
        print(f"   Total vectors: {collection_info.points_count}")
        print(f"   Vector dimension: 1536")

        # Test search
        print("\n[Test] Searching for 'Perfect Orders'...")
        results = qdrant_manager.get_related_documentation("Perfect Orders", limit=1)
        if results:
            print(f"✅ RAG search working! Found: {results[0].get('title', 'N/A')}")
        else:
            print("⚠️ No results found")

    except Exception as e:
        print(f"❌ Verification error: {e}")

    print("\n" + "=" * 70)
    print("RAG initialization complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
