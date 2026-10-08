# Atlas CEEP

Aplicação web escolar com áreas específicas para alunos, professores e administração. O backend é feito em Flask e SQLite; as páginas usam HTML, CSS e JavaScript sem etapa de compilação do frontend.

## Requisitos

- Python instalado e disponível no terminal.
- `pip`, instalado com Python.
- Navegador web atualizado.

Não é necessário instalar Node.js ou executar um processo separado para o frontend.

## Instalação e execução

Execute os comandos a partir da pasta raiz do repositório.

### Linux e macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m backend.app
```

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m backend.app
```

Quando o servidor iniciar, acesse <http://127.0.0.1:5000>. Para parar o servidor, use `Ctrl+C` no terminal.

## Primeiro acesso

Na primeira inicialização, a aplicação cria o banco SQLite em `backend/database/atlas.db` e prepara o acesso inicial de administrador:

| Login | Senha |
| --- | --- |
| `admin@atlas.com` | `atlas123` |

Essa credencial é apenas para desenvolvimento local. Antes de criar uma instalação fora do ambiente de desenvolvimento, altere `ADMIN_BOOTSTRAP_PASSWORD` em `backend/database/database.py` e configure uma chave de sessão própria. O banco e as credenciais de usuários são dados locais; não os publique nem os inclua em commits.

Para definir a chave de sessão no ambiente local antes de iniciar o servidor:

```bash
export ATLAS_SECRET_KEY="substitua-por-uma-chave-longa-e-aleatoria"
python -m backend.app
```

No PowerShell:

```powershell
$env:ATLAS_SECRET_KEY = "substitua-por-uma-chave-longa-e-aleatoria"
python -m backend.app
```

Sem `ATLAS_SECRET_KEY`, o app usa uma chave fixa de desenvolvimento definida em `backend/app.py`; ela não deve ser usada em produção.

## Como a aplicação funciona

1. `backend/app.py` cria a aplicação Flask, inicializa o banco, registra as rotas da API e entrega as páginas HTML.
2. O login cria uma sessão Flask em cookie `HttpOnly`. O papel do usuário determina qual página ele pode acessar: aluno, professor ou administrador.
3. O JavaScript das páginas consulta a API em `/api/...` usando a sessão do navegador. `static/js/main.js` reúne funções comuns para chamadas à API, sessão, tema, menu do perfil e saída.
4. `backend/database/database.py` cria e atualiza a estrutura SQLite. A conexão habilita chaves estrangeiras, e as consultas das rotas usam parâmetros SQL.

### Páginas

- `/login`: autenticação.
- `/aluno`: atividades, prazos, calendário e avisos do aluno.
- `/professor`: publicação e gerenciamento de atividades, materiais e avisos para turmas e matérias.
- `/adm`: eventos escolares e gerenciamento de alunos, professores, turmas e matérias.
- `/`: redireciona usuários autenticados para a página correspondente ao papel; sem sessão, direciona para o login.

### API

As rotas são registradas sob `/api`. Entre os principais grupos estão:

- `/api/auth`: login, consulta da sessão atual (`/me`) e logout.
- `/api/alunos`, `/api/professores`, `/api/adms`: cadastros e operações de perfil.
- `/api/turmas` e `/api/materias`: turmas, matérias e vínculos entre elas.
- `/api/eventos`: agenda institucional.
- `/api/professor/publicacoes`: publicações feitas por professores.
- `/api/aluno/agenda`: dados da agenda do aluno, atividades pessoais e avisos.

As operações protegidas verificam a sessão e o papel necessário no backend. Para conferir os caminhos e exemplos de requisição, consulte `backend/testes_api.http`.

## Estrutura do projeto

```text
backend/
  app.py                 Configuração Flask e páginas
  auth_utils.py          Sessão e controle de acesso por papel
  database/
    database.py          Criação e conexão com SQLite
  routes/                Blueprints da API
  testes_api.http        Exemplos manuais de requisições
templates/               Páginas HTML renderizadas pelo Flask
static/
  css/style.css          Estilos compartilhados
  js/                    Scripts por página e funções comuns
  assets/                Imagens e outros recursos estáticos
requirements.txt         Dependências Python fixadas
```

## Dados e desenvolvimento

- O banco é criado automaticamente ao iniciar o app. A inicialização preserva os dados existentes e cria o administrador inicial quando necessário.
- O arquivo SQLite, ambientes virtuais, caches Python e arquivos `.env` estão listados no `.gitignore`.
- Não há pipeline de build nem suíte de testes automatizada configurada. `backend/testes_api.http` contém exemplos para uso manual com um cliente HTTP.
- `python -m backend.app` inicia o servidor de desenvolvimento do Flask, que usa modo debug. Não exponha esse servidor diretamente na internet.
