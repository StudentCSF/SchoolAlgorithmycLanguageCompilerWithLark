from lark import Lark
from lark.visitors import InlineTransformer

from sal_ast import *

parser = Lark('''
    %import common.NUMBER
    %import common.CNAME
    %import common.NEWLINE
    %import common.WS

    %ignore WS

    COMMENT: "/*" /(.|\\n|\\r)+/ "*/"
        |  "//" /(.)+/ NEWLINE
    %ignore COMMENT

    num: NUMBER
    ident: CNAME
    true: "да"
    false: "нет"
    not: "не"

    ?group: num
        | ident
        | "(" add ")"

    ?mult: group
        | mult "*" group    -> mul
        | mult "/" group    -> div

    ?add: mult
        | add "+" mult      -> add
        | add "-" mult      -> sub
        
    ?less: add "<" add -> less
    
    ?more: add ">" add -> more
    
    ?equals: add "=" add -> equals
    
    ?m_or_eq: add ">=" add -> more_or_equals
    
    ?l_or_eq: add "<=" add -> less_or_equals
    
    func_call: ident ("(" expr ("," expr)* ")")?

    ?expr: add
        | less
        | more
        | equals
        | m_or_eq
        | l_or_eq
        | func_call
        

    if:  "если" expr "то" stmt ("иначе" stmt)?

    if2:  "если" expr "то" stmt "иначе" stmt  -> if
        | "если" expr "то" stmt              -> if

    while: "нц" "пока" expr (stmt_list)? "кц"
    
    do_while: "нц" (stmt_list)? "кц_при" expr
    
    for: "нц" "для" ident "от" expr "до" expr (stmt_list)? "кц"
    
    cycle: "нц" "пока" expr (stmt_list) "кц" -> while
        | "нц" (stmt_list)? "кц_при" expr -> do_while
        | "нц" "для" ident "от" expr "до" expr (stmt_list)? "кц" -> for
        
    func_decl: "алг" ident ("(" ident ("," ident)* ")")? "нач" (stmt_list)? "кон"

    ?stmt: "ввод" ident     -> input
        | "вывод" expr     -> output
        | ident ":=" expr    -> assign
        | if2
        | cycle
        | func_decl
        | "{" stmt_list "}"

    stmt_list: stmt*

    ?prog: stmt_list

    ?start: prog
''', start="start", debug=True)


class MelASTBuilder(InlineTransformer):
    def __getattr__(self, item):
        if isinstance(item, str) and item.upper() == item:
            return lambda x: x

        if item == 'true':
            return lambda: NumNode(1)
        if item in ('mul', 'div', 'add', 'sub'):
            def get_bin_op_node(*args):
                op = BinOp[item.upper()]
                return BinOpNode(op, *args)

            return get_bin_op_node
        if item in ('more', 'less', 'equals', 'more_or_equals', 'less_or_equals'):
            def get_compare_op_node(*args):
                op = CompareOp[item.upper()]
                return CompareOpNode(op, *args)

            return get_compare_op_node
        if item == 'func_decl':
            def get_func_decl_node(*args):
                #op = FuncDeclNode()
                print(args)
                return FuncDeclNode(*args)

            return get_func_decl_node
        else:
            def get_node(*args):
                cls = eval(''.join(x.capitalize() or '_' for x in item.split('_')) + 'Node')
                return cls(*args)

            return get_node


def parse(prog: str) -> StmtListNode:
    prog = parser.parse(str(prog))
    prog = MelASTBuilder().transform(prog)
    return prog
