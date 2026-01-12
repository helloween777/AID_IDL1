import os
from supabase import create_client, Client
import streamlit as st

def get_supabase_connection() -> Client:
    """Conectar a Supabase usando secrets de Streamlit Cloud o .env local"""
    try:
        # Para Streamlit Cloud
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
    except:
        # Para desarrollo local con .env
        from dotenv import load_dotenv
        load_dotenv()
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("❌ No se encontraron credenciales de Supabase")
    
    return create_client(url, key)

def obtener_pedidos(limite=5000):
    """Obtener pedidos desde Supabase"""
    supabase = get_supabase_connection()
    
    try:
        response = supabase.table("pedidos").select("*").limit(limite).execute()
        return response.data
    except Exception as e:
        st.error(f"Error al obtener datos: {e}")
        return []