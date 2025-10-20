import streamlit as st
import requests
import json
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
import pandas as pd
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Rappi Analytics Chat",
    page_icon="🛵",
    layout="wide"
)

# Función para preprocesar los datos de visualización
def preprocess_chart_data(viz_data):
    """
    Preprocesa los datos de visualización del webhook para generar gráficos correctos.
    
    Args:
        viz_data: Diccionario con los datos de visualización del webhook
        
    Returns:
        Diccionario con la estructura corregida para Plotly
    """
    try:
        if not viz_data or not viz_data.get("success"):
            return None
            
        chart_json = viz_data.get("chart_json")
        if not chart_json:
            return None
            
        # Parsear el JSON
        if isinstance(chart_json, str):
            chart_dict = json.loads(chart_json)
        else:
            chart_dict = chart_json
            
        # Verificar si los datos necesitan preprocesamiento
        if "data" in chart_dict and len(chart_dict["data"]) > 0:
            first_trace = chart_dict["data"][0]
            
            # Detectar si los datos X son objetos complejos (problema principal)
            if "x" in first_trace and len(first_trace["x"]) > 0:
                first_x = first_trace["x"][0]
                
                # Si X contiene objetos complejos, necesitamos preprocesarlos
                if isinstance(first_x, dict) and any(key in first_x for key in ["zone", "city", "country"]):
                    return preprocess_complex_data(chart_dict)
        
        return chart_dict
        
    except Exception as e:
        st.error(f"Error en preprocesamiento: {str(e)}")
        return None


def preprocess_complex_data(chart_dict):
    """
    Preprocesa datos complejos donde X e Y son objetos JSON.
    
    Args:
        chart_dict: Diccionario original del gráfico
        
    Returns:
        Diccionario con datos corregidos
    """
    try:
        original_data = chart_dict["data"][0]
        raw_x_data = original_data.get("x", [])
        
        # Extraer datos de los objetos complejos
        zones = []
        lead_penetration = []
        perfect_order = []
        countries = []
        cities = []
        
        for item in raw_x_data:
            if isinstance(item, dict):
                # Crear etiqueta descriptiva
                zone_label = f"{item.get('zone', 'N/A')}"
                city = item.get('city', '')
                country = item.get('country', '')
                
                if city:
                    zone_label += f", {city}"
                    
                zones.append(zone_label)
                countries.append(country)
                cities.append(city)
                
                # Extraer valores numéricos
                lead_val = float(item.get('lead_penetration_value', 0))
                perfect_val = float(item.get('perfect_order_value', 0)) * 100
                
                lead_penetration.append(lead_val)
                perfect_order.append(perfect_val)
        
        # Determinar tipo de gráfico basado en los datos
        chart_type = original_data.get("type", "bar")
        
        # Crear nueva estructura de datos
        new_data = []
        
        if chart_type == "bar":
            # Gráfico de barras agrupadas para comparar ambas métricas
            new_data = [
                {
                    "x": zones,
                    "y": lead_penetration,
                    "type": "bar",
                    "name": "Lead Penetration (%)",
                    "marker": {"color": "#FF6B35", "opacity": 0.8},
                    "text": [f"{v:.1f}%" for v in lead_penetration],
                    "textposition": "auto",
                    "hovertemplate": "<b>%{x}</b><br>Lead Penetration: %{y:.1f}%<extra></extra>"
                },
                {
                    "x": zones,
                    "y": perfect_order,
                    "type": "bar",
                    "name": "Perfect Order (%)",
                    "marker": {"color": "#4CAF50", "opacity": 0.8},
                    "text": [f"{v:.1f}%" for v in perfect_order],
                    "textposition": "auto",
                    "hovertemplate": "<b>%{x}</b><br>Perfect Order: %{y:.1f}%<extra></extra>"
                }
            ]
        
        # Actualizar layout
        new_layout = chart_dict.get("layout", {})
        new_layout.update({
            "xaxis": {
                "title": "Zona",
                "tickangle": -45,
                "gridcolor": "#E0E0E0"
            },
            "yaxis": {
                "title": "Porcentaje (%)",
                "gridcolor": "#E0E0E0"
            },
            "barmode": "group",
            "paper_bgcolor": "#FAFAFA",
            "plot_bgcolor": "white",
            "margin": {"t": 80, "r": 30, "l": 60, "b": 140},
            "font": {"family": "Arial, sans-serif"},
            "showlegend": True,
            "height": 500,
            "hovermode": "x unified"
        })
        
        # Mantener el título original si existe
        if "title" in chart_dict.get("layout", {}):
            new_layout["title"] = chart_dict["layout"]["title"]
            if isinstance(new_layout["title"], dict):
                new_layout["title"]["text"] = "Lead Penetration vs Perfect Order por Zona"
        
        return {
            "data": new_data,
            "layout": new_layout,
            "config": chart_dict.get("config", {
                "responsive": True,
                "displayModeBar": True,
                "displaylogo": False
            })
        }
        
    except Exception as e:
        st.error(f"Error procesando datos complejos: {str(e)}")
        return chart_dict


def extract_data_table_from_chart(viz_data):
    """
    Extrae una tabla de datos del JSON de visualización.
    
    Args:
        viz_data: Diccionario con los datos de visualización
        
    Returns:
        DataFrame con los datos extraídos o None
    """
    try:
        chart_json = viz_data.get("chart_json")
        if not chart_json:
            return None
            
        if isinstance(chart_json, str):
            chart_dict = json.loads(chart_json)
        else:
            chart_dict = chart_json
            
        if "data" in chart_dict and len(chart_dict["data"]) > 0:
            first_trace = chart_dict["data"][0]
            
            if "x" in first_trace and len(first_trace["x"]) > 0:
                first_x = first_trace["x"][0]
                
                # Si X contiene objetos complejos, extraer tabla
                if isinstance(first_x, dict):
                    raw_data = first_trace["x"]
                    df = pd.DataFrame(raw_data)
                    
                    # Renombrar columnas para mejor legibilidad
                    column_rename = {
                        "country": "País",
                        "city": "Ciudad", 
                        "zone": "Zona",
                        "lead_penetration_value": "Lead Penetration",
                        "perfect_order_value": "Perfect Order"
                    }
                    df = df.rename(columns=column_rename)
                    
                    # Convertir valores a numéricos y formatear
                    if "Lead Penetration" in df.columns:
                        df["Lead Penetration"] = pd.to_numeric(df["Lead Penetration"], errors='coerce')
                        df["Lead Penetration (%)"] = df["Lead Penetration"].round(1)
                        
                    if "Perfect Order" in df.columns:
                        df["Perfect Order"] = pd.to_numeric(df["Perfect Order"], errors='coerce')
                        df["Perfect Order (%)"] = (df["Perfect Order"] * 100).round(1)
                        
                    return df
                    
        return None
        
    except Exception as e:
        return None


def send_feedback(question, sql_query, feedback_score, user_id, results):
    """
    Envía feedback al webhook de N8N.
    
    Args:
        question: La pregunta original
        sql_query: La consulta SQL
        feedback_score: Score de 1-5
        user_id: ID del usuario
        results: Resultados de la consulta
        
    Returns:
        Respuesta del webhook
    """
    try:
        payload = {
            "question": question,
            "sql_query": sql_query,
            "feedback_score": feedback_score,
            "user_id": user_id,
            "execution_time": datetime.now().isoformat(),
            "row_count": len(results),
            "results": results[:3] if results else []  # Solo primeros 3 resultados
        }
        
        # Usar el webhook de feedback
        feedback_url = "https://sswebhookss.gaussiana.io/webhook/rappi-feedback"
        response = requests.post(
            feedback_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Webhook URL
WEBHOOK_URL = "https://sswebhookss.gaussiana.io/webhook/604b1f14-eacb-4f33-91c7-60a914831b3c"
#"https://sswebhookss.gaussiana.io/webhook/rappi-analytics"

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_id" not in st.session_state:
    st.session_state.user_id = "streamlit_user"

# Header
st.title("🛵 Rappi Analytics Agent")
st.markdown("**Pregunta cualquier cosa sobre las métricas de Rappi y obtén respuestas basadas en datos reales**")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuración")
    st.session_state.user_id = st.text_input("User ID", value=st.session_state.user_id)

    st.markdown("---")
    st.markdown("### 💡 Ejemplos de preguntas:")
    st.markdown("""
    - ¿Cuál es el país con mejor Perfect Orders?
    - Muestra la evolución de Gross Profit UE en México
    - ¿Qué zonas tienen mejor Lead Penetration?
    - Compara Pro Adoption entre países
    - Top 5 ciudades por órdenes
    """)

    if st.button("🗑️ Limpiar historial"):
        st.session_state.messages = []
        st.rerun()

# Display chat messages
for msg_idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # Show additional data if available
        if "data" in message:
            data = message["data"]

            # Business Value Scores
            if "business_value" in data:
                bv = data["business_value"]
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📊 Score General", f"{bv.get('overall_score', 0):.1f}/10")
                with col2:
                    time_saved = bv.get('time_saved_minutes', 'N/A')
                    st.metric("⏱️ Tiempo Ahorrado", f"{time_saved} min" if time_saved != 'N/A' else 'N/A')
                with col3:
                    st.metric("🔄 Iteraciones", bv.get('improvement_iterations', 0))

                # Only show details if there are criteria scores
                if bv.get('criteria_scores') and len(bv['criteria_scores']) > 0:
                    with st.expander("📈 Detalles de evaluación"):
                        if 'business_impact' in bv:
                            st.write(f"**Impacto:** {bv['business_impact']}")
                        st.write("**Scores por criterio:**")
                        scores = bv['criteria_scores']
                        for key, value in scores.items():
                            st.progress(value / 10, text=f"{key.replace('_', ' ').title()}: {value}/10")

            # Show SQL Query
            if "sql_query" in data:
                with st.expander("🔍 Ver SQL Query"):
                    st.code(data["sql_query"], language="sql")

            # Show Results Table - extract json objects from N8N format
            if "results" in data and len(data["results"]) > 0:
                row_count = data.get('row_count', len(data['results']))
                with st.expander(f"📋 Ver datos ({row_count} filas)"):
                    # Extract the 'json' field from each result object
                    data_rows = [item.get('json', item) for item in data['results']]
                    df = pd.DataFrame(data_rows)
                    st.dataframe(df, width='stretch')

            # Show Visualization (only if it exists and was successful)
            if "visualization" in data and data["visualization"]:
                viz = data["visualization"]
                if viz.get("success") and viz.get("chart_json"):
                    try:
                        # Preprocesar los datos antes de renderizar
                        processed_chart = preprocess_chart_data(viz)
                        
                        if processed_chart:
                            st.markdown("### 📊 Visualización")
                            fig = go.Figure(processed_chart)
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Mostrar tabla de datos extraída del gráfico
                            extracted_df = extract_data_table_from_chart(viz)
                            if extracted_df is not None and not extracted_df.empty:
                                with st.expander("📋 Ver datos de la visualización"):
                                    # Seleccionar columnas relevantes
                                    display_cols = [col for col in extracted_df.columns if col in 
                                                  ["País", "Ciudad", "Zona", "Lead Penetration (%)", "Perfect Order (%)"]]
                                    if display_cols:
                                        st.dataframe(extracted_df[display_cols], use_container_width=True)
                            
                            # Mostrar estadísticas del gráfico
                            if viz.get("data_points"):
                                st.caption(f"📊 {viz.get('data_points', 0)} zonas analizadas")
                        else:
                            st.warning("⚠️ No se pudo procesar la visualización")
                            
                    except Exception as e:
                        st.warning(f"⚠️ Error al renderizar gráfica: {str(e)}")
                        # Show the raw chart_json for debugging
                        with st.expander("🔍 Debug: Ver JSON de gráfica"):
                            st.json(viz.get("chart_json"))
            
            # Feedback Component
            if "data" in message and "sql_query" in message["data"]:
                st.markdown("---")
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown("**¿Te fue útil esta respuesta?**")
                    feedback_score = st.radio(
                        "Califica:",
                        options=[1, 2, 3, 4, 5],
                        format_func=lambda x: "⭐" * x,
                        horizontal=True,
                        key=f"feedback_score_msg_{msg_idx}",
                        label_visibility="collapsed"
                    )
                
                with col2:
                    if st.button("👍 Enviar", key=f"submit_feedback_msg_{msg_idx}", type="secondary"):
                        result = send_feedback(
                            question=message["content"],
                            sql_query=message["data"]["sql_query"],
                            feedback_score=feedback_score,
                            user_id=st.session_state.user_id,
                            results=message["data"].get("results", [])
                        )
                        
                        if result.get("success"):
                            if result.get("stored_in_vector_db"):
                                st.success("✅ Guardado para aprendizaje!")
                            else:
                                st.success("✅ Gracias!")
                        else:
                            st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
                
                with col3:
                    if feedback_score >= 4:
                        st.caption("💾 Se guardará")

# Chat input
if prompt := st.chat_input("Escribe tu pregunta sobre las métricas de Rappi..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response with loading
    with st.chat_message("assistant"):
        with st.spinner("🤔 Analizando tu pregunta y consultando la base de datos..."):
            try:
                # Prepare request payload
                payload = {
                    "chatInput": prompt,
                    "sessionId": st.session_state.user_id,
                    "user_context": "Streamlit Chat Interface"
                }

                # Call webhook
                response = requests.post(
                    WEBHOOK_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=120  # 2 minutes timeout
                )

                if response.status_code == 200:
                    result = response.json()

                    if result.get("success"):
                        # Display formatted response
                        answer = result.get("answer", "No se generó una respuesta.")
                        st.markdown(answer)

                        # Store message with data
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer,
                            "data": result
                        })

                        # Display business value
                        if "business_value" in result:
                            bv = result["business_value"]
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("📊 Score General", f"{bv.get('overall_score', 0):.1f}/10")
                            with col2:
                                time_saved = bv.get('time_saved_minutes', 'N/A')
                                st.metric("⏱️ Tiempo Ahorrado", f"{time_saved} min" if time_saved != 'N/A' else 'N/A')
                            with col3:
                                st.metric("🔄 Iteraciones", bv.get('improvement_iterations', 0))

                            # Only show details if there are criteria scores
                            if bv.get('criteria_scores') and len(bv['criteria_scores']) > 0:
                                with st.expander("📈 Detalles de evaluación"):
                                    if 'business_impact' in bv:
                                        st.write(f"**Impacto:** {bv['business_impact']}")
                                    st.write("**Scores por criterio:**")
                                    scores = bv['criteria_scores']
                                    for key, value in scores.items():
                                        st.progress(value / 10, text=f"{key.replace('_', ' ').title()}: {value}/10")

                        # Show SQL Query
                        if "sql_query" in result:
                            with st.expander("🔍 Ver SQL Query"):
                                st.code(result["sql_query"], language="sql")

                        # Show Results Table - extract json objects from N8N format
                        if "results" in result and len(result["results"]) > 0:
                            row_count = result.get('row_count', len(result['results']))
                            with st.expander(f"📋 Ver datos ({row_count} filas)"):
                                # Extract the 'json' field from each result object
                                data_rows = [item.get('json', item) for item in result['results']]
                                df = pd.DataFrame(data_rows)
                                st.dataframe(df, width='stretch')

                        # Show Visualization (only if it exists and was successful)
                        if "visualization" in result and result["visualization"]:
                            viz = result["visualization"]
                            if viz.get("success") and viz.get("chart_json"):
                                try:
                                    # Preprocesar los datos antes de renderizar
                                    processed_chart = preprocess_chart_data(viz)
                                    
                                    if processed_chart:
                                        st.markdown("### 📊 Visualización")
                                        fig = go.Figure(processed_chart)
                                        st.plotly_chart(fig, use_container_width=True)
                                        
                                        # Mostrar tabla de datos extraída del gráfico
                                        extracted_df = extract_data_table_from_chart(viz)
                                        if extracted_df is not None and not extracted_df.empty:
                                            with st.expander("📋 Ver datos de la visualización"):
                                                # Seleccionar columnas relevantes
                                                display_cols = [col for col in extracted_df.columns if col in 
                                                              ["País", "Ciudad", "Zona", "Lead Penetration (%)", "Perfect Order (%)"]]
                                                if display_cols:
                                                    st.dataframe(extracted_df[display_cols], use_container_width=True)
                                        
                                        # Mostrar estadísticas del gráfico
                                        if viz.get("data_points"):
                                            st.caption(f"📊 {viz.get('data_points', 0)} zonas analizadas")
                                    else:
                                        st.warning("⚠️ No se pudo procesar la visualización")
                                        
                                except Exception as e:
                                    st.warning(f"⚠️ Error al renderizar gráfica: {str(e)}")
                                    # Show the raw chart_json for debugging
                                    with st.expander("🔍 Debug: Ver JSON de gráfica"):
                                        st.json(viz.get("chart_json"))
                        
                        # Feedback Component
                        st.markdown("---")
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.markdown("**¿Te fue útil esta respuesta?**")
                            feedback_score = st.radio(
                                "Califica:",
                                options=[1, 2, 3, 4, 5],
                                format_func=lambda x: "⭐" * x,
                                horizontal=True,
                                key=f"feedback_score_new",
                                label_visibility="collapsed"
                            )
                        
                        with col2:
                            if st.button("👍 Enviar", key=f"submit_feedback_new", type="secondary"):
                                result_feedback = send_feedback(
                                    question=prompt,
                                    sql_query=result["sql_query"],
                                    feedback_score=feedback_score,
                                    user_id=st.session_state.user_id,
                                    results=result.get("results", [])
                                )
                                
                                if result_feedback.get("success"):
                                    if result_feedback.get("stored_in_vector_db"):
                                        st.success("✅ Guardado para aprendizaje!")
                                    else:
                                        st.success("✅ Gracias!")
                                else:
                                    st.error(f"❌ Error: {result_feedback.get('error', 'Unknown error')}")
                        
                        with col3:
                            if feedback_score >= 4:
                                st.caption("💾 Se guardará")

                    else:
                        error_msg = "❌ Error: No se pudo procesar la consulta."
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg
                        })

                else:
                    error_msg = f"❌ Error del servidor: {response.status_code}"
                    try:
                        error_detail = response.text
                        st.error(f"{error_msg}\n\n```\n{error_detail}\n```")
                    except:
                        st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })

            except requests.exceptions.Timeout:
                error_msg = "⏱️ La consulta tardó demasiado tiempo. Por favor, intenta con una pregunta más simple."
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

        # Rerun to show the new message
        st.rerun()

# Footer
st.markdown("---")
st.markdown("Powered by N8N + OpenAI + PostgreSQL | 🛵 Rappi Analytics")
