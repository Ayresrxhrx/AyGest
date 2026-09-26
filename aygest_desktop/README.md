# AyGest Desktop

Aplicação desktop profissional de gestão comercial, POS e stock, preparada para operação online multi-tenant.

## Módulos

- Dashboard
- POS / Vendas
- Produtos e categorias
- Stock e armazéns
- Reservas temporárias de stock
- Cotações
- Facturação
- Clientes e fornecedores
- Compras
- Financeiro e caixa
- Relatórios
- Utilizadores e permissões
- Licenciamento por Activation Key
- Impressão POS/térmica e documentos A4
- Exportação profissional para PDF

## Arquitectura alvo

Desktop Python com UI separada da camada de serviços, persistência local segura para cache/offline e API cloud para dados multi-tenant. O servidor deve ser a autoridade para tenant, autenticação, licença e transacções críticas de stock.

## Regra central

Stock disponível = stock físico - stock reservado.

Reservas, vendas e conversões de cotação devem ser processadas com transacções atómicas no backend.

## Licenciamento

Cada tenant utiliza uma Activation Key emitida pelo servidor. A licença suporta plano, estado, expiração, limites e revogação. O cliente mantém um token assinado para tolerância temporária a indisponibilidade da internet, sem transformar o cliente desktop na autoridade da licença.
