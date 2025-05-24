// Funções utilitárias para o sistema de notas fiscais

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips do Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Inicializar popovers do Bootstrap
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Toggle do sidebar em dispositivos móveis
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            document.querySelector('.sidebar').classList.toggle('show');
        });
    }
    
    // Fechar alertas automaticamente após 5 segundos
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000);
    });
    
    // Formatadores de entrada para valores monetários
    const currencyInputs = document.querySelectorAll('.currency-input');
    currencyInputs.forEach(function(input) {
        input.addEventListener('input', function(e) {
            let value = e.target.value;
            
            // Remove todos os caracteres não numéricos
            value = value.replace(/[^\d]/g, '');
            
            // Converte para formato monetário (ex: R$ 99,99)
            if (value) {
                // Divide por 100 para obter os centavos
                value = (parseInt(value) / 100).toFixed(2);
                // Formata com separador de milhar e decimal
                value = value.replace('.', ',');
                value = value.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
                e.target.value = `R$ ${value}`;
            } else {
                e.target.value = '';
            }
        });
    });
    
    // Formatador de documento (CNPJ/CPF)
    const documentInputs = document.querySelectorAll('.document-input');
    documentInputs.forEach(function(input) {
        input.addEventListener('input', function(e) {
            let value = e.target.value;
            
            // Remove todos os caracteres não numéricos
            value = value.replace(/[^\d]/g, '');
            
            // Formata como CNPJ se tiver 14 dígitos (XX.XXX.XXX/XXXX-XX)
            if (value.length > 11) {
                value = value.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2}).*/, '$1.$2.$3/$4-$5');
            } 
            // Formata como CPF se tiver 11 dígitos (XXX.XXX.XXX-XX)
            else if (value.length === 11) {
                value = value.replace(/^(\d{3})(\d{3})(\d{3})(\d{2}).*/, '$1.$2.$3-$4');
            }
            
            e.target.value = value;
        });
    });
    
    // Formatador de telefone
    const phoneInputs = document.querySelectorAll('.phone-input');
    phoneInputs.forEach(function(input) {
        input.addEventListener('input', function(e) {
            let value = e.target.value;
            
            // Remove todos os caracteres não numéricos
            value = value.replace(/[^\d]/g, '');
            
            // Formata como (XX) XXXXX-XXXX
            if (value.length > 10) {
                value = value.replace(/^(\d{2})(\d{5})(\d{4}).*/, '($1) $2-$3');
            } 
            // Formata como (XX) XXXX-XXXX
            else if (value.length > 6) {
                value = value.replace(/^(\d{2})(\d{4})(\d{0,4}).*/, '($1) $2-$3');
            }
            // Formata como (XX
            else if (value.length > 2) {
                value = value.replace(/^(\d{2})(\d{0,5}).*/, '($1) $2');
            }
            
            e.target.value = value;
        });
    });
    
    // Confirmação de ações críticas
    document.querySelectorAll('.confirm-action').forEach(function(element) {
        element.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm-message') || 'Tem certeza que deseja realizar esta ação?';
            if (!confirm(message)) {
                e.preventDefault();
                e.stopPropagation();
                return false;
            }
        });
    });
    
    // Adicionar ação de impressão
    document.querySelectorAll('.btn-print').forEach(function(button) {
        button.addEventListener('click', function() {
            window.print();
        });
    });
});

// HTMX evento após envio de formulário
document.addEventListener('htmx:afterSwap', function(event) {
    if (event.detail.target.id === 'alerts-container') {
        // Animar para chamar atenção
        const alerts = document.querySelectorAll('#alerts-container .alert');
        alerts.forEach(function(alert) {
            alert.classList.add('animate__animated', 'animate__fadeIn');
            
            // Fechar automaticamente após 5 segundos, se não for permanente
            if (!alert.classList.contains('alert-permanent')) {
                setTimeout(function() {
                    const closeButton = alert.querySelector('.btn-close');
                    if (closeButton) {
                        closeButton.click();
                    }
                }, 5000);
            }
        });
    }
});

// Função para enviar nota fiscal via WhatsApp
function sendInvoiceViaWhatsApp(invoiceId) {
    // Mostra spinner durante o envio
    const button = document.querySelector(`button[data-invoice-id="${invoiceId}"]`);
    const originalContent = button.innerHTML;
    button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Enviando...';
    button.disabled = true;
    
    // Faz a requisição para o endpoint de envio
    fetch(`/api/invoices/${invoiceId}/send`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Exibir mensagem de sucesso
            const alertsContainer = document.getElementById('alerts-container');
            alertsContainer.innerHTML = `
                <div class="alert alert-success alert-dismissible fade show" role="alert">
                    <strong>Sucesso!</strong> Nota fiscal enviada com sucesso via WhatsApp.
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>
                </div>
            `;
            
            // Atualizar o status da nota fiscal na tabela
            const statusCell = document.querySelector(`tr[data-invoice-id="${invoiceId}"] .status-cell`);
            if (statusCell) {
                statusCell.innerHTML = '<span class="badge bg-success">Enviado</span>';
            }
        } else {
            // Exibir mensagem de erro
            const alertsContainer = document.getElementById('alerts-container');
            alertsContainer.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show" role="alert">
                    <strong>Erro!</strong> ${data.message || 'Ocorreu um erro ao enviar a nota fiscal.'}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        
        // Exibir mensagem de erro
        const alertsContainer = document.getElementById('alerts-container');
        alertsContainer.innerHTML = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                <strong>Erro!</strong> Ocorreu um erro ao enviar a nota fiscal.
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>
            </div>
        `;
    })
    .finally(() => {
        // Restaurar o botão para o estado original
        button.innerHTML = originalContent;
        button.disabled = false;
    });
}

// Função auxiliar para formatação de moeda
function formatCurrency(value) {
    if (!value) return 'R$ 0,00';
    
    // Converte para número e formata com 2 casas decimais
    const numberValue = typeof value === 'string' ? parseFloat(value.replace(',', '.')) : value;
    
    // Formata para o padrão brasileiro
    return numberValue.toLocaleString('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    });
}