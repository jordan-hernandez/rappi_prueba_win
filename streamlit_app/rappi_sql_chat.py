import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Rappi Analytics Chat",
    page_icon="🛵",
    layout="wide"
)



def send_feedback(feedback_text, user_id, question, sql_query, results):
    """
    Envía feedback al webhook de N8N.
    
    Args:
        feedback_text: Texto del feedback (positivo/negativo)
        user_id: ID del usuario
        question: Pregunta original
        sql_query: Query SQL ejecutada
        results: Resultados de la consulta
        
    Returns:
        Respuesta del webhook
    """
    try:
        payload = {
            "feedback": feedback_text,
            "user_id": user_id,
            "question": question,
            "sql_query": sql_query,
            "results": results[:3] if results else [],  # Solo primeros 3 resultados
            "timestamp": datetime.now().isoformat(),
            "row_count": len(results) if results else 0
        }
        
        # Usar el webhook principal del N8N para feedback
        feedback_url = "https://jordan-gauss.app.n8n.cloud/webhook/db7b2529-6614-4008-9cee-b01d1d0e5b92"
        response = requests.post(
            feedback_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": "Feedback enviado correctamente"
            }
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
WEBHOOK_URL = "https://jordan-gauss.app.n8n.cloud/webhook/604b1f14-eacb-4f33-91c7-60a914831b3c"

#"https://jordan-gauss.app.n8n.cloud/webhook/604b1f14-eacb-4f33-91c7-60a914831b3c"
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
for message in st.session_state.messages:
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
                    st.metric("🎯 Valor Estratégico", f"{bv.get('strategic_value', 0):.1f}/10")
                with col3:
                    st.metric("✅ Correctitud", f"{bv.get('query_correctness', 0):.1f}/10")

                # Show details
                with st.expander("📈 Detalles de evaluación"):
                    if 'feedback' in bv:
                        st.write(f"**Feedback:** {bv['feedback']}")
                    st.write("**Scores por criterio:**")
                    
                    # Mostrar scores individuales
                    if 'strategic_value' in bv:
                        st.progress(bv['strategic_value'] / 10, text=f"Valor Estratégico: {bv['strategic_value']}/10")
                    if 'query_correctness' in bv:
                        st.progress(bv['query_correctness'] / 10, text=f"Correctitud de Query: {bv['query_correctness']}/10")
                    if 'efficiency_gain' in bv:
                        st.progress(bv['efficiency_gain'] / 10, text=f"Ganancia de Eficiencia: {bv['efficiency_gain']}/10")

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

            
            # Feedback Component
            if "data" in message and "sql_query" in message["data"]:
                st.markdown("---")
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown("**¿Te fue útil esta respuesta?**")
                    message_index = st.session_state.messages.index(message)
                    feedback_choice = st.radio(
                        "Feedback:",
                        options=["positivo", "negativo"],
                        format_func=lambda x: "👍 Positivo" if x == "positivo" else "👎 Negativo",
                        horizontal=True,
                        key=f"feedback_choice_msg_{message_index}",
                        label_visibility="collapsed"
                    )
                
                with col2:
                    if st.button("📤 Enviar", key=f"submit_feedback_msg_{message_index}", type="secondary"):
                        result = send_feedback(
                            feedback_text=feedback_choice,
                            user_id=st.session_state.user_id,
                            question=message["content"],
                            sql_query=message["data"]["sql_query"],
                            results=message["data"].get("results", [])
                        )
                        
                        if result.get("success"):
                            st.success("✅ ¡Gracias por tu feedback!")
                        else:
                            st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
                
                with col3:
                    if feedback_choice == "positivo":
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
                                st.metric("🎯 Valor Estratégico", f"{bv.get('strategic_value', 0):.1f}/10")
                            with col3:
                                st.metric("✅ Correctitud", f"{bv.get('query_correctness', 0):.1f}/10")

                            # Show details
                            with st.expander("📈 Detalles de evaluación"):
                                if 'feedback' in bv:
                                    st.write(f"**Feedback:** {bv['feedback']}")
                                st.write("**Scores por criterio:**")
                                
                                # Mostrar scores individuales
                                if 'strategic_value' in bv:
                                    st.progress(bv['strategic_value'] / 10, text=f"Valor Estratégico: {bv['strategic_value']}/10")
                                if 'query_correctness' in bv:
                                    st.progress(bv['query_correctness'] / 10, text=f"Correctitud de Query: {bv['query_correctness']}/10")
                                if 'efficiency_gain' in bv:
                                    st.progress(bv['efficiency_gain'] / 10, text=f"Ganancia de Eficiencia: {bv['efficiency_gain']}/10")

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

                        
                        # Feedback Component
                        st.markdown("---")
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.markdown("**¿Te fue útil esta respuesta?**")
                            feedback_choice = st.radio(
                                "Feedback:",
                                options=["positivo", "negativo"],
                                format_func=lambda x: "👍 Positivo" if x == "positivo" else "👎 Negativo",
                                horizontal=True,
                                key=f"feedback_choice_new_{len(st.session_state.messages)}",
                                label_visibility="collapsed"
                            )
                        
                        with col2:
                            if st.button("📤 Enviar", key=f"submit_feedback_new_{len(st.session_state.messages)}", type="secondary"):
                                result_feedback = send_feedback(
                                    feedback_text=feedback_choice,
                                    user_id=st.session_state.user_id,
                                    question=prompt,
                                    sql_query=result["sql_query"],
                                    results=result.get("results", [])
                                )
                                
                                if result_feedback.get("success"):
                                    st.success("✅ ¡Gracias por tu feedback!")
                                else:
                                    st.error(f"❌ Error: {result_feedback.get('error', 'Unknown error')}")
                        
                        with col3:
                            if feedback_choice == "positivo":
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
