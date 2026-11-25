#!/usr/bin/env python3
"""Demonstra as operações CRUD (Create, Read, Update, Delete) no RavenDB.

Usa a API HTTP do RavenDB com um filme fictício (movies/900001), que é
criado, lido, atualizado e excluído. Os filmes importados não são alterados.
"""

import sys

import requests

from import_ravendb import DATABASE, RAVEN_URL, build_put_command

DOCS_URL = f"{RAVEN_URL}/databases/{DATABASE}/docs"
QUERIES_URL = f"{RAVEN_URL}/databases/{DATABASE}/queries"

TEST_ID = "movies/900001"


def create_movie(movie: dict) -> str:
    """CREATE: grava um novo documento (PUT) e devolve o seu ID."""
    command = build_put_command(movie)
    response = requests.put(
        DOCS_URL, params={"id": command["Id"]}, json=command["Document"], timeout=10
    )
    response.raise_for_status()
    return response.json()["Id"]


def read_movie(doc_id: str) -> dict | None:
    """READ: busca um documento pelo ID. Devolve None se não existir."""
    response = requests.get(DOCS_URL, params={"id": doc_id}, timeout=10)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()["Results"][0]


def query_movies(rql: str, parameters: dict | None = None) -> list[dict]:
    """READ: executa uma consulta RQL e devolve os documentos encontrados."""
    payload = {"Query": rql, "QueryParameters": parameters or {}}
    # Os índices do RavenDB são atualizados em segundo plano; aqui esperamos
    # o índice processar as últimas gravações para a consulta não vir desatualizada.
    response = requests.post(
        QUERIES_URL, params={"waitForNonStaleResults": "true"}, json=payload, timeout=10
    )
    response.raise_for_status()
    return response.json()["Results"]


def update_movie(doc_id: str, script: str, values: dict) -> None:
    """UPDATE: altera só os campos indicados, com um script de patch (JavaScript).

    Dentro do script, `this` é o documento e `args` são os valores enviados.
    """
    payload = {"Patch": {"Script": script, "Values": values}}
    response = requests.patch(DOCS_URL, params={"id": doc_id}, json=payload, timeout=10)
    response.raise_for_status()
    if response.json()["Status"] != "Patched":
        raise RuntimeError(f"Documento {doc_id} não foi atualizado")


def delete_movie(doc_id: str) -> None:
    """DELETE: remove um documento pelo ID."""
    response = requests.delete(DOCS_URL, params={"id": doc_id}, timeout=10)
    response.raise_for_status()


def check(condition: bool, message: str) -> None:
    """Mostra o resultado de uma verificação e interrompe se ela falhar."""
    if not condition:
        raise AssertionError(f"FALHOU: {message}")
    print(f"  ok: {message}")


def main() -> int:
    # Filme fictício, apenas para a demonstração. Campos sem valor ficam como null.
    new_movie = {
        "tmdb_id": 900001,
        "title": "Filme de Teste CRUD",
        "original_title": "Filme de Teste CRUD",
        "original_language": "pt",
        "overview": "Documento criado para demonstrar o CRUD no RavenDB.",
        "release_date": None,
        "status": "Planned",
        "budget": 0,
        "revenue": 0,
        "vote_average": 0.0,
        "vote_count": 0,
        "genres": [{"id": 18, "name": "Drama"}],
        "cast": [],
        "crew": [],
    }

    if read_movie(TEST_ID) is not None:
        print(f"Removendo {TEST_ID}, que sobrou de uma execução anterior.")
        delete_movie(TEST_ID)

    print("1. CREATE")
    doc_id = create_movie(new_movie)
    print(f"  documento criado: {doc_id}")
    check(doc_id == TEST_ID, "ID segue o padrão movies/<tmdb_id>")

    print("2. READ")
    movie = read_movie(TEST_ID)
    check(movie is not None, "documento encontrado pelo ID")
    check(movie["title"] == "Filme de Teste CRUD", "título lido é o gravado")
    check(movie["@metadata"]["@collection"] == "Movies", "documento está na coleção Movies")

    found = query_movies("from Movies where title = $title", {"title": "Filme de Teste CRUD"})
    check(len(found) == 1, "documento encontrado por consulta RQL")

    print("3. UPDATE")
    update_movie(
        TEST_ID,
        "this.status = args.status; this.vote_average = args.vote; this.genres.push(args.genre);",
        {"status": "Released", "vote": 8.5, "genre": {"id": 35, "name": "Comedy"}},
    )
    movie = read_movie(TEST_ID)
    check(movie["status"] == "Released", "status alterado para Released")
    check(movie["vote_average"] == 8.5, "nota alterada para 8.5")
    check([g["name"] for g in movie["genres"]] == ["Drama", "Comedy"], "gênero adicionado ao array")
    check(movie["title"] == "Filme de Teste CRUD", "campos não citados no patch continuam iguais")

    print("4. DELETE")
    delete_movie(TEST_ID)
    check(read_movie(TEST_ID) is None, "documento não existe mais")

    print("CRUD concluído com sucesso.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except requests.ConnectionError:
        print(f"Erro: RavenDB não está acessível em {RAVEN_URL}. Rode 'docker compose up -d'.", file=sys.stderr)
        sys.exit(1)
