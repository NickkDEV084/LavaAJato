"""Operações CRUD usadas pela tela do cliente. Não abre servidor nem API."""

try:
    from .lavaAjato import conectar, criar_tabelas
except ImportError:
    from lavaAjato import conectar, criar_tabelas


def _consultar(sql, dados=(), varios=False):
    criar_tabelas()
    conexao = conectar()
    try:
        cursor = conexao.execute(sql, dados)
        if varios:
            return [dict(linha) for linha in cursor.fetchall()]
        linha = cursor.fetchone()
        return dict(linha) if linha else None
    finally:
        conexao.close()


def _alterar(sql, dados=(), criar=False):
    criar_tabelas()
    conexao = conectar()
    try:
        cursor = conexao.execute(sql, dados)
        conexao.commit()
        return cursor.lastrowid if criar else cursor.rowcount == 1
    finally:
        conexao.close()



def criar_cliente(nome, telefone="", carro="", marca="", placa=""):
    return _alterar(
        "INSERT INTO clientes (nome, telefone, carro, marca, placa) VALUES (?, ?, ?, ?, ?)",
        (nome, telefone, carro, marca, (placa or "").upper()),
        criar=True,
    )


def buscar_cliente(cliente_id):
    return _consultar("SELECT * FROM clientes WHERE id = ?", (cliente_id,))


def atualizar_cliente(cliente_id, nome, telefone="", carro="", marca="", placa=""):
    return _alterar(
        "UPDATE clientes SET nome = ?, telefone = ?, carro = ?, marca = ?, placa = ? WHERE id = ?",
        (nome, telefone, carro, marca, (placa or "").upper(), cliente_id),
    )



def listar_servicos():
    return _consultar(
        "SELECT id, nome, descricao, preco, duracao_min FROM servicos "
        "WHERE ativo = 1 ORDER BY nome",
        varios=True,
    )



def criar_agendamento(cliente_id, servico_id, data, horario):
    return _alterar(
        "INSERT INTO agendamentos (cliente_id, servico_id, data, horario) VALUES (?, ?, ?, ?)",
        (cliente_id, servico_id, data, horario),
        criar=True,
    )


def buscar_agendamento(agendamento_id, cliente_id):
    return _consultar(
        "SELECT a.id, a.cliente_id, s.nome AS servico, a.data, a.horario, a.status, "
        "s.preco, s.duracao_min FROM agendamentos a "
        "JOIN servicos s ON s.id = a.servico_id "
        "WHERE a.id = ? AND a.cliente_id = ?",
        (agendamento_id, cliente_id),
    )


def listar_agendamentos(cliente_id):
    return _consultar(
        "SELECT a.id, s.nome AS servico, a.data, a.horario, a.status, "
        "s.preco, s.duracao_min FROM agendamentos a "
        "JOIN servicos s ON s.id = a.servico_id "
        "WHERE a.cliente_id = ? ORDER BY a.data, a.horario",
        (cliente_id,),
        varios=True,
    )


def remarcar_agendamento(agendamento_id, cliente_id, data, horario):
    return _alterar(
        "UPDATE agendamentos SET data = ?, horario = ? "
        "WHERE id = ? AND cliente_id = ? AND status = 'agendado'",
        (data, horario, agendamento_id, cliente_id),
    )


def cancelar_agendamento(agendamento_id, cliente_id):
    return _alterar(
        "UPDATE agendamentos SET status = 'cancelado' "
        "WHERE id = ? AND cliente_id = ? AND status = 'agendado'",
        (agendamento_id, cliente_id),
    )
