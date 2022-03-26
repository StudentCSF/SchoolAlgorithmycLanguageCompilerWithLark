from abc import ABC, abstractmethod
from typing import Callable, Tuple, Union, Optional, List
from enum import Enum


class AstNode(ABC):
    @property
    def childs(self) -> Tuple['AstNode', ...]:
        return ()

    @abstractmethod
    def __str__(self) -> str:
        pass

    @property
    def tree(self) -> [str, ...]:
        res = [str(self)]
        childs = self.childs
        for i, child in enumerate(childs):
            ch0, ch = '├', '│'
            if i == len(childs) - 1:
                ch0, ch = '└', ' '
            res.extend(((ch0 if j == 0 else ch) + ' ' + s for j, s in enumerate(child.tree)))
        return res

    def visit(self, func: Callable[['AstNode'], None]) -> None:
        func(self)
        map(func, self.childs)

    def __getitem__(self, index):
        return self.childs[index] if index < len(self.childs) else None


class ExprNode(AstNode):
    pass


class ValueNode(ExprNode):
    pass


class NumNode(ValueNode):
    def __init__(self, num: float):
        super().__init__()
        self.num = float(num)

    def __str__(self) -> str:
        return str(self.num)


class IdentNode(ValueNode):
    def __init__(self, name: str):
        super().__init__()
        self.name = str(name)

    def __str__(self) -> str:
        return str(self.name)


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
    def childs(self) -> Tuple[ValueNode, ValueNode]:
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
    def childs(self) -> Tuple[ValueNode, ValueNode]:
        return self.arg1, self.arg2

    def __str__(self) -> str:
        return str(self.op.value)


class StmtNode(AstNode):
    pass


class InputNode(StmtNode):
    def __init__(self, var: IdentNode):
        self.var = var

    @property
    def childs(self) -> Tuple[IdentNode]:
        return self.var,

    def __str__(self) -> str:
        return 'ввод'


class OutputNode(StmtNode):
    def __init__(self, arg: ValueNode):
        self.arg = arg

    @property
    def childs(self) -> Tuple[ValueNode]:
        return self.arg,

    def __str__(self) -> str:
        return 'вывод'


class AssignNode(StmtNode):
    def __init__(self, var: IdentNode, val: ValueNode):
        super().__init__()
        self.var = var
        self.val = val

    @property
    def childs(self) -> Tuple[IdentNode, ValueNode]:
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
    def childs(self) -> Tuple[ExprNode, StmtNode, Optional[StmtNode]]:
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
    def childs(self) -> Tuple[ExprNode, StmtNode]:
        return self.cond, not_none(self.body)

    def __str__(self) -> str:
        return 'пока'


class DoWhileNode(StmtNode):
    def __init__(self, cond: ExprNode, body: Optional[StmtNode]):
        super().__init__()
        self.cond = cond
        self.body = body

    @property
    def childs(self) -> Tuple[ExprNode, StmtNode]:
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
    def childs(self) -> Tuple[AstNode, AstNode, AstNode, StmtNode]:
        return not_none(self.init), not_none(self.cond), not_none(self.step), self.body

    def __str__(self) -> str:
        return 'для'


class StmtListNode(AstNode):
    def __init__(self, *exprs: AstNode):
        super().__init__()
        self.exprs = exprs

    @property
    def childs(self) -> Tuple[AstNode]:
        return self.exprs

    def __str__(self) -> str:
        return '...'


class FuncCallNode(ExprNode):
    def __init__(self, name: IdentNode, *params: ExprNode):
        super().__init__()
        self.name = name
        self.params = params

    @property
    def childs(self) -> Tuple[ExprNode, ...]:
        return self.params

    def __str__(self) -> str:
        return str(self.name)


class ChildListNode(AstNode):
    def __init__(self, node_name: str, childs: List[AstNode]):
        self.node_name = node_name
        self.childs_ = childs

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return self.childs_,

    def __str__(self) -> str:
        return str(self.node_name)


class FuncDeclNode(StmtNode):
    def __init__(self, name: IdentNode, params: List[IdentNode], body: 'StmtListNode'):
        super().__init__()
        self.name = name
        self.params = params
        self.body = body

    @property
    def childs(self) -> Tuple[IdentNode, AstNode, 'StmtListNode']:
        return self.name, ChildListNode('арг', self.params), self.body

    def __str__(self) -> str:
        return 'алг'
