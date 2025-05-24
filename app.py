from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from connection.nfe_utils import enviar_nfe_por_whatsapp
from connection.db import get_db_connection
from connection import config
from reportlab.pdfgen import canvas
import os


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessário para utilizar flash messages

# Garante que a pasta de PDFs existe
if not os.path.exists(config.DATA_DIR):
    os.makedirs(config.DATA_DIR)

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.pedido_id, c.nome_cliente, p.valor_total, p.data_pedido, he.status_envio
        FROM pedidos p
        JOIN clientes c ON p.cliente_id = c.cliente_id
        LEFT JOIN historico_envios he ON p.pedido_id = he.pedido_id
        ORDER BY p.data_pedido DESC
    """)
    pedidos = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', pedidos=pedidos)

@app.route('/pedidos/novo')
def novo_pedido():
    return render_template('pedidos_novo.html')

@app.route('/registrar_pedido', methods=['POST'])
def registrar_pedido():
    nome_cliente = request.form['nome_cliente']
    nome_vendedor = request.form['nome_vendedor']
    produtos = request.form['produtos']
    quantidade = int(request.form['quantidade'])
    valor_unitario = float(request.form['valor_unitario'])
    desconto = float(request.form['desconto'] or 0)
    numero_whatsapp = request.form['numero_whatsapp']
    forma_pagamento = request.form['forma_pagamento']
    observacao = request.form.get('observacao', '')

    rua = request.form.get('rua', '')
    numero = request.form.get('numero', '')
    bairro = request.form.get('bairro', '')
    cidade = request.form.get('cidade', '')
    estado = request.form.get('estado', '')
    cep = request.form.get('cep', '')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Verifica cliente
    cursor.execute("SELECT cliente_id FROM clientes WHERE whatsapp = %s", (numero_whatsapp,))
    cliente = cursor.fetchone()

    if cliente:
        cliente_id = cliente[0]
    else:
        cursor.execute("""
            INSERT INTO clientes (nome_cliente, whatsapp)
            VALUES (%s, %s)
        """, (nome_cliente, numero_whatsapp))
        cliente_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO enderecos (cliente_id, rua, numero, bairro, cidade, estado, cep)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (cliente_id, rua, numero, bairro, cidade, estado, cep))

    # Calcula o valor total com desconto
    valor_total = (valor_unitario * quantidade) * (1 - (desconto / 100))

    # Insere pedido
    cursor.execute("""
        INSERT INTO pedidos (cliente_id, nome_vendedor, valor_unitario, valor_total, desconto, forma_pagamento, observacao)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (cliente_id, nome_vendedor, valor_unitario, valor_total, desconto, forma_pagamento, observacao))
    pedido_id = cursor.lastrowid

    # Insere item na tabela pedido_produto
    cursor.execute("""
        INSERT INTO pedido_produto (pedido_id, produto_id, quantidade, valor_unitario)
        VALUES (%s, %s, %s, %s)
    """, (pedido_id, None, quantidade, valor_unitario))

    conn.commit()

    # Gera o PDF
    pdf_path = gerar_pdf_nfe(
        pedido_id, nome_vendedor, nome_cliente, produtos, quantidade,
        valor_unitario, desconto, forma_pagamento, rua, numero,
        bairro, cidade, estado, cep
    )

    # Envia a NFE por WhatsApp
    sucesso_envio = enviar_nfe_por_whatsapp(pdf_path, pedido_id, numero_whatsapp)

    # Atualiza histórico de envio
    cursor.execute("""
        INSERT INTO historico_envios (pedido_id, status_envio)
        VALUES (%s, %s)
    """, (pedido_id, 'sucesso' if sucesso_envio else 'falha'))

    conn.commit()
    conn.close()

    flash(f'NFE gerada e enviada com sucesso para {numero_whatsapp}!', 'success')
    return redirect(url_for('dashboard'))

def gerar_pdf_nfe(pedido_id, nome_vendedor, nome_cliente, produtos, quantidade, valor_unitario, desconto, forma_pagamento, rua, numero, bairro, cidade, estado, cep):
    filename = f"nfe_{pedido_id}.pdf"
    filepath = os.path.join(config.DATA_DIR, filename)

    c = canvas.Canvas(filepath)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 800, "NOTA FISCAL ELETRÔNICA")

    c.setFont("Helvetica", 12)
    c.drawString(50, 760, f"Funcionário: {nome_vendedor}")
    c.drawString(50, 740, f"Nome do Cliente: {nome_cliente}")
    c.drawString(50, 720, f"Produto: {produtos}")
    c.drawString(50, 700, f"Quantidade: {quantidade}")
    c.drawString(50, 680, f"Valor Unitário: R$ {valor_unitario:.2f}")
    valor_total = (valor_unitario * int(quantidade)) * (1 - (float(desconto) / 100))
    c.drawString(50, 660, f"Valor Total: R$ {valor_total:.2f}")
    c.drawString(50, 640, f"Desconto: % {desconto:.2f}")
    c.drawString(50, 620, f"Forma de Pagamento: {forma_pagamento}")

    # Endereço
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 590, "Endereço de Entrega:")
    c.setFont("Helvetica", 12)
    c.drawString(50, 570, f"Rua: {rua}")
    c.drawString(50, 550, f"Numero: {numero}")
    c.drawString(50, 530, f"Bairro: {bairro}")
    c.drawString(50, 510, f"Cidade: {cidade}")
    c.drawString(50, 490, f"Estado: {estado}")
    c.drawString(50, 470, f"CEP: {cep}")

    c.drawString(50, 450, "Obrigado pela sua compra!")

    c.save()
    return filepath

# Visualizar Pedido

@app.route('/visualizar_pedido/<int:pedido_id>')
def visualizar_pedido(pedido_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pedidos WHERE pedido_id = %s", (pedido_id,))
    pedido = cursor.fetchone()
    conn.close()
    return render_template('visualizar_pedido.html', pedido=pedido)

# Baixar NFE

@app.route('/baixar_nfe/<int:pedido_id>')
def baixar_nfe(pedido_id):
    pdf_path = os.path.join(config.DATA_DIR, f"nfe_{pedido_id}.pdf")
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    flash('Arquivo não encontrado!', 'danger')
    return redirect(url_for('dashboard'))

# Configurações

@app.route('/configuracoes')
def configuracoes():
    return render_template('configuracoes.html')

# Deletar Pedido

@app.route('/deletar_pedido/<int:pedido_id>', methods=['POST'])
def deletar_pedido(pedido_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Remove relacionamentos primeiro (pedido_produto, historico_envios, etc.)
    cursor.execute(
        "DELETE FROM pedido_produto WHERE pedido_id = %s", (pedido_id,))
    cursor.execute(
        "DELETE FROM historico_envios WHERE pedido_id = %s", (pedido_id,))
    cursor.execute("DELETE FROM pedidos WHERE pedido_id = %s", (pedido_id,))
    conn.commit()

    # Remove o PDF gerado (se existir)
    pdf_path = os.path.join(config.DATA_DIR, f"nfe_{pedido_id}.pdf")
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

    conn.close()
    flash('Pedido deletado com sucesso.', 'success')
    return redirect(url_for('dashboard'))

# Iniciar app
if __name__ == '__main__':
    app.run(debug=True)