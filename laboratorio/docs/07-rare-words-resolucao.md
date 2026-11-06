# Rare Words: resolução da pendência e limites de proveniência

Em 29/10/2026 a avaliação RW do fastText foi concluída, com o modelo já treinado e o avaliador oficial preservado. A solução foi usar uma cópia documentada nos exemplos AWS SageMaker, corroborando os pares e notas médias contra outro repositório acadêmico. Não houve novo treinamento.

## O problema era o download

Nova tentativa no Ubuntu retornou `No route to host` para `nlp.stanford.edu:443`; log `25-rw-nova-tentativa.txt`. A resolução DNS funcionou, apontando para 171.64.67.140; o alias `www-nlp` apontou para o mesmo IP. Trocar apenas o nome para esse alias não ofereceu outro servidor. Essa falha não demonstrava defeito na instalação fastText.

## Alternativa utilizada

O notebook do repositório oficial `aws/amazon-sagemaker-examples` referencia o mesmo conjunto RW no bucket regional `sagemaker-example-files-prod-{regiao}`, chave `datasets/text/stanford_rare_words/rw.zip`.

O notebook foi removido do ramo atual em uma limpeza de exemplos, mas foi recuperado no histórico oficial, revisão **4883224d0032906f1a2bafd4887544ff5ddae606**. O arquivo está preservado em `manifests/rw/amazon-notebook.ipynb`; os metadados da consulta ao histórico também foram salvos. O notebook não foi executado: somente seu endereço público do dataset foi utilizado, sem criar treinamento ou endpoint na AWS.

- [Notebook AWS na revisão preservada](https://github.com/aws/amazon-sagemaker-examples/blob/4883224d0032906f1a2bafd4887544ff5ddae606/introduction_to_amazon_algorithms/blazingtext_word2vec_subwords_text8/blazingtext_word2vec_subwords_text8.ipynb).
- [Arquivo público AWS usado](https://sagemaker-example-files-prod-us-east-1.s3.amazonaws.com/datasets/text/stanford_rare_words/rw.zip).
- [Cópia acadêmica usada somente para conferir pares/notas](https://github.com/mfaruqui/eval-word-vectors/blob/master/data/word-sim/EN-RW-STANFORD.txt).

O bucket histórico `sagemaker-sample-files` também forneceu um ZIP, idêntico em SHA-256 ao bucket regional documentado na revisão recuperada. O ZIP contém `rw/README.txt` atribuindo o dataset a Luong, Socher e Manning, e `rw/rw.txt`, com 2.034 registros. O arquivo foi verificado pelo CRC do ZIP.

## Verificações próprias antes de avaliar

O script `12-auditar-rw.py`:

1. Confere o endereço do dataset no notebook AWS preservado e a estrutura do ZIP.
2. Valida 2.034 registros, quantidade de campos e notas médias finitas no intervalo 0–10.
3. Confere que a cópia acadêmica corresponde ao blob Git `35498f2fb426bc8e663cb426ed597455b3ecd8cf`, usando o hash de objeto Git do conteúdo recebido.
4. Compara integralmente cada par de palavras e a nota média, usando decimais e preservando repetições. Todos os 2.034 registros coincidiram, inclusive a ordem.
5. Só após as conferências disponibiliza o arquivo RW ao pipeline local.

A cópia acadêmica tem três colunas; portanto, essa comparação corrobora palavras e médias, não os ratings individuais de cada anotador. O arquivo usado na avaliação vem do ZIP AWS completo. Não foi encontrado um checksum publicado pelos autores de Stanford para estabelecer identidade binária com o download original inacessível. **Corroboração de conteúdo não é prova de identidade byte a byte com Stanford.** A redação científica deve registrar o espelho e esse limite, em vez de declarar download direto do servidor original.

| Artefato | Valor |
|---|---|
| ZIP AWS | 36.102 bytes |
| rw.txt | 92.466 bytes |
| SHA-256 ZIP | `057ca4b47ea9515bd90c9147ba4d6b8aa6a4df3732e3266bc731144743f5508d` |
| SHA-256 rw.txt | `f38941b02b85cf20e9d857ab4ee06ee0dfcb1c9ce0df6c546f1134fc5e625dae` |

Detalhes verificáveis: `manifests/rw/auditoria.json`. A primeira chamada da auditoria recusou o notebook porque esperava o nome do bucket antigo; o notebook oficial recuperado usava o bucket regional. Foi baixado esse endereço e o código de auditoria foi ajustado à evidência observada; a tentativa está preservada em `27-rw-copia-verificada.txt`. Nenhum resultado foi produzido antes de as verificações passarem.

## Avaliação oficial executada

`13-rw-copia-verificada.sh` executou a auditoria e chamou `07-avaliar-rw.sh`. Este último usa os comandos do exemplo fastText: prepara os termos, carrega `result/fil9.bin`, obtém os vetores e executa **o `eval.py` oficial sem alteração**. Logs: `28-rw-avaliacao.txt` e pasta `fasttext-rw-20261029T135536Z-BwFCmr` em `logs/execucoes/`.

O programa oficial arredonda a correlação multiplicada por 100 para um inteiro e exibiu `42`. Para preservar o número exato, `14-rw-resultado-exato.py` executou o mesmo arquivo oficial via `runpy`, sem alterá-lo, e salvou as variáveis numéricas em JSON; log `29-rw-resultado-exato.txt`.

| Medida | Resultado |
|---|---|
| Código de saída | 0 |
| Pares avaliados | 2.034 |
| Pares descartados | 0 |
| Spearman rho | 0,4177019229655776 |
| Rho × 100 | 41,77019229655776 |

É **correlação de similaridade com notas humanas**, não acurácia, porcentagem de recomendações corretas ou medida de qualidade no catálogo anime. O rótulo `OOV` do avaliador refere-se aos pares descartados por ausência de vetores utilizáveis; não significa que todas as palavras RW pertencem ao vocabulário de treinamento, pois fastText compõe representações para palavras ausentes.

## Outras alternativas e decisões

- Obter futuramente o arquivo diretamente do servidor Stanford, inclusive por outra rede, permitiria comparar hashes com a cópia preservada. Não foi alterada a configuração de rede da máquina.
- Um arquivo fornecido pelos autores poderia ser verificado da mesma forma. Não foi enviado email nem mensagem aos autores.
- Outros benchmarks de similaridade ou analogias podem ser avaliados como experimentos adicionais. Eles não devem ser apresentados como RW, e não são necessários para substituir silenciosamente este resultado.

O procedimento oficial de avaliação foi mantido; a origem de obtenção dos dados foi adaptada e registrada. Essa solução encerra a pendência operacional RW, preservando o limite de proveniência descrito acima.
