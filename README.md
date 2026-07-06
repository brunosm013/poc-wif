# Helm Chart `char-wif`

Template Helm para publicar uma aplicação no Kubernetes com suporte opcional a **Google Cloud Workload Identity Federation (WIF)**, sem uso de chaves estáticas de Service Account.

Este chart cria os principais recursos de deploy da aplicação, como `Namespace`, `ServiceAccount`, `Deployment`, `Service`, `HPA`, `Ingress`, `HTTPRoute` e, quando habilitado, um `ConfigMap` com a configuração de credencial externa usada pelas bibliotecas/CLI da Google Cloud.

## Objetivo

O objetivo deste template é permitir que uma aplicação rodando fora da Google Cloud, por exemplo em um cluster Kubernetes externo, consiga acessar recursos da Google Cloud usando a identidade do próprio Pod.

Com o WIF habilitado, o Pod recebe um token temporário emitido pelo Kubernetes. Esse token é usado pela Google Cloud para validar a identidade da workload e emitir credenciais temporárias, evitando o uso de arquivos JSON com chave privada.

## Estrutura do chart

```text
cicd/
├── Chart.yaml
├── values.yaml
├── values-example.yaml
├── .helmignore
└── templates/
    ├── _helpers.tpl
    ├── namespace.yaml
    ├── serviceaccount.yaml
    ├── deployment.yaml
    ├── service.yaml
    ├── hpa.yaml
    ├── ingress.yaml
    ├── httproute.yaml
    ├── workloadidentity-configmap.yaml
    ├── NOTES.txt
    └── tests/
        └── test-connection.yaml
```

## O que cada template faz

| Arquivo | Função |
|---|---|
| `Chart.yaml` | Define metadados do chart, como nome, versão e tipo. |
| `values.yaml` | Valores reais usados na POC. Neste caso, usa a imagem `google-cloud-cli` para validar autenticação WIF, Cloud Storage e Vertex AI/Gemini. |
| `values-example.yaml` | Arquivo de exemplo mais genérico, útil como base para novas aplicações. |
| `templates/_helpers.tpl` | Helpers de nome, labels, namespace e ServiceAccount usados pelos outros templates. |
| `templates/namespace.yaml` | Cria o namespace definido em `values.namespace`. |
| `templates/serviceaccount.yaml` | Cria a Kubernetes ServiceAccount usada pelo Pod. |
| `templates/deployment.yaml` | Cria o Deployment da aplicação e, se WIF estiver habilitado, monta o token projetado e o arquivo de credenciais externas. |
| `templates/service.yaml` | Cria o Service apontando para o container da aplicação. |
| `templates/hpa.yaml` | Cria o HorizontalPodAutoscaler quando `autoscaling.enabled=true`. |
| `templates/ingress.yaml` | Cria um Ingress quando `ingress.enabled=true`. |
| `templates/httproute.yaml` | Cria um HTTPRoute da Gateway API quando `httpRoute.enabled=true`. |
| `templates/workloadidentity-configmap.yaml` | Cria o `credentials.json` de external account usado pelo WIF. |
| `templates/NOTES.txt` | Mostra instruções após o deploy via Helm. |
| `templates/tests/test-connection.yaml` | Cria um teste Helm simples para validar conectividade com o Service. |

## Como o fluxo de Workload Identity Federation funciona

Quando `workloadIdentity.enabled=true`, o chart configura o Pod para usar WIF da seguinte forma:

1. O Pod roda associado a uma Kubernetes ServiceAccount.
2. O Kubernetes projeta um token temporário para essa ServiceAccount no caminho configurado em `workloadIdentity.tokenMountPath`.
3. O token é criado com a `audience` esperada pelo Workload Identity Provider da Google Cloud.
4. O chart cria um `ConfigMap` com um arquivo `credentials.json` do tipo `external_account`.
5. A variável `GOOGLE_APPLICATION_CREDENTIALS` aponta para esse `credentials.json`.
6. A aplicação, SDK ou `gcloud` lê esse arquivo, encontra o token Kubernetes e troca esse token no STS da Google Cloud.
7. A Google Cloud valida o token contra o Workload Identity Provider configurado.
8. Se o token for válido e as permissões IAM estiverem corretas, a aplicação recebe credenciais temporárias para acessar os serviços da Google Cloud.

Em resumo:

```text
Pod Kubernetes
  └── usa Kubernetes ServiceAccount
        └── recebe token JWT temporário
              └── token é validado pelo Workload Identity Provider
                    └── Google Cloud emite credenciais temporárias
                          └── aplicação acessa GCS, Vertex AI, APIs Google etc.
```

## Recursos criados

Com os valores atuais do `values.yaml`, o chart cria:

- `Namespace`: `poc-wif`
- `ServiceAccount`: `serviceaccount-poc-wif`
- `Deployment`: `poc-wif`
- `Service`: `poc-wif`
- `HorizontalPodAutoscaler`: `poc-wif`
- `ConfigMap`: `poc-wif-workload-identity`

O `Ingress` e o `HTTPRoute` existem no template, mas estão desabilitados por padrão.

## Configuração principal

Exemplo baseado no `values.yaml` atual:

```yaml
namespace: poc-wif
fullnameOverride: poc-wif
nameOverride: poc-wif

image:
  repository: gcr.io/google.com/cloudsdktool/google-cloud-cli
  tag: alpine
  pullPolicy: IfNotPresent

serviceAccount:
  create: true
  name: serviceaccount-poc-wif
  automount: false

workloadIdentity:
  enabled: true
  audience: "//iam.googleapis.com/projects/630729803660/locations/global/workloadIdentityPools/poc-workload-identity/providers/mgc-k8s-cluster"
  tokenMountPath: /var/run/secrets/tokens
  tokenFileName: token
  tokenExpirationSeconds: 3600
  credentialsMountPath: /var/run/secrets/google-cloud
  credentialsFileName: credentials.json
```

## Parâmetros importantes

| Parâmetro | Descrição |
|---|---|
| `namespace` | Namespace onde os recursos serão criados. É obrigatório neste chart. |
| `nameOverride` | Sobrescreve o nome base usado nos labels e recursos. |
| `fullnameOverride` | Sobrescreve o nome final dos recursos. |
| `replicaCount` | Quantidade de réplicas quando o HPA está desabilitado. |
| `image.repository` | Imagem do container. |
| `image.tag` | Tag da imagem. Se vazio, usa `appVersion` do `Chart.yaml`. |
| `image.pullPolicy` | Política de pull da imagem. |
| `command` | Comando executado pelo container. |
| `args` | Argumentos ou script executado pelo container. |
| `envs` | Variáveis de ambiente adicionais injetadas no container. |
| `service.type` | Tipo do Service: `ClusterIP`, `NodePort` ou `LoadBalancer`. |
| `service.port` | Porta exposta pelo Service e usada como `containerPort`. |
| `serviceAccount.create` | Define se o chart deve criar a ServiceAccount. |
| `serviceAccount.name` | Nome da ServiceAccount usada pelo Pod. |
| `workloadIdentity.enabled` | Habilita ou desabilita o fluxo de WIF. |
| `workloadIdentity.audience` | Audience esperada pelo Workload Identity Provider da Google Cloud. |
| `workloadIdentity.tokenMountPath` | Caminho onde o token projetado será montado no container. |
| `workloadIdentity.tokenFileName` | Nome do arquivo do token projetado. |
| `workloadIdentity.tokenExpirationSeconds` | Tempo de vida do token Kubernetes, em segundos. |
| `workloadIdentity.credentialsMountPath` | Caminho onde o `credentials.json` será montado. |
| `workloadIdentity.credentialsFileName` | Nome do arquivo de credenciais externas. |
| `autoscaling.enabled` | Habilita ou desabilita o HPA. |
| `ingress.enabled` | Habilita ou desabilita o Ingress. |
| `httpRoute.enabled` | Habilita ou desabilita o HTTPRoute da Gateway API. |

## Sobre o `ConfigMap` de Workload Identity

Quando WIF está habilitado, o chart cria um `ConfigMap` semelhante a este:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: poc-wif-workload-identity
data:
  credentials.json: |
    {
      "type": "external_account",
      "audience": "//iam.googleapis.com/projects/.../providers/...",
      "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
      "token_url": "https://sts.googleapis.com/v1/token",
      "credential_source": {
        "file": "/var/run/secrets/tokens/token"
      }
    }
```

Esse arquivo **não é uma chave privada**. Ele apenas informa às bibliotecas da Google Cloud onde encontrar o token temporário do Kubernetes e como trocá-lo por credenciais temporárias na Google Cloud.

Por isso, neste template, faz sentido usar `ConfigMap` e não `Secret`, desde que nenhuma chave, senha ou segredo seja adicionado a esse arquivo.

## Sobre o Deployment

O `Deployment` é o principal recurso do template. Ele:

- Define a imagem da aplicação.
- Aplica `command` e `args`, se configurados.
- Injeta variáveis de ambiente via `envs`.
- Configura probes de liveness e readiness, se existirem.
- Aplica requests e limits de CPU/memória.
- Usa a ServiceAccount configurada.
- Monta volumes extras definidos em `volumes` e `volumeMounts`.
- Quando WIF está habilitado, monta:
  - token projetado em `/var/run/secrets/tokens/token`;
  - arquivo `credentials.json` em `/var/run/secrets/google-cloud/credentials.json`.

Quando `workloadIdentity.enabled=true`, o template também define:

```yaml
automountServiceAccountToken: false
```

Isso evita montar automaticamente o token padrão da ServiceAccount. Em vez disso, o chart monta explicitamente um token projetado com `audience` e expiração controladas.

## Sobre o `values.yaml` atual

O `values.yaml` atual está configurado como uma POC de validação. Ele usa a imagem:

```yaml
gcr.io/google.com/cloudsdktool/google-cloud-cli:alpine
```

O container executa um script que:

1. Instala `curl` e `jq`.
2. Autentica o `gcloud` usando o arquivo indicado por `GOOGLE_APPLICATION_CREDENTIALS`.
3. Lista a conta ativa no `gcloud`.
4. Valida acesso ao bucket configurado em `GCS_BUCKET_NAME`.
5. Gera um access token via ADC.
6. Faz uma chamada para o Gemini via Vertex AI.
7. Mantém o container vivo com `sleep infinity` para permitir inspeção.

Variáveis usadas pela POC:

```yaml
envs:
  - name: GCP_PROJECT_ID
    value: "poc-workload-identity-501203"
  - name: GCP_LOCATION
    value: "us-central1"
  - name: GCS_BUCKET_NAME
    value: "poc-wif"
  - name: GEMINI_MODEL
    value: "gemini-2.5-flash"
```

Para uma aplicação real, normalmente você substituiria a imagem, o comando e os argumentos pelo container da sua aplicação.

## Exemplo para aplicação real

```yaml
image:
  repository: ghcr.io/sua-org/sua-api
  tag: "1.0.0"
  pullPolicy: IfNotPresent

command: []
args: []

envs:
  - name: GCP_PROJECT_ID
    value: "meu-projeto-gcp"
  - name: GCP_LOCATION
    value: "us-central1"

workloadIdentity:
  enabled: true
  audience: "//iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID"
  tokenMountPath: /var/run/secrets/tokens
  tokenFileName: token
  tokenExpirationSeconds: 3600
  credentialsMountPath: /var/run/secrets/google-cloud
  credentialsFileName: credentials.json
```

Na aplicação, basta usar as bibliotecas oficiais da Google Cloud com Application Default Credentials. O chart já configura a variável:

```text
GOOGLE_APPLICATION_CREDENTIALS=/var/run/secrets/google-cloud/credentials.json
```

## Como renderizar os manifests

Antes de aplicar no cluster, valide o resultado gerado pelo Helm:

```bash
helm template poc-wif ./cicd -f ./cicd/values.yaml
```

Para salvar a saída em um arquivo:

```bash
helm template poc-wif ./cicd -f ./cicd/values.yaml > rendered.yaml
```

## Como instalar

```bash
helm upgrade --install poc-wif ./cicd \
  --namespace poc-wif \
  --create-namespace \
  -f ./cicd/values.yaml
```

## Como validar o deploy

Verifique os recursos criados:

```bash
kubectl get all -n poc-wif
kubectl get serviceaccount -n poc-wif
kubectl get configmap -n poc-wif
```

Verifique o Pod:

```bash
kubectl get pods -n poc-wif
kubectl describe pod -n poc-wif -l app.kubernetes.io/instance=poc-wif
```

Veja os logs da POC:

```bash
kubectl logs -n poc-wif deploy/poc-wif
```

Se o fluxo estiver funcionando, os logs devem indicar:

- autenticação do `gcloud` via WIF;
- conta ativa configurada;
- listagem do bucket GCS;
- geração de access token;
- resposta da API Gemini/Vertex AI.

## Como testar o chart

O chart possui um teste Helm simples que tenta acessar o Service:

```bash
helm test poc-wif -n poc-wif
```

## Como desinstalar

```bash
helm uninstall poc-wif -n poc-wif
```

Caso queira remover também o namespace:

```bash
kubectl delete namespace poc-wif
```

## Ingress e HTTPRoute

Por padrão, ambos estão desabilitados:

```yaml
ingress:
  enabled: false

httpRoute:
  enabled: false
```

Use `ingress.enabled=true` se o cluster usa Ingress Controller tradicional, como NGINX Ingress.

Use `httpRoute.enabled=true` se o cluster usa Gateway API e já possui um Gateway configurado.

Não é comum habilitar os dois ao mesmo tempo para o mesmo serviço. Escolha o padrão de exposição usado pelo cluster.

## HPA

O HPA é controlado por:

```yaml
autoscaling:
  enabled: true
  minReplicas: 1
  maxReplicas: 1
  targetCPUUtilizationPercentage: 80
```

Quando `autoscaling.enabled=true`, o campo `replicas` não é definido diretamente no Deployment. O número de réplicas passa a ser controlado pelo HPA.

Para uma POC, `minReplicas` e `maxReplicas` podem ficar iguais a `1`. Para produção, ajuste esses valores conforme a necessidade da aplicação.

## Pré-requisitos para o WIF funcionar

Antes de aplicar o chart, a parte da Google Cloud precisa estar configurada corretamente:

- Workload Identity Pool criado.
- Workload Identity Provider criado.
- Issuer do cluster Kubernetes configurado no provider.
- JWKS ou mecanismo equivalente de validação configurado no provider.
- `audience` do token Kubernetes compatível com o provider.
- Mapeamento de atributos configurado no provider.
- Permissões IAM concedidas para a identidade externa ou para a Service Account que será impersonada, dependendo do modelo escolhido.

Do lado do Kubernetes, o cluster precisa suportar projected ServiceAccount tokens, recurso usado para montar tokens temporários com audience e expiração controladas.

## Troubleshooting

### Erro de audience inválida

Verifique se o valor abaixo é exatamente o provider esperado pela Google Cloud:

```yaml
workloadIdentity:
  audience: "//iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID"
```

Também confirme se o token projetado no Pod foi criado com essa mesma audience.

### Erro `Permission denied`

A autenticação pode estar funcionando, mas a identidade externa pode não ter permissão no recurso acessado.

Valide as permissões IAM para o bucket, projeto, Vertex AI ou serviço específico que a aplicação está tentando acessar.

### `GOOGLE_APPLICATION_CREDENTIALS` não encontrado

Confirme se o WIF está habilitado:

```yaml
workloadIdentity:
  enabled: true
```

E verifique se o arquivo foi montado no Pod:

```bash
kubectl exec -n poc-wif deploy/poc-wif -- ls -la /var/run/secrets/google-cloud
kubectl exec -n poc-wif deploy/poc-wif -- cat /var/run/secrets/google-cloud/credentials.json
```

### Token Kubernetes não encontrado

Verifique o volume do token projetado:

```bash
kubectl exec -n poc-wif deploy/poc-wif -- ls -la /var/run/secrets/tokens
```

O arquivo esperado é:

```text
/var/run/secrets/tokens/token
```

### HPA não aparece

Confirme se o autoscaling está habilitado:

```yaml
autoscaling:
  enabled: true
```

Depois valide:

```bash
kubectl get hpa -n poc-wif
```

## Observações importantes

- O `credentials.json` gerado pelo chart não contém chave privada.
- O token Kubernetes é temporário e montado apenas dentro do Pod.
- Quando WIF está habilitado, o token padrão da ServiceAccount não é montado automaticamente.
- A `audience` precisa estar alinhada com o Workload Identity Provider da Google Cloud.
- O namespace é obrigatório neste chart, pois o helper `char-wif.namespace` usa `required`.
- O nome interno dos helpers é `char-wif`. Se o chart for renomeado profundamente, revise também os `include "char-wif.*"` nos templates.

## Resumo

Este template entrega uma base reutilizável para deploy de aplicações Kubernetes com autenticação segura na Google Cloud via Workload Identity Federation.

Ele permite trocar chaves estáticas por credenciais temporárias, reduzindo risco operacional e simplificando a rotação de credenciais. Para usar em uma aplicação real, normalmente basta trocar a imagem, ajustar as variáveis de ambiente e manter a configuração de WIF compatível com o provider configurado na Google Cloud.
