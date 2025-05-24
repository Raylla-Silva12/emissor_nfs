CREATE DATABASE nfe;
USE nfe;

CREATE TABLE clientes (
    cliente_id INT AUTO_INCREMENT PRIMARY KEY,
    nome_cliente VARCHAR(255) NOT NULL,
    whatsapp VARCHAR(20) NOT NULL UNIQUE,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pedidos (
    pedido_id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT,
    nome_vendedor VARCHAR(255),
    valor_unitario DECIMAL(10, 2) NOT NULL,
    valor_total DECIMAL(10, 2) NOT NULL,
    desconto DECIMAL(10, 2) DEFAULT 0,
    forma_pagamento ENUM('Cartão de Débito', 'Cartão de Crédito', 'Dinheiro', 'PIX') NOT NULL,
    status_envio ENUM('pendente', 'sucesso', 'falha') DEFAULT 'sucesso',
    data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    observacao VARCHAR(255),
    FOREIGN KEY (cliente_id) REFERENCES clientes(cliente_id)
);

CREATE TABLE produtos (
    produto_id INT AUTO_INCREMENT PRIMARY KEY,
    nome_produto VARCHAR(255) NOT NULL,
    preco DECIMAL(10, 2) NOT NULL,
    descricao TEXT
);

CREATE TABLE pedido_produto (
    pedido_produto_id INT AUTO_INCREMENT PRIMARY KEY,
    pedido_id INT,
    produto_id INT,
    quantidade INT NOT NULL,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(pedido_id),
    FOREIGN KEY (produto_id) REFERENCES produtos(produto_id)
);

CREATE TABLE enderecos (
    endereco_id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT,
    rua VARCHAR(255),
    numero INT,
    bairro VARCHAR(100),
    cidade VARCHAR(100),
    estado VARCHAR(100),
    cep VARCHAR(10),
    FOREIGN KEY (cliente_id) REFERENCES clientes(cliente_id)
);

CREATE TABLE historico_envios (
    envio_id INT AUTO_INCREMENT PRIMARY KEY,
    pedido_id INT,
    data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status_envio ENUM('sucesso', 'falha') NOT NULL,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(pedido_id)
);

CREATE TABLE dados_empresa (
    empresa_id INT AUTO_INCREMENT PRIMARY KEY,
    nome_empresa VARCHAR(255) NOT NULL,
    cnpj VARCHAR(20),
    endereco_empresa VARCHAR(255) NOT NULL,
    email_empresa VARCHAR(255) NOT NULL,
    numero_empresa VARCHAR(20)
);