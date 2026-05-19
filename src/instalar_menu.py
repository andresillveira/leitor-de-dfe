"""
instalar_menu.py — Integração com o menu de contexto do Windows.

Registra/remove a opção "Abrir DFe" no clique-direito de arquivos .xml
usando HKEY_CLASSES_ROOT (requer privilégio de administrador).
"""

import sys
import os
import winreg
from pathlib import Path


# ──────────────────────────────────────────────
# Configurações do registro
# ──────────────────────────────────────────────

# Caminho no registro do Windows
REGISTRY_PATH = r"SystemFileAssociations\.xml\shell\LeitorDFe"
REGISTRY_COMMAND_PATH = REGISTRY_PATH + r"\command"

# Texto que aparece no menu de contexto
MENU_LABEL = "Abrir DFe"

# Raiz do projeto (dois níveis acima deste arquivo: src/instalar_menu.py → leitor_de_dfe/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MAIN_SCRIPT = PROJECT_ROOT / "src" / "main.py"


def _encontrar_pythonw() -> str:
    """
    Encontra o caminho completo do pythonw.exe.
    
    Tenta, em ordem:
    1. pythonw.exe no mesmo diretório do Python atual
    2. pythonw.exe no PATH do sistema
    
    Returns:
        Caminho absoluto do pythonw.exe.
    
    Raises:
        FileNotFoundError: Se pythonw.exe não for encontrado.
    """
    # Tenta no mesmo diretório do interpretador atual
    python_dir = Path(sys.executable).parent
    pythonw = python_dir / "pythonw.exe"
    if pythonw.exists():
        return str(pythonw)
    
    # Tenta localizar no PATH
    import shutil
    pythonw_path = shutil.which("pythonw.exe")
    if pythonw_path:
        return pythonw_path
    
    raise FileNotFoundError(
        "pythonw.exe nao encontrado. Verifique a instalacao do Python."
    )


def instalar():
    """
    Registra a opção 'Abrir DFe' no menu de contexto do Windows
    para arquivos .xml.
    
    Requer privilégio de administrador (HKEY_CLASSES_ROOT).
    """
    try:
        pythonw = _encontrar_pythonw()
    except FileNotFoundError as e:
        print(f"ERRO: {e}")
        return False
    
    # Verifica se o main.py existe
    if not MAIN_SCRIPT.exists():
        print(f"ERRO: Arquivo nao encontrado: {MAIN_SCRIPT}")
        return False
    
    # Comando que será executado ao clicar no menu
    # %1 é substituído pelo caminho do arquivo clicado
    comando = f'"{pythonw}" "{MAIN_SCRIPT}" "%1"'
    
    try:
        # Cria a chave principal do menu
        key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, REGISTRY_PATH)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, MENU_LABEL)
        winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, f'"{pythonw}",0')
        winreg.CloseKey(key)
        
        # Cria a chave de comando
        key_cmd = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, REGISTRY_COMMAND_PATH)
        winreg.SetValueEx(key_cmd, "", 0, winreg.REG_SZ, comando)
        winreg.CloseKey(key_cmd)
        
        print("=" * 50)
        print("  [OK] Menu de contexto instalado com sucesso!")
        print("=" * 50)
        print()
        print("  Agora voce pode clicar com o botao direito")
        print('  em qualquer arquivo .xml e escolher "Abrir DFe".')
        print()
        print(f"  Python:  {pythonw}")
        print(f"  Script:  {MAIN_SCRIPT}")
        print()
        return True
        
    except PermissionError:
        print("=" * 50)
        print("  [ERRO] Permissao negada!")
        print("=" * 50)
        print()
        print("  A instalacao no menu de contexto requer")
        print("  privilegio de ADMINISTRADOR.")
        print()
        print("  Execute este script como Administrador:")
        print("  - Clique direito em 'instalar_menu.bat'")
        print("  - Selecione 'Executar como administrador'")
        print()
        return False
    except Exception as e:
        print(f"ERRO inesperado: {e}")
        return False


def desinstalar():
    """
    Remove a opção 'Abrir DFe' do menu de contexto do Windows.
    
    Requer privilégio de administrador (HKEY_CLASSES_ROOT).
    """
    try:
        # Remove a chave de comando primeiro
        try:
            winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, REGISTRY_COMMAND_PATH)
        except FileNotFoundError:
            pass  # Chave já não existe
        
        # Remove a chave principal
        try:
            winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, REGISTRY_PATH)
        except FileNotFoundError:
            pass  # Chave já não existe
        
        print("=" * 50)
        print("  [OK] Menu de contexto removido com sucesso!")
        print("=" * 50)
        print()
        print('  A opcao "Abrir DFe" foi removida do menu')
        print("  de contexto de arquivos .xml.")
        print()
        return True
        
    except PermissionError:
        print("=" * 50)
        print("  [ERRO] Permissao negada!")
        print("=" * 50)
        print()
        print("  A desinstalacao requer privilegio de ADMINISTRADOR.")
        print()
        print("  Execute este script como Administrador:")
        print("  - Clique direito em 'desinstalar_menu.bat'")
        print("  - Selecione 'Executar como administrador'")
        print()
        return False
    except Exception as e:
        print(f"ERRO inesperado: {e}")
        return False


def esta_instalado() -> bool:
    """Verifica se o menu de contexto está instalado."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, REGISTRY_PATH)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False


def main():
    """Ponto de entrada via linha de comando."""
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python instalar_menu.py --instalar")
        print("  python instalar_menu.py --desinstalar")
        print("  python instalar_menu.py --status")
        return
    
    acao = sys.argv[1].lower().strip("-")
    
    if acao in ("instalar", "install"):
        instalar()
    elif acao in ("desinstalar", "uninstall", "remover", "remove"):
        desinstalar()
    elif acao in ("status", "verificar", "check"):
        if esta_instalado():
            print("[OK] Menu de contexto esta INSTALADO.")
        else:
            print("[--] Menu de contexto NAO esta instalado.")
    else:
        print(f"Acao desconhecida: {acao}")
        print("Use --instalar, --desinstalar ou --status")


if __name__ == "__main__":
    main()
