# Kraken — Gerenciador de LCD e sensores do NZXT Kraken para Linux

> Monitore os sensores e controle o visor LCD do seu water cooler **NZXT Kraken** no
> **Linux** — sem o software oficial (que só existe para Windows). Interface de **linha de
> comando** e **gráfica (GUI)**, com carrossel de imagens, reprodução de GIF e telas de
> temperatura do sistema.

![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)
![Platform: Linux](https://img.shields.io/badge/Platform-Linux-informational.svg)
![Not affiliated with NZXT](https://img.shields.io/badge/NZXT-não%20afiliado-lightgrey.svg)

---

## ⚡ Início rápido

```bash
# 1. Instalar (com interface gráfica)
pip install --user ".[gui]"

# 2. Permitir acesso ao dispositivo sem root (uma vez só)
sudo cp assets/udev/99-kraken.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
# reconecte o cabo USB do Kraken

# 3. Conferir e usar
kraken device list           # detecta o dispositivo
kraken status                # lê temperatura/RPM
kraken lcd static imagem.png # envia uma imagem para o visor
kraken-gui                   # abre a interface gráfica
```

A documentação completa (Manual do Usuário e Documentação Técnica) está **logo abaixo neste
README** e também em arquivos separados na pasta [`docs/`](docs/).

---

## ⚠️ Avisos importantes (Disclaimers)

- **Marca registrada:** *NZXT* e *Kraken* são marcas da **NZXT, Inc.** Este é um projeto
  **independente e de código aberto**, mantido pela comunidade, **sem qualquer afiliação,
  endosso ou patrocínio da NZXT**. O nome é usado apenas para identificar a compatibilidade
  de hardware.
- **Somente leitura do dispositivo:** o Kraken **lê** sensores (temperatura, RPM) e **escreve
  conteúdo no visor** (imagens, animações, telas geradas). Ele **não** altera a velocidade da
  bomba, a curva dos ventiladores nem a iluminação RGB.
- **Sem garantias:** este software é fornecido "COMO ESTÁ", **sem nenhuma garantia**, nos
  termos da Licença Pública Geral GNU v3 (veja [LICENSE](LICENSE)). Ele se comunica com
  hardware via USB; **use por sua conta e risco**.
- **Mídia de exemplo não incluída:** imagens e GIFs de demonstração **não acompanham** este
  repositório por questões de direitos autorais. Use seus próprios arquivos (PNG, JPG, BMP,
  WebP ou GIF).

---

## 📜 Licença

Distribuído sob a **GNU General Public License v3.0 ou posterior (GPL-3.0-or-later)**.
Veja o arquivo [LICENSE](LICENSE) para o texto completo.

> A escolha da GPLv3 é também uma exigência de compatibilidade: o projeto utiliza a
> biblioteca **liquidctl**, licenciada sob GPL-3.0.

---

## 🙏 Créditos e software de código aberto utilizado

Este projeto só é possível graças aos seguintes projetos de código aberto:

| Projeto | Licença | Uso no Kraken |
|---|---|---|
| [liquidctl](https://github.com/liquidctl/liquidctl) | GPL-3.0-or-later | Comunicação USB com o dispositivo e operações de LCD |
| [Click](https://github.com/pallets/click) | BSD-3-Clause | Framework da interface de linha de comando |
| [Pillow](https://github.com/python-pillow/Pillow) | HPND (MIT-CMU) | Validação, redimensionamento e renderização de imagens |
| [psutil](https://github.com/giampaolo/psutil) | BSD-3-Clause | Temperaturas de CPU e métricas do sistema |
| [tomli-w](https://github.com/hukkin/tomli-w) | MIT | Escrita do arquivo de configuração TOML |
| [PySide6 / Qt](https://wiki.qt.io/Qt_for_Python) | LGPL-3.0 *(opcional)* | Interface gráfica (GUI) |
| [Python](https://www.python.org/) | PSF License | Linguagem base (≥ 3.12) |

Agradecimento especial ao driver de kernel **`nzxt-kraken3`** (parte do kernel Linux,
GPL-2.0), que expõe os sensores via `hwmon`/sysfs e é a fonte primária de leitura usada aqui.

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir *issues* (relatos de bug, pedidos
de recurso) e *pull requests*. Ao contribuir, mantenha o estilo do projeto: núcleo (`core`)
sem dependências de UI, testes em `tests/` com `pytest`, e Python 3.12+.

---

# 📚 Documentação

Abaixo, na sequência: **(1) Manual do Usuário** — para qualquer pessoa, mesmo sem
conhecimento técnico — e **(2) Documentação Técnica** — arquitetura, decisões de projeto e
referência interna. Os mesmos textos estão disponíveis separadamente em
[`docs/MANUAL_DO_USUARIO.md`](docs/MANUAL_DO_USUARIO.md) e
[`docs/DOCUMENTACAO_TECNICA.md`](docs/DOCUMENTACAO_TECNICA.md).

---

# Manual do Usuário — Kraken

> **Kraken** é um programa para Linux que mostra **informações** e **imagens** no
> visor (a telinha redonda/LCD) do seu water cooler **NZXT Kraken**.

Este manual foi escrito para qualquer pessoa, mesmo sem conhecimento técnico.
Vá lendo na ordem: cada seção parte da anterior.

---

## Índice

1. [O que é o Kraken (e o que ele NÃO faz)](#1-o-que-é-o-kraken-e-o-que-ele-não-faz)
2. [O que você precisa](#2-o-que-você-precisa)
3. [Instalação passo a passo](#3-instalação-passo-a-passo)
4. [Primeiros passos](#4-primeiros-passos)
5. [Usando pela interface gráfica (a janela)](#5-usando-pela-interface-gráfica-a-janela)
6. [Usando pela linha de comando (o terminal)](#6-usando-pela-linha-de-comando-o-terminal)
7. [Deixando o Kraken trabalhar sozinho](#7-deixando-o-kraken-trabalhar-sozinho)
8. [Perguntas frequentes e solução de problemas](#8-perguntas-frequentes-e-solução-de-problemas)
9. [Glossário](#9-glossário)

---

## 1. O que é o Kraken (e o que ele NÃO faz)

O NZXT Kraken é um water cooler — uma peça que refrigera o processador do computador.
Os modelos mais novos têm um **pequeno visor (LCD)** no centro da bomba. De fábrica, esse
visor é controlado por um aplicativo que só existe para Windows.

O **Kraken** (este programa) é a alternativa para quem usa **Linux**. Pense nele como um
**"controle remoto do visor"**: com ele você decide o que aparece naquela telinha —
uma imagem, uma animação, a temperatura da CPU, etc. — e também consegue **ler** a
temperatura da água e a velocidade da bomba e do ventilador.

### O que o Kraken faz

- 📊 **Mostra os sensores**: temperatura do líquido, rotação da bomba (RPM) e do ventilador.
- 🖼️ **Põe uma imagem** no visor (PNG, JPG, BMP, WebP).
- 🎞️ **Toca um GIF animado** no visor.
- 🌡️ **Mostra a temperatura da CPU/GPU** desenhada na telinha.
- 🔁 **Faz um "carrossel"**: várias imagens/telas se alternando automaticamente.
- 🔆 **Ajusta o brilho** e a **orientação** (rotação) do visor.

### O que o Kraken **NÃO** faz

O Kraken é **somente leitura** no que diz respeito ao funcionamento do cooler. Ou seja:

- ❌ Ele **não** muda a velocidade da bomba.
- ❌ Ele **não** controla a curva dos ventiladores.
- ❌ Ele **não** mexe na iluminação RGB.

Ele só **lê** esses números e **escreve** conteúdo no **visor**. Nada que ele faça
coloca a refrigeração do seu computador em risco.

---

## 2. O que você precisa

- Um computador com **Linux**.
- Um water cooler **NZXT Kraken** com visor. Modelos suportados:

  | Modelo | Tamanho do visor |
  |---|---|
  | Kraken 2023 Standard | 240×240 |
  | Kraken 2023 Elite | 640×640 |
  | Kraken 2024 Plus | 240×240 |
  | Kraken 2024 Elite RGB | 640×640 |

- Uma **permissão** para o programa conversar com o aparelho via USB. Isso é resolvido
  uma única vez, instalando um pequeno arquivo de "regra" (explicado na próxima seção).
  Sem essa permissão, você teria que usar o programa como administrador (`sudo`) toda vez —
  o que não é recomendado.

---

## 3. Instalação passo a passo

> As etapas abaixo usam o **Terminal** (aquele programa de texto onde você digita comandos).
> Não tenha medo: é só copiar e colar.

### Passo 1 — Instalar o programa

O Kraken é um programa em Python. A forma recomendada é instalar com `pip`:

```bash
# instala o Kraken junto com a interface gráfica
pip install --user ".[gui]"
```

> Se você só quer a linha de comando (sem janela), pode instalar sem o `[gui]`.

### Passo 2 — Dar permissão de acesso ao aparelho (faz uma vez só)

O projeto já traz pronto o arquivo de permissão. Copie-o para a pasta do sistema e
recarregue as regras:

```bash
sudo cp assets/udev/99-kraken.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
```

Depois disso, **desconecte e reconecte** o cabo USB do Kraken (ou reinicie o computador)
para a permissão valer.

### Passo 3 — Conferir se está funcionando

```bash
kraken device list
```

Se aparecer o nome do seu Kraken, está tudo certo! 🎉
Se der erro, pule para a seção [8. Solução de problemas](#8-perguntas-frequentes-e-solução-de-problemas).

---

## 4. Primeiros passos

### Preparar o aparelho

Antes de enviar imagens, é bom "acordar" o aparelho uma vez:

```bash
kraken device init
```

Isso mostra informações como versão de firmware, número de série e o tamanho do visor.

### Ver as temperaturas

```bash
kraken status
```

Você verá algo como:

```
Liquid Temp: 29.1 C
Pump Speed:  2703 RPM
Fan Speed:   1050 RPM
```

Quer acompanhar ao vivo? Adicione `--watch` (atualiza sozinho; pare com `Ctrl+C`):

```bash
kraken status --watch
```

---

## 5. Usando pela interface gráfica (a janela)

Se você instalou com `[gui]`, abra a janela com:

```bash
kraken-gui
```

A janela tem **5 abas** no topo. Veja o que cada uma faz:

### Aba "Status"

Mostra três mostradores grandes, atualizados a cada 2 segundos:

- **Temperatura do líquido** (em °C)
- **Velocidade da bomba** (RPM)
- **Velocidade do ventilador** (RPM)

É a aba para **monitorar** o cooler.

### Aba "LCD" (a mais usada)

Aqui você controla o que aparece no visor:

1. Clique em **"Escolher Imagem/GIF…"** e selecione um arquivo (PNG, JPG, BMP, WebP ou GIF).
2. Veja uma **prévia** de como vai ficar.
3. Clique em **Upload** para enviar a imagem.
4. Se escolher um **GIF**, ele começa a tocar e aparece o botão **"Stop GIF"** (com a
   contagem dos quadros, ex.: *"frame 5/120"*). Clique nele para parar a animação.
5. Use o **controle de brilho** (0 a 100%) e clique em **Aplicar**.
6. Use a **orientação** (0°, 90°, 180° ou 270°) para girar a imagem e clique em **Aplicar**.
7. O botão **"Modo Temperatura do Líquido"** volta o visor para a tela nativa de temperatura.

### Aba "Carousel" (carrossel)

Monta uma sequência de telas que se alternam sozinhas:

1. Use **"Adicionar Imagem…"** (pode escolher várias de uma vez).
2. Ou **"Adicionar SysInfo"** (slide com a temperatura da CPU/GPU).
3. Ou **"Adicionar Liquid"** (slide com a temperatura do líquido nativa).
4. Defina por **quantos segundos** cada slide fica na tela.
5. Reordene arrastando os itens na lista.
6. Clique em **Iniciar** para começar. Você pode **Pausar/Retomar** e **Parar** quando quiser.

A sua lista é **salva automaticamente**, então ela continua lá na próxima vez que abrir.

### Aba "System Info" (informações do sistema)

Desenha a temperatura do computador no visor:

1. Marque **"Mostrar Temperatura da CPU"** e/ou **"Mostrar Temperatura da GPU"**.
2. Escolha de quantos em quantos segundos atualizar.
3. Clique em **Iniciar**. Clique em **Salvar** para guardar a configuração.

### Aba "Config"

Mostra (somente para leitura) os dados do aparelho — nome, firmware, resolução, série —
e tem um botão para **abrir o arquivo de configuração** num editor de texto.

---

## 6. Usando pela linha de comando (o terminal)

Quem prefere o terminal tem **todos** os recursos disponíveis. Abaixo, "receitas" prontas.

### Mostrar uma imagem no visor

```bash
kraken lcd static /caminho/para/minha-imagem.png
```

### Tocar um GIF animado

```bash
kraken lcd gif /caminho/para/animacao.gif
```

Por padrão, ele toca **para sempre** (pare com `Ctrl+C`). Para tocar um número fixo de vezes:

```bash
kraken lcd gif /caminho/para/animacao.gif --loops 3
```

> 💡 Os GIFs tocam no máximo a cerca de **8 quadros por segundo** — é um limite do
> próprio aparelho, não do programa. Por isso animações muito rápidas ficam mais lentas.

### Ajustar brilho e rotação

```bash
kraken lcd brightness 75          # brilho em 75%
kraken lcd orientation 90         # gira o visor 90 graus
```

### Voltar para a tela de temperatura nativa

```bash
kraken lcd liquid
```

### Mostrar a temperatura da CPU no visor

```bash
kraken sysinfo config --cpu --no-gpu --refresh 2.5   # configura
kraken sysinfo start                                 # começa a mostrar
```

### Montar um carrossel pelo terminal

```bash
kraken carousel add /fotos/logo.png --seconds 15     # adiciona uma imagem
kraken carousel add --sysinfo --seconds 20           # adiciona a tela de CPU/GPU
kraken carousel add --liquid --seconds 10            # adiciona a tela de líquido
kraken carousel list                                 # confere a lista
kraken carousel start                                # inicia (Ctrl+C para parar)
```

### Ver e editar as configurações

```bash
kraken config show      # mostra tudo
kraken config path      # mostra ONDE fica o arquivo de configuração
kraken config edit      # abre o arquivo no seu editor
```

> 📁 O arquivo de configuração fica em `~/.config/kraken/config.toml`.

---

## 7. Deixando o Kraken trabalhar sozinho

Você pode fazer o carrossel (ou o ícone na bandeja) iniciar junto com o computador,
sem precisar abrir nada manualmente.

### Ícone na bandeja do sistema

```bash
kraken tray
```

Isso coloca um ícone perto do relógio, mostrando a temperatura do líquido ao passar o mouse.

### Iniciar automaticamente com o sistema (systemd)

O projeto traz "serviços" prontos. Para o carrossel iniciar sozinho:

```bash
cp assets/systemd/kraken-carousel.service ~/.config/systemd/user/
systemctl --user enable kraken-carousel
systemctl --user start kraken-carousel
```

Para o ícone da bandeja iniciar sozinho, faça o mesmo com `kraken-tray.service`.

> ⚠️ **Atenção:** o arquivo de serviço do carrossel, como vem hoje, usa uma opção
> (`--foreground`) que **a versão atual do programa não reconhece**. Se o serviço não
> iniciar, edite o arquivo e troque a linha `ExecStart` para usar simplesmente
> `kraken carousel start` (sem `--foreground`). Veja mais detalhes na documentação técnica.

---

## 8. Perguntas frequentes e solução de problemas

**"Nenhum dispositivo encontrado" / o programa não acha o Kraken.**
- Confirme que o cabo USB interno do Kraken está conectado.
- Verifique se você instalou a regra de permissão (Passo 2 da instalação) e reconectou o cabo.
- Teste com `kraken device list`.

**"Pede senha / só funciona com `sudo`."**
- Isso quer dizer que a regra de permissão (udev) não foi aplicada. Refaça o Passo 2 da
  instalação e reconecte o cabo USB (ou reinicie).

**"O GIF está lento ou 'travado'."**
- Isso é esperado em animações rápidas. O visor aceita no máximo ~8 quadros por segundo.
- Na primeira vez, o programa precisa "preparar" o GIF (separar os quadros). As próximas
  vezes são mais rápidas, pois ele reaproveita o que já preparou
  (guardado em `~/.cache/kraken/gif_frames/`).

**"A imagem não aparece / aparece cortada."**
- Use imagens **quadradas**. O visor é redondo/quadrado (240×240 ou 640×640), então
  imagens muito largas ou muito altas podem ficar estranhas.
- Formatos aceitos: PNG, JPG, JPEG, BMP, WebP (e GIF para animação).

**"Não aparece a temperatura da CPU."**
- Nem todo computador expõe esse sensor. Tente `--gpu` em vez de `--cpu`, ou veja se o
  `kraken status` (temperatura do líquido) funciona — esse quase sempre funciona.

---

## 9. Glossário

- **LCD / visor**: a telinha no centro da bomba do Kraken.
- **Sensor**: medidor. Aqui: temperatura do líquido e rotação da bomba/ventilador.
- **RPM**: "rotações por minuto" — a velocidade de giro da bomba ou do ventilador.
- **Firmware**: o "programa interno" que vem de fábrica dentro do aparelho.
- **Carrossel**: sequência de telas que se alternam automaticamente.
- **Terminal**: a janela preta onde você digita comandos.
- **udev**: o sistema do Linux que decide quem pode usar cada aparelho USB.
- **systemd**: o sistema do Linux que inicia programas automaticamente.
- **GIF**: tipo de imagem que contém uma pequena animação.
- **Brilho / orientação**: intensidade da luz do visor e o ângulo de rotação da imagem.

---

*Quer entender como o Kraken funciona por dentro? Veja a **Documentação Técnica** a seguir
neste README (também em [`docs/DOCUMENTACAO_TECNICA.md`](docs/DOCUMENTACAO_TECNICA.md)).*


---

# Documentação Técnica — Kraken

Gerenciador de LCD e sensores do **NZXT Kraken** para Linux.

Este documento descreve a especificação, a arquitetura, as decisões críticas e a
referência interna do projeto, de forma que qualquer pessoa com conhecimento em
informática consiga entender o que foi feito, como foi projetado, estruturado e
desenvolvido. Para uso final, consulte o **Manual do Usuário** acima neste README (também em
[`docs/MANUAL_DO_USUARIO.md`](docs/MANUAL_DO_USUARIO.md)).

---

## Índice

1. [Visão geral e objetivos](#1-visão-geral-e-objetivos)
2. [Stack e requisitos](#2-stack-e-requisitos)
3. [Arquitetura em camadas](#3-arquitetura-em-camadas)
4. [Estrutura de diretórios](#4-estrutura-de-diretórios)
5. [Módulos em detalhe](#5-módulos-em-detalhe)
6. [Decisões críticas de projeto](#6-decisões-críticas-de-projeto)
7. [Modelo de dados e esquema de configuração](#7-modelo-de-dados-e-esquema-de-configuração)
8. [Referência da CLI e mapeamento da GUI](#8-referência-da-cli-e-mapeamento-da-gui)
9. [Fluxos principais](#9-fluxos-principais)
10. [Suporte multi-modelo, udev e systemd](#10-suporte-multi-modelo-udev-e-systemd)
11. [Testes](#11-testes)
12. [Problemas conhecidos e evoluções futuras](#12-problemas-conhecidos-e-evoluções-futuras)

---

## 1. Visão geral e objetivos

O **Kraken** é uma ferramenta em Python para Linux que **monitora sensores** e
**gerencia o visor LCD** dos water coolers NZXT Kraker da geração com tela.

Princípios que guiaram o projeto:

- **Somente leitura do dispositivo**: o programa lê sensores (temperatura, RPM) e escreve
  **conteúdo no visor** (imagens, animações, telas geradas). Ele **não** altera curva da
  bomba, dos ventiladores nem iluminação RGB. Isso elimina toda uma classe de riscos
  operacionais sobre a refrigeração.
- **Núcleo (`core`) independente de UI**: a lógica de negócio não importa nada de Click
  (CLI) nem de PySide6 (GUI). As duas interfaces consomem o mesmo núcleo, garantindo
  paridade de comportamento entre CLI e GUI.
- **Simplicidade operacional para um cenário de usuário único / dispositivo único**:
  sem daemon próprio, sem DBus, sem servidor. As operações em segundo plano usam
  *threads* simples.
- **`hwmon`/`sysfs` como fonte primária de sensores**: leitura rápida e não bloqueante,
  evitando contenção no canal USB; `liquidctl` é o caminho de *fallback*.

---

## 2. Stack e requisitos

| Item | Valor |
|---|---|
| Linguagem | Python **≥ 3.12** |
| Layout | `src/` layout |
| CLI | **Click** ≥ 8 |
| GUI | **PySide6 (Qt6)** ≥ 6.5 *(opcional)* |
| Comunicação USB | **liquidctl** ≥ 1.14 *(como biblioteca, não subprocess)* |
| Imagens | **Pillow** ≥ 10 |
| Sistema/temperaturas | **psutil** ≥ 5.9 |
| Config (escrita) | **tomli_w** ≥ 1.0 *(leitura via `tomllib` da stdlib)* |
| Testes | **pytest** ≥ 8, pytest-cov, ruff, mypy |

**Pontos de entrada** (`pyproject.toml`):

```toml
[project.scripts]
kraken = "kraken.cli.app:cli"

[project.gui-scripts]
kraken-gui = "kraken.gui.app:main"
```

---

## 3. Arquitetura em camadas

A aplicação é organizada em camadas, das fontes de hardware (embaixo) até as interfaces
de usuário (em cima). As setas indicam dependência ("usa").

```
        ┌─────────────────────────┐   ┌─────────────────────────┐
        │        CLI (Click)      │   │       GUI (PySide6)     │
        │   src/kraken/cli/       │   │   src/kraken/gui/       │
        └────────────┬────────────┘   └────────────┬────────────┘
                     │  (ambas dependem só do núcleo)
        ┌────────────┴───────────────────────────────┴───────────┐
        │                    NÚCLEO / serviços                    │
        │  core/  ·  carousel/  ·  sysinfo/  ·  config/           │
        │  (sem nenhuma importação de Click ou PySide6)           │
        └───────┬──────────────────────────────────────┬─────────┘
                │                                        │
        ┌───────┴────────┐                      ┌────────┴────────┐
        │  hwmon/ (sysfs)│  ← fonte primária    │   liquidctl     │ ← fallback / LCD
        │  /sys/class/.. │                      │   (USB HID)     │
        └────────────────┘                      └─────────────────┘
                          ▼                                ▼
                         ┌──────────────────────────────────┐
                         │     NZXT Kraken (hardware)        │
                         └──────────────────────────────────┘
```

Observações:

- **Leitura de sensores** prefere `hwmon` (sysfs) e cai para `liquidctl` se necessário.
- **Escrita no LCD** (imagens, brilho, orientação, modo líquido) é sempre via `liquidctl`.
- `carousel`, `sysinfo` e `config` são serviços que orquestram o `core`, mas continuam
  livres de qualquer dependência de UI.

---

## 4. Estrutura de diretórios

```
src/kraken/
├── core/                # Lógica central, independente de UI
│   ├── device.py        # KrakenDevice: ciclo de vida USB, set_screen, lock
│   ├── sensors.py       # read_sensors(): abstração hwmon/liquidctl
│   ├── lcd.py           # validação + upload de imagem, brilho, orientação, modo líquido
│   ├── models.py        # dataclasses de dados e de configuração
│   ├── gif.py           # extração/cache de frames + reprodução de GIF
│   └── exceptions.py    # hierarquia de exceções de domínio
├── hwmon/               # Leitura direta de sysfs
│   ├── discovery.py     # find_kraken_hwmon()
│   └── reader.py        # read_hwmon_sensors()
├── carousel/            # Engine de carrossel de imagens
│   ├── playlist.py      # Playlist (add/remove/move/clear/validate)
│   └── engine.py        # CarouselEngine: thread de ciclo em segundo plano
├── sysinfo/             # Renderização de stats do sistema para o LCD
│   ├── collector.py     # collect_stats() (CPU/GPU/uso)
│   └── renderer.py      # render_stats_image() + SysInfoEngine
├── config/              # Configuração TOML (XDG)
│   ├── paths.py         # diretórios XDG (~/.config/kraken/…)
│   ├── schema.py        # (de)serialização dict ↔ dataclasses
│   └── manager.py       # load_config() / save_config()
├── cli/                 # Interface de linha de comando (Click)
│   ├── app.py           # grupo raiz `cli` + versão
│   └── commands/        # device, status, lcd, carousel, sysinfo, tray, config_cmd
└── gui/                 # Interface gráfica (PySide6/Qt6)
    ├── app.py           # main()
    ├── main_window.py   # MainWindow (5 abas)
    ├── threads.py       # SensorWorker, LCDUploadWorker, GifPlaybackWorker
    ├── tray.py          # ícone de bandeja
    └── widgets/         # status_panel, lcd_panel, carousel_panel, sysinfo_panel, device_info
```

Recursos de apoio fora de `src/`:

```
assets/
├── sample_config.toml         # config de exemplo comentada
├── udev/99-kraken.rules        # permissão de acesso USB sem root
└── systemd/                    # serviços de usuário (carousel, tray)
scripts/gif_black_bg.py         # utilitário de conversão de GIF (fundo preto)
tests/                          # 133 testes (pytest)
```

---

## 5. Módulos em detalhe

### 5.1 `core/device.py` — wrapper thread-safe do dispositivo

`KrakenDevice` encapsula uma instância de dispositivo do `liquidctl` e serializa todas as
operações USB através de um `threading.Lock` interno (evita contenção entre leitura de
sensores e upload para o LCD).

```python
class KrakenDevice:
    @classmethod
    def find() -> KrakenDevice      # descobre o primeiro Kraken suportado pelo PID
    def connect() -> None           # abre a conexão USB
    def initialize() -> DeviceInfo  # consulta firmware, série, resolução do LCD
    def disconnect() -> None
    def get_status() -> list        # lê sensores via liquidctl
    def set_screen(mode, value=None) -> None  # imagem / brilho / orientação / modo líquido
    def __enter__/__exit__          # suporte a context manager
```

Constantes relevantes: `KRAKEN_LCD_PIDS` (PIDs suportados) e `LCD_RESOLUTIONS`
(mapa PID → resolução).

### 5.2 `core/sensors.py` — abstração de sensores

```python
def read_sensors(device, hwmon_path) -> SensorData
```

Prefere `hwmon` (leitura de sysfs, rápida e não bloqueante) e cai para `liquidctl`
(`_read_from_liquidctl`) quando o `hwmon` não está disponível. Devolve um `SensorData`
com `liquid_temp_c`, `pump_rpm`, `fan_rpm` e `timestamp` (relógio monotônico).

### 5.3 `core/lcd.py` — operações de LCD

```python
def validate_image_file(path) -> Path     # existência + extensão suportada
def upload_static(device, path)           # imagem fixa
def upload_gif(device, path)              # delega para core.gif
def upload_image(device, path)            # auto-detecta tipo e roteia
def set_liquid_mode(device)               # tela nativa de temperatura
def set_brightness(device, value)         # 0–100
def set_orientation(device, degrees)      # 0/90/180/270
```

Constantes: `SUPPORTED_STATIC_EXTENSIONS` = {.png, .jpg, .jpeg, .bmp, .webp};
`SUPPORTED_GIF_EXTENSIONS` = {.gif}; `BRIGHTNESS_MIN/MAX` = 0/100;
`VALID_ORIENTATIONS` = (0, 90, 180, 270).

### 5.4 `core/models.py` — modelos de dados

Dataclasses imutáveis para **dados** e mutáveis (com validação em `__post_init__`) para
**configuração**:

- `SensorData(liquid_temp_c, pump_rpm, fan_rpm, timestamp)` *(frozen)*
- `DeviceInfo(description, firmware_version, lcd_resolution, serial_number, product_id)` *(frozen)*
- `LCDConfig(brightness=50, orientation=0)` — valida faixa/valores
- `CarouselItem(path, display_seconds=10.0, media_type="")` — `is_special` p/ `sysinfo`/`liquid`
- `CarouselConfig(enabled=False, items=[], loop=True)`
- `SysInfoConfig(enabled=False, show_cpu_temp=True, show_gpu_temp=False, refresh_seconds=5.0)`
- `TrayConfig(enabled=False, show_temp=True)`
- `AppConfig(device_serial="", lcd, carousel, sysinfo, tray)` — raiz da configuração

### 5.5 `core/gif.py` — reprodução de GIF (contornando o firmware)

O firmware 2.x **ignora a animação nativa** de GIFs. A solução: **explodir o GIF em
quadros PNG**, guardá-los em cache em disco e reproduzi-los como uploads estáticos
sequenciais.

```python
def extract_frames(gif_path, cache_root=CACHE_ROOT) -> list[GifFrame]
def play_animated_gif(device, gif_path, loops=0, stop_event=None,
                      deadline=None, on_frame=None, on_error=None,
                      cache_root=CACHE_ROOT)
```

- Quadros redimensionados para **240×240** com reamostragem **LANCZOS** e salvos como
  `frame_NNNN.png`.
- Cache em `~/.cache/kraken/gif_frames/<hash>/`, com `manifest.txt` (nome do quadro +
  duração). A **chave de cache** é um *fingerprint* estável: `mtime + tamanho +
  hash dos primeiros 4 KB` do arquivo. Apagar o cache força a re-extração.
- **Teto de hardware** `MIN_FRAME_INTERVAL_MS = 120` (~8 fps): durações abaixo disso são
  limitadas.
- `loops=0` = infinito; `stop_event`/`deadline` permitem cancelamento cooperativo entre
  quadros; `on_frame(i, total)` atualiza a UI.

### 5.6 `core/exceptions.py` — hierarquia de erros

`KrakenError` (base) → `DeviceNotFoundError`, `DeviceConnectionError`,
`DeviceNotInitializedError`, `LCDError` (→ `ImageValidationError`), `CarouselError`,
`ConfigError`, `HwmonNotFoundError`.

### 5.7 `hwmon/` — leitura direta de sysfs

- `discovery.find_kraken_hwmon(base=None)`: varre `/sys/class/hwmon/*/name` procurando
  drivers `kraken2023` / `nzxt-kraken3` / `kraken3`; devolve o diretório do hwmon.
- `reader.read_hwmon_sensors(hwmon_path)`: lê `temp1_input` (m°C → °C ÷1000),
  `fan1_input` (bomba, RPM) e `fan2_input` (ventilador, RPM); devolve `SensorData`.

### 5.8 `carousel/` — playlist e engine

- `playlist.Playlist`: `add`, `add_special` (`sysinfo`/`liquid`), `remove`, `move`,
  `clear`, `validate_paths`. Valida caminhos de imagem (exceto itens especiais) e
  auto-detecta o tipo pela extensão.
- `engine.CarouselEngine(device, playlist, loop=True, on_item_changed=None, on_error=None,
  sysinfo_refresh_seconds=5.0)`: roda uma *thread* daemon que percorre os itens. Para cada
  item: dispara `on_item_changed`, trata o tipo (`liquid` → modo nativo; `sysinfo` →
  renderização periódica; `gif` → reprodução por quadros; estático → `upload_image`),
  espera `display_seconds` (interrompível) e avança. Suporta `start`/`stop`/`pause`/`resume`.

### 5.9 `sysinfo/` — coleta e renderização de stats

- `collector.collect_stats(include_cpu=True, include_gpu=False) -> SystemStats`:
  CPU via `psutil.sensors_temperatures()` (tenta `coretemp`, `k10temp`, `zenpower`,
  `cpu_thermal`); GPU varrendo `/sys/class/hwmon` por `amdgpu`/`nvidia`; uso via
  `psutil.cpu_percent`.
- `renderer.render_stats_image(stats, size=(240,240)) -> PIL.Image`: fundo preto,
  texto de temperatura + barra de progresso, com **cor dependente da temperatura**
  (≈ azul ≤30 °C → verde → amarelo → vermelho >70 °C via `_temp_color`). Layout adapta-se
  a 1 ou 2 sensores. Usa fonte DejaVu Sans quando disponível.
- `renderer.SysInfoEngine(device, config, on_error=None)`: *thread* que coleta, renderiza
  e envia ao LCD a cada `refresh_seconds`.

### 5.10 `config/` — configuração TOML (XDG)

- `paths`: respeita `$XDG_CONFIG_HOME` (default `~/.config`) e `$XDG_DATA_HOME`; expõe
  `get_config_dir()`, `get_config_file()` (→ `~/.config/kraken/config.toml`), `get_data_dir()`.
- `schema`: `config_from_dict` / `config_to_dict` convertem entre `dict` (TOML) e
  `AppConfig`, com defaults para chaves ausentes.
- `manager`: `load_config(path=None)` (devolve default se o arquivo não existir; `ConfigError`
  em falha de parse) e `save_config(config, path=None)` (cria diretórios; `ConfigError` em falha).

### 5.11 `gui/` — interface PySide6

- `main_window.MainWindow`: `QMainWindow` com **5 abas** (Status, LCD, Carousel, System Info,
  Config) e barra de status. Inicializa hwmon e dispositivo e dispara o `SensorWorker`.
- `threads`:
  - `SensorWorker(QThread)` — *polling* de sensores (≈2 s), emite `data_updated`.
  - `LCDUploadWorker(QThread)` — uploads (imagem/brilho/orientação) sem travar a UI.
  - `GifPlaybackWorker(QThread)` — reprodução de GIF por quadros com sinal de parada e
    progresso de frame.
- `widgets`: `status_panel` (gauges), `lcd_panel` (preview, escolher arquivo, upload, Stop
  GIF, brilho, orientação, modo líquido), `carousel_panel` (lista com *drag-drop*,
  add imagem/sysinfo/liquid, duração, start/pause/stop), `sysinfo_panel` (toggles CPU/GPU,
  refresh, start/stop, salvar), `device_info` (dados do dispositivo + abrir config).
- `tray.py`: `QSystemTrayIcon` com tooltip de temperatura e menu (mostrar janela / sair).

---

## 6. Decisões críticas de projeto

| Decisão | Motivo |
|---|---|
| **`hwmon`/sysfs como fonte primária de sensores** | Leitura rápida e não bloqueante; evita contenção no canal USB usado para o LCD. `liquidctl` fica só como *fallback*. |
| **`liquidctl` como biblioteca (não subprocess)** | Evita custo e fragilidade de iniciar processos; permite reaproveitar a mesma conexão e o *lock* interno. |
| **Threading, não asyncio** | `liquidctl` é síncrono e o domínio é simples (1 usuário/1 dispositivo). Threads daemon bastam para carrossel, sysinfo e *polling*. |
| **Lock de USB + *drain* da fila HID antes de `set_screen`** | Operações USB são serializadas por um `threading.Lock`; relatórios HID não solicitados são drenados antes de enviar a tela, evitando erros de "mensagens faltando". |
| **GIF por extração + cache + teto de ~8 fps** | Contorna a limitação do firmware 2.x (ignora animação nativa). O cache por *fingerprint* evita re-decodificar a cada execução. |
| **`core` sem dependência de UI** | Paridade entre CLI e GUI e testabilidade; UI vira uma casca fina sobre o núcleo. |
| **Dataclasses imutáveis com validação** | Dados (`SensorData`, `DeviceInfo`) *frozen*; configs validam faixa/valores em `__post_init__`, falhando cedo. |
| **Sem daemon próprio / sem DBus** | Simplicidade. Persistência em segundo plano fica por conta de serviços `systemd --user`, quando desejado. |

---

## 7. Modelo de dados e esquema de configuração

A configuração vive em `~/.config/kraken/config.toml` (respeitando `$XDG_CONFIG_HOME`).
Exemplo comentado em `assets/sample_config.toml`.

```toml
[device]
serial = ""                 # vazio = auto-detecta

[lcd]
brightness = 50             # 0–100
orientation = 0             # 0, 90, 180 ou 270

[carousel]
enabled = false
loop = true

[[carousel.items]]
path = "/home/user/images/logo.png"
seconds = 10                # media_type auto-detectado pela extensão

[[carousel.items]]
path = ""
media_type = "sysinfo"      # item especial: stats do sistema
seconds = 20

[[carousel.items]]
path = ""
media_type = "liquid"       # item especial: temperatura nativa
seconds = 10

[sysinfo]
enabled = false
show_cpu_temp = true
show_gpu_temp = false
refresh_seconds = 5.0       # >= 1.0

[tray]
enabled = false
show_temp = true
```

**Tipos de mídia do carrossel**: `static` (PNG/JPG/BMP/WebP), `gif`, `sysinfo`, `liquid`
(string vazia ⇒ auto-detecta pela extensão).

**Validações**: brilho 0–100; orientação ∈ {0,90,180,270}; `display_seconds` > 0;
`refresh_seconds` ≥ 1.0.

---

## 8. Referência da CLI e mapeamento da GUI

### 8.1 Referência completa da CLI

| Comando | Opções/Argumentos | Função |
|---|---|---|
| `kraken --version` / `--help` | — | versão / ajuda |
| `kraken device list` | — | lista o dispositivo detectado |
| `kraken device init` | — | inicializa (firmware, série, resolução) |
| `kraken device info` | — | mostra metadados, incl. PID em hex |
| `kraken status` | `--watch/-w`, `--interval/-i` (def. 2.0), `--json-output`/`--json` | leitura de sensores |
| `kraken lcd static` | `<image_path>` | envia imagem fixa |
| `kraken lcd gif` | `<gif_path>`, `--loops N` (def. 0 = infinito) | reproduz GIF |
| `kraken lcd liquid` | — | tela nativa de temperatura |
| `kraken lcd brightness` | `<0–100>` | ajusta brilho |
| `kraken lcd orientation` | `<0\|90\|180\|270>` | rotaciona |
| `kraken carousel start` | `--daemon/-d` | inicia o carrossel |
| `kraken carousel stop` | — | para o carrossel |
| `kraken carousel add` | `[<image_path>]`, `--seconds/-s` (def. 10), `--position/-p`, `--sysinfo`, `--liquid` | adiciona item |
| `kraken carousel remove` | `<index>` | remove pelo índice |
| `kraken carousel list` / `clear` / `status` | — | lista / limpa / estado |
| `kraken sysinfo start` | `--daemon/-d` | inicia render de stats |
| `kraken sysinfo stop` | — | para |
| `kraken sysinfo config` | `--cpu/--no-cpu`, `--gpu/--no-gpu`, `--refresh N` | configura |
| `kraken tray` | `--no-gui` | ícone de bandeja |
| `kraken config show` / `path` / `edit` | — | mostra / caminho / edita ($EDITOR) |

### 8.2 Mapeamento GUI → núcleo

| Aba da GUI | Usa do núcleo |
|---|---|
| Status | `sensors.read_sensors` (via `SensorWorker`) |
| LCD | `lcd.upload_image/upload_static`, `gif.play_animated_gif`, `lcd.set_brightness/set_orientation/set_liquid_mode` |
| Carousel | `carousel.Playlist` + `carousel.CarouselEngine`; persiste via `config.save_config` |
| System Info | `sysinfo.SysInfoEngine` + `sysinfo.collect_stats/render_stats_image` |
| Config | `device.initialize` (DeviceInfo) + `config.paths.get_config_file` |

---

## 9. Fluxos principais

### 9.1 Inicialização do dispositivo

```
KrakenDevice.find()      → varre USB via liquidctl pelos PIDs suportados
        ↓
.connect()               → abre conexão HID (precisa da regra udev p/ rodar sem root)
        ↓
.initialize()            → consulta firmware, série, resolução → DeviceInfo
        ↓
operações set_screen()   → serializadas pelo lock; fila HID drenada antes do envio
```

### 9.2 Leitura de sensores

```
read_sensors(device, hwmon_path)
        │
        ├─ hwmon disponível? → read_hwmon_sensors()  (temp1/fan1/fan2 do sysfs)
        │
        └─ senão            → _read_from_liquidctl(device)  (parse do status)
                                          ↓
                                  SensorData(liquid_temp_c, pump_rpm, fan_rpm, timestamp)
```

### 9.3 Reprodução de GIF

```
play_animated_gif()
  → extract_frames()  (cache hit? reusa : decodifica, redimensiona 240², salva + manifest)
  → para cada loop / quadro:
       upload do PNG como imagem estática
       respeita duração (mínimo 120 ms)
       checa stop_event / deadline; chama on_frame(i, total)
```

---

## 10. Suporte multi-modelo, udev e systemd

### Modelos suportados (VID `0x1e71`)

| PID | Modelo | Resolução |
|---|---|---|
| `0x300C` | Kraken 2023 Elite | 640×640 |
| `0x300E` | Kraken 2023 Standard | 240×240 |
| `0x3012` | Kraken 2024 Elite RGB | 640×640 |
| `0x3014` | Kraken 2024 Plus | 240×240 |

> Os quadros de GIF são sempre gerados em 240×240. O dispositivo-alvo de desenvolvimento é
> o **Kraken 2023 Standard (`0x300E`, 240×240)**.

### udev (`assets/udev/99-kraken.rules`)

Concede acesso USB sem root (`MODE="0666"`, `TAG+="uaccess"`) para os quatro PIDs.
Instalação:

```bash
sudo cp assets/udev/99-kraken.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
# reconectar o cabo USB do Kraken
```

### systemd `--user` (`assets/systemd/`)

- `kraken-carousel.service` — mantém o carrossel rodando.
- `kraken-tray.service` — mantém o ícone de bandeja (`kraken tray --no-gui`).

```bash
cp assets/systemd/kraken-*.service ~/.config/systemd/user/
systemctl --user enable --now kraken-tray
```

---

## 11. Testes

**133 testes** com `pytest`, cobrindo núcleo, serviços e CLI. Distribuição por arquivo:

| Arquivo | Testes | Cobertura |
|---|---:|---|
| `tests/test_carousel.py` | 24 | playlist (add/remove/move/clear) e engine (start/stop/pause/resume) |
| `tests/test_cli.py` | 21 | comandos via `click.testing.CliRunner` |
| `tests/test_lcd.py` | 21 | upload estático/GIF, validação de brilho/orientação |
| `tests/test_models.py` | 21 | validação dos dataclasses |
| `tests/test_config.py` | 10 | (de)serialização e load/save TOML |
| `tests/test_gif.py` | 10 | extração de frames, cache, durações, playback |
| `tests/test_hwmon.py` | 10 | discovery e leitura de sysfs |
| `tests/test_sysinfo.py` | 10 | coleta de stats e renderização |
| `tests/test_sensors.py` | 6 | leitura de sensores e *fallback* |

Padrões: `unittest.mock` para dispositivo/arquivos, fixtures compartilhadas em
`conftest.py`, `tmp_path` para arquivos temporários e `CliRunner` para a CLI (sem
subprocesso). Execução: `pytest tests/`.

---

## 12. Problemas conhecidos e evoluções futuras

### Problemas conhecidos

- **Serviço de carrossel desatualizado.** `assets/systemd/kraken-carousel.service` executa
  `kraken carousel start --foreground`, mas a CLI atual **não possui** a opção
  `--foreground` (o padrão já é primeiro plano; a opção existente é `--daemon`). Como está,
  o serviço falharia ao iniciar. *Workaround:* editar o `ExecStart` para
  `… kraken carousel start` (sem `--foreground`). **Documentado, não corrigido**, conforme
  a natureza somente-leitura desta tarefa.

### Limitações inerentes ao hardware/firmware

- **Teto de ~8 fps** na reprodução de GIF (firmware 2.x ignora animação nativa). Animações
  rápidas são limitadas a `MIN_FRAME_INTERVAL_MS = 120` ms por quadro.

### Evoluções futuras possíveis

- Suporte/validação mais ampla dos demais modelos (Elite/Plus/RGB 640×640) — a arquitetura
  (mapa PID → resolução em `LCD_RESOLUTIONS`) já está preparada.
- Alinhar o serviço systemd à CLI atual.

---

*Documento gerado a partir de leitura direta do código-fonte (núcleo, CLI, GUI, testes,
assets), sem qualquer modificação no projeto.*
