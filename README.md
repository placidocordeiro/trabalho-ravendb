# Trabalho RavenDB

Projeto acadêmico para estudo do RavenDB usando TMDB 5000 Movie Dataset.
link: https://huggingface.co/datasets/Adpacci/tmdb-5000/tree/main

## Objetivos

- Preparar dados do TMDB.
- Converter registros CSV em documentos JSON.
- Importar documentos para RavenDB.
- Demonstrar operações CRUD e consultas RQL.

## Estrutura

- `dataset/raw/` — CSVs originais (`tmdb_5000_movies.csv`, `tmdb_5000_credits.csv`)
- `dataset/processed/` — documentos JSON gerados
- `scripts/` — scripts de preparação e importação
- `docs/` — pesquisa, imagens e apresentação
- `report/` — relatório final

## Pré-requisitos

- Python 3.10+
- Docker
- RavenDB

## Como preparar os dados

> `dataset/raw/` e `dataset/processed/` não são versionados no git (estão no `.gitignore`). Baixe os CSVs pelo link no topo deste README e gere os JSONs com o script abaixo.

1. Certifique-se de que os arquivos `tmdb_5000_movies.csv` e `tmdb_5000_credits.csv` estejam em `dataset/raw/`.
2. Execute o script de preparação:

```bash
python3 scripts/prepare_dataset.py
```

O script irá:

- Ler os dois CSVs.
- Combinar filmes e créditos pelo identificador do filme (`movies.id` ↔ `credits.movie_id`).
- Converter campos JSON-string em listas/objetos nativos.
- Converter campos numéricos para `int` ou `float`.
- Substituir valores ausentes (string vazia ou `nan`) por `null`.
- Preservar listas JSON vazias (`[]`) como listas vazias.
- Gerar `dataset/processed/movies.jsonl` com um documento por linha.
- Gerar arquivos individuais opcionais em `dataset/processed/movies/`.
- Validar quantidade de registros, integridade, tipos e correspondência dos arquivos.

### Identificadores

Cada documento contém `tmdb_id`. Na importação futura para o RavenDB, o identificador será `movies/<tmdb_id>` (por exemplo, `movies/19995`).

## Como iniciar o RavenDB

```bash
docker compose up -d
# ou, com o justfile:
just up
```

Acesse o RavenDB Studio em `http://localhost:8080`.

> **`docker compose` ou `docker-compose`?** As instalações atuais do Docker trazem o Compose como plugin, e o comando é `docker compose` (com espaço). Esse é o comando usado no `justfile`. Em algumas máquinas, só existe a versão antiga, `docker-compose` (com hífen). Se aparecer `docker: 'compose' is not a docker command` ou `command not found`, use `docker-compose up -d` (e `docker-compose down`, `docker-compose stop`). Para usar o `justfile` nessas máquinas, troque `docker compose` por `docker-compose` nele.

## Como importar os documentos

Após preparar os dados e iniciar o RavenDB:

```bash
venv/bin/python scripts/import_ravendb.py
```

O script cria o banco `Movies`, caso ainda não exista, e importa os 4.803 documentos na coleção `Movies`.

## Consultas e CRUD (demonstração)

A demonstração é feita principalmente no **RavenDB Studio**, com o roteiro de [`docs/consultas.rql`](docs/consultas.rql):

- **Partes 1 a 5:** consultas RQL (filtros, dados aninhados, busca de texto, agregação e índices).
- **Parte 6:** CRUD completo (criar, ler, atualizar, atualizar em massa e excluir).

Como complemento, o mesmo CRUD pode ser feito por script, via API HTTP:

```bash
just crud   # ou: venv/bin/python scripts/crud_ravendb.py
```

O script cria, lê (por ID e por consulta RQL), atualiza (patch parcial) e exclui o filme fictício `movies/900001`, verificando cada etapa. Os filmes importados não são alterados.

## Voltar o banco ao estado inicial

Para ensaiar a demonstração e repeti-la depois:

```bash
just reset   # ou: venv/bin/python scripts/reset_ravendb.py
```

Apaga o banco `Movies`, recria e reimporta os 4.803 filmes (alguns segundos). Tudo o que foi criado, alterado ou excluído, inclusive os índices, é descartado.

## Como executar os testes

O script `prepare_dataset.py` executa validações automáticas ao final:

- Quantidade de documentos igual à quantidade de filmes (4.803).
- Ausência de IDs duplicados.
- Conjunto correto de campos em cada documento.
- Tipos corretos para campos numéricos (`int`/`float`) e JSON (`list`/`dict`).
- Correspondência entre filmes e créditos.
- Cada linha do JSONL é um JSON válido e independente.
- Cada arquivo individual corresponde exatamente ao documento do JSONL.

Para validar manualmente o JSONL gerado:

```bash
wc -l dataset/processed/movies.jsonl
python3 -m json.tool dataset/processed/movies/19995.json
```

## Estado atual

A preparação dos dados está concluída e validada.

- Dataset: TMDB 5000 Movie Dataset.
- Arquivos originais preservados em `dataset/raw/`.
- Script `scripts/prepare_dataset.py` implementado e testado.
- 4.803 documentos gerados em `dataset/processed/movies.jsonl`.
- 4.803 arquivos JSON individuais em `dataset/processed/movies/`.
- Merge entre `movies` e `credits` validado, sem registros órfãos.
- IDs únicos e integridade dos documentos verificados.
- Listas e objetos JSON vazios (`[]` e `{}`) preservados.
- Valores ausentes convertidos para `null`.
- Valores numéricos zero preservados.
- CSVs originais verificados por MD5 e intactos.

Não é necessário refazer a preparação dos dados.

## Próximas etapas

1. **Configurar o RavenDB**
   - Criar/atualizar `docker-compose.yml`.
   - Subir o servidor RavenDB.
   - Acessar o RavenDB Studio.
   - Criar o banco de dados do projeto.

2. **Importar o dataset**
   - Importar os 4.803 documentos de `movies.jsonl`.
   - Utilizar `movies/<tmdb_id>` como identificador.
   - Validar a importação pelo Studio.

3. **Implementar CRUD**
   - Create, Read, Update e Delete.
   - Demonstrar busca por identificador.

4. **Implementar consultas RQL**
   - Filtros, ordenação e consultas em campos aninhados.

5. **Completar a pesquisa teórica**
   - Modelo documental, RQL, indexação, transações, backup, segurança, replicação.

6. **Comparação com bancos relacionais**
   - Modelagem, relacionamentos, consultas, consistência, casos de uso.

7. **Finalizar entrega acadêmica**
   - Relatório, slides, distribuição da apresentação, demonstração ao vivo.

## Tecnologias

- Python
- RavenDB
- Docker Compose
- Git
