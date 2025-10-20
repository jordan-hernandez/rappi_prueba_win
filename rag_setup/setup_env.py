"""
Setup Environment Variables for Supabase Migration
=================================================
Este script ayuda a configurar las variables de entorno necesarias.
"""
import os
from pathlib import Path

def create_env_file():
    """Crea un archivo .env con las variables necesarias"""
    env_path = Path(__file__).parent.parent / '.env'
    
    print("🔧 Setting up environment variables...")
    print(f"📁 .env file will be created at: {env_path}")
    
    # Verificar si ya existe
    if env_path.exists():
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/n): ").strip().lower()
        if response != 'y':
            print("❌ Cancelled")
            return
    
    # Solicitar valores al usuario
    print("\n📝 Please provide the following information:")
    
    supabase_url = input("Supabase URL: ").strip()
    if not supabase_url:
        print("❌ Supabase URL is required")
        return
    
    supabase_key = input("Supabase Key (anon key): ").strip()
    if not supabase_key:
        print("❌ Supabase Key is required")
        return
    
    # Crear contenido del .env
    env_content = f"""# Supabase Configuration
SUPABASE_URL={supabase_url}
SUPABASE_KEY={supabase_key}

# Excel File Paths
EXCEL_FILE=data/raw/rappi_data.xlsx
CLEAN_EXCEL_FILE=data/processed/rappi_data_clean_final.xlsx
"""
    
    # Escribir archivo
    try:
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        print(f"✅ .env file created successfully at {env_path}")
        print("\n📋 Variables set:")
        print(f"   SUPABASE_URL: {supabase_url}")
        print(f"   SUPABASE_KEY: {supabase_key[:20]}...")
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")


def check_env_file():
    """Verifica si el archivo .env existe y tiene las variables necesarias"""
    env_path = Path(__file__).parent.parent / '.env'
    
    if not env_path.exists():
        print("❌ .env file not found")
        return False
    
    # Cargar variables
    env_vars = {}
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False
    
    # Verificar variables requeridas
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
    missing_vars = []
    
    for var in required_vars:
        if var not in env_vars or not env_vars[var]:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ .env file is properly configured")
    print(f"   SUPABASE_URL: {env_vars['SUPABASE_URL']}")
    print(f"   SUPABASE_KEY: {env_vars['SUPABASE_KEY'][:20]}...")
    
    return True


def main():
    """Main function"""
    print("=" * 60)
    print("Supabase Environment Setup")
    print("=" * 60)
    
    print("\nChoose an option:")
    print("1. Create new .env file")
    print("2. Check existing .env file")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == '1':
        create_env_file()
    elif choice == '2':
        check_env_file()
    elif choice == '3':
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()

