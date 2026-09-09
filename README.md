# Aprobador de PR's XD

Mini herramienta de terminal para revisar y aprobar Pull Requests de GitHub usando GitHub CLI (`gh`).

La app está pensada para mantener una terminal abierta durante el día: pegas una URL de PR, revisas la información, confirmas manualmente y recién ahí se ejecuta el approve.

## Qué hace

- Lee URLs de Pull Requests desde la terminal.
- Consulta el PR usando `gh pr view`.
- Valida organización permitida y rama destino permitida desde variables de entorno.
- Evita aprobar PRs cerrados, mergeados, Draft, propios o ya aprobados por tu usuario.
- Pide confirmación manual antes de aprobar.
- Aprueba con `gh pr review URL --approve`.
- Vuelve a esperar otra URL sin cerrar el programa.

## Requisitos

- Windows PowerShell o Windows Terminal.
- Python 3.10 o superior.
- GitHub CLI instalado.
- Sesión activa en GitHub CLI.
- Acceso al repositorio privado o público que vas a revisar.

## Preparación Desde Cero

Clona o descarga el proyecto y entra a la carpeta:

```powershell
cd C:\ruta\al\auto-aprob-pr
```

Crea un entorno virtual:

```powershell
python -m venv .venv
```

Activa el entorno virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instala dependencias:

```powershell
pip install -r requirements.txt
```

Si PowerShell bloquea la activación del entorno virtual, ejecuta esto una vez:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Luego cierra y abre PowerShell, vuelve a la carpeta del proyecto y activa nuevamente:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Configuración Del `.env`

La app necesita dos variables:

```text
ALLOWED_ORG=tu-organizacion
ALLOWED_BASE_BRANCH=dev
```

Crea tu archivo `.env` local copiando el ejemplo:

```powershell
copy .env.example .env
```

Abre el archivo:

```powershell
notepad .env
```

Edita los valores según tu caso:

```text
ALLOWED_ORG=tu-organizacion-real
ALLOWED_BASE_BRANCH=dev
```

Importante: `.env` no se sube a GitHub. Está ignorado por `.gitignore`.

## Configurar GitHub CLI

Instala GitHub CLI si todavía no lo tienes:

```powershell
winget install --id GitHub.cli
```

Inicia sesión manualmente:

```powershell
gh auth login
```

Verifica que tu sesión esté activa:

```powershell
gh auth status
```

Prueba que puedes leer un Pull Request:

```powershell
gh pr view https://github.com/tu-organizacion/tu-repo/pull/123
```

## Ejecución

Cada vez que quieras usar la herramienta:

```powershell
cd C:\ruta\al\auto-aprob-pr
.\.venv\Scripts\Activate.ps1
python approve_pr.py
```

Si ya tienes el entorno virtual activo, solo ejecuta:

```powershell
python approve_pr.py
```

## Flujo De Uso

1. Ejecuta `python approve_pr.py`.
2. Pega una URL de Pull Request.
3. Revisa la información mostrada en pantalla.
4. Si todo está correcto, responde `S`.
5. Si no quieres aprobar, responde `N` o cualquier otra cosa.
6. Para salir, escribe `q`, `quit`, `exit` o `salir`.

Ejemplo de URL:

```text
https://github.com/tu-organizacion/tu-repo/pull/123
```

Confirmación:

```text
¿Aprobar este PR? [S/N]:
```

Opciones aceptadas para aprobar:

```text
S
s
SI
si
sí
```

## Variables De Entorno

`ALLOWED_ORG`

Organización permitida para aprobar PRs. El `owner` de la URL debe coincidir con este valor, sin importar mayúsculas/minúsculas.

`ALLOWED_BASE_BRANCH`

Rama destino permitida. La comparación es exacta.

Ejemplo:

```text
ALLOWED_BASE_BRANCH=dev
```

Esto permite solamente:

```text
baseRefName == "dev"
```

No acepta variantes como:

```text
Dev
DEV
develop
main
master
qa
uat
release/*
```

## Validaciones

Antes de aprobar, la app valida:

- Que GitHub CLI exista en `PATH`.
- Que exista una sesión activa de GitHub CLI.
- Que la URL sea de un Pull Request.
- Que el owner coincida con `ALLOWED_ORG`.
- Que el PR exista y sea accesible.
- Que el PR esté abierto.
- Que el PR no esté mergeado.
- Que el PR no esté en Draft.
- Que el PR no haya sido creado por tu propio usuario.
- Que la rama destino coincida exactamente con `ALLOWED_BASE_BRANCH`.
- Que tu usuario no haya aprobado antes el mismo PR.
- Que no se haya aprobado durante esta misma ejecución.
- Que confirmes manualmente con `[S/N]`.

## Seguridad

- No usa Personal Access Tokens.
- No usa `GITHUB_TOKEN`.
- No guarda credenciales.
- No ejecuta `gh auth login` automáticamente.
- Usa la sesión existente de GitHub CLI.
- Ejecuta comandos con `subprocess.run([...], shell=False)`.
- Nunca aprueba automáticamente al pegar una URL.
- El archivo `.env` es local y no debe subirse al repositorio.

## Archivos Del Proyecto

```text
auto-aprob-pr/
├── .env.example
├── .gitignore
├── README.md
├── approve_pr.py
└── requirements.txt
```

No subas:

```text
.env
.venv/
__pycache__/
```

## Problemas Comunes

`Faltan variables de configuración.`

Crea el archivo `.env` y configura `ALLOWED_ORG` y `ALLOWED_BASE_BRANCH`.

`GitHub CLI no está instalado o no está disponible en PATH.`

Instala GitHub CLI, cierra y abre PowerShell, y valida con:

```powershell
gh --version
```

`No hay una sesión activa de GitHub CLI.`

Ejecuta:

```powershell
gh auth login
```

`Pull Request no encontrado o no tienes acceso.`

Valida la URL, tu VPN si aplica, y tus permisos sobre el repositorio.

`No puedes aprobar tu propio Pull Request.`

GitHub no permite que una aprobación propia cuente como review válida.

`Este PR no apunta a la rama permitida.`

Revisa `ALLOWED_BASE_BRANCH` en tu `.env` y la rama destino real del PR.

## Comando Rápido Para Devs

Después de clonar y configurar `.env`:

```powershell
cd C:\ruta\al\auto-aprob-pr
.\.venv\Scripts\Activate.ps1
gh auth status
python approve_pr.py
```
