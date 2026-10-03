# Tarefa atual — reconstrução da baseline técnica

## Status: concluída

Baseline dos quatro documentos de `.ai` reconstruída a partir do checkout
rastreado. O conteúdo antigo que descrevia módulos removidos, configurações
locais não verificadas, métricas históricas e roadmaps concluídos foi retirado
ou substituído por estado observável no código.

## Escopo executado

- Conferidos os documentos anteriores de estado, arquitetura, tarefa e
  auditoria contra a estrutura atual do repositório.
- Atualizadas as descrições do runtime, UI, tools, providers, memória, contexto,
  plugins, persistência e recursos opcionais.
- Separados defaults do código, dependências de ambiente e configuração local
  não verificada.
- Mantido o escopo exclusivamente documental; nenhum arquivo de implementação
  foi alterado.
- Executado `python -m pytest tests/ -q`: **151 testes passaram**.
- Revisada a consistência dos quatro documentos e removidas referências a
  componentes que não pertencem ao checkout atual.

## Próxima etapa sugerida

Validar manualmente no computador-alvo os fluxos que os testes automatizados
não cobrem: captura/reprodução de voz e câmera, configuração efetiva do wake
word e confirmação/execução de ações de sistema. Registrar resultados somente
após observação direta da configuração e do comportamento em execução.
