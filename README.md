# Processador Distribuído de Mídia

Protótipo acadêmico cliente-servidor para envio e processamento de arquivos de
mídia. O cliente desktop PySide6 se comunica exclusivamente por HTTP com uma API
FastAPI. O servidor executa o FFmpeg e persiste o estado dos processamentos em um
PostgreSQL instalado diretamente no Windows por meio do SQLAlchemy.

> Decisão de arquitetura: este projeto **não usa Docker** e não requer nenhuma
> configuração Docker.

## Funcionalidades implementadas

- envio de vídeo ou áudio por `multipart/form-data`;
- conversão de vídeo para MP4 (H.264 + AAC);
- extração de áudio para MP3;
- compactação de vídeo para MP4;
- execução em segundo plano no servidor e consulta periódica pelo cliente;
- estados `pending`, `processing`, `completed` e `failed` persistidos;
- listagem dos 100 processamentos mais recentes;
- download e remoção de resultados;
- limite configurável de upload e validação de extensões;
- endpoint de saúde do PostgreSQL e do FFmpeg;
- testes da API com banco SQLite temporário e FFmpeg simulado.

## Arquitetura

```text
┌──────────────────────┐       HTTP/JSON + upload       ┌──────────────────────┐
│ Cliente desktop      │ ──────────────────────────────> │ Servidor FastAPI      │
│ PySide6              │ <────────────────────────────── │ worker em background │
└──────────────────────┘       status + download         └──────────┬───────────┘
                                                                    │
                                                    ┌───────────────┴───────────────┐
                                                    ▼                               ▼
                                             FFmpeg local                 PostgreSQL local
                                             arquivos                     metadados/estados
```

A fila em background é interna ao processo do FastAPI nesta primeira versão. A
separação distribuída ocorre entre cliente e servidor, que podem executar em
computadores diferentes alterando a URL do servidor no cliente.

## Estrutura

```text
trabalho3 sd/
├── client/                  # aplicação PySide6
│   ├── app/api.py           # cliente HTTP
│   ├── app/main_window.py   # interface e tarefas não bloqueantes
│   └── main.py
├── server/
│   ├── app/                 # FastAPI, SQLAlchemy e integração FFmpeg
│   ├── tests/               # testes isolados do PostgreSQL/FFmpeg reais
│   ├── create_database.sql
│   └── main.py
```

## Pré-requisitos no Windows

- Python 3.11 ou superior;
- PostgreSQL instalado como serviço local;
- FFmpeg instalado e disponível no `PATH` ou configurado por caminho absoluto.

Confira o FFmpeg:

```powershell
ffmpeg -version
```

### 1. Criar o banco local

No terminal SQL do PostgreSQL, execute como administrador:

```powershell
cd server
psql -U postgres -f create_database.sql
```

Troque primeiro a senha de exemplo em `create_database.sql`. Se o usuário ou o
banco já existirem, não execute novamente os respectivos comandos.

### 2. Configurar e iniciar o servidor

```powershell
cd server
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edite `server/.env` e use a mesma senha criada no PostgreSQL. Se o FFmpeg não
estiver no `PATH`, informe seu executável, por exemplo:

```dotenv
FFMPEG_PATH=C:\ferramentas\ffmpeg\bin\ffmpeg.exe
```

Inicie a API pelo ambiente virtual (esse formato também funciona sem ativá-lo):

```powershell
.\venv\Scripts\python.exe main.py
```

Para desenvolvimento com recarga automática, depois de ativar o ambiente, use
`uvicorn main:app --reload`.

Não execute `server/main.py` com o Python global de `WindowsApps`: as dependências
do servidor, incluindo `psycopg`, estão instaladas em `server/venv`. A partir da
pasta raiz do projeto, o comando equivalente é:

```powershell
& ".\server\venv\Scripts\python.exe" ".\server\main.py"
```

A documentação interativa estará em <http://127.0.0.1:8000/docs>.

### 3. Configurar e iniciar o cliente

Em outro PowerShell:

```powershell
cd client
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Para executar cliente e servidor em máquinas diferentes, libere a porta 8000 no
firewall do servidor, inicie o Uvicorn com `--host 0.0.0.0` e informe no cliente
uma URL como `http://192.168.1.10:8000`.

## API

| Método | Rota | Descrição |
| --- | --- | --- |
| `GET` | `/api/health` | Verifica banco e FFmpeg |
| `POST` | `/api/jobs` | Envia mídia e cria processamento |
| `GET` | `/api/jobs` | Lista processamentos recentes |
| `GET` | `/api/jobs/{id}` | Consulta estado e erro |
| `GET` | `/api/jobs/{id}/download` | Baixa o resultado concluído |
| `DELETE` | `/api/jobs/{id}` | Remove registro e arquivos |

## Testes

Os testes não exigem PostgreSQL nem processam mídia real:

```powershell
cd server
.\venv\Scripts\Activate.ps1
python -m pytest -q
```

Para uma validação manual completa, envie um arquivo real pelo cliente e confirme
que o resultado abre em um reprodutor de mídia.

## Print da aplicação
<img width="1456" height="856" alt="image" src="https://github.com/user-attachments/assets/16172422-ed74-4cf3-92d8-4cdaf0dcbc75" />

