import os
from supabase import create_client, Client
from dotenv import load_dotenv

def get_supabase_connection() -> Client:
    """Conectar a Supabase usando .env"""
    load_dotenv()
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("No se encontraron credenciales de Supabase en .env")
    
    return create_client(url, key)

def obtener_pedidos(limite=5000):
    """Obtener todos los pedidos desde Supabase"""
    supabase = get_supabase_connection()
    
    try:
        response = supabase.table("pedidos").select("*").limit(limite).execute()
        return response.data
    except Exception as e:
        st.error(f"Error al conectar con Supabase: {e}")
        return []