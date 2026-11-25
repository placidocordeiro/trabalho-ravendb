#!/usr/bin/env python3
"""Importa documentos processados para o RavenDB."""

import json
import sys
from pathlib import Path

import requests

PROC_DIR = Path(__file__).parent.parent / "dataset" / "processed"
JSONL_PATH = PROC_DIR / "movies.jsonl"

RAVEN_URL = "http://localhost:8080"
DATABASE = "Movies"
BULK_DOCS_URL = f"{RAVEN_URL}/databases/{DATABASE}/bulk_docs"
BATCH_SIZE = 100


def database_exists() -> bool:
    response = requests.get(f"{RAVEN_URL}/databases", timeout=10)
    response.raise_for_status()
    return any(db["Name"] == DATABASE for db in response.json()["Databases"])


def create_database_if_missing() -> None:
    """Cria o banco de dados, caso ainda não exista."""
    if database_exists():
        return
    response = requests.put(
        f"{RAVEN_URL}/admin/databases", json={"DatabaseName": DATABASE}, timeout=30
    )
    response.raise_for_status()
    print(f"Banco '{DATABASE}' criado.")


def build_put_command(doc: dict) -> dict:
    """Monta um comando PUT para a API bulk_docs do RavenDB."""
    tmdb_id = doc["tmdb_id"]
    doc_id = f"movies/{tmdb_id}"

    # Metadados definem a coleção e o identificador do documento.
    doc["@metadata"] = {
        "@collection": "Movies",
        "@id": doc_id,
    }

    return {
        "Type": "PUT",
        "Id": doc_id,
        "Document": doc,
    }


def send_batch(commands: list[dict]) -> None:
    """Envia um lote de comandos para o RavenDB."""
    payload = {"Commands": commands}
    response = requests.post(BULK_DOCS_URL, json=payload, timeout=30)
    response.raise_for_status()


def main() -> int:
    print(f"Importando documentos de {JSONL_PATH}")
    print(f"Destino: {BULK_DOCS_URL}")

    if not JSONL_PATH.exists():
        print(f"Erro: arquivo não encontrado: {JSONL_PATH}", file=sys.stderr)
        return 1

    create_database_if_missing()

    commands = []
    total = 0

    with JSONL_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            doc = json.loads(line)
            commands.append(build_put_command(doc))

            if len(commands) >= BATCH_SIZE:
                send_batch(commands)
                total += len(commands)
                print(f"  {total} documentos importados...")
                commands = []

    # Envia o restante, se houver.
    if commands:
        send_batch(commands)
        total += len(commands)

    print(f"Importação concluída: {total} documentos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
