# 📊 Dashboard de Caixa — Streamlit + Google Sheets

Dashboard financeiro profissional com atualização **ao vivo** via Google Sheets.

---

## ⚡ Como configurar (passo a passo)

### 1. Criar a planilha Google Sheets

Acesse [sheets.google.com](https://sheets.google.com) e crie uma nova planilha com exatamente esta estrutura na **linha 1**:

| A | B | C | D | E |
|---|---|---|---|---|
| Data | Descrição | Categoria | Tipo | Valor (R$) |

Exemplos de dados para preencher:

| Data | Descrição | Categoria | Tipo | Valor (R$) |
|------|-----------|-----------|------|------------|
| 26/06/2025 | Venda produto #001 | Vendas | Entrada | 1500 |
| 26/06/2025 | Pagamento fornecedor | Fornecedores | Saída | 800 |
| 27/06/2025 | Prestação de serviço | Serviços | Entrada | 2200 |

> **Regras importantes:**
> - Coluna **Tipo**: sempre `Entrada` ou `Saída` (com acento)
> - Coluna **Data**: formato `DD/MM/AAAA`
> - Coluna **Valor**: só números, sem R$ (ex: `1500.00`)

---

### 2. Publicar a planilha (tornar pública)

1. No Google Sheets, clique em **Compartilhar** (botão azul, canto superior direito)
2. Em "Acesso geral", selecione **"Qualquer pessoa com o link"**
3. Permissão: **Leitor** (só leitura)
4. Clique em **Concluído**

---

### 3. Pegar o ID da planilha

A URL da sua planilha tem este formato:
```
https://docs.google.com/spreadsheets/d/XXXXXXXXXXXXXXXXX/edit
```
Copie o trecho `XXXXXXXXXXXXXXXXX` — esse é o **ID**.

---

### 4. Atualizar o código

Abra `dashboard_caixa.py` e substitua na linha `SHEET_URL`:

```python
# Antes:
SHEET_URL = "https://docs.google.com/spreadsheets/d/SEU_ID_AQUI/export?format=csv&gid=0"

# Depois (com seu ID real):
SHEET_URL = "https://docs.google.com/spreadsheets/d/1ABC123XYZ.../export?format=csv&gid=0"
```

---

### 5. Subir no GitHub

Suba estes 3 arquivos no repositório:
```
📦 repositório
 ┣ 📜 dashboard_caixa.py
 ┣ 📋 requirements.txt
 ┗ 📖 README.md
```

---

### 6. Deploy no Streamlit Cloud

1. Acesse [share.streamlit.io](https://share.streamlit.io)
2. Clique em **New app**
3. Selecione o repositório e o arquivo `dashboard_caixa.py`
4. Clique em **Deploy** ✅

---

## 🎬 Como demonstrar ao cliente

1. Abra o dashboard no navegador (aba 1)
2. Abra o Google Sheets (aba 2) — compartilhe a tela das duas abas lado a lado
3. Digite uma nova linha no Sheets e pressione **Enter**
4. Aguarde ~5 segundos → o dashboard atualiza automaticamente com o novo valor

---

## 📋 Dependências

```
streamlit>=1.35.0
pandas>=2.0.0
plotly>=5.18.0
openpyxl>=3.1.0
```

---

*Desenvolvido com [Streamlit](https://streamlit.io) + [Plotly](https://plotly.com) + Google Sheets*
