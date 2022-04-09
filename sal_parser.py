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
    string: /\".*\"+/
    character: /\'.?'+/
        
    true_false: "да"  -> true
            | "нет" -> false
    
    or_and: or | and

    ?group: num
        | ident
        | "(" or ")"
        | true_false
        | func_call
        | string
        | character

    ?mult: group
        | mult "*" group    -> mul
        | mult "/" group    -> div

    ?add: mult
        | add "+" mult      -> add
        | add "-" mult      -> sub
        
    ?compare: add
        | add ">" add -> more
        | add ">=" add -> more_or_equals
        | add "=" add  -> equals
        | add "<" add  -> less
        | add "<=" add -> less_or_equals
        
    ?not: "не" compare -> not
        | compare
    
    ?and: not
        | and "и" not -> and
        
    ?or: and
        | or "или" and -> or
    
    func_call: ident "(" (expr ("," expr)*)? ")"
    
    var_decl: "сим" ident (":=" expr)?  -> char
        | "лит" ident (":=" expr)?       -> str
        | "цел" ident (":=" expr)?       -> int
        | "лог" ident (":=" expr)?       -> bool
        | "вещ" ident (":=" expr)?       -> float 

    ?expr: or
        

    if:  "если" expr "то" stmt_list ("иначе" stmt_list)? "все"

    if2:  "если" expr "то" stmt_list "иначе" stmt_list "все"  -> if
        | "если" expr "то" stmt_list "все"             -> if

    while: "нц" "пока" expr (stmt_list)? "кц"
    
    do_while: "нц" (stmt_list)? "кц_при" expr
    
    for: "нц" "для" ident "от" expr "до" expr (stmt_list)? "кц"
    
    cycle: "нц" "пока" expr (stmt_list) "кц" -> while
        | "нц" (stmt_list)? "кц_при" expr -> do_while
        | "нц" "для" ident "от" expr "до" expr (stmt_list)? "кц" -> for
        
    func_decl: "алг" ident "(" ("арг" var_decl ("," var_decl)*)? ")" "нач" (stmt_list)? "кон"

    ?stmt: "ввод" ident     -> input
        | "вывод" expr ("," expr)*     -> output
        | ident ":=" expr    -> assign
        | if2
        | cycle
        | var_decl
        | func_decl
        | expr
        

    stmt_list: stmt*

    ?prog: stmt_list

    ?start: prog
''', start="start", debug=True)


class MelASTBuilder(InlineTransformer):
    def __getattr__(self, item):
        if isinstance(item, str) and item.upper() == item:
            return lambda x: x
        if item in ('true', 'false'):
            return lambda: BoolNode(item == 'true')
        if item in ('mul', 'div', 'add', 'sub'):
            def get_bin_op_node(*args):
                op = BinOp[item.upper()]
                return BinOpNode(op, *args)

            return get_bin_op_node
        if item in ('char', 'str', 'int', 'bool', 'float'):
            def get_type_node(*args):
                anode = None
                if len(args) == 2:
                    anode = AssignNode(args[0], args[1])
                op = Type[item.upper()]
                return VarDeclNode(op, args[0], anode)

            return get_type_node
        if item in ('more', 'less', 'equals', 'more_or_equals', 'less_or_equals'):
            def get_compare_op_node(*args):
                op = CompareOp[item.upper()]
                return CompareOpNode(op, *args)

            return get_compare_op_node
        if item in ('not', 'or', 'and'):
            def get_log_op_node(*args):
                op = LogOp[item.upper()]
                return LogOpNode(op, *args)

            return get_log_op_node
        else:
            def get_node(*args):
                cls = eval(''.join(x.capitalize() or '_' for x in item.split('_')) + 'Node')
                return cls(*args)

            return get_node


def parse(prog: str) -> StmtListNode:
    prog = parser.parse(str(prog))
    prog = MelASTBuilder().transform(prog)
    return prog
