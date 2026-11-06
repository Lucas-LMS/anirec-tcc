# Ambiente e decisões

## Inventário observado

Consulta em 29/10/2026, nesta máquina:

| Recurso | Observação |
|---|---|
| Sistema | Windows 10 Home, 64 bits, build 19045 |
| CPU | AMD Ryzen 5 2400G, 4 núcleos e 8 processadores lógicos |
| Memória utilizável pelo Windows | 14.597.676 KiB, aproximadamente 13,92 GiB |
| GPU | AMD Radeon RX Vega 11 integrada; WMI informa 2 GiB em AdapterRAM |
| Espaço livre inicial em C: | Aproximadamente 43,6 GiB; varia com os downloads |
| Ferramentas presentes | Git for Windows e seu Bash/Perl/unzip; winget; executável wsl.exe |
| Ferramentas não encontradas no PATH | GCC, G++, GNU Make, CMake e Docker |
| Python no PATH | Atalho da Microsoft Store; não foi considerado Python funcional |
| WSL | `wsl --list --verbose` retornou ajuda e código 1, sem distribuição utilizável identificada |

Ter `wsl.exe` não demonstra uma distribuição instalada. `AdapterRAM` em uma GPU integrada também não demonstra VRAM dedicada disponível para LLMs. Não foi validado backend GPU. O plano inicial usa CPU.

Existe Python interno do aplicativo Codex. Ele pode auxiliar na inspeção de arquivos nesta sessão, mas não é dependência reproduzível do laboratório e não será tratado como Python instalado pelo usuário para o TCC.

## Por que compilar os códigos dos autores

GloVe disponibiliza programas em C e uma demonstração completa. fastText disponibiliza código C++ e um Makefile. A proposta é utilizar esses códigos, e não substituir GloVe por uma biblioteca homônima de terceiros ou fastText por um wheel não oficial. A primeira integração será pela linha de comando; o binding Python do fastText é uma instalação adicional, ainda não realizada.

GloVe: revisão `52f7dbc512be3f72e9c11e7cbb19dfdfa4651e9c`.

fastText: tag `v0.9.2`, revisão `5b5943c118b0ec5fb9cd8d20587de2b2d3966dfe`, escolhida porque o README oficial utiliza essa versão no procedimento com Make. O repositório fastText está arquivado; registrar essa condição ao discutir manutenção do software.

Os clones foram feitos com `git -c core.autocrlf=false clone ...`, para manter scripts shell com terminações LF. Esses comandos baixam software; não treinam modelos.

## Plataforma

O README fastText descreve Linux/macOS. Cygwin oferece compatibilidade POSIX no Windows, mas seria uma adaptação de plataforma. Seu instalador oficial foi baixado para `C:\tcc-tools\downloads\setup-x86_64.exe` e apenas `--help` foi executado.

A chamada que iniciaria a instalação oculta do Cygwin e, no mesmo comando, clonaria os repositórios, foi rejeitada antes da execução pela revisão automática, com a mensagem `blocked by policy`. Não foi fornecida justificativa mais específica. Não houve tentativa de contornar essa rejeição. Os clones foram posteriormente executados como operações independentes de download. Não há Cygwin funcional constatado.

Para conservar o requisito de seguir a plataforma documentada, o roteiro final usa Ubuntu/WSL. Essa é uma composição de instruções oficiais Microsoft, Ubuntu, Python e dos modelos; os autores do fastText não certificam aqui uma configuração específica de WSL. Na continuação autorizada, `wsl --install -d Ubuntu --no-launch` foi executado. O instalador confirmou os componentes e Ubuntu, com código zero, exigindo reinicialização; também mostrou mensagem de elevação ao final. Após a reinicialização às 09:48:14, o Ubuntu 26.04.1 LTS foi validado em execução no WSL 2 com o usuário `lucas`. As dependências foram instaladas e os experimentos passaram a ser executados no Linux; ver `05-execucoes-reais.md`.

## Dados e alterações de transporte

text8 e enwik9 vêm do endereço de Matt Mahoney indicado pelos exemplos oficiais. Os scripts dos autores usam HTTP; os downloads preparatórios usaram HTTPS **no mesmo domínio e caminho**. Registrar isso como alteração de transporte, sem alegar mudança de corpus. ZIPs são mantidos para auditoria, ao contrário do demo GloVe que remove seu ZIP após extrair.

Um SHA-256 calculado localmente identifica os bytes recebidos, mas não prova autenticidade sem comparação com um hash publicado pelo mantenedor. A checagem ZIP verifica CRC/estrutura, não qualidade científica, licença ou ausência de contaminação. O manifesto distingue esses conceitos.

As licenças do software não devem ser estendidas automaticamente aos corpora. Antes de redistribuir dados ou modelos treinados, verificar as condições específicas do conteúdo. Nesta etapa os dados são preservados localmente para os exemplos.
