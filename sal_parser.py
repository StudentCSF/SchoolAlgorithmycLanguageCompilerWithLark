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
    character: /'.?'+/
    
        
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
        | add ">" add -> gt
        | add ">=" add -> ge
        | add "=" add  -> equals
        | add "<" add  -> lt
        | add "<=" add -> le
        
    ?not: "не" compare -> not
        | compare
    
    ?and: not
        | and "и" not -> and
        
    ?or: and
        | or "или" and -> or
    
    func_call: ident "(" (expr ("," expr)*)? ")"

    assign: ident ":=" expr
    
    var_decl: "сим" ident   -> char
        | "сим" assign  -> char
        | "лит" ident       -> str
        | "лит" assign       -> str
        | "цел" ident        -> int
        | "цел" assign        -> int
        | "лог" ident        -> bool
        | "лог" assign       -> bool
        | "вещ" ident        -> float 
        | "вещ" assign        -> float 

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
        
    params: "арг" var_decl ("," var_decl)*

    

    res: "рез" var_decl
        
    func_decl: "алг" ident "(" (params ",")? res ")" "нач" (stmt_list)? "кон"
        |   "алг" ident "(" params? ")" "нач" (stmt_list)? "кон"

    ?stmt: "ввод" ident                 -> input
        | "вывод" expr ("," expr)*      -> output
        | var_decl
        | assign
        | if2
        | cycle
        | func_decl
        | expr
        

    stmt_list: stmt*

    ?prog: stmt_list

    ?start: prog
''', start="start", debug=True)

loc = None


class MelASTBuilder(InlineTransformer):
    def __getattr__(self, item):
        if isinstance(item, str) and item.upper() == item:
            return lambda x: x
        if item in ('true', 'false'):
            return lambda: BoolNode(item == 'true', loc=loc)

        if item in ('mul', 'div', 'add', 'sub'):
            def get_bin_op_node(*args):
                op = BinOp[item.upper()]
                return BinOpNode(op, *args, loc=loc)

            return get_bin_op_node
        if item in ('char', 'str', 'int', 'bool', 'float'):
            def get_type_node(*args):
                anode = None
                if len(args) == 2:
                    anode = AssignNode(args[0], args[1])
                op = TypeNode(Type[item.upper()].value, *args, loc=loc)
                return VarDeclNode(op, args[0], anode, loc=loc)

            return get_type_node
        if item in ('gt', 'lt', 'equals', 'le', 'ge'):
            def get_compare_op_node(*args):
                op = CompareOp[item.upper()]
                return CompareOpNode(op, *args, loc=loc)

            return get_compare_op_node
        if item in ('not', 'or', 'and'):
            def get_log_op_node(*args):
                op = LogOp[item.upper()]
                return LogOpNode(op, *args, loc=loc)

            return get_log_op_node

        # if item == 'var_decl':
        #     def get_var_decl_node(*args):
        #         un: Union[IdentNode, AssignNode] = args[1], args[2]
        #         return VarDeclNode(args[0], un, loc=loc)

        #     return get_var_decl_node

        else:
            def get_node(*args):
                cls = eval(''.join(x.capitalize() or '_' for x in item.split('_')) + 'Node')
                return cls(*args, loc=loc)

            return get_node


def parse(prog: str) -> StmtListNode:
    locs = []
    row, col = 0, 0
    for c in prog:
        if c == '\n':
            row += 1
            col = 0
        elif c == '\r':
            pass
        else:
            col += 1
        locs.append((row, col))

    old_init_action = AstNode.init_action

    def init_action(node: AstNode) -> None:
        loc = getattr(node, 'loc', None)
        if isinstance(loc, int):
            node.row = locs[loc][0] + 1
            node.col = locs[loc][1] + 1

    AstNode.init_action = init_action
    try:
        prog: StmtListNode = parser.parse(str(prog))
        prog.program = True
        prog = MelASTBuilder().transform(prog)
        return prog
    finally:
        AstNode.init_action = old_init_action
    # return prog
