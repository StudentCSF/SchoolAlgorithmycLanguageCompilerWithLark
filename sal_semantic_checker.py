from tkinter.messagebox import NO
from typing import Optional, List
from xml.dom.minidom import CharacterData

import visitor
from sal_ast import AstNode, CharacterNode, CompareOpNode, LogOpNode, NumNode, StmtListNode, ExprNode, FuncCallNode, ForNode, IfNode, ParamsNode, IdentNode, \
    BinOpNode, AssignNode, ResNode, FuncDeclNode, EMPTY_IDENT, StringNode, TypeConvertNode, TypeNode, EMPTY_STMT, BoolNode, VarDeclNode, \
    WhileNode
from sal_semantic_base import IdentScope, ScopeType, TypeDesc, BIN_OP_TYPE_COMPATIBILITY, TYPE_CONVERTIBILITY, IdentDesc, \
    SemanticException

def type_convert(expr: ExprNode, type_: TypeDesc, except_node: Optional[AstNode] = None,
                 comment: Optional[str] = None) -> ExprNode:
    """Метод преобразования ExprNode узла AST-дерева к другому типу
    :param expr: узел AST-дерева
    :param type_: требуемый тип
    :param except_node: узел, о которого будет исключение
    :param comment: комментарий
    :return: узел AST-дерева c операцией преобразования
    """

    if expr.node_type is None:
        # except_node.semantic_error('Тип выражения не определен')
        return
    if expr.node_type == type_:
        return expr
    if expr.node_type.is_simple and type_.is_simple and \
            expr.node_type.base_type in TYPE_CONVERTIBILITY and type_.base_type in TYPE_CONVERTIBILITY[
        expr.node_type.base_type]:
        return TypeConvertNode(expr, type_)
    else:
        (except_node if except_node else expr).semantic_error('Тип {0}{2} не конвертируется в {1}'.format(
            expr.node_type, type_, ' ({})'.format(comment) if comment else ''
        ))

class SemanticChecker:
    @visitor.on('AstNode')
    def semantic_check(self, AstNode):
        pass

    @visitor.when(NumNode)
    def semantic_check(self, node: NumNode, scope: IdentScope):
        if isinstance(node.value, int):
            node.node_type = TypeDesc.INT
        else:
            node.node_type = TypeDesc.FLOAT

    @visitor.when(BoolNode)
    def semantic_check(self, node: BoolNode, scope: IdentScope):
        node.node_type = TypeDesc.BOOL
    
    @visitor.when(CharacterNode)
    def semantic_check(self, node: CharacterNode, scope: IdentScope):
        node.node_type = TypeDesc.CHAR

    @visitor.when(StringNode)
    def semantic_check(self, node: StringNode, scope: IdentScope):
        node.node_type = TypeDesc.STR

    @visitor.when(IdentNode)
    def semantic_check(self, node: IdentNode, scope: IdentScope):
        if node.name == 'res':
            pass
        ident = scope.get_ident(node.name)
        if ident is None:
            v = 5
            # ident = scope.curr_func.get_ident(node.name)
            # if ident is None:
            node.semantic_error(f'Идентификатор {node.name} не найден')
        node.node_type = ident.type
        node.node_ident = ident

    @visitor.when(TypeNode)
    def semantic_check(self, node: TypeNode, scope: IdentScope):
        if node.type is None:
            node.semantic_error(f'Неизвестный тип {node.name}')

    @visitor.when(BinOpNode)
    def semantic_check(self, node: BinOpNode, scope: IdentScope):
        node.arg1.semantic_check(self, scope)
        node.arg2.semantic_check(self, scope)

        if node.arg1.node_type.is_simple or node.arg2.node_type.is_simple:
            compatibility = BIN_OP_TYPE_COMPATIBILITY[node.op]
            args_types = (node.arg1.node_type.base_type, node.arg2.node_type.base_type)
            if args_types in compatibility:
                node.node_type = TypeDesc.from_base_type(compatibility[args_types])
                return

            if node.arg1.node_type.base_type in TYPE_CONVERTIBILITY:
                for arg1_type in TYPE_CONVERTIBILITY[node.arg1.node_type.base_type]:
                    args_types = (arg1_type, node.arg2.node_type.base_type)
                    if args_types in compatibility:
                        node.arg1 = type_convert(node.arg1, TypeDesc.from_base_type(arg1_type))
                        node.node_type = TypeDesc.from_base_type(compatibility[args_types])
                        return

            if node.arg2.node_type.base_type in TYPE_CONVERTIBILITY:
                for arg2_type in TYPE_CONVERTIBILITY[node.arg1.node_type.base_type]:
                    args_types = (node.arg2.node_type.base_type, arg2_type)
                    if args_types in compatibility:
                        node.arg2 = type_convert(node.arg1, TypeDesc.from_base_type(arg2_type))
                        node.node_type = TypeDesc.from_base_type(compatibility[args_types])
                        return

        node.semantic_error(f'Оператор {node.op} не применим к типам ({node.arg1.node_type}, {node.arg2.node_type})')

    @visitor.when(LogOpNode)
    def semantic_check(self, node: LogOpNode, scope: IdentScope) -> None:
        node.arg1.semantic_check(self, scope)
        node.arg2.semantic_check(self, scope)
        if node.arg1.node_type.is_simple or node.arg2.node_type.is_simple:
            compatibility = BIN_OP_TYPE_COMPATIBILITY[node.op]
            args_types = (node.arg1.node_type.base_type, node.arg2.node_type.base_type)
            if args_types in compatibility:
                node.node_type = TypeDesc.from_base_type(compatibility[args_types])
                return

    @visitor.when(CompareOpNode)
    def semantic_check(self, node: CompareOpNode, scope: IdentScope) -> None:
        node.arg1.semantic_check(self, scope)
        node.arg2.semantic_check(self, scope)
        if node.arg1.node_type.is_simple or node.arg2.node_type.is_simple:
            compatibility = BIN_OP_TYPE_COMPATIBILITY[node.op]
            args_types = (node.arg1.node_type.base_type, node.arg2.node_type.base_type)
            if args_types in compatibility:
                node.node_type = TypeDesc.from_base_type(compatibility[args_types])
                return

    @visitor.when(AssignNode)
    def semantic_check(self, node: AssignNode, scope: IdentScope):
        node.var.semantic_check(self, scope)
        if node.var.name == 'flag' and node.val is None:
            pass
        node.val.semantic_check(self, scope)
        node.val = type_convert(node.val, node.var.node_type, node, 'присваиваемое значение')
        if node.var.name == 'flag':
            pass
        node.node_type = node.var.node_type

    @visitor.when(VarDeclNode)
    def semantic_check(self, node: VarDeclNode, scope: IdentScope):
        node.type.semantic_check(self, scope)
        for var in node.vars:
            if var is None:
                pass
            var_node: IdentNode = var.var if isinstance(var, AssignNode) else var
            # if var_node is None: continue
            try:
                scope.add_ident(IdentDesc(var_node.name, node.type.type))
            except SemanticException as e:
                var_node.semantic_error(e.message)
            var.semantic_check(self, scope)
        node.node_type = TypeDesc.VOID

    @visitor.when(ParamsNode)
    def semantic_check(self, node: ParamsNode, scope: IdentScope):
        for var in node.vars:
            var.type.semantic_check(self, scope)
        node.node_type = TypeDesc.VOID

    @visitor.when(ResNode)
    def semantic_check(self, node: ResNode, scope: IdentScope):
        # node.res.semantic_check(self, IdentScope(scope))
        # func = scope.curr_func
        # if func is None:
        #     node.semantic_error('Ошибка в ResNode')
        # node.res = type_convert(node.res, func.func.type.return_type, node, 'возвращаемое значение')
        # node.node_type = TypeDesc.VOID
        # node.type.semantic_check(self, IdentScope(scope))
        # node.node_type = node.type.type
        # try:
        #     node.name.node_ident = scope.add_ident(IdentDesc(node.name.name, node.type.type, ScopeType.LOCAL))
        # except SemanticException:
        #     raise node.name.semantic_error('Ошибка в ResNode')
        i = 3
        node.res.semantic_check(self, scope)
        node.node_type = TypeDesc.VOID

    @visitor.when(FuncDeclNode)
    def semantic_check(self, node: FuncDeclNode, scope: IdentScope):
        if scope.curr_func:
            node.semantic_error(f'Объявление функции ({node.name.name}) внутри другой функции не поддерживается')
        parent_scope = scope
        # if 1 or node.res is not None:
        node.type.semantic_check(self, scope)
        scope = IdentScope(scope)
        scope.func = EMPTY_IDENT
        params: List[TypeDesc] = []
        for param in node.params:
            if param is None:
                break
            param.semantic_check(self, scope)
            params.append(param.type.type)

        if node.res is not None:
            node.res.semantic_check(self, scope)

        type_ = TypeDesc(None, node.type.type, tuple(params))
        func_ident = IdentDesc(node.name.name, type_)
        scope.func = func_ident
        node.name.node_type = type_
        try:
            node.name.node_ident = parent_scope.curr_global.add_ident(func_ident)
        except SemanticException as e:
            node.name.semantic_error(f'Повторное объявление функции {node.name.name}')
        node.body.semantic_check(self, scope)
        node.node_type = TypeDesc.VOID

    @visitor.when(StmtListNode)
    def semantic_check(self, node: StmtListNode, scope: IdentScope):
        if not node.program:
            scope = IdentScope(scope)
        for stmt in node.stmts:
            stmt.semantic_check(self, scope)
        node.node_type = TypeDesc.VOID

    @visitor.when(ForNode)
    def semantic_check(self, node: ForNode, scope: IdentScope):
        scope = IdentScope(scope)
        node.init.semantic_check(self, scope)
        if node.cond == EMPTY_STMT:
            node.cond = BoolNode('да')
        node.cond.semantic_check(self, scope)
        node.cond = type_convert(node.cond, TypeDesc.BOOL, None, 'условие')
        node.step.semantic_check(self, scope)
        node.body.semantic_check(self, IdentScope(scope))
        node.node_type = TypeDesc.VOID

    @visitor.when(IfNode)
    def semantic_check(self, node: IfNode, scope: IdentScope):
        node.cond.semantic_check(self, scope)
        node.cond = type_convert(node.cond, TypeDesc.BOOL, None, 'условие')
        node.then_stmt.semantic_check(self, IdentScope(scope))
        if node.else_stmt:
            node.else_stmt.semantic_check(self, IdentScope(scope))
        node.node_type = TypeDesc.VOID

    @visitor.when(WhileNode)
    def semantic_check(self, node: WhileNode, scope: IdentScope):
        node.cond.semantic_check(self, scope)
        node.cond = type_convert(node.cond, TypeDesc.BOOL, None, 'условие')
        node.body.semantic_check(self, IdentScope(scope))
        node.node_type = TypeDesc.VOID

    @visitor.when(FuncCallNode)
    def semantic_check(self, node: FuncCallNode, scope: IdentScope):
        func = scope.get_ident(node.name.name)
        if func is None:
            node.semantic_error('Функция {} не найдена'.format(node.name.name))
        if not func.type.func:
            node.semantic_error('Идентификатор {} не является функцией'.format(func.name))
        if len(func.type.params) != len(node.params):
            node.semantic_error('Кол-во аргументов {} не совпадает (ожидалось {}, передано {})'.format(
                func.name, len(func.type.params), len(node.params)
            ))
        params = []
        error = False
        decl_params_str = fact_params_str = ''
        for i in range(len(node.params)):
            param: ExprNode = node.params[i]
            param.semantic_check(self, scope)
            if len(decl_params_str) > 0:
                decl_params_str += ', '
            decl_params_str += str(func.type.params[i])
            if len(fact_params_str) > 0:
                fact_params_str += ', '
            fact_params_str += str(param.node_type)
            try:
                params.append(type_convert(param, func.type.params[i]))
            except:
                error = True
        if error:
            node.semantic_error(
                f'Фактические типы ({fact_params_str}) аргументов функции {func.name} не совпадают с формальными ({decl_params_str}) и не приводимы')
        else:
            node.params = tuple(params)
            node.name.node_type = func.type
            node.name.node_ident = func
            node.node_type = func.type.return_type


def prepare_global_scope() -> IdentScope:
    from sal_parser import parse

    prog = parse(BUILT_IN_OBJECTS)
    checker = SemanticChecker()
    scope = IdentScope()
    checker.semantic_check(prog, scope)
    for name, ident in scope.idents.items():
        ident.built_in = True
    scope.var_index = 0
    return scope


def semantic_error(self, param):
    pass


BUILT_IN_OBJECTS = ''' 
    '''
