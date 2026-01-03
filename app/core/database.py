from supabase import create_client, Client
from app.core.config import settings

# Initialize Supabase client
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# Service role client for admin operations
supabase_admin: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


def get_supabase() -> Client:
    """Dependency for getting Supabase client"""
    return supabase

def get_db() -> Client:
    """Dependency for getting Supabase client"""
    return supabase


def get_supabase_admin() -> Client:
    """Dependency for getting Supabase admin client"""
    return supabase_admin
