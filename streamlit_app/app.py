"""
Streamlit Frontend para Rappi Analytics
========================================
Conecta con API que llama a N8N workflow
"""
import streamlit as st
import requests
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import uuid

# Configuration
API_URL = "http://localhost:8000"  # Change to your deployed API URL
st.set_page_config(
    page_title="Rappi Analytics Bot",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        color: #FF5A5F;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.3rem;
        color: #555;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .query-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
    }
    .score-badge {
        background-color: #28a745;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.85rem;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state"""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "user_id" not in st.session_state:
        st.session_state.user_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def call_api_ask(question: str, user_id: str, user_context: str = None):
    """Call API to ask question"""
    try:
        response = requests.post(
            f"{API_URL}/api/v1/ask",
            json={
                "question": question,
                "user_id": user_id,
                "user_context": user_context
            },
            timeout=60
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {
                "success": False,
                "error": f"API error: {response.status_code} - {response.text}"
            }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timeout. Query may be too complex."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def render_sidebar():
    """Render sidebar"""
    with st.sidebar:
        st.markdown("### 🚀 Rappi Analytics Bot")
        st.markdown("**Powered by N8N + AI**")
        st.markdown("---")

        # User context
        user_context = st.selectbox(
            "Tu rol",
            ["RGM", "Growth Team", "Operations", "Analytics", "Other"],
            key="user_context"
        )

        # New conversation
        if st.button("🔄 Nueva Conversación", use_container_width=True):
            st.session_state.messages = []
            st.session_state.user_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            st.rerun()

        st.markdown("---")

        # Example questions
        st.markdown("### 💡 Preguntas Ejemplo")
        examples = [
            "🏆 Top 5 zonas por Perfect Order",
            "📊 Compara Perfect Order MX vs CO",
            "📈 Evolución Gross Profit últimas 4 semanas",
            "🎯 Promedio Pro Adoption por país",
            "🔍 Zonas con Lead Penetration > 50"
        ]

        for example in examples:
            clean = example.split(" ", 1)[1] if " " in example else example
            if st.button(example, key=f"ex_{clean[:15]}", use_container_width=True):
                st.session_state.example_question = clean

        st.markdown("---")

        # API Status
        st.markdown("### 🔌 API Status")
        try:
            health = requests.get(f"{API_URL}/health", timeout=3).json()
            st.success(f"✅ API: {health['status']}")
            st.info(f"🔗 N8N: {health['n8n_webhook']}")
        except:
            st.error("❌ API: Disconnected")


def render_message(role: str, content: str):
    """Render chat message"""
    with st.chat_message(role):
        st.markdown(content)


def render_query_details(result: dict):
    """Render query details"""
    if not result.get("success"):
        return

    with st.expander("🔍 Detalles del Query", expanded=False):
        # SQL Query
        st.markdown("**SQL Query:**")
        st.markdown(f'<div class="query-box">{result.get("sql_query", "N/A")}</div>', unsafe_allow_html=True)

        # Results info
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Filas", result.get("row_count", 0))

        with col2:
            bv = result.get("business_value", {})
            score = bv.get("overall_score", 0)
            emoji = "🌟" if score >= 8 else "✅" if score >= 6 else "⚠️"
            st.metric(f"{emoji} Score", f"{score:.1f}/10")

        with col3:
            time_saved = bv.get("time_saved_minutes", 0)
            st.metric("⏱️ Tiempo ahorrado", f"~{time_saved} min")

        # Business value details
        if result.get("business_value"):
            bv = result["business_value"]

            st.markdown("**Criterios de Evaluación:**")

            criteria = bv.get("criteria_scores", {})
            for criterion, score in criteria.items():
                emoji = "🌟" if score >= 8 else "✅" if score >= 6 else "⚠️"
                st.write(f"{emoji} {criterion.replace('_', ' ').title()}: {score:.1f}/10")

            if bv.get("business_impact"):
                st.markdown(f"**💡 Impacto de Negocio:**")
                st.info(bv["business_impact"])

            if bv.get("improvement_iterations", 0) > 0:
                st.warning(f"⚠️ Query mejorada en {bv['improvement_iterations']} iteraciones")


def render_visualization(viz_data: dict):
    """Render Plotly visualization"""
    if not viz_data or not viz_data.get("success"):
        return

    st.markdown("### 📊 Visualización")

    try:
        # Load from JSON
        chart_json = viz_data.get("chart_json")
        if chart_json:
            if isinstance(chart_json, str):
                chart_dict = json.loads(chart_json)
            else:
                chart_dict = chart_json

            fig = go.Figure(chart_dict)
            st.plotly_chart(fig, use_container_width=True)

            st.caption(f"📊 {viz_data['data_points']} puntos | X: {viz_data['x_column']} | Y: {viz_data['y_column']}")

    except Exception as e:
        st.warning(f"No se pudo renderizar visualización: {e}")


def main():
    """Main function"""
    initialize_session_state()

    # Header
    st.markdown('<p class="main-header">🚀 Rappi Analytics Bot</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Preguntas inteligentes | SQL de calidad | Powered by N8N</p>', unsafe_allow_html=True)

    # Sidebar
    render_sidebar()

    # Display message history
    for message in st.session_state.messages:
        render_message(message["role"], message["content"])

        if message.get("result"):
            render_query_details(message["result"])

            if message["result"].get("visualization"):
                render_visualization(message["result"]["visualization"])

    # Chat input
    if prompt := st.chat_input("💬 Escribe tu pregunta sobre métricas de Rappi..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        render_message("user", prompt)

        # Call API
        with st.spinner("🤔 Procesando con N8N workflow..."):
            result = call_api_ask(
                question=prompt,
                user_id=st.session_state.user_id,
                user_context=st.session_state.get("user_context", "Unknown")
            )

            if result.get("success"):
                # Format response
                answer = result.get("answer", "")

                # Add business value info
                if result.get("business_value"):
                    bv = result["business_value"]
                    score = bv.get("overall_score", 0)
                    emoji = "🌟" if score >= 8 else "✅" if score >= 6 else "⚠️"

                    answer += f"\n\n{emoji} **Score de Calidad:** {score:.1f}/10"
                    answer += f" | ⏱️ Tiempo ahorrado: ~{bv.get('time_saved_minutes', 0)} min"

                # Add to messages
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "result": result
                })

                render_message("assistant", answer)
                render_query_details(result)

                if result.get("visualization"):
                    render_visualization(result["visualization"])

            else:
                error_msg = f"❌ Error: {result.get('error', 'Unknown error')}"
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })
                render_message("assistant", error_msg)

    # Handle example question
    if st.session_state.get("example_question"):
        prompt = st.session_state.example_question
        del st.session_state.example_question
        st.rerun()


if __name__ == "__main__":
    main()
