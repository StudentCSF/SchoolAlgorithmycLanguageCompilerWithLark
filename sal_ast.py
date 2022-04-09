from abc import ABC, abstractmethod
from typing import Callable, Tuple, Union, Optional, List
from enum import Enum


class AstNode(ABC):
    @property
    def children(self) -> Tuple['AstNode', ...]:
        return ()

    @abstractmethod
    def __str__(self) -> str:
        pass

    @property
    def tree(self) -> [str, ...]:
        res = [str(self)]
        childs = self.children
        for i, child in enumerate(childs):
            ch0, ch = '├', '│'
            if i == len(childs) - 1:
                ch0, ch = '└', ' '
            res.extend(((ch0 if j == 0 else ch) + ' ' + s for j, s in enumerate(child.tree)))
        return res

    def visit(self, func: Callable[['AstNode'], None]) -> None:
        func(self)
        map(func, self.children)

    def __getitem__(self, index):
        return self.children[index] if index < len(self.children) else None


class ExprNode(AstNode, ABC):
    pass


class ValueNode(ExprNode, ABC):
    pass


class NumNode(ValueNode):
    def __init__(self, num: float):
        super().__init__()
        self.num = float(num)

    def __str__(self) -> str:
        return str(self.num)


class StringNode(ValueNode):
    def __init__(self, str: str):
        super().__init__()
        self.str = str

    def __str__(self):
        return self.str


class CharacterNode(ValueNode):
    def __init__(self, char: str):
        super().__init__()
        self.char = char

    def __str__(self):
        return self.char


class IdentNode(ValueNode):
    def __init__(self, name: str):
        super().__init__()
        self.name = str(name)

    def __str__(self) -> str:
        return str(self.name)


class BoolNode(ValueNode):
    def __init__(self, value: bool):
        super().__init__()
        self.value = value

    def __str__(self) -> str:
        return "да" if self.value else "нет"


class BinOp(Enum):
    ADD = '+'
    SUB = '-'
    MUL = '*'
    DIV = '/'


class BinOpNode(ExprNode):
    def __init__(self, op: BinOp, arg1: ValueNode, arg2: ValueNode):
        super().__init__()
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2

    @property
    def children(self) -> Tuple[ValueNode, ValueNode]:
        return self.arg1, self.arg2

    def __str__(self) -> str:
        return str(self.op.value)


class CompareOp(Enum):
    MORE = '>'
    LESS = '<'
    EQUALS = '='
    MORE_OR_EQUALS = '>='
    LESS_OR_EQUALS = '<='


class CompareOpNode(ExprNode):
    def __init__(self, op: CompareOp, arg1: ValueNode, arg2: ValueNode):
        super().__init__()
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
    def __init__(self, op: LogOp, arg1: ValueNode, arg2: Optional[ValueNode] = None):
        super().__init__()
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2

    @property
    def children(self) -> tuple['ValueNode', ...]:
        return (self.arg1, self.arg2) if self.op.value != 'не' else (self.arg1,)

    def __str__(self):
        return self.op.value


class StmtNode(AstNode, ABC):
    pass


class InputNode(StmtNode):
    def __init__(self, var: IdentNode):
        self.var = var

    @property
    def children(self) -> Tuple[IdentNode]:
        return self.var,

    def __str__(self) -> str:
        return 'ввод'


class OutputNode(StmtNode):
    def __init__(self, arg: ExprNode, *args: ExprNode):
        self.args = (arg,) + args

    @property
    def children(self) -> Tuple[ExprNode, ...]:
        return self.args

    def __str__(self) -> str:
        return 'вывод'


class AssignNode(StmtNode):
    def __init__(self, var: IdentNode, val: ValueNode):
        super().__init__()
        self.var = var
        self.val = val

    @property
    def children(self) -> Tuple[IdentNode, ValueNode]:
        return self.var, self.val

    def __str__(self) -> str:
        return ':='


class IfNode(StmtNode):
    def __init__(self, cond: ExprNode, then_stmt: StmtNode, else_stmt: Optional[StmtNode] = None):
        super().__init__()
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
    def __init__(self, cond: ExprNode, body: Optional[StmtNode]):
        super().__init__()
        self.cond = cond
        self.body = body

    @property
    def children(self) -> tuple[ExprNode, AstNode]:
        return self.cond, not_none(self.body)

    def __str__(self) -> str:
        return 'пока'


class DoWhileNode(StmtNode):
    def __init__(self, cond: ExprNode, body: Optional[StmtNode]):
        super().__init__()
        self.cond = cond
        self.body = body

    @property
    def children(self) -> tuple[ExprNode, AstNode]:
        return self.cond, not_none(self.body)

    def __str__(self) -> str:
        return 'делать_пока'


class ForNode(StmtNode):
    def __init__(self, init: Optional[StmtNode], cond: Optional[ExprNode], step: Optional[StmtNode], body: StmtNode):
        super().__init__()
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
    def __init__(self, *exprs: AstNode):
        super().__init__()
        self.exprs = exprs

    @property
    def children(self) -> Tuple[AstNode]:
        return self.exprs

    def __str__(self) -> str:
        return '...'


class FuncCallNode(ExprNode):
    def __init__(self, name: IdentNode, *params: ExprNode):
        super().__init__()
        self.name = name
        self.params = params

    @property
    def children(self) -> Tuple[ExprNode, ...]:
        return self.params

    def __str__(self) -> str:
        return "call_" + str(self.name)


class ChildListNode(AstNode):
    def __init__(self, node_name: str, childs: Optional[List[AstNode]]):
        self.node_name = node_name
        self.childs_ = childs

    @property
    def children(self) -> Tuple[AstNode, ...]:
        return not_none(self.childs_),

    def __str__(self) -> str:
        return str(self.node_name)


class FuncDeclNode(StmtNode):
    def __init__(self, name: IdentNode, params: Optional[List[IdentNode]] = None,
                 body: Optional['StmtListNode'] = None):
        super().__init__()
        self.name = name
        if body is None:
            self.body = params
            self.params = None
        else:
            self.params = params
            self.body = body

    @property
    def children(self) -> tuple[IdentNode, AstNode, AstNode]:
        return self.name, not_none(ChildListNode('арг', self.params)), not_none(ChildListNode('тело', self.body))

    def __str__(self) -> str:
        return 'алг'


class Type(Enum):
    INT = 'цел'
    FLOAT = 'вещ'
    STR = 'лит'
    CHAR = 'сим'
    BOOL = 'лог'


class VarDeclNode(StmtNode):
    def __init__(self, type: Type, ident: IdentNode, assign: Optional[AssignNode]):
        super().__init__()
        self.type = type
        self.ident = ident
        self.assign = assign

    @property
    def children(self) -> tuple[IdentNode, AstNode]:
        return self.ident, not_none(self.assign)

    def __str__(self):
        return self.type.value
