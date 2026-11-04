# 0002: Disponibilizar a página como PWA no Android e no iOS

- **Estado:** aceita, implementação pendente.
- **Data:** 2026-11-04, depois de auditar uma pesquisa sobre o suporte a PWA nas duas plataformas.

## Contexto

A página de chat (`src/judo_chat/static/index.html`) sai pelo GitHub Pages em
`/judoka-assistant/` e chama a API pública pela URL que o `pages.yml` grava no `config.js`. Ela já
tem `viewport` e `theme-color`, mas não tem manifest, ícones nem service worker, então não pode ser
instalada como app. O objetivo é que o judoka a abra pela tela inicial do celular, no Android e no
iOS, sem passar por loja.

A pesquisa que motivou a decisão acertava o essencial e errava detalhes que mudam o desenho. O que
vale hoje:

| Ponto | Android | iOS / iPadOS |
|-|-|-|
| Instalação | Automática no Chrome, Edge e Samsung Internet quando o manifest está completo, há service worker com `fetch` e o usuário interagiu com a página. Pelo menu, o Chrome instala sem o `fetch` desde a versão 108. O Firefox não tem `beforeinstallprompt`. | Sempre manual ("Compartilhar → Adicionar à Tela de Início"), sem API para provocar o aviso. Desde o iOS 16.4 funciona também no Chrome, no Edge e no Firefox, todos sobre WebKit. No iOS 26, todo site adicionado abre como web app por padrão. |
| Armazenamento | "Best-effort" até `navigator.storage.persist()` ser concedido, o que costuma acontecer com o app instalado. | O limite de 7 dias sem uso vale para o Safari. O app da Tela de Início tem contador próprio e pode receber modo persistente. Seu armazenamento é separado do Safari. |
| Push | Suportado. | Desde o iOS 16.4, só com o app instalado e com permissão pedida num gesto do usuário. |
| Hardware | Web Bluetooth e Web NFC no Chrome. | Sem Bluetooth e sem NFC. Nenhum dos dois serve ao produto. |

Três pontos que a pesquisa não cobria:

1. Um link aberto no navegador embutido do WhatsApp ou do Instagram não pode ser instalado. É
   por esses apps que o link deve circular.
2. Toda resposta depende da API. O offline só consegue mostrar a página e avisar que não há
   conexão.
3. A página vive num subcaminho do Pages, então `start_url`, `scope` e o registro do service worker
   são relativos a `/judoka-assistant/`. A origem não muda e o CORS (`cors_origins` em
   `src/judo_chat/config.py`) fica como está.

## Decisão

**Manifest e ícones.** A pasta `static/` ganha um `manifest.webmanifest` com `name`, `short_name`,
`start_url` e `scope` relativos, `display: standalone`, `theme_color` e `background_color` da
página, e ícones de 192 e 512 px, incluindo uma versão `maskable`. O `index.html` aponta para o
manifest e para um `apple-touch-icon`, que o iOS ainda usa.

**Service worker só para a página.** O `sw.js` guarda no cache o `index.html`, o manifest e os
ícones. O `config.js` e as chamadas à API vão sempre à rede: guardar o `config.js` serviria a URL
antiga da API depois de uma troca, e guardar respostas pediria invalidação e cuidado com
privacidade. Sem conexão, a página aparece e a pergunta mostra "sem conexão". O nome do cache leva a
versão da publicação, para que cada deploy do Pages troque o cache velho. O service worker existe
também porque o aviso automático do Chrome ainda exige o `fetch`.

**Android: botão próprio.** A página captura o `beforeinstallprompt` e mostra um botão "Instalar"
discreto, que some depois da instalação (`appinstalled`) ou quando a página já roda instalada. No
Firefox, onde o evento não existe, o botão dá lugar a um texto curto com o caminho pelo menu.

**iOS: banner com os passos.** Quando o aparelho é iOS e a página não está instalada
(`matchMedia("(display-mode: standalone)")` e `navigator.standalone` falsos), aparece um banner com
"Compartilhar → Adicionar à Tela de Início". Ele pode ser dispensado, e a dispensa fica no
`localStorage`, dentro de um `try/catch`, para não voltar a cada visita.

**Navegador embutido.** Dentro do WhatsApp, do Instagram ou do Facebook, detectados pelo user agent,
o banner pede para abrir o link no navegador antes de qualquer passo de instalação. A detecção pode
errar; o banner falso só custa um aviso a mais.

## Fora do escopo agora

Cada item tem a condição que leva a revê-lo.

- **Lojas.** A Play Store pede empacotar como TWA (Bubblewrap) e manter a chave de assinatura e o
  `assetlinks.json`. A App Store pede um invólucro nativo (Capacitor) e corre o risco de rejeição
  pela regra 4.2 da Apple, que recusa apps que só embrulham um site. Rever se a divulgação precisar
  da loja, por exemplo numa parceria com federação.
- **Notificações push.** Exigem um servidor de push, o pedido de permissão e, no iOS, o app
  instalado. O produto responde perguntas e não tem o que avisar. Rever se entrar algum conteúdo
  com data, como calendário de exames.
- **Histórico local.** Guardar conversas no aparelho traz decisões de privacidade e de limpeza. No
  iOS o app instalado não vê o que o Safari guardou, então o histórico não migraria. Rever se os
  usuários pedirem para retomar perguntas.

## Consequências para a implementação

- Se a versão do cache for gravada pelo `pages.yml`, como hoje acontece com o `config.js`, a mudança
  é no fluxo de deploy: o mesmo PR atualiza `docs/operacao/deploy.md` e o `AGENTS.md`.
- O diagrama de onde a API roda (`docs/arquitetura/producao-implantacao`) passa a mostrar o service
  worker entre a página e a rede, gerado de novo por `scripts/diagramas_arquitetura.py`.
- A verificação manual cobre Chrome no Android, Safari no iOS, Firefox no Android e um link aberto
  pelo WhatsApp, com a página instalada e sem conexão.

## Referências

- Chrome, revisão dos critérios de instalação (versões 108 e 112):
  <https://developer.chrome.com/blog/update-install-criteria>
- WebKit, política de armazenamento do Safari 17 (`persist()`, cotas, despejo):
  <https://webkit.org/?p=14403>
- heise, mudança do iOS 26 e do iPadOS 26 nos web apps da Tela de Início:
  <https://heise.de/-10749652>
