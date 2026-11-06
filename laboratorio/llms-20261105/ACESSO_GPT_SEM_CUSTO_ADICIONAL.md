# Possibilidades de incluir GPT sem gasto adicional

> Atualização da execução: Lucas escolheu Groq Free, configurou a chave localmente e autorizou a comparação. A autenticação e a inferência GPT-OSS 20B funcionaram. O texto abaixo preserva a investigação anterior. Não foi usada API OpenAI tarifada. O programa não configura cobrança, não faz upgrade e não tem fallback pago. A validade da chave comprova acesso, não certifica por si só a modalidade de cobrança da conta.

Consulta documental em 05/11/2026 após Lucas perguntar sobre cotas pequenas gratuitas. Nenhuma inferência externa foi executada. Uma quantidade pequena de requisições não torna gratuita uma API tarifada; é necessário confirmar a modalidade de acesso da conta.

## API OpenAI e créditos de assinatura

Não foi estabelecida uma cota universal gratuita da API de GPT disponível a qualquer conta. A documentação atual oferece créditos incluídos para assinaturas elegíveis Pro e Business. Requer plano pago ativo há pelo menos sete dias, titularidade apropriada e vínculo entre assinatura e organização API com o mesmo email. Free trials/assinaturas gratuitas não qualificam. A documentação consultada não lista Plus ou Free nessa modalidade.

Esses créditos podem permitir um experimento sem gasto adicional a quem já possui o plano, mas não são uma API universalmente gratuita. Não sabemos o plano de Lucas nem seu saldo. Não haverá compra de assinatura ou créditos para cumprir esta etapa. A documentação permite usar o benefício ativo sem cadastrar pagamento na API. O crédito expira com o ciclo e é proporcional no primeiro período.

Se existirem créditos comprados, o serviço pode continuar consumindo-os depois de acabar o benefício. Portanto, só chamar a API quando a modalidade/saldo estiverem confirmados e sem recarga automática ou uso de saldo pago. Limite interno de requisições/tokens ajuda a conter uso, mas não substitui conferir o estado de cobrança da conta.

Fonte oficial: https://developers.openai.com/api/docs/guides/chatgpt-api-credits

## GPT OSS por Groq Free

O catálogo e a tabela Free consultados incluem `openai/gpt-oss-20b` e `openai/gpt-oss-120b`. Limites gerais publicados por modelo: 30 requisições/minuto, 1.000/dia, 8.000 tokens/minuto e 200.000 tokens/dia. Os limites da conta e disponibilidade precisam ser confirmados; podem mudar.

É uma alternativa para avaliar um modelo OpenAI de pesos abertos remotamente sem carregar um modelo 20B/120B nesta máquina. Não equivale a avaliar um GPT proprietário usado no ChatGPT; identificar explicitamente modelo e provedor nos resultados.

O piloto comum de 200 mensagens cabe no limite de quantidade de requisições se cada mensagem usar uma chamada, mas o orçamento de tokens inclui entrada e saída, podendo exigir pausas ou mais dias. Não prometer que toda a execução cabe numa única cota sem estimar tokens e repetições.

Exige conta e chave Groq. Manter Free, não cadastrar meio de pagamento/fazer upgrade; conferir a modalidade antes de executar. Não enviar chave pelo chat. Nenhuma conta/chave está configurada nesta etapa, e o programa não deve alternar para um provedor pago em caso de limite. Um 429 deve interromper/adiar conforme o protocolo.

Fontes: https://console.groq.com/docs/rate-limits e https://console.groq.com/docs/models

## Virtualização após a reinicialização

Em 05/11/2026, após Lucas informar reinicialização, VirtualizationFirmwareEnabled passou a true. `wsl -d Ubuntu` iniciou como usuário lucas, UID 1000. Os arquivos `/home/lucas/tcc-lab/GloVe/vectors.txt` e `/home/lucas/tcc-lab/fastText/result/fil9.bin` foram encontrados. Isso confirma o retorno do ambiente e a presença desses arquivos; os demais ambientes/modelos ainda serão conferidos antes do benchmark comum. Não houve reinstalação do Ubuntu.
