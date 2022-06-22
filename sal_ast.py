from abc import ABC, abstractmethod
from contextlib import suppress
import imp
from typing import Callable, Tuple, Union, Optional, List
from enum import Enum
from sal_semantic_base import VOID, BinOp

from sal_semantic_base import TypeDesc, IdentDesc, SemanticException, IdentScope, TYPE_CONVERTIBILITY


class AstNode(ABC):
    init_action: Callable[['AstNode'], None] = None

    def __init__(self, row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__()
        self.row = row
        self.col = col
        for k, v in props.items():
            setattr(self, k, v)
        if AstNode.init_action is not None:
            AstNode.init_action(self)
        self.node_type: Optional[TypeDesc] = None
        self.node_ident: Optional[IdentDesc] = None

    @property
    def children(self) -> Tuple['AstNode', ...]:
        return ()

    @abstractmethod
    def __str__(self) -> str:
        pass

    @property
    def tree(self) -> [str, ...]:
        res = [self.to_str_full()]
        childs = self.children
        for i, child in enumerate(childs):
            # if child.__str__() == '': continue
            ch0, ch = '├', '│'
            if i == len(childs) - 1:
                ch0, ch = '└', ' '
            if child is not None:
                res.extend(((ch0 if j == 0 else ch) + ' ' + s for j, s in enumerate(child.tree)))
        return tuple(res)

    def visit(self, func: Callable[['AstNode'], None]) -> None:
        func(self)
        map(func, self.children)

    def __getitem__(self, index):
        return self.children[index] if index < len(self.children) else None

    def to_str(self):
        return str(self)

    def to_str_full(self):
        r = ''
        if self.node_ident:
            r = str(self.node_ident)
        elif self.node_type:
            r = str(self.node_type)
        return self.to_str() + (' : ' + r if r else '')

    def semantic_error(self, message: str):
        raise SemanticException(message, self.row, self.col)

    def semantic_check(self, checker, scope: IdentScope) -> None:
        checker.semantic_check(self, scope)

    def msil_gen(self, generator) -> None:
        generator.msil_gen(self)



class ExprNode(AstNode, ABC):
    pass


class ValueNode(ExprNode, ABC):
    pass


class NumNode(ValueNode):
    def __init__(self, num: str,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row, col, **props)
        if '.' in num:
            self.value = float(num)
        else:
            self.value = int(num)

    def __str__(self) -> str:
        return str(self.value)


class StringNode(ValueNode):
    def __init__(self, str_: str,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row, col, **props)
        self.value = str_

    def __str__(self):
        return self.value


class CharacterNode(ValueNode):
    def __init__(self, char: str,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.value = char

    def __str__(self):
        return self.value


class IdentNode(ExprNode):

    def __init__(self, name: str,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.name = str(name)

    def __str__(self) -> str:
        return str(self.name)


class TypeNode(IdentNode):
    """Класс для представления в AST-дереве типов данный
       (при появлении составных типов данных должен быть расширен)
    """

    def __init__(self, name: str,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(name, row=row, col=col, **props)
        self.type = None
        with suppress(SemanticException):
            self.type = TypeDesc.from_str(name)

    def to_str_full(self):
        return self.to_str()


class BoolNode(ValueNode):
    def __init__(self, value: bool,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row, col, **props)
        self.value = value

    def __str__(self) -> str:
        return "да" if self.value else "нет"


# class BinOp(Enum):
#     ADD = '+'
#     SUB = '-'
#     MUL = '*'
#     DIV = '/'


class BinOpNode(ExprNode):
    def __init__(self, op: BinOp, arg1: ExprNode, arg2: ExprNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2

    @property
    def children(self) -> Tuple[ExprNode, ExprNode]:
        return self.arg1, self.arg2

    def __str__(self) -> str:
        return str(self.op.value)


class CompareOp(Enum):
    GT = '>'
    LT = '<'
    EQUALS = '='
    GE = '>='
    LE = '<='


class CompareOpNode(ExprNode):
    def __init__(self, op: CompareOp, arg1: ValueNode, arg2: ValueNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row, col, **props)
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2

    @property
    def children(self) -> Tuple[ValueNode, ValueNode]:
        return self.arg1, self.arg2

    def __str__(self) -> str:
        return str(self.op.value)


class LogOp(Enum):
    OR = 'или'
    AND = 'и'
    NOT = 'не'


class LogOpNode(ExprNode):
    def __init__(self, op: LogOp, arg1: ValueNode, arg2: Optional[ValueNode] = None,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row, col, **props)
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2

    @property
    def children(self) -> tuple[ValueNode, ...]:
        return (self.arg1, self.arg2) if self.op.value != 'не' else (self.arg1,)

    def __str__(self):
        return self.op.value


class StmtNode(AstNode, ABC):
    pass


class InputNode(StmtNode):
    def __init__(self, var: IdentNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row, col, **props)
        self.var = var

    @property
    def children(self) -> Tuple[IdentNode]:
        return self.var,

    def __str__(self) -> str:
        return 'ввод'


class OutputNode(StmtNode):
    def __init__(self, arg: ExprNode, *args: ExprNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row, col, **props)
        self.args = (arg,) + args

    @property
    def children(self) -> Tuple[ExprNode, ...]:
        return self.args

    def __str__(self) -> str:
        return 'вывод'


class AssignNode(ExprNode):
    def __init__(self, var: IdentNode, val: ExprNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.var = var
        if var.name == 'flag':
            pass
        self.val = val

    @property
    def children(self) -> Tuple[IdentNode, ExprNode]:
        return self.var, self.val

    def __str__(self) -> str:
        return ':='


class IfNode(StmtNode):
    def __init__(self, cond: ExprNode, then_stmt: StmtNode, else_stmt: Optional[StmtNode] = None,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row, col, **props)
        self.cond = cond
        self.then_stmt = then_stmt
        self.else_stmt = else_stmt

    @property
    def children(self) -> tuple[ExprNode | StmtNode, ...]:
        return (self.cond, self.then_stmt) + ((self.else_stmt,) if self.else_stmt else tuple())

    def __str__(self) -> str:
        return 'если'


def not_none(value: Union[AstNode, None]) -> AstNode:
    return value if value else IdentNode('')


class WhileNode(StmtNode):
    def __init__(self, cond: ExprNode, body: Optional[StmtNode],
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row, col, **props)
        self.cond = cond
        self.body = body

    @property
    def children(self):  # -> tuple[ExprNode, AstNode]:
        return self.cond, not_none(self.body)
        # return (self.cond,) if self.body is None else self.cond, self.body

    def __str__(self) -> str:
        return 'пока'


class DoWhileNode(StmtNode):
    def __init__(self, cond: ExprNode, body: Optional[StmtNode],
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row, col, **props)
        self.cond = cond
        self.body = body

    @property
    def children(self) -> tuple[ExprNode, AstNode]:
        return self.cond, not_none(self.body)

    def __str__(self) -> str:
        return 'делать_пока'


class ForNode(StmtNode):
    def __init__(self, init: Optional[StmtNode], cond: Optional[ExprNode], step: Optional[StmtNode], body: StmtNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row, col, **props)
        self.init = init
        self.cond = cond
        self.step = step
        self.body = body

    @property
    def children(self) -> Tuple[AstNode, AstNode, AstNode, StmtNode]:
        return not_none(self.init), not_none(self.cond), not_none(self.step), self.body

    def __str__(self) -> str:
        return 'для'


class StmtListNode(AstNode):
    def __init__(self, *stmts: StmtNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row, col, **props)
        self.program = False
        self.stmts = stmts

    @property
    def children(self) -> Tuple[StmtNode]:
        return self.stmts

    def __str__(self) -> str:
        return '...'


class FuncCallNode(ExprNode):
    def __init__(self, name: IdentNode, *params: ExprNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row, col, **props)
        self.name = name
        self.params = params

    @property
    def children(self) -> Tuple[ExprNode, ...]:
        return self.params

    def __str__(self) -> str:
        return 'call_' + str(self.name)


class ChildListNode(AstNode):
    def __init__(self, node_name: str, childs: Optional[List[AstNode]],
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.node_name = node_name
        self.childs_ = childs

    @property
    def children(self) -> Tuple[AstNode, ...]:
        return not_none(self.childs_),

    def __str__(self) -> str:
        return str(self.node_name)


class Type(Enum):
    INT = 'цел'
    FLOAT = 'вещ'
    STR = 'лит'
    CHAR = 'сим'
    BOOL = 'лог'


class VarDeclNode(StmtNode):
    def __init__(self, type_: TypeNode,
    # vars_: AssignNode,
    *vars_,
    #Union[IdentNode, 'AssignNode'],
    # ident: IdentNode, assign: Optional[AssignNode] = None,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.type = type_
        # self.ident = ident
        # self.assign = assign
        # self.vars = []
        # self.vars.append(v for v in vars if v)
        if isinstance(vars_[0], AssignNode) and vars_[0].val is None:
            self.vars = vars_[0].var
        else:
            self.vars = vars_# if vars_[1].val is not None else vars_[0]
        # for v in self.vars:

        # self.var = assign if assign is not None else ident

    @property
    def children(self) -> tuple[AstNode, ...]:  # -> tuple[IdentNode, AstNode]:
        # return self.ident, not_none(self.assign)
        return self.vars
        # self.var
        # if self.assign is None:
        #     return self.ident, 
        # else:
        #     return self.assign,

    def __str__(self) -> str:
        return str(self.type)


class ParamsNode(AstNode, ABC):
    def __init__(self, *vars: VarDeclNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row, col, **props)
        self.vars = vars

    def __str__(self):
        return 'арг'

    @property
    def children(self) -> Tuple['VarDeclNode', ...]:
        return self.vars


class ResNode(StmtNode):
    def __init__(self,
                 res: VarDeclNode,
                #type: TypeNode, ident: IdentNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.type = res.type
        self.res = res
        self.name = res.vars[0]
        # self.res = res

    @property
    def children(self) -> Tuple[AstNode]:
        return self.name, self.res,

    def __str__(self):
        return 'рез' #str(self.type) #'рез'


class FuncDeclNode(StmtNode):
    def __init__(self, name: IdentNode, params: Optional[ParamsNode] = None, res: Optional[ResNode] = None,
                 body: Optional['StmtListNode'] = None,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row, col, **props)
        self.name = name
        self.params = ParamsNode(params=[])
        self.res = None
        self.body = None
        if params is not None:
            if params.__str__() == 'арг':
                self.params = params
            elif params.__str__() == 'рез':
                self.res = params
            else:
                self.body = params
            if res is not None:
                if res.__str__() == 'рез':
                    self.res = res
                else:
                    self.body = res
                if body is not None:
                    self.body = body
        if self.res is None:
            self.type = TypeNode('void')
        else:
            self.type = res.type

    @property
    def children(self):  # -> tuple[IdentNode, AstNode, AstNode, AstNode]:
        list = [self.type, self.name]
        if self.params is not None:
            for param in self.params.children:
                list.append(param)
        if self.res is not None:
            list.append(self.res)
        if self.body is not None:
            list.append(self.body)
        return tuple(list)

    def __str__(self) -> str:
        return 'алг'


class TypeConvertNode(ExprNode):
    """Класс для представления в AST-дереве операций конвертации типов данных
       (в языке программирования может быть как expression, так и statement)
    """

    def __init__(self, expr: ExprNode, type_: TypeDesc,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.expr = expr
        self.type = type_
        self.node_type = type_

    def __str__(self) -> str:
        return 'конвертация'

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return ChildListNode(str(self.type), self.expr),


def type_convert(expr: ExprNode, type_: TypeDesc, except_node: Optional[AstNode] = None, comment: Optional[str] = None) -> ExprNode:
    """Метод преобразования ExprNode узла AST-дерева к другому типу
    :param expr: узел AST-дерева
    :param type_: требуемый тип
    :param except_node: узел, о которого будет исключение
    :param comment: комментарий
    :return: узел AST-дерева c операцией преобразования
    """

    if expr.node_type is None:
        except_node.semantic_error('Тип выражения не определен')
    if expr.node_type == type_:
        return expr
    if expr.node_type.is_simple and type_.is_simple and \
            expr.node_type.base_type in TYPE_CONVERTIBILITY and type_.base_type in TYPE_CONVERTIBILITY[expr.node_type.base_type]:
        return TypeConvertNode(expr, type_)
    else:
        (except_node if except_node else expr).semantic_error('Тип {0}{2} не конвертируется в {1}'.format(
            expr.node_type, type_, ' ({})'.format(comment) if comment else ''
        ))


EMPTY_STMT = StmtListNode()
EMPTY_IDENT = IdentDesc('', TypeDesc.VOID)
