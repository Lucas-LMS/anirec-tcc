# Retomar após ativar virtualização no firmware

> **Resolvido:** Lucas ativou a virtualização e reiniciou. Ubuntu e os ambientes/modelos foram recuperados. O benchmark SMS está em execução, incluindo GPT-OSS 20B pela Groq Free após escolha e configuração pelo usuário. Este arquivo preserva o diagnóstico anterior; não repetir a configuração/reinstalação com base nos estados antigos abaixo. Consulte README e DIARIO_BENCHMARK para o estado atualizado.

Estado salvo em 05/11/2026. Lucas informou retirada da bateria da placa-mãe. Windows registrou VirtualizationFirmwareEnabled=False; Ubuntu/WSL não inicia. Placa observada: Gigabyte B450M S2H. Não há treinamento nem download ativo ao finalizar esta etapa.

## Ação manual

Ativar SVM Mode ou AMD-V na BIOS/UEFI, salvar e reiniciar. A posição do menu depende da versão da BIOS. Não remover/reinstalar Ubuntu ou seus dados. A ativação e reinicialização serão feitas por Lucas.

## Conferência na próxima sessão

1. Consultar Win32_Processor.VirtualizationFirmwareEnabled e iniciar `wsl -d Ubuntu`.
2. Se o erro persistir, diagnosticar Plataforma da Máquina Virtual e configuração de inicialização do hipervisor com a documentação Microsoft; não assumir perda dos pesos.
3. Verificar modelos e ambientes em `/home/lucas/tcc-lab`; não repetir treinos nem apagar versões anteriores.
4. Validar acesso ao dataset já congelado em `laboratorio/llms-20261105/dados`. Não recriar freeze nem alterar rótulos depois de ver predições.
5. Preparar benchmark de classificação com o mesmo conjunto comum de 200 mensagens para estáticos, MiniLM e os três geradores locais. O teste completo tem 775 mensagens e deve ser relatado separadamente.
6. Fixar prompts, agregação e condições de raciocínio conforme o protocolo antes de avaliar. Ainda não existem resultados comparativos de spam.

## Instalações prontas no Windows

- Runtime CPU: `C:/tcc-lab/LLMs/runtime-b12110`.
- Pesos: `C:/tcc-lab/LLMs/models`.
- Manifesto de arquivos/revisões/hashes: `resultados/instalacao.json`.
- Verificações finais: `smoke-llama.json`, `smoke-deepseek-thinking.json`, `smoke-qwen-official-sampling-thinking.json`.
- Falhas/diagnósticos anteriores preservados, incluindo Qwen sem raciocínio e DeepSeek com saída insuficiente.
- Nenhuma chave API, conta Groq ou pagamento configurado. Qwen substitui o GPT hospedado no plano gratuito local; não chamar Qwen de GPT.

É possível usar os LLMs nativos mesmo sem WSL. Para comparar todos sob condições próximas e reutilizar os estáticos, retomar o Linux primeiro. O TCC final continua restrito a modelos estáticos; geradores são comparadores.
