#!/usr/bin/env python3
"""Volta o banco Movies ao estado inicial: apaga, recria e reimporta os filmes.

Útil para ensaiar a apresentação: tudo o que foi criado, alterado ou excluído
(documentos e índices) é descartado, e os 4.803 filmes originais voltam.
"""

import time

import requests

import import_ravendb
from import_ravendb import DATABASE, RAVEN_URL, database_exists


def delete_database() -> None:
    """Apaga o banco e espera o servidor concluir a exclusão."""
    payload = {"DatabaseNames": [DATABASE], "HardDelete": True}
    response = requests.delete(f"{RAVEN_URL}/admin/databases", json=payload, timeout=30)
    response.raise_for_status()

    for _ in range(30):
        if not database_exists():
            print(f"Banco '{DATABASE}' apagado.")
            return
        time.sleep(1)
    raise RuntimeError(f"O banco '{DATABASE}' não foi apagado a tempo")


def main() -> int:
    if database_exists():
        delete_database()
    return import_ravendb.main()


if __name__ == "__main__":
    raise SystemExit(main())
