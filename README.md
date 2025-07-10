# Sistema de Gestão para Clínica de Fisioterapia

Este é um sistema de gestão completo para clínicas de fisioterapia, desenvolvido para simplificar e automatizar o gerenciamento de pacientes, agendamentos e finanças. A aplicação foi construída em **Python** com o framework **Flask** e projetada para ser executada como um programa de desktop independente.

## ✨ Funcionalidades

- **Dashboard de Controle**
    - Visualização rápida do total de pacientes e novos cadastros no mês.
    - Lista dos próximos agendamentos para fácil acesso.

- **Gestão de Pacientes**
    - Cadastro, edição, busca e exclusão de pacientes.
    - Página de detalhes do paciente com histórico completo de sessões, pagamentos e próximos agendamentos.
    - Alerta visual para pacientes com planos de tratamento próximos do fim.

- **Controle de Agendamentos**
    - **Calendário Interativo:** Agenda visual com suporte a arrastar e soltar para reagendar consultas facilmente.
    - **Agendamento Recorrente:** Agende todas as sessões de um plano de tratamento de uma só vez, com base em dias da semana e horários fixos.
    - **Finalização de Sessão:** Converta um agendamento em uma sessão realizada, adicionando anotações clínicas e registrando pagamentos.

- **Controle Financeiro**
    - Relatório financeiro com faturamento total, mensal e valores pendentes.
    - Registro de pagamentos avulsos ou adiantados, desvinculados de uma sessão específica.
    - Histórico detalhado de todas as transações financeiras.

- **Planos e Relatórios**
    - Gerenciamento completo de planos de tratamento (criar, editar, excluir).
    - Geração de relatório final de tratamento por paciente, pronto para impressão ou PDF.

## 🚀 Tecnologias Utilizadas

- **Backend:** Python
- **Framework:** Flask
- **Banco de Dados:** SQLite3
- **Servidor WSGI:** Waitress
- **Frontend:** HTML5, CSS3, JavaScript
- **Biblioteca de Calendário:** FullCalendar.js
- **Empacotamento:** PyInstaller

## ⚙️ Como Executar

### Para Usuários Finais

1. Localize o arquivo `run.exe` (ou nome definido durante o empacotamento).
2. Dê um duplo clique para iniciar o sistema.
3. O programa iniciará um servidor local e abrirá o navegador padrão com a aplicação pronta para uso.

> **Atenção:** Mantenha o arquivo `run.exe` sempre na mesma pasta que o arquivo `clinica.db`.

### Para Desenvolvedores

**Pré-requisitos:** Python 3 instalado.

1. Clone o repositório:
     ```bash
     git clone https://github.com/CarlosNatanael/clinica_fisioterapia
     cd clinica_fisioterapia
     ```
2. Instale as dependências:
     ```bash
     pip install Flask waitress
     ```
3. Inicialize o banco de dados:
     ```bash
     python init_db.py
     ```
4. Inicie a aplicação:
     ```bash
     python run.py
     ```
5. Acesse o sistema no navegador pelo endereço fornecido no terminal (normalmente [http://127.0.0.1:5000](http://127.0.0.1:5000)).

## 📁 Estrutura do Projeto

```
/
├── static/             # Arquivos estáticos (CSS, JS, Imagens)
│   ├── css/
│   ├── img/
│   └── js/
├── templates/          # Arquivos HTML do Flask
├── app.py              # Lógica principal do Flask e rotas
├── run.py              # Ponto de entrada para iniciar o servidor Waitress
├── init_db.py          # Script para criar e inicializar o banco de dados
├── clinica.db          # Banco de dados SQLite
└── README.md           # Este arquivo
```
