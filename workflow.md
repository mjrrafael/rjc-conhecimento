# Workflow Do Portal Tributário Aberto

Este arquivo é o fio condutor do projeto. Sempre que o contexto ficar longo, retomar daqui antes de alterar conteúdo tributário.

## Objetivo

Construir um corpus tributário aberto, gratuito e versionado, útil para pessoas e para LLMs, com legislação em tela, fonte oficial, leitura didática, prova documental e histórico de curadoria.

## Decisão Editorial De 26/04/2026

- Goiás permanece aprovado: RCTE, Anexo IX, cBenef e leitura didática foram revisados e aceitos.
- Os demais Estados ficam em `revisao_fonte` até nova curadoria. A publicação profunda anterior gerava risco de erro porque misturava texto extraído de PDF, partes duplicadas, fallback amplo e atos que não eram exatamente RICMS/benefícios de ICMS.
- O portal não deve ensinar regra estadual profunda sem pacote curado. Melhor preservar a página estrutural do Estado do que publicar orientação tributária fraca.
- A trava de publicação fica em `data/state_curadoria.json`. Apenas UFs com `publish_deep: true` podem gerar páginas profundas em `estados/{uf}/legislacao/`.

## Ordem De Trabalho Por Região

1. Centro-Oeste: GO aprovado; revisar DF, MT e MS.
2. Sudeste: SP, MG, RJ e ES.
3. Sul: PR, RS e SC.
4. Nordeste: AL, BA, CE, MA, PB, PE, PI, RN e SE.
5. Norte: AC, AP, AM, PA, RO, RR e TO.

## Pacote Mínimo Por Estado

Cada UF só pode sair de `revisao_fonte` para `aprovado_v1` quando houver:

- RICMS vigente salvo em texto local.
- Anexos/capítulos de benefícios fiscais de ICMS salvos em texto local.
- Lei estadual material do ICMS, quando separada do regulamento.
- Atos modificadores relevantes, especialmente os que alteram benefícios, alíquotas, ST, fundos, regimes especiais ou códigos de benefício.
- Link oficial da Secretaria da Fazenda/Receita Estadual ou diário oficial.
- Data de captura.
- Hash do texto salvo.
- Separação entre texto legal, comentário didático e conclusão operacional.

## Onde Salvar As Fontes Curadas

Usar esta estrutura dentro do repositório:

```text
data/fontes-estaduais-curadas/
  centro-oeste/
    DF/
      RICMS_DF_YYYY-MM-DD.txt
      BENEFICIOS_ICMS_DF_YYYY-MM-DD.txt
      manifest.json
  sudeste/
    SP/
      RICMS_SP_YYYY-MM-DD.txt
      BENEFICIOS_ICMS_SP_YYYY-MM-DD.txt
      manifest.json
```

O `manifest.json` de cada UF deve conter:

- `uf`
- `estado`
- `regiao`
- `fonte_oficial`
- `data_captura`
- `arquivos`
- `sha256`
- `status_curadoria`
- `observacoes`

## Fluxo Por UF

1. Inventariar o que já existe no `BD_LEGISLACAO`.
2. Verificar se o arquivo local é texto normativo limpo ou apenas compilado ruidoso.
3. Pesquisar fonte oficial atual: Secretaria da Fazenda/Receita Estadual, diário oficial ou portal legislativo oficial.
4. Baixar ou extrair o RICMS vigente e os benefícios fiscais de ICMS.
5. Salvar em `.txt` no repositório em `data/fontes-estaduais-curadas/{regiao}/{UF}/`.
6. Criar ou atualizar `manifest.json` da UF.
7. Atualizar `data/state_curadoria.json` para `publish_deep: true` somente depois da conferência.
8. Gerar o portal.
9. Auditar links, busca, âncoras, fontes e conteúdo.
10. Publicar no GitHub.

## Modelo Das Paginas Estaduais

Cada Estado aprovado deve ter, no minimo:

- `ICMS completo`
- `Benefícios fiscais de ICMS`
- `Alíquotas e base de cálculo`
- `Substituição tributária`
- `Diferimento, suspensão e regimes especiais`
- `Documentos, SPED, cBenef quando houver e prova`
- `Fiscalizacao, penalidades e riscos`
- `Fontes oficiais em tela`

## Regra Para Benefícios Fiscais

Benefício fiscal não pode ser classificado apenas por contagem de palavra. O bloco setorial só entra quando o dispositivo legal for identificado e vinculado a:

- produto, NCM, atividade ou operação;
- tipo de benefício: isenção, redução de base, crédito outorgado/presumido, diferimento, suspensão, não incidência ou regime especial;
- condições;
- vedações;
- documento fiscal;
- prova;
- risco de uso indevido.

## Auditorias Obrigatorias

Rodar antes de cada publicação:

```powershell
python scripts\audit_state_source_quality.py
python scripts\build_portal.py
python scripts\export_legal_registry.py
python scripts\audit_portal.py
```

O portal nao deve passar na auditoria se:

- houver página profunda de Estado com `publish_deep: false`;
- houver item no índice de busca apontando para arquivo ou âncora inexistente;
- houver benefício fiscal sem fonte legal em tela;
- houver conclusão didática sem texto legal que a sustente.

## Estado Atual

- Federal: publicado com legislação em tela.
- Folha/CLT: publicado com legislação em tela.
- Goiás: aprovado.
- Demais Estados: em revisão fonte-a-fonte.
- Mato Grosso: RICMS/2014 capturado da SEFAZ-MT em `data/fontes-estaduais-curadas/centro-oeste/MT/`, ainda sem aprovação para publicação profunda.
