# Relatório de auditoria da baseline atual

## Escopo e evidência

Auditoria documental e estática do checkout rastreado: inventário de fontes,
comparação entre código e os quatro documentos existentes em `.ai`, inspeção
dos entrypoints, UI, tools, memória/contexto, configuração/dependências e
testes. A suíte atual foi executada com Python 3.11:

```text
python -m pytest tests/ -q
151 passed in 6.22s
```

O resultado confirma os testes automatizados, não a operação real com
credenciais, serviços externos, microfone, câmera ou configuração privada. O
conteúdo de `config/api_keys.json` e outros dados privados/locais não foi
inspecionado.

## Baseline confirmada

- Entry point da aplicação: `main.py`; `JarvisLive` mantém a sessão Gemini Live,
  coordena áudio e ferramentas e inicia os loops de runtime.
- Interface ativa: `ui.py` com PyQt6/WebEngine/WebChannel, carregando
  `ui_web/index.html`.
- Superfície declarada: 25 tools — 23 registradas em
  `core/tool_registry.py` e duas (`screen_process`, `close_camera`) roteadas
  especificamente em `main.py`.
- Plugins: carregamento dinâmico com opção local de ativação; os plugins
  desconhecidos são desativados por padrão. Configuração real não confirmada.
- Memória: política de quatro estados e vault Markdown configurável; fatos,
  notas e resumos são armazenados em notas. O estado operacional tem arquivo
  próprio.
- Contexto: resolução local e SQLite/FTS5 com fallback de busca. Não há
  embeddings no caminho documentado.
- Segurança operacional: `write_guard` centraliza confirmações e auditoria
  para os fluxos integrados a ele. Não se deve generalizar essa garantia a
  todas as ações sem rastrear cada handler.
- Ferramentas/texto: o cliente implementa fallback resiliente Groq → OpenRouter
  e contém suporte adicional a providers configuráveis compatíveis com
  OpenAI, inclusive Ollama. As credenciais e a configuração efetiva não foram
  verificadas. `deep_reasoning` usa uma rota separada.
- Persistência local inclui vault, estado de runtime, índice FTS5, log de
  auditoria e backups. Não foi confirmada a presença ou localização efetiva
  desses dados neste ambiente.

## Resultado da sincronização documental

Os documentos em `.ai` agora distinguem implementação confirmada, defaults do
código, recursos dependentes de pacotes/serviços e configuração local não
verificada. A arquitetura descreve os módulos ativos e os limites reais dos
contratos; o estado do projeto e o relatório usam a mesma contagem de tools e
os mesmos resultados de teste. Histórico operacional e métricas sem evidência
reproduzível no checkout não foram mantidos como estado atual.

## Lacunas e limitações comprováveis

1. **Dependências declaradas incompletas para recursos opcionais/da UI.**
   `ui.py` importa Qt WebEngine, mas `requirements.txt` não declara
   `PyQt6-WebEngine` separadamente. O gate importa `openwakeword`, que também
   não consta no manifesto; se indisponível, a inicialização do gate falha e o
   áudio continua passando sem wake word.
2. **Dependências sem import direto identificado.** `google-generativeai`,
   `pypdf`, `screen-brightness-control`, `httpx` e `beautifulsoup4` aparecem em
   `requirements.txt`, mas não há import direto correspondente no código
   rastreado. Isso não prova ausência de uso transitivo ou necessidade de
   distribuição. Para PDF há imports de `pdfplumber` e `PyPDF2`.
3. **Configuração real não verificável nesta auditoria.** Não foram confirmados
   provider ativo, chaves, modelos disponíveis, caminho do vault, plugins,
   wake word ou proatividade habilitados.
4. **Validação de execução limitada.** Os 151 testes não cobrem SLA de APIs,
   qualidade de reconhecimento de fala, uso prolongado, compatibilidade de
   todos os dispositivos nem cada ação em sistema real.
5. **Agente de desenvolvimento com efeitos.** `dev_agent` contém caminhos de
   escrita e instalação de dependências; o efeito depende da ação específica.
6. **Orquestrador ainda concentra responsabilidades.** `main.py` integra sessão
   Live, áudio, roteamento de tools, reconexão e serviços; há extrações para
   `core/`, mas a separação não elimina esse acoplamento.

## Limites da conclusão

- Não foi feita auditoria de segurança dedicada nem teste de penetração.
- Não foram abertas configurações que possam conter segredos nem dados locais
  ignorados pelo Git.
- Não foram medidos custo, latência ou disponibilidade de provedores nesta
  revisão.
- Não se concluiu que dependências sem import direto devam ser removidas; a
  necessidade externa/transitiva não foi avaliada.
- A revisão alterou somente documentação dentro de `.ai`; a suíte foi usada
  como evidência do estado do checkout, não como teste das alterações
  documentais.
