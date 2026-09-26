# NETSYS 2027 — análise do projecto

Este directório contém a análise do ficheiro `projeto.wps` enviado para revisão.

## O que o projecto faz

É uma aplicação desktop em Python/Tkinter focada num pequeno sistema de vendas/stock. A ideia principal é impedir vendas acima do stock disponível através de reservas temporárias.

Funcionalidades identificadas no código:
- Gestão de stock em ficheiros JSON.
- Produto e unidades de venda (LATA, EMBALAGEM e CAIXA).
- Conversão das unidades para uma unidade-base.
- Reserva temporária de stock para um caixa.
- Bloqueio de venda quando o stock livre não chega.
- Finalização de venda e baixa de stock.
- Criação de cotações com reserva por 3 dias.
- Lista de cotações e aprovação de uma cotação para venda.

## Problemas encontrados

### Críticos
1. **`simpledialog` não é importado.** `criar_cotacao()` chama `simpledialog.askstring`, mas só `ttk` e `messagebox` são importados.
2. **A segunda parte da interface está depois de `root.mainloop()`.** O `mainloop()` bloqueia a execução normal até a janela fechar; por isso os botões de cotações só são definidos depois do encerramento da aplicação e não ficam disponíveis durante a utilização normal.
3. **`finalizar()` apaga todas as reservas.** A operação escreve `[]` em `reservas.json`, removendo reservas de outros caixas/cotações.
4. **A aprovação de cotação pode baixar stock sem validar novamente o stock disponível.** Isto pode permitir stock negativo em cenários de concorrência/alterações.
5. **A cotação pode continuar a ser aprovada depois da reserva expirar.** O código não valida `expira` da cotação antes de transformar a cotação em venda.
6. **A mesma reserva pode ser criada várias vezes.** O fluxo de cotação acrescenta reservas sem uma chave/ID robusta que impeça duplicação.

### Graves
7. **Concorrência insegura:** ficheiros JSON são usados como base de dados sem lock/transacção. Dois caixas podem ler o mesmo stock e gravar resultados conflitantes.
8. **Escritas não atómicas:** `open(..., 'w').write(...)` pode deixar os ficheiros incompletos se a aplicação for interrompida durante a gravação.
9. **Produto hardcoded:** só existe `COCA-COLA` no código.
10. **Stock inicial hardcoded:** o primeiro arranque cria automaticamente 240 latas.
11. **Dados da empresa hardcoded:** nome `NETSYS 2027`, NUIT e IVA estão directamente no código.
12. **Preços definidos mas não usados no cálculo da venda/cotação.** Não existe total monetário real nem registo de pagamentos.
13. **A mensagem diz que imprime numa Xprinter, mas não existe código de impressão.**
14. **Sem autenticação/perfis de caixa.** O caixa é simplesmente a string `Caixa1`.
15. **Sem histórico de vendas.** Depois da baixa, não existe documento de venda guardado.
16. **Sem clientes estruturados, produtos, categorias, fornecedores ou movimentos de stock.**
17. **Tratamento de erros demasiado amplo:** `except: pass` em `atualizar_status()` pode esconder falhas reais.

### Arquitectura / manutenção
18. O projecto mistura interface, regras de negócio e persistência no mesmo ficheiro.
19. JSON não é uma boa escolha para stock multi-caixa se o objectivo for utilização real em rede.
20. Não há validação robusta de quantidades negativas/zero, produto inexistente ou unidade inválida.
21. Não existe mecanismo de recuperação/transacção para vendas interrompidas.
22. Não existe sincronização real entre computadores; partilhar os mesmos ficheiros JSON numa pasta de rede não resolve concorrência de forma segura.

## Resultado da análise

O código tem uma **prova funcional da ideia de reserva de stock**, mas ainda não é uma implementação segura de POS multi-caixa. A parte de stock/reserva é o núcleo do projecto; cotações e impressão aparecem como funcionalidades iniciadas, mas estão incompletas.

## Teste realizado

O código extraído do WPS foi convertido para `projeto_original.py` e passou pela verificação de sintaxe Python (`py_compile`). Isso significa que o texto extraído é sintacticamente compilável, mas **não significa que a aplicação esteja funcional em runtime**. Os problemas acima são principalmente de fluxo, arquitectura e execução.

## Próximo passo técnico recomendado

Para uma versão real, a base deveria ser migrada para SQLite (ou PostgreSQL se for multi-PC/cloud), com tabelas para produtos, stock, reservas, vendas, itens de venda, cotações, clientes e caixas; transacções atómicas para reservar/baixar stock; IDs únicos; expiração validada no servidor; e uma camada de serviços separada da UI.

> Nota: o GitHub connector disponível nesta sessão permite trabalhar em repositórios existentes, mas não expõe criação de um novo repositório vazio. Por isso esta análise foi colocada numa branch separada do repositório `Ayresrxhrx/AyGest`, sem alterar a `main`.
