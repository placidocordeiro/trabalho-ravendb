# Sobe o RavenDB em segundo plano
up:
    docker compose up -d

# Para e remove o container (os dados ficam salvos no volume)
down:
    docker compose down

# Para o container sem removê-lo (mais rápido para ligar depois)
stop:
    docker compose stop

# Mostra os containers que estão rodando
status:
    docker ps

# Volta o banco Movies ao estado inicial (apaga, recria e reimporta os 4.803 filmes)
reset:
    venv/bin/python scripts/reset_ravendb.py

# Demonstra o CRUD completo via script
crud:
    venv/bin/python scripts/crud_ravendb.py
