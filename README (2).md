# 📊 Dashboard de Caixa — Streamlit + Excel

> Dashboard financeiro profissional com gráficos em tempo real, alimentado por planilha Excel.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-red)
![Plotly](https://img.shields.io/badge/Plotly-5.18%2B-purple)

---

## 📋 Funcionalidades

- 📈 **Fluxo diário** de entradas e saídas
- 🍕 **Gráficos de pizza** por categoria (entradas e saídas separados)
- 📊 **Barras comparativas** por categoria
- 📆 **Resumo mensal** com saldo em linha secundária
- 🏆 **Ranking de categorias** (horizontal)
- 🔄 **Atualização automática** ao salvar o Excel
- 🗂️ **Tabela detalhada** filtrável
- 🎨 Design profissional com KPIs coloridos

---

## 🚀 Deploy no Streamlit Cloud (recomendado)

1. Faça **fork** deste repositório
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Clique em **New app**
4. Selecione seu repositório e o arquivo `dashboard_caixa.py`
5. Clique em **Deploy** ✅

---

## 💻 Rodar localmente

```bash
# 1. Clone o repositório
git clone https://github.com/SEU_USUARIO/SEU_REPO.git
cd SEU_REPO

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Execute
streamlit run dashboard_caixa.py
```

Acesse em: `http://localhost:8501`

---

## 📝 Estrutura do Excel (`caixa_demo.xlsx`)

| Coluna | Campo | Exemplo |
|--------|-------|---------|
| A | Data | `26/06/2025` |
| B | Descrição | `Venda produto #123` |
| C | Categoria | `Vendas` / `Fornecedores` |
| D | Tipo | `Entrada` ou `Saída` |
| E | Valor (R$) | `1500.00` |
| F | Observação | *(livre)* |

> Para usar **seu próprio arquivo**, substitua `caixa_demo.xlsx` na raiz do repositório e ajuste a variável `EXCEL_PATH` no topo do script.

---

## 📁 Estrutura do repositório

```
📦 repositório
 ┣ 📜 dashboard_caixa.py   ← app principal
 ┣ 📊 caixa_demo.xlsx      ← dados de exemplo
 ┣ 📋 requirements.txt     ← dependências Python
 ┗ 📖 README.md
```

---

## 🔄 Atualização automática

1. Ative o toggle **"Atualização automática"** na sidebar
2. Defina o intervalo desejado (5–60 segundos)
3. Edite e salve o Excel — o dashboard recarrega sozinho

---

*Desenvolvido com [Streamlit](https://streamlit.io) + [Plotly](https://plotly.com)*
