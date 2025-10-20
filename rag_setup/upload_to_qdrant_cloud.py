"""
Upload Business Context to Qdrant Cloud
========================================
Este script sube los contextos de negocio a una colección de Qdrant Cloud.
"""
import os
import sys
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from openai import OpenAI
import uuid
from typing import List, Dict

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
QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
COLLECTION_NAME = "rappi_business_context"

# Inicializar clientes (lazy initialization)
openai_client = None
qdrant_client = None

# Datos de contexto de negocio
business_contexts = [
    {
        "title": "% PRO Users Who Breakeven",
        "content": "Usuarios con suscripción Pro cuyo valor generado para la empresa (a través de compras, comisiones, etc.) ha cubierto el costo total de su membresía dividido por el total de usuarios con suscripción Pro.",
        "category": "metrics"
    },
    {
        "title": "% Restaurants Sessions With Optimal Assortment",
        "content": "Sesiones con un mínimo de 40 restaurantes dividido por el total de sesiones.",
        "category": "metrics"
    },
    {
        "title": "Gross Profit UE",
        "content": "Margen bruto de ganancia dividido por el total de órdenes. Indica la rentabilidad por orden.",
        "category": "metrics"
    },
    {
        "title": "Lead Penetration",
        "content": "Tiendas habilitadas en Rappi dividido por (Tiendas previamente identificadas como prospectos (leads) + Tiendas habilitadas + tiendas que salieron de Rappi). Mide la penetración de mercado.",
        "category": "metrics"
    },
    {
        "title": "MLTV Top Verticals Adoption",
        "content": "Usuarios con órdenes en diferentes verticales (restaurantes, super, pharmacy, liquors) dividido por el total de usuarios. Indica adopción multi-vertical.",
        "category": "metrics"
    },
    {
        "title": "Non-Pro PTC > OP",
        "content": "Conversión de usuarios No Pro de 'Proceed to Checkout' a 'Order Placed'. Métrica de conversión de checkout.",
        "category": "metrics"
    },
    {
        "title": "Perfect Orders",
        "content": "Órdenes sin cancelaciones, defectos o demora dividido por el total de órdenes. Indica calidad operacional.",
        "category": "metrics"
    },
    {
        "title": "Pro Adoption",
        "content": "Usuarios con suscripción Pro dividido por el total de usuarios de Rappi. Mide adopción del programa de suscripción.",
        "category": "metrics"
    },
    {
        "title": "Restaurants Markdowns / GMV",
        "content": "Descuentos totales en órdenes de restaurantes dividido por el total Gross Merchandise Value de Restaurantes. Indica nivel de descuentos.",
        "category": "metrics"
    },
    {
        "title": "Restaurants SS > ATC CVR",
        "content": "Conversión en restaurantes de 'Select Store' a 'Add to Cart'. Métrica de conversión en funnel de compra.",
        "category": "metrics"
    },
    {
        "title": "Restaurants SST > SS CVR",
        "content": "Porcentaje de usuarios que después de seleccionar Restaurantes, proceden a seleccionar una tienda en particular. Métrica de conversión de categoría a tienda.",
        "category": "metrics"
    },
    {
        "title": "Retail SST > SS CVR",
        "content": "Porcentaje de usuarios que después de seleccionar Supermercados, proceden a seleccionar una tienda en particular. Métrica de conversión de categoría a tienda.",
        "category": "metrics"
    },
    {
        "title": "Turbo Adoption",
        "content": "Total de usuarios que compran en Turbo (Servicio fast de Rappi) dividido por el total de usuarios de Rappi con tiendas de Turbo disponibles.",
        "category": "metrics"
    },
    {
        "title": "Zone Segmentation",
        "content": "Las zonas se clasifican en Wealthy (zonas ricas) y Non Wealthy (zonas no ricas) según el nivel socioeconómico.",
        "category": "geography"
    },
    {
        "title": "Zone Prioritization",
        "content": "Las zonas tienen tres niveles de priorización: High Priority (alta prioridad), Prioritized (priorizada), Not Prioritized (no priorizada).",
        "category": "geography"
    },
    {
        "title": "Time Series Data",
        "content": "Los datos históricos se almacenan en columnas L8W (hace 8 semanas) hasta L0W (semana actual). L0W siempre representa la semana más reciente.",
        "category": "data_structure"
    },
    {
        "title": "Countries",
        "content": "Rappi opera en 9 países: Argentina (AR), Brasil (BR), Chile (CL), Colombia (CO), Costa Rica (CR), Ecuador (EC), México (MX), Perú (PE), Uruguay (UY).",
        "category": "geography"
    }
]


def create_embedding(text: str) -> List[float]:
    """Genera embedding usando OpenAI"""
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def create_collection():
    """Crea la colección en Qdrant Cloud si no existe"""
    try:
        qdrant_client.get_collection(collection_name=COLLECTION_NAME)
        print(f"✅ Collection '{COLLECTION_NAME}' already exists")
    except:
        print(f"📦 Creating collection '{COLLECTION_NAME}'...")
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
        )
        print(f"✅ Collection created successfully")


def upload_contexts():
    """Sube los contextos de negocio a Qdrant Cloud"""
    print("\n" + "=" * 70)
    print("Uploading Business Context to Qdrant Cloud")
    print("=" * 70)

    # Crear colección
    create_collection()

    # Subir cada contexto
    points = []
    for idx, context in enumerate(business_contexts):
        try:
            # Generar embedding del contenido
            text_to_embed = f"{context['title']}\n\n{context['content']}"
            embedding = create_embedding(text_to_embed)

            # Crear punto
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "title": context["title"],
                    "content": context["content"],
                    "category": context["category"],
                    "type": "business_context"
                }
            )
            points.append(point)

            print(f"✅ [{idx+1}/{len(business_contexts)}] Prepared: {context['title']}")

        except Exception as e:
            print(f"❌ Error preparing {context['title']}: {e}")

    # Subir todos los puntos de una vez
    if points:
        try:
            print(f"\n📤 Uploading {len(points)} points to Qdrant Cloud...")
            qdrant_client.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )
            print(f"✅ Successfully uploaded {len(points)} contexts")
        except Exception as e:
            print(f"❌ Error uploading points: {e}")

    # Verificar
    print("\n[Verification]")
    try:
        collection_info = qdrant_client.get_collection(collection_name=COLLECTION_NAME)
        print(f"✅ Collection: {COLLECTION_NAME}")
        print(f"   Total points: {collection_info.points_count}")
        print(f"   Vector dimension: 1536")

        # Test de búsqueda
        print("\n[Test Search] Searching for 'Perfect Orders'...")
        test_embedding = create_embedding("Perfect Orders")
        results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=test_embedding,
            limit=3
        )

        if results:
            print(f"✅ Found {len(results)} results:")
            for i, result in enumerate(results):
                print(f"   {i+1}. {result.payload.get('title')} (score: {result.score:.3f})")
        else:
            print("⚠️  No results found")

    except Exception as e:
        print(f"❌ Verification error: {e}")

    print("\n" + "=" * 70)
    print("Upload complete!")
    print("=" * 70)
    print(f"\nQdrant Cloud URL: {QDRANT_URL}")
    print(f"Collection Name: {COLLECTION_NAME}")


def upload_content_only():
    """
    Sube SOLO el contenido a Qdrant Cloud.
    Payload mínimo: solo el texto completo en el campo 'content'.
    REEMPLAZA todos los datos anteriores.
    """
    print("\n" + "=" * 70)
    print("Uploading Business Context - CONTENT ONLY FORMAT")
    print("=" * 70)

    # Recrear colección (borra datos anteriores)
    try:
        print(f"🗑️  Deleting existing collection '{COLLECTION_NAME}'...")
        qdrant_client.delete_collection(collection_name=COLLECTION_NAME)
        print(f"✅ Collection deleted")
    except:
        print(f"ℹ️  Collection doesn't exist yet")

    print(f"📦 Creating fresh collection '{COLLECTION_NAME}'...")
    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
    )
    print(f"✅ Collection created")

    # Subir cada contexto con payload mínimo
    points = []
    for idx, context in enumerate(business_contexts):
        try:
            # TODO en un solo texto
            full_content = f"""Título: {context['title']}
Categoría: {context['category']}

Definición:
{context['content']}"""

            # Generar embedding
            embedding = create_embedding(full_content)

            # Payload MÍNIMO - solo el contenido
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "content": full_content  # SOLO esto
                }
            )
            points.append(point)

            print(f"✅ [{idx+1}/{len(business_contexts)}] Prepared: {context['title']}")

        except Exception as e:
            print(f"❌ Error preparing {context['title']}: {e}")

    # Subir
    if points:
        try:
            print(f"\n📤 Uploading {len(points)} points...")
            qdrant_client.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )
            print(f"✅ Successfully uploaded {len(points)} contexts")
        except Exception as e:
            print(f"❌ Error uploading: {e}")

    # Verificar
    print("\n[Verification]")
    try:
        collection_info = qdrant_client.get_collection(collection_name=COLLECTION_NAME)
        print(f"✅ Collection: {COLLECTION_NAME}")
        print(f"   Total points: {collection_info.points_count}")

        # Test
        print("\n[Test Search] Searching for 'Perfect Orders'...")
        test_embedding = create_embedding("Perfect Orders")
        results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=test_embedding,
            limit=3
        )

        if results:
            print(f"✅ Found {len(results)} results:")
            for i, result in enumerate(results):
                content = result.payload.get('content', '')
                print(f"\n   {i+1}. Score: {result.score:.3f}")
                print(f"   {content[:150]}...")
        else:
            print("⚠️  No results found")

    except Exception as e:
        print(f"❌ Verification error: {e}")

    print("\n" + "=" * 70)
    print("Upload complete!")
    print("=" * 70)
    print(f"\nCollection: {COLLECTION_NAME}")
    print(f"Format: payload = {{ 'content': 'texto completo' }}")
    print(f"Total points: {len(points)}")


def main():
    """Main function"""
    global openai_client, qdrant_client

    # Verificar variables de entorno
    if not QDRANT_URL:
        print("❌ QDRANT_URL not set")
        print("   Set it in n8n_workflows/.env file")
        return

    if not QDRANT_API_KEY:
        print("❌ QDRANT_API_KEY not set")
        print("   Set it in n8n_workflows/.env file")
        return

    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not set")
        print("   Set it in n8n_workflows/.env file")
        return

    # Inicializar clientes
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)

        # Intentar conectar con la URL original
        print(f"🔗 Connecting to Qdrant at: {QDRANT_URL}")
        try:
            qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
            # Test connection
            qdrant_client.get_collections()
            print("✅ Clients initialized successfully")
        except Exception as ssl_error:
            # Si falla con SSL error, intentar con el protocolo opuesto
            if "SSL" in str(ssl_error) or "WRONG_VERSION_NUMBER" in str(ssl_error):
                print(f"⚠️  SSL error detected, trying alternate protocol...")
                alternate_url = QDRANT_URL.replace("https://", "http://") if "https://" in QDRANT_URL else QDRANT_URL.replace("http://", "https://")
                print(f"🔗 Trying: {alternate_url}")
                qdrant_client = QdrantClient(url=alternate_url, api_key=QDRANT_API_KEY)
                qdrant_client.get_collections()
                print(f"✅ Connected successfully with {alternate_url}")
                print(f"💡 Update your .env file to use: QDRANT_URL={alternate_url}")
            else:
                raise

    except Exception as e:
        print(f"❌ Error initializing clients: {e}")
        return

    # Llamar a la función de solo contenido
    upload_content_only()


if __name__ == "__main__":
    main()
