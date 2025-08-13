# Cloudhabil CLI (Windows)

Este paquete contiene la CLI mínima para enrutar tareas entre tres modelos locales servidos con `llama.cpp`.

## Requisitos
- Python 3.11 o 3.12 instalado y en PATH.
- `llama.cpp` server (server.exe) ejecutándose por modelo.
- Los modelos GGUF descargados en tu máquina.

## Instalación rápida
PowerShell:
```powershell
cd <carpeta donde descomprimiste>\ch-cli

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

## Configurar modelos
Edita `configs\models.yaml` si usas otros puertos o nombres de modelo.

Ejemplos de arranque en Windows (ajusta rutas):
```powershell
# Router (codegemma-2b)
.\server.exe -m ".\models\codegemma-2b_Q8_0.gguf" -c 8192 -ngl 999 --port 8081

# Qwen 7B
.\server.exe -m ".\models\Qwen2.5-Coder-7B-Instruct_Q5_K_M.gguf" -c 8192 -ngl 999 --port 8082

# DeepSeek 7B
.\server.exe -m ".\models\DeepSeek-Coder-7B-Instruct-v1.5_Q8_0.gguf" -c 8192 -ngl 999 --port 8083
```

> Nota: En PowerShell no se ejecuta C++. El error "int no se reconoce..." aparece si escribes `int main` como si fuera un comando. Compila o ejecuta el código C++ desde Visual Studio, pero esta CLI es Python y se lanza con `python`.

## Uso
Crear una tarea:
```powershell
python .\ch_cli.py new --name "migrar-auth-a-app-router" `
  --context "Next.js 14, Node 20, Postgres" `
  --task "Migrar el middleware de auth a App Router con rutas protegidas." `
  --constraints "No romper API; mantener compatibilidad Node 20; tests deben pasar."
```

Ejecutar con routing automático:
```powershell
python .\ch_cli.py run --name "migrar-auth-a-app-router"
```

Forzar modelo:
```powershell
python .\ch_cli.py run --name "migrar-auth-a-app-router" --model qwen
```

Revisión rápida:
```powershell
python .\ch_cli.py qa --slug "migrar-auth-a-app-router"
```

Aplicar el último parche sugerido (comando a ejecutar desde tu repo objetivo):
```powershell
python .\ch_cli.py apply --slug "migrar-auth-a-app-router"
# Copia el comando que imprime y ejecútalo en la raíz del proyecto destino:
# git apply "<ruta al .patch>"
```

## Estructura
```
ch-cli/
  ch_cli.py
  requirements.txt
  configs/
    models.yaml
  prompts/
    system_router.md
    system_qwen.md
    system_deepseek.md
  tasks/
    ...
```
