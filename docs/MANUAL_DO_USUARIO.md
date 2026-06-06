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

*Quer entender como o Kraken funciona por dentro? Veja a
[Documentação Técnica](DOCUMENTACAO_TECNICA.md).*
