# Basix Engine

To build and update image on DockerHub, follow this steps
```sh
# Só build
make build
```

```sh
# Build + push
make build-push
```

```sh
# (Opcional) com tag personalizada
make build IMAGE_TAG=v0.1.0
make build-push IMAGE_TAG=v0.1.0
```

### **📂 Arquitetura**

* O webhook dispara um fluxo one-shot no Kestra.
* O fluxo executa um container Docker responsável por:

  * criar o agente Maria
  * carregar memória no Qdrant
  * processar intenção
  * gerar resposta
  * salvar memória
  * retornar JSON padronizado

### **🔥 Tarefas do fluxo**

| Task            | Função                                                |
| --------------- | ----------------------------------------------------- |
| `agent`         | Executa o container com o agente                      |
| `return_output` | Converte `outputs.agent.vars` em output final do flow |

### **📤 Retorno do webhook**

Sempre retorna:

```json
{
  "result": {
    "success": true,
    "response": "texto da Maria",
    "metadata": {
      "session_id": "...",
      "intent": "schedule",
      "needs_handoff": false
    }
  }
}
```

### **🔌 Integrações**

* Qdrant (memória vetorial)
* OpenAI (LLM)
* Postgres (logs SQL)
* Kestra (orquestração)

---

# 3️⃣ **Definir lista final de tools (escopo fechado)**

### ✔ STATUS: **CONCLUÍDO**

Essas são as tools necessárias para a versão 1 do agente (mínimo funcional real):

---

## 🧰 **TOOL LIST — SVIM Maria**

### **1. `criar_agendamento`**

Tool: Agendamento
Descrição: Agenda um horário usando a API Trinks.

Args:
  servicoId (int): O ID do serviço.
  clienteId (int): O ID do cliente.
  profissionalId (int): O ID do profissional.
  dataHoraInicio (str): A data e hora de início do agendamento (ex: "AAAA-MM-DDTHH:MM:SS").
  duracaoEmMinutos (int): A duração do agendamento em minutos.
  valor (int): O valor do agendamento.
  observacoes (str): Quaisquer observações ou notas para o agendamento.
  confirmado (bool): Um booleano indicando se o agendamento está confirmado.

Returns:
  dict: Um dicionário contendo os detalhes do agendamento se bem-sucedido, ou uma mensagem de erro se o agendamento falhar.

### **2. `listar_agendamentos`**
Tool: Listar Agendamentos
Descrição: Lista os agendamentos usando a API Trinks.

Args:
  dataInicio (str): A data de início para filtrar agendamentos (ex: "AAAA-MM-DD").
  dataFim (str): A data de fim para filtrar agendamentos (ex: "AAAA-MM-DD").
  clienteId (int, optional): O ID do cliente para filtrar agendamentos.

Returns:
  dict: Um dicionário contendo os detalhes dos agendamentos se bem-sucedido, ou uma mensagem de erro se a listagem falhar.

### **3. `listar_servicos`**
Tool: Listar Servicos
Descrição: Lista os serviços usando a API Trinks.

Args:
  nome (str | None): O nome do serviço.
  categoria (str | None): A categoria do serviço.
  somenteVisiveisCliente (bool | None): Um booleano indicando se o serviço deve ser visível para o cliente.

Returns:
  dict: Um dicionário contendo os detalhes dos serviços se bem-sucedido, ou uma mensagem de erro se a listagem falhar.

### **4. `listar_profissionais`**
Tool: Listar Profissionais
Descrição: Lista os profissionais do estabelecimento.

Args:
  page (int): Número da página (default 1).
  pageSize (int): Tamanho da página (default 50).

Returns:
  dict: Um dicionário contendo os detalhes dos profissionais se bem-sucedido, ou uma mensagem de erro se a listagem falhar.

### **5. `listar_servicos_profissional`**
Tool: Listar Serviços de um Profissional
Descrição: Lista os serviços de um profissional específico.

Args:
  profissionalId (int): ID do profissional.
  page (int): Número da página (default 1).
  pageSize (int): Tamanho da página (default 50).

Returns:
  dict: Um dicionário contendo os detalhes dos serviços do profissional se bem-sucedido, ou uma mensagem de erro se a listagem falhar.

---

# 4️⃣ **Desenhar o fluxo de decisão do agente por intenção**

### ✔ STATUS: **CONCLUÍDO**

Aqui está o diagrama lógico simplificado usado no SVIM v0.1:

---

## 🤖 **Fluxo de decisão da Maria (Intent Router)**

### **INTENT: SCHEDULE**

1. Extrair entidades → serviço, data, horário, profissional
2. Se faltar dado → perguntar
3. Chamar `tool_find_available_slots`
4. Se disponível → `tool_create_appointment`
5. Confirmar com o cliente

---

### **INTENT: RESCHEDULE**

1. Pedir ID ou identificar o agendamento ativo
2. Verificar disponibilidade
3. Chamar `tool_reschedule_appointment`
4. Confirmar

---

### **INTENT: CANCEL**

1. Pedir ID do agendamento
2. Validar regras pelo `tool_get_policies`
3. Chamar `tool_cancel_appointment`
4. Confirmar

---

### **INTENT: INFO**

1. Classificar tipo de dúvida
2. Se for sobre política → `tool_get_policies`
3. Se for serviço → `tool_get_services`
4. Se for profissional → `tool_get_professionals`

---

### **INTENT: SMALLTALK**

Apenas conversa — não chama tool.

---

### **INTENT: UNKNOWN**

Responder educadamente e pedir mais contexto.

---

# 5️⃣ **Contrato de entrada/saída de cada tool (interfaces)**

### ✔ STATUS: **CONCLUÍDO**

## 📄 **Interface dos Tools — versão final**

---

### **1. tool_find_available_slots**

**Input**

```json
{
  "service_id": "cut",
  "professional_id": "123",
  "date": "2025-01-10"
}
```

**Output**

```json
{
  "slots": [
    "10:00",
    "11:30",
    "14:00"
  ]
}
```

---

### **2. tool_create_appointment**

**Input**

```json
{
  "customer_id": "gui",
  "service_id": "cut",
  "professional_id": "123",
  "datetime": "2025-01-10T14:00"
}
```

**Output**

```json
{
  "appointment_id": "abc123",
  "status": "confirmed"
}
```

---

### **3. tool_reschedule_appointment**

**Input**

```json
{
  "appointment_id": "abc123",
  "new_datetime": "2025-01-11T13:00"
}
```

**Output**

```json
{
  "status": "rescheduled"
}
```

---

### **4. tool_cancel_appointment**

**Input**

```json
{
  "appointment_id": "abc123",
  "reason": "cliente solicitou"
}
```

**Output**

```json
{
  "status": "cancelled"
}
```

---

### **5. tool_get_services**

**Output**

```json
{
  "services": [
    {
      "id": "cut",
      "name": "Corte",
      "duration": 45
    }
  ]
}
```

---

### **6. tool_get_professionals**

**Input**

```json
{ "service_id": "cut" }
```

**Output**

```json
{
  "professionals": [
    { "id": "123", "name": "Paulo", "senior": true }
  ]
}
```