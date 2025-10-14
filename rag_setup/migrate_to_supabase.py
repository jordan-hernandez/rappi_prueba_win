"""
Migrate Excel Data to Supabase
================================
Este script migra los datos del Excel a dos tablas en Supabase:
1. metrics_input - Todas las métricas de negocio
2. orders - Conteo de órdenes por zona
"""
import os
import sys
from pathlib import Path
import pandas as pd
from supabase import create_client, Client
from typing import List, Dict
import numpy as np

# Cargar .env
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)
    print(f"✅ Loaded .env from {env_path}")
except ImportError:
    print("⚠️  python-dotenv not installed. Using environment variables only.")
except Exception as e:
    print(f"⚠️  Could not load .env: {e}")

# Configuración
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
EXCEL_FILE = os.getenv("EXCEL_FILE", "../../rappi_data.xlsx")

# Inicializar cliente
supabase: Client = None


def read_excel_data(file_path: str) -> pd.DataFrame:
    """Lee el archivo Excel"""
    print(f"📂 Reading Excel file: {file_path}")

    # Intentar rutas relativas
    paths_to_try = [
        file_path,
        Path(__file__).parent / file_path,
        Path(__file__).parent.parent / file_path,
        Path(__file__).parent.parent.parent / file_path,
        Path(__file__).parent.parent.parent / "rappi_data.xlsx",
        Path(__file__).parent.parent.parent / "data" / "raw" / "rappi_data.xlsx"
    ]

    for path in paths_to_try:
        if Path(path).exists():
            print(f"✅ Found file at: {path}")
            df = pd.read_excel(path)
            print(f"   Shape: {df.shape}")
            print(f"   Columns: {list(df.columns)}")
            return df

    raise FileNotFoundError(f"❌ Could not find Excel file. Tried: {paths_to_try}")


def create_supabase_tables():
    """Crea las tablas en Supabase si no existen"""
    print("\n📋 Creating Supabase tables...")

    # DDL para metrics_input
    metrics_ddl = """
    CREATE TABLE IF NOT EXISTS metrics_input (
        id BIGSERIAL PRIMARY KEY,
        country VARCHAR(10),
        city VARCHAR(100),
        zone VARCHAR(200),
        zone_type VARCHAR(50),
        metric VARCHAR(100),
        l0w_value NUMERIC(10,4),
        l1w_value NUMERIC(10,4),
        l2w_value NUMERIC(10,4),
        l3w_value NUMERIC(10,4),
        l4w_value NUMERIC(10,4),
        l5w_value NUMERIC(10,4),
        l6w_value NUMERIC(10,4),
        l7w_value NUMERIC(10,4),
        l8w_value NUMERIC(10,4),
        created_at TIMESTAMP DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_metrics_input_metric ON metrics_input(metric);
    CREATE INDEX IF NOT EXISTS idx_metrics_input_country ON metrics_input(country);
    CREATE INDEX IF NOT EXISTS idx_metrics_input_zone ON metrics_input(zone);
    """

    # DDL para orders
    orders_ddl = """
    CREATE TABLE IF NOT EXISTS orders (
        id BIGSERIAL PRIMARY KEY,
        country VARCHAR(10),
        city VARCHAR(100),
        zone VARCHAR(200),
        l0w INTEGER,
        l1w INTEGER,
        l2w INTEGER,
        l3w INTEGER,
        l4w INTEGER,
        l5w INTEGER,
        l6w INTEGER,
        l7w INTEGER,
        l8w INTEGER,
        created_at TIMESTAMP DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_orders_country ON orders(country);
    CREATE INDEX IF NOT EXISTS idx_orders_zone ON orders(zone);
    """

    print("⚠️  Note: You need to run these DDL statements in Supabase SQL Editor:")
    print("\n--- METRICS_INPUT TABLE ---")
    print(metrics_ddl)
    print("\n--- ORDERS TABLE ---")
    print(orders_ddl)
    print("\n")


def clean_numeric_value(value):
    """Limpia valores numéricos - maneja strings vacíos y valores inválidos"""
    # Manejar NaN, None, y valores vacíos
    if pd.isna(value) or value is None:
        return None

    # Si es string, limpiar y validar
    if isinstance(value, str):
        value = value.strip()
        # Si está vacío o es placeholder, devolver None
        if value == "" or value.lower() in ['nan', 'null', 'none', 'n/a', '#n/a', '-', '--']:
            return None
        # Intentar convertir string a número
        try:
            value = float(value)
        except (ValueError, TypeError):
            return None

    # Si es número, verificar que sea válido
    if isinstance(value, (int, float)):
        if np.isnan(value) or np.isinf(value):
            return None
        return float(value)

    return None


def clean_string_value(value):
    """Limpia valores de string"""
    if pd.isna(value) or value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value == "" or value.lower() in ['nan', 'null', 'none', 'n/a', '#n/a']:
            return None
        return value
    return str(value) if value else None


def clean_integer_value(value):
    """Limpia valores enteros (para órdenes)"""
    if pd.isna(value) or value is None:
        return None

    # Si es string vacío, devolver None
    if isinstance(value, str):
        value = value.strip()
        if value == "" or value.lower() in ['nan', 'null', 'none', 'n/a', '#n/a', '-', '--']:
            return None
        try:
            value = int(float(value))
        except (ValueError, TypeError):
            return None

    if isinstance(value, (int, float)):
        if np.isnan(value) or np.isinf(value):
            return None
        return int(value)

    return None


def prepare_metrics_data(df: pd.DataFrame) -> List[Dict]:
    """Prepara datos para la tabla metrics_input - compatible con formato RAW_INPUT_METRICS"""
    print("\n📊 Preparing metrics_input data...")

    # Convertir columnas a minúsculas
    df.columns = df.columns.str.lower()

    # Mapeo de columnas _roll a _value (igual que en migrate.py)
    column_mapping = {
        'l8w_roll': 'l8w_value',
        'l7w_roll': 'l7w_value',
        'l6w_roll': 'l6w_value',
        'l5w_roll': 'l5w_value',
        'l4w_roll': 'l4w_value',
        'l3w_roll': 'l3w_value',
        'l2w_roll': 'l2w_value',
        'l1w_roll': 'l1w_value',
        'l0w_roll': 'l0w_value',
    }

    df = df.rename(columns=column_mapping)

    # Columnas del schema
    schema_columns = [
        'country', 'city', 'zone', 'zone_type', 'zone_prioritization', 'metric',
        'l8w_value', 'l7w_value', 'l6w_value', 'l5w_value', 'l4w_value',
        'l3w_value', 'l2w_value', 'l1w_value', 'l0w_value'
    ]

    # Filtrar solo columnas disponibles
    available_columns = [col for col in schema_columns if col in df.columns]

    print(f"   Available columns: {available_columns}")
    print(f"   Total rows: {len(df)}")

    # Filtrar DataFrame
    df_filtered = df[available_columns].copy()

    # Convertir a lista de diccionarios con limpieza
    records = []
    for _, row in df_filtered.iterrows():
        record = {}
        for col in available_columns:
            value = row.get(col)

            # Limpiar según el tipo de columna
            if 'value' in col or any(x in col for x in ['l0w', 'l1w', 'l2w', 'l3w', 'l4w', 'l5w', 'l6w', 'l7w', 'l8w']):
                # Columna numérica
                record[col] = clean_numeric_value(value)
            else:
                # Columna string
                record[col] = clean_string_value(value)

        records.append(record)

    print(f"   Total records before deduplication: {len(records)}")

    # Deduplicar por (country, zone, metric) - mantener el último
    seen_keys = {}
    for record in records:
        key = (record.get('country'), record.get('zone'), record.get('metric'))
        # Mantener el último registro para cada key (sobrescribe si existe)
        seen_keys[key] = record

    deduplicated_records = list(seen_keys.values())

    print(f"   Total records after deduplication: {len(deduplicated_records)}")
    print(f"   Removed {len(records) - len(deduplicated_records)} duplicates from source data")

    return deduplicated_records


def prepare_orders_data(df: pd.DataFrame) -> List[Dict]:
    """Prepara datos para la tabla orders - compatible con formato RAW_ORDERS"""
    print("\n📦 Preparing orders data...")

    # Convertir columnas a minúsculas
    df.columns = df.columns.str.lower()

    # Columnas del schema
    schema_columns = [
        'country', 'city', 'zone',
        'l8w', 'l7w', 'l6w', 'l5w', 'l4w', 'l3w', 'l2w', 'l1w', 'l0w'
    ]

    # Filtrar solo columnas disponibles
    available_columns = [col for col in schema_columns if col in df.columns]

    print(f"   Available columns: {available_columns}")
    print(f"   Total rows: {len(df)}")

    # Filtrar DataFrame
    df_filtered = df[available_columns].copy()

    # Convertir a lista de diccionarios con limpieza
    records = []
    for _, row in df_filtered.iterrows():
        record = {}
        for col in available_columns:
            value = row.get(col)

            # Limpiar según el tipo de columna
            if col.startswith('l') and col.endswith('w'):
                # Columna de órdenes (entero)
                record[col] = clean_integer_value(value)
            else:
                # Columna string
                record[col] = clean_string_value(value)

        records.append(record)

    print(f"   Total records before deduplication: {len(records)}")

    # Deduplicar por (country, zone) - mantener el último
    seen_keys = {}
    for record in records:
        key = (record.get('country'), record.get('zone'))
        # Mantener el último registro para cada key
        seen_keys[key] = record

    deduplicated_records = list(seen_keys.values())

    print(f"   Total records after deduplication: {len(deduplicated_records)}")
    print(f"   Removed {len(records) - len(deduplicated_records)} duplicates from source data")

    return deduplicated_records


def clear_table(table_name: str):
    """Limpia una tabla antes de insertar (opcional)"""
    try:
        print(f"🗑️  Clearing table {table_name}...")
        # Eliminar todos los registros
        supabase.table(table_name).delete().neq('id', 0).execute()
        print(f"   ✅ Table {table_name} cleared")
    except Exception as e:
        print(f"   ⚠️  Could not clear table: {e}")


def upload_to_supabase(table_name: str, data: List[Dict], batch_size: int = 100, use_upsert: bool = True):
    """Sube datos a Supabase en batches usando UPSERT para evitar duplicados"""
    print(f"\n📤 Uploading {len(data)} records to {table_name}...")
    print(f"   Mode: {'UPSERT (replaces duplicates)' if use_upsert else 'INSERT (may create duplicates)'}")

    total_uploaded = 0
    errors = 0
    error_details = []

    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        try:
            if use_upsert:
                # UPSERT sin on_conflict (Supabase upsert por defecto usa primary key)
                # Como no tenemos primary key en los datos, necesitamos otro approach
                # Solución: usar .upsert() sin parámetros (usa ignoring duplicates)
                response = supabase.table(table_name).upsert(batch, ignore_duplicates=False).execute()
            else:
                # INSERT simple
                response = supabase.table(table_name).insert(batch).execute()

            total_uploaded += len(batch)
            print(f"   ✅ Uploaded batch {i//batch_size + 1}/{(len(data)-1)//batch_size + 1}: {len(batch)} records")

        except Exception as e:
            errors += len(batch)
            error_msg = str(e)
            print(f"   ❌ Error uploading batch {i//batch_size + 1}: {error_msg[:100]}")
            error_details.append({
                'batch': i//batch_size + 1,
                'error': error_msg,
                'sample_record': batch[0] if batch else None
            })

    print(f"\n✅ Upload complete:")
    print(f"   Total uploaded: {total_uploaded}")
    print(f"   Errors: {errors}")

    if error_details:
        print(f"\n⚠️  Error details (first 3):")
        for detail in error_details[:3]:
            print(f"   Batch {detail['batch']}: {detail['error'][:150]}")
            if detail['sample_record']:
                print(f"      Sample: {detail['sample_record']}")


def verify_upload():
    """Verifica los datos subidos"""
    print("\n🔍 Verifying upload...")

    try:
        # Contar registros en metrics_input
        metrics_count = supabase.table('metrics_input').select('id', count='exact').execute()
        print(f"   metrics_input: {metrics_count.count} records")

        # Contar registros en orders
        orders_count = supabase.table('orders').select('id', count='exact').execute()
        print(f"   orders: {orders_count.count} records")

        # Muestra de datos
        print("\n   Sample from metrics_input:")
        sample = supabase.table('metrics_input').select('*').limit(3).execute()
        for row in sample.data:
            print(f"      {row.get('country')} - {row.get('zone')} - {row.get('metric')}: {row.get('l0w_value')}")

    except Exception as e:
        print(f"❌ Error verifying: {e}")


def main():
    """Main function"""
    global supabase

    print("=" * 70)
    print("Migrate Excel Data to Supabase")
    print("=" * 70)

    # Verificar variables de entorno
    if not SUPABASE_URL:
        print("❌ SUPABASE_URL not set")
        print("   Set it in n8n_workflows/.env file")
        return

    if not SUPABASE_KEY:
        print("❌ SUPABASE_KEY not set")
        print("   Set it in n8n_workflows/.env file")
        return

    # Inicializar cliente Supabase
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(f"✅ Connected to Supabase: {SUPABASE_URL}")
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {e}")
        return

    # Mostrar DDL
    create_supabase_tables()

    # Leer Excel - Sheet RAW_INPUT_METRICS
    try:
        print("\n📂 Reading sheet 'RAW_INPUT_METRICS'...")
        df_metrics = read_excel_data(EXCEL_FILE)
    except Exception as e:
        print(f"❌ Error reading metrics sheet: {e}")
        return

    # Leer Excel - Sheet RAW_ORDERS
    try:
        print("\n📂 Reading sheet 'RAW_ORDERS'...")
        excel_path = Path(__file__).parent.parent.parent / "rappi_data.xlsx"
        df_orders = pd.read_excel(excel_path, sheet_name="RAW_ORDERS")
        print(f"   Shape: {df_orders.shape}")
        print(f"   Columns: {list(df_orders.columns)}")
    except Exception as e:
        print(f"⚠️  Could not read RAW_ORDERS sheet: {e}")
        print(f"   Will skip orders migration")
        df_orders = None

    # Preguntar al usuario
    print("\n⚠️  This will upload data to Supabase. Continue? (y/n)")
    response = input().strip().lower()
    if response != 'y':
        print("❌ Cancelled by user")
        return

    # Opción para limpiar tabla antes de insertar (evita duplicados)
    print("\n⚠️  Do you want to clear existing data before uploading? (y/n)")
    print("   (Recommended if re-running the script)")
    clear_response = input().strip().lower()
    if clear_response == 'y':
        clear_table('metrics_input')

    # Preparar y subir datos de métricas (usar INSERT sin upsert por limitación de Supabase client)
    metrics_data = prepare_metrics_data(df_metrics)
    if metrics_data:
        upload_to_supabase('metrics_input', metrics_data, use_upsert=False)

    # Preparar y subir datos de órdenes
    if df_orders is not None:
        orders_data = prepare_orders_data(df_orders)
        if orders_data:
            if clear_response == 'y':
                clear_table('orders')
            upload_to_supabase('orders', orders_data, use_upsert=False)
    else:
        print("\n⚠️  Skipping orders migration (sheet not found)")

    # Verificar
    verify_upload()

    print("\n" + "=" * 70)
    print("Migration complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
