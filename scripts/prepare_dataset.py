#!/usr/bin/env python3
"""Lê CSVs brutos do TMDB e gera documentos JSON processados para RavenDB.

Este script:
- Lê movies e credits de dataset/raw/
- Combina pelo identificador do filme
- Converte campos JSON-string em estruturas nativas
- Preserva tipos numéricos
- Converte strings vazias/NAN para null
- Mantém listas/objetos JSON vazios como [] / {}
- Gera dataset/processed/movies.jsonl (um documento por linha)
- Gera arquivos individuais opcionais em dataset/processed/movies/
- Valida integridade dos documentos gerados
"""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "dataset" / "raw"
PROC_DIR = Path(__file__).parent.parent / "dataset" / "processed"

MOVIES_CSV = RAW_DIR / "tmdb_5000_movies.csv"
CREDITS_CSV = RAW_DIR / "tmdb_5000_credits.csv"
OUTPUT_JSONL = PROC_DIR / "movies.jsonl"
OUTPUT_DIR_MOVIES = PROC_DIR / "movies"

JSON_FIELDS_MOVIES = [
    "genres",
    "keywords",
    "production_companies",
    "production_countries",
    "spoken_languages",
]
JSON_FIELDS_CREDITS = ["cast", "crew"]
JSON_FIELDS = JSON_FIELDS_MOVIES + JSON_FIELDS_CREDITS

INTEGER_FIELDS = ["budget", "revenue", "runtime", "vote_count"]
FLOAT_FIELDS = ["popularity", "vote_average"]
STRING_FIELDS = [
    "homepage",
    "original_language",
    "original_title",
    "overview",
    "release_date",
    "status",
    "tagline",
    "title",
]

EXPECTED_FIELDS = (
    ["tmdb_id"]
    + STRING_FIELDS
    + INTEGER_FIELDS
    + FLOAT_FIELDS
    + JSON_FIELDS
)


def is_blank(value: str) -> bool:
    """Verifica se valor CSV deve ser considerado ausente."""
    if value is None:
        return True
    stripped = value.strip()
    return stripped == "" or stripped.lower() == "nan"


def parse_number(value: str, as_int: bool = False):
    """Converte string numérica para int ou float. Ausentes viram null."""
    if is_blank(value):
        return None
    try:
        if as_int:
            return int(float(value))
        return float(value)
    except ValueError as exc:
        raise ValueError(f"Valor numérico inválido: {value!r}") from exc


def parse_json_field(value: str):
    """Converte string JSON em objeto/lista. Ausentes viram null.

    Listas vazias e objetos vazios são preservados, não convertidos para null.
    """
    if is_blank(value):
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON inválido: {exc}") from exc


def clean_string(value: str):
    """Remove espaços excessivos; strings vazias viram null."""
    if is_blank(value):
        return None
    return value.strip()


def load_csv(path: Path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def build_document(movie: dict, credits: dict) -> dict:
    doc = {"tmdb_id": int(movie["id"])}

    for field in STRING_FIELDS:
        doc[field] = clean_string(movie.get(field))

    for field in INTEGER_FIELDS:
        doc[field] = parse_number(movie.get(field, ""), as_int=True)

    for field in FLOAT_FIELDS:
        doc[field] = parse_number(movie.get(field, ""), as_int=False)

    for field in JSON_FIELDS_MOVIES:
        doc[field] = parse_json_field(movie.get(field, ""))

    for field in JSON_FIELDS_CREDITS:
        doc[field] = parse_json_field(credits.get(field, ""))

    return doc


def raven_id(tmdb_id: int) -> str:
    """Retorna o identificador RavenDB futuro para o documento."""
    return f"movies/{tmdb_id}"


def save_jsonl(documents: list[dict], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for doc in documents:
            f.write(json.dumps(doc, ensure_ascii=False, separators=(",", ":")))
            f.write("\n")


def save_individual_files(documents: list[dict], base_dir: Path):
    base_dir.mkdir(parents=True, exist_ok=True)
    for doc in documents:
        file_path = base_dir / f"{doc['tmdb_id']}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)


def validate_structure(documents: list[dict], expected_count: int):
    print(f"Validando estrutura de {len(documents)} documentos...")

    assert len(documents) == expected_count, (
        f"Quantidade incorreta: esperado {expected_count}, obtido {len(documents)}"
    )

    ids = {doc["tmdb_id"] for doc in documents}
    assert len(ids) == len(documents), "IDs duplicados encontrados"

    for doc in documents:
        assert set(doc.keys()) == set(EXPECTED_FIELDS), (
            f"Campos inesperados em {doc['tmdb_id']}: {set(doc.keys()) ^ set(EXPECTED_FIELDS)}"
        )
        assert isinstance(doc["tmdb_id"], int), "tmdb_id deve ser inteiro"

        for field in INTEGER_FIELDS:
            value = doc[field]
            assert value is None or isinstance(value, int), (
                f"{field} deve ser int ou null em {doc['tmdb_id']}"
            )

        for field in FLOAT_FIELDS:
            value = doc[field]
            assert value is None or isinstance(value, float), (
                f"{field} deve ser float ou null em {doc['tmdb_id']}"
            )

        for field in JSON_FIELDS:
            value = doc[field]
            assert value is None or isinstance(value, (list, dict)), (
                f"{field} deve ser lista, objeto ou null em {doc['tmdb_id']}"
            )

    print("Estrutura validada com sucesso.")


def validate_relationships(movies: list[dict], documents: list[dict]):
    print("Validando relacionamentos...")

    movie_ids = {int(m["id"]) for m in movies}
    doc_ids = {d["tmdb_id"] for d in documents}

    assert movie_ids == doc_ids, (
        f"Diferença entre IDs de movies e documentos: {movie_ids ^ doc_ids}"
    )

    for doc in documents:
        if doc["cast"] is not None:
            assert isinstance(doc["cast"], list)
        if doc["crew"] is not None:
            assert isinstance(doc["crew"], list)

    print("Relacionamentos validados com sucesso.")


def validate_files_against_jsonl(documents: list[dict], jsonl_path: Path, dir_path: Path):
    print("Validando arquivos individuais contra JSONL...")

    loaded = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                loaded.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSON inválido na linha {line_number}: {exc}") from exc

    assert len(loaded) == len(documents), "JSONL não contém todos os documentos"

    for doc in loaded:
        tmdb_id = doc["tmdb_id"]
        file_path = dir_path / f"{tmdb_id}.json"
        assert file_path.exists(), f"Arquivo individual ausente: {file_path}"
        with open(file_path, encoding="utf-8") as f:
            from_file = json.load(f)
        assert from_file == doc, f"Conteúdo divergente para {tmdb_id}"

    print("Arquivos individuais validados com sucesso.")


def print_missing_summary(documents: list[dict]):
    null_counts = Counter()
    empty_lists = Counter()
    for doc in documents:
        for field, value in doc.items():
            if value is None:
                null_counts[field] += 1
            elif value == []:
                empty_lists[field] += 1

    print("\nResumo de valores ausentes:")
    for field, count in sorted(null_counts.items(), key=lambda x: -x[1]):
        print(f"  {field}: {count} null")

    if empty_lists:
        print("\nResumo de listas vazias preservadas:")
        for field, count in sorted(empty_lists.items(), key=lambda x: -x[1]):
            print(f"  {field}: {count} []")


def print_sample(documents: list[dict]):
    sample = next(doc for doc in documents if doc["tmdb_id"] == 19995)
    print("\nExemplo de documento (tmdb_id 19995):")
    print(json.dumps(sample, ensure_ascii=False, indent=2))


def main():
    PROC_DIR.mkdir(parents=True, exist_ok=True)

    print("Carregando CSVs brutos...")
    movies = load_csv(MOVIES_CSV)
    credits = load_csv(CREDITS_CSV)

    print(f"Movies: {len(movies)} registros")
    print(f"Credits: {len(credits)} registros")

    credits_by_movie_id = {int(row["movie_id"]): row for row in credits}

    print("Combinando e transformando registros...")
    documents = []
    missing_credits = []
    for movie in movies:
        tmdb_id = int(movie["id"])
        credit = credits_by_movie_id.get(tmdb_id)
        if credit is None:
            missing_credits.append(tmdb_id)
            continue
        documents.append(build_document(movie, credit))

    if missing_credits:
        raise ValueError(f"Filmes sem créditos: {missing_credits}")

    save_jsonl(documents, OUTPUT_JSONL)
    print(f"Arquivo JSONL salvo em: {OUTPUT_JSONL}")

    save_individual_files(documents, OUTPUT_DIR_MOVIES)
    print(f"Arquivos individuais salvos em: {OUTPUT_DIR_MOVIES}")

    validate_structure(documents, len(movies))
    validate_relationships(movies, documents)
    validate_files_against_jsonl(documents, OUTPUT_JSONL, OUTPUT_DIR_MOVIES)
    print_missing_summary(documents)
    print_sample(documents)


if __name__ == "__main__":
    main()
