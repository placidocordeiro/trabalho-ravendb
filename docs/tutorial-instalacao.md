# Tutorial: do zero até o RavenDB Studio (Fedora)

Roteiro para o vídeo de instalação. Parte de um Fedora recém-instalado e termina com o RavenDB Studio aberto no navegador.

- **Sistema:** Fedora 43, 44 ou 45 (as versões suportadas pela documentação do Docker).
- **O que vamos instalar:** apenas o **Docker Engine** e o plugin **Docker Compose**, usados pelo terminal.
- **O que NÃO vamos instalar:** o *Docker Desktop*. Ele é uma interface gráfica opcional que roda dentro de uma máquina virtual e não é necessário para este trabalho. Por isso a página de instalação dele pede o `gnome-terminal`, que não faz sentido no Fedora KDE.

Cada etapa traz três partes:
- **Na tela:** o que mostrar no vídeo.
- **Comandos:** o que digitar.
- **Resultado esperado:** o que deve aparecer.

---

## Etapa 0 — Conferir o sistema

**Na tela:** abrir o terminal (Konsole, no KDE).

```bash
cat /etc/os-release
```

**Resultado esperado:** `NAME="Fedora Linux"` e `VERSION="44 (...)"`, ou outra versão suportada.

---

## Etapa 1 — Encontrar a documentação oficial do Docker

**Na tela:**
1. Abrir o navegador e pesquisar no Google: `docker engine install fedora`.
2. Abrir o resultado de **docs.docker.com**: <https://docs.docker.com/engine/install/fedora/>.
3. Mostrar o título **"Install Docker Engine on Fedora"**.

**Fala sugerida:** se o resultado for "Docker Desktop on Fedora", trata-se do aplicativo gráfico, que não vamos usar. O que queremos é o **Docker Engine**.

Todos os comandos das etapas 2 a 5 são copiados dessa página.

---

## Etapa 2 — Remover versões antigas (seção "Uninstall old versions")

Remove pacotes antigos ou não oficiais do Docker que possam existir. Em um sistema limpo, o `dnf` só avisa que não há nada para remover.

```bash
sudo dnf remove docker \
                docker-client \
                docker-client-latest \
                docker-common \
                docker-latest \
                docker-latest-logrotate \
                docker-logrotate \
                docker-selinux \
                docker-engine-selinux \
                docker-engine
```

**Resultado esperado:** `No packages marked for removal` ou mensagem parecida. Não é um erro.

---

## Etapa 3 — Adicionar o repositório oficial (seção "Set up the repository")

O Fedora não traz o Docker oficial nos repositórios padrão. Este comando ensina o `dnf` a baixar os pacotes direto da Docker:

```bash
sudo dnf config-manager addrepo --from-repofile https://download.docker.com/linux/fedora/docker-ce.repo
```

**Resultado esperado:** o comando termina sem erro.

---

## Etapa 4 — Instalar o Docker Engine e o Compose (seção "Install Docker Engine")

```bash
sudo dnf install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

**Na tela:** quando o `dnf` pedir para aceitar a chave GPG, mostrar que a impressão digital confere com a publicada na página da documentação e responder `y`.

| Pacote | Para que serve |
|---|---|
| `docker-ce` | o serviço (daemon) que roda os containers |
| `docker-ce-cli` | o comando `docker` usado no terminal |
| `containerd.io` | o runtime que efetivamente executa os containers |
| `docker-buildx-plugin` | constrói imagens (não usamos, mas faz parte da instalação padrão) |
| `docker-compose-plugin` | o comando `docker compose`, que sobe serviços a partir de um arquivo YAML |

> **Atenção:** o Compose atual é um *plugin*, e o comando é `docker compose` (com espaço). O comando antigo `docker-compose` (com hífen) é outra ferramenta, descontinuada, que não é instalada aqui.

---

## Etapa 5 — Iniciar o Docker e testar (seções "Start Docker Engine" e "Verify")

```bash
sudo systemctl enable --now docker
```

`enable` faz o Docker iniciar junto com o sistema, e `--now` também o inicia agora.

```bash
sudo docker run hello-world
```

**Resultado esperado:** o Docker baixa a imagem de teste e imprime `Hello from Docker!`.

> Se `journalctl -u docker` mostrar `failed to find iptables`, a página oficial manda rodar:
> `sudo alternatives --set iptables /usr/bin/iptables-nft` e depois `sudo systemctl restart docker`.

---

## Etapa 6 — Usar o Docker sem `sudo` (pós-instalação)

**Na tela:** na mesma documentação, abrir **"Linux post-installation steps for Docker Engine"**: <https://docs.docker.com/engine/install/linux-postinstall/>.

```bash
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```

- `groupadd` cria o grupo `docker`. Se ele já existir, aparece um aviso, sem problema.
- `usermod -aG` adiciona o seu usuário a esse grupo.
- `newgrp` aplica o grupo no terminal atual. Nos outros terminais, a mudança só vale depois de **sair da sessão e entrar de novo** (ou reiniciar).

Teste sem `sudo`:

```bash
docker run hello-world
```

Confira as versões instaladas:

```bash
docker --version
docker compose version
```

**Resultado esperado:** algo como `Docker version 29.x` e `Docker Compose version v5.x`.

> **E as variáveis de ambiente do sistema?** Com a instalação via `dnf`, nenhuma é necessária: os comandos já ficam em `/usr/bin`, que está no `PATH`. As variáveis de ambiente que importam neste projeto são as **do container do RavenDB**, configuradas na etapa 8.

---

## Etapa 7 — Encontrar a imagem oficial do RavenDB

**Na tela:**
1. Pesquisar no Google: `ravendb docker`.
2. Abrir a página oficial da imagem no Docker Hub: <https://hub.docker.com/r/ravendb/ravendb>.
3. Abrir também a documentação do RavenDB sobre containers: <https://docs.ravendb.net/7.1/start/containers/image-usage>. Mostrar os trechos sobre as variáveis `RAVEN_Setup_Mode` e `RAVEN_Security_UnsecuredAccessAllowed` e sobre o volume de dados `/var/lib/ravendb/data`.

Baixar a imagem (comando mostrado no Docker Hub):

```bash
docker pull ravendb/ravendb
```

**Resultado esperado:** o download de várias camadas (cerca de 380 MB) e, ao final, `Status: Downloaded newer image for ravendb/ravendb:latest`.

```bash
docker image ls ravendb/ravendb
```

---

## Etapa 8 — Configurar o RavenDB com Docker Compose

Em vez de digitar um `docker run` enorme toda vez, descrevemos o serviço no arquivo `docker-compose.yml`, na raiz do projeto:

```yaml
services:
  ravendb:
    image: ravendb/ravendb:latest
    container_name: ravendb
    ports:
      - "8080:8080"
    environment:
      - RAVEN_Setup_Mode=None
      - RAVEN_Security_UnsecuredAccessAllowed=PrivateNetwork
    volumes:
      - ravendb_data:/var/lib/ravendb/data
    restart: unless-stopped

volumes:
  ravendb_data:
```

| Linha | Significado |
|---|---|
| `image` | a imagem oficial baixada na etapa 7 |
| `container_name` | nome fixo do container, para facilitar os comandos (`docker logs ravendb`) |
| `ports: "8080:8080"` | a porta 8080 do computador aponta para a porta 8080 do container, onde fica o Studio |
| `RAVEN_Setup_Mode=None` | pula o assistente de configuração segura (certificados/HTTPS), que é desnecessário em ambiente local |
| `RAVEN_Security_UnsecuredAccessAllowed=PrivateNetwork` | permite acesso sem certificado, mas só a partir da rede local/privada |
| `volumes` | guarda os bancos em um volume do Docker, para que os dados sobrevivam quando o container for removido |
| `restart: unless-stopped` | reinicia o RavenDB automaticamente, a menos que você o pare manualmente |

**Variáveis de ambiente do RavenDB:** toda configuração do servidor pode ser passada como variável de ambiente com o prefixo `RAVEN_`, trocando os pontos do nome da configuração por `_`. Por exemplo, a configuração `Setup.Mode` vira `RAVEN_Setup_Mode`.

> Esta configuração é **apenas para desenvolvimento local**. O acesso não usa senha nem certificado.

---

## Etapa 9 — Subir o RavenDB

Na pasta do projeto (onde está o `docker-compose.yml`):

```bash
docker compose up -d
```

`-d` (detached) roda o container em segundo plano e devolve o terminal.

```bash
docker ps
docker logs ravendb
```

**Resultado esperado:**
- `docker ps` lista o container `ravendb` com status `Up` e a porta `0.0.0.0:8080->8080/tcp`.
- No log, aparecem o banner do RavenDB e a linha `Server started, listening to requests...`.

Teste rápido pelo terminal (opcional):

```bash
curl http://localhost:8080/build/version
```

**Resultado esperado:** algo como `{"ProductVersion":"7.2","FullVersion":"7.2.8", ...}`.

---

## Etapa 10 — Abrir o RavenDB Studio

**Na tela:**
1. No navegador, acessar <http://localhost:8080>.
2. Na primeira vez, o Studio mostra o **contrato de licença (EULA)**. Rolar até o fim e aceitar.
3. O painel do Studio abre. A licença usada é a **AGPL – Open Source**, gratuita e suficiente para o trabalho.

**Próximo passo (opcional no vídeo):** em **Databases → New database**, criar o banco **`Movies`**. É esse o nome que o script `scripts/import_ravendb.py` usa para importar os filmes.

---

## Comandos do dia a dia

| Comando | O que faz |
|---|---|
| `docker compose up -d` | sobe o RavenDB |
| `docker compose stop` | para o container (mais rápido para ligar depois) |
| `docker compose down` | para e remove o container; **os dados continuam no volume** |
| `docker compose down -v` | remove o container **e o volume**, apagando todos os bancos |
| `docker logs -f ravendb` | acompanha o log em tempo real (`Ctrl+C` para sair) |
| `docker ps` | lista os containers em execução |

## Problemas comuns

| Sintoma | Causa provável e solução |
|---|---|
| `permission denied while trying to connect to the Docker daemon socket` | Seu usuário ainda não está no grupo `docker` nesta sessão. Refaça a etapa 6 e saia/entre da sessão. |
| `docker-compose: command not found` | Use `docker compose` (com espaço). Veja a etapa 4. |
| `Cannot connect to the Docker daemon` | O serviço está parado: `sudo systemctl start docker`. |
| `port is already allocated` ao subir | Outro programa usa a porta 8080. Descubra qual com `sudo ss -ltnp \| grep 8080` ou troque para `"8081:8080"` no YAML e acesse `localhost:8081`. |
| O navegador não abre o Studio logo após o `up` | O servidor leva alguns segundos para iniciar. Aguarde a linha `Server started` em `docker logs ravendb`. |
