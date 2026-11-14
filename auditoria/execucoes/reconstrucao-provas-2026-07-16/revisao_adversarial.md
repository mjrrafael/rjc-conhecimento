# Revisão adversarial — reconstrução inicial de prova material

## 1. Hipóteses que poderiam derrubar a reconstrução

1. Uma data jurídica foi copiada de catálogo, captura ou metadado, em vez de ter ato e localizador próprios.
2. O resumo humano omite uma condição, exceção, transição ou alteração posterior do dispositivo.
3. O mesmo card chega à superfície de pessoa e à de IA com campos ou fontes diferentes.

## 2. Re-derivação a partir de fontes cruas

cadeia re-derivada: NORMA_GERAL/CTN | fonte crua: `C:\Users\rafae\.codex\automations\monitor-portal-rjc-tributario\evidencias\2026-07-16-prova-material\atos-iniciais\lote-com-camara\tentativa-1\bodies\BR-CTN-TEXTO-COMPILED-99ab35a13a6bdfc465b3c613dafb62ea254fed9b5452c557e2a6d83b2d04299b.bin` sha256 `99ab35a13a6bdfc465b3c613dafb62ea254fed9b5452c557e2a6d83b2d04299b` | fonte oficial: https://legis.senado.gov.br/norma/547034/publicacao/34620375 | resultado: divergiu parcialmente — arts. 96 e 218 bateram, mas a data de publicação não constava deste corpo.

cadeia re-derivada: PUBLICACAO/CTN | fonte crua: `C:\Users\rafae\.codex\automations\monitor-portal-rjc-tributario\evidencias\2026-07-16-prova-material\atos-iniciais\lote-com-registro-senado\tentativa-3\bodies\BR-CTN-SENADO-REGISTRO-7e287d66f8298a97d3fafe36e26d072d61783556864d5adbaa58716a69920fc2.bin` sha256 `7e287d66f8298a97d3fafe36e26d072d61783556864d5adbaa58716a69920fc2` | fonte oficial: https://legis.senado.gov.br/norma/547034 | resultado: bateu — registro oficial traz “Diário Oficial da União de 27/10/1966” e p. 12451, col. 1; o card foi corrigido para usar esta fonte neste campo.

cadeia re-derivada: NORMA_GERAL/LC214 | fontes cruas: `C:\Users\rafae\.codex\automations\monitor-portal-rjc-tributario\evidencias\2026-07-16-prova-material\atos-iniciais\lote-com-registro-senado\tentativa-3\bodies\BR-LC214-DOU-ORIGINAL-1723a606d2fed5c8f3e63854a9273e6e3f19d4e1d1e13d0ea63a46731d2e420c.bin` sha256 `1723a606d2fed5c8f3e63854a9273e6e3f19d4e1d1e13d0ea63a46731d2e420c` e `C:\Users\rafae\.codex\automations\monitor-portal-rjc-tributario\evidencias\2026-07-16-prova-material\atos-iniciais\lote-com-registro-senado\tentativa-3\bodies\BR-LC214-TEXTO-ATUAL-cc78f94f664c5e1717da540582ca1907215867e285fa950f1534f49890ada8b0.bin` sha256 `cc78f94f664c5e1717da540582ca1907215867e285fa950f1534f49890ada8b0` | fontes oficiais: https://pesquisa.in.gov.br/imprensa/servlet/INPDFViewer?captchafield=firstAccess&data=16%2F01%2F2025&jornal=601&pagina=1 e https://legis.senado.gov.br/norma/40180341/publicacao/40181429 | resultado: bateu — arts. 1º e 4º sustentam instituição/incidência; art. 544 sustenta vigência e eficácia residual em 01/01/2026.

cadeia re-derivada: SUPERFICIES/HUMANO_E_IA | fonte crua: `data/prova_material/cards_em_reconstrucao.json` e renderização temporária em `preview/index.html` e `preview/normas-ia.json` | resultado: bateu — os dois IDs do registro aparecem nas duas saídas de prévia; o teste automatizado ainda recusa emissão pública.

## 3. Defeitos encontrados e correção aplicada

- **CORRIGIR:** a publicação do CTN estava ligada ao corpo consolidado, que declarava não substituir o DOU e não carregava o dado de publicação. Correção aplicada: fonte específica `BR-CTN-SENADO-REGISTRO`, capturada duas vezes e usada somente para `temporal.publicacao` e apelido.
- **CORRIGIR:** fatos jurídicos não nulos estavam faltando em parte da proveniência. Correção aplicada: resumo humano, apelido do CTN e lista de tributos da LC 214 passaram a ter trecho/localizador próprios; avisos editoriais foram separados dos dados jurídicos.
- **A VALIDAR:** a LC 214 tem redação vigente alterada pela LC 227/2026. O card limita-se ao caput do art. 4º e ao art. 544; a revisão independente confirmou que o caput permanece, mas todo novo campo deve partir do texto consolidado vigente.

## 4. Detalhe interno que ainda derrubaria uma conclusão positiva

O maior risco remanescente é chamar de cobertura nacional uma matriz com fontes institucionais ainda inacessíveis e sem leitura dos atos individuais. A evidência que o revelaria é uma matriz sem falhas, atos específicos por regra e refetches cegos com recibos nativos. Essa evidência ainda não existe.

## 5. Veredito do passe

Veredito: defeito CORRIGIR — a correção de publicação/proveniência aguarda revalidação cega e a cobertura nacional continua pendente.
