from ast import If
from ctypes import Union
from re import L
from typing import List
from sal_ast import *
from sal_semantic_base import BaseType, ScopeType
import visitor

RUNTIME_CLASS_NAME = 'CompilerDemo.Runtime'
PROGRAM_CLASS_NAME = 'Program'

class CodeLabel:
    def __init__(self):
        self.index = None
    
    def __str__(self):
        return 'IL_' + str(self.index)

class CodeLine:
    def __init__(self, code: str, *params: Union[str, CodeLabel], label: CodeLabel) -> None:
        self.code = code
        self.label = label
        self.params = params

    def __str__(self) -> str:
        line = ''
        if self.label:
            line += str(self.label) + ': '
        line += self.code
        for p in self.params:
            line += ' ' + str(p)
        return line

class MsilException(Exception):
    def __init__(self, message, *args: object) -> None:
        self.message = message


MSIL_TYPE_NAMES = {
    BaseType.VOID: 'void',
    BaseType.INT: 'int32',
    BaseType.STR: 'string',
    BaseType.BOOL: 'bool',
    BaseType.CHAR: 'char',
    BaseType.FLOAT: 'float64'
}


def find_vars_decls(node: AstNode) -> List[VarDeclNode]:
    var_nodes: List[VarDeclNode] = []

    def find(node: AstNode) -> None:
        if node is None:
            return
        for n in (node.children or []):
            if isinstance(n, VarDeclNode):
                var_nodes.append(n)
            else:
                find(n)

    find(node)
    return var_nodes


class CodeGenerator:
    def __init__(self) -> None:
        self.code_lines: List[CodeLine] = []

    def add(self, code: str, *params: Union[str, int, CodeLabel], label: CodeLabel = None):
        self.code_lines.append(CodeLine(code, *params, label=label))
    
    @property
    def code(self) -> [str, ...]:
        index = 0
        for cl in self.code_lines:
            line = cl.code
            if cl.label:
                cl.label.index = index
                index += 1
        code: List[str] = []
        for cl in self.code_lines:
            code.append(str(cl))
        return code
    
    def start(self) -> None:
        self.add('.assembly program')
        self.add('{')
        self.add('}')
        self.add('.class public ' + PROGRAM_CLASS_NAME)
        self.add('{')
    
    def end(self) -> None:
        self.add("}")
    
    @visitor.on('AstNode')
    def msil_gen(self, AstNode):
        pass

    @visitor.when(NumNode)
    def msil_gen(self, node: NumNode) -> None:
        if isinstance(node.value, int):
            self.add('      ldc.i4', node.value)
        else:
            self.add('      ldc.r8', node.value)
    
    @visitor.when(CharacterNode)
    def msil_gen(self, node: StringNode) -> None:
        self.add(f'     ldstr "{node.value}"')

    @visitor.when(BoolNode)
    def msil_gen(self, node: StringNode) -> None:
        self.add(f'     ldc.i4 "{node.value}"')

    @visitor.when(IdentNode)
    def msil_gen(self, node: IdentNode) -> None:
        if node.node_ident.scope == ScopeType.LOCAL:
            self.add('      ldloc', node.node_ident.index)
        elif node.node_ident.scope == ScopeType.PARAM:
            self.add('      ldarg', node.node_ident.index)
        elif node.node_ident.scope in (ScopeType.GLOBAL, ScopeType.GLOBAL_LOCAL):
            self.add(f'     ldsfld {MSIL_TYPE_NAMES[node.node_ident.type.base_type]} {PROGRAM_CLASS_NAME}::_gv{node.node_ident.index}')
    
    @visitor.when(AssignNode)
    def msil_gen(self, node: AssignNode) -> None:
        if node is None:
            return
        node.val.msil_gen(self)
        var = node.var
        if var.node_ident.scope == ScopeType.LOCAL:
            self.add('      stloc', var.node_ident.index)
        elif var.node_ident.scope == ScopeType.PARAM:
            self.add('      starg', var.node_ident.index)
        elif var.node_ident.scope in (ScopeType.GLOBAL, ScopeType.GLOBAL_LOCAL):
            self.add(f'     stsfld {MSIL_TYPE_NAMES[var.node_ident.type.base_type]} Program::_gv{var.node_ident.index}')
    
    @visitor.when(VarDeclNode)
    def msil_gen(self, node: VarDeclNode) -> None:
        for var in node.vars:
            if isinstance(var, AssignNode):
                if var.val is None:
                    var.var.msil_gen(self)
                else:
                    var.msil_gen(self)

    @visitor.when(BinOpNode)
    def msil_gen(self, node: BinOpNode) -> None:
        node.arg1.msil_gen(self)
        node.arg2.msil_gen(self)
        #TODO add
        if node.op == BinOp.EQUALS:
            if node.arg1.node_type == TypeDesc.STR:
                self.add('      call bool [mscorlib]System.String::op_Inequality(string, string')
        elif node.op == BinOp.GT:
            self.add('      cgt')
        elif node.op == BinOp.ADD:
            self.add('      add')
        else:
            pass
    
    @visitor.when(TypeConvertNode)
    def msil_gen(self, node: TypeConvertNode) -> None:
        node.expr.msil_gen(self)
        cmd = f'        call {MSIL_TYPE_NAMES[node.node_type.base_type]} class {RUNTIME_CLASS_NAME}::convert({MSIL_TYPE_NAMES[node.expr.node_type.base_type]})'
        self.add(cmd)

    @visitor.when(FuncCallNode)
    def msil_gen(self, node: FuncCallNode) -> None:
        for param in node.params:
            param.msil_gen(self)
        class_name = RUNTIME_CLASS_NAME if node.func.node_ident.built_in else PROGRAM_CLASS_NAME
        param_types = ', '.join(MSIL_TYPE_NAMES[param.node_type.base_type] for param in node.params)
        cmd = f'        call {MSIL_TYPE_NAMES[node.node_type.base_type]} class {class_name}::{node.func.name}({param_types})'
        self.add(cmd)

    @visitor.when(ResNode)
    def msil_gen(self, node: ResNode) -> None:
        node.res.msil_gen(self)
        self.add('      ret')

    @visitor.when(IfNode)
    def msil_gen(self, node: IfNode) -> None:
        node.cond.msil_gen(self)
        self.add('      ldc.i4', 0)
        self.add('      ceq')
        else_label = CodeLabel()
        end_label = CodeLabel()
        self.add('      brtrue', else_label)
        node.then_stmt.msil_gen(self)
        self.add('      br', end_label)
        self.add('', label=else_label)
        if node.else_stmt:
            node.else_stmt.msil_gen(self)
        self.add('', label=end_label)
    
    @visitor.when(FuncDeclNode)
    def msil_gen(self, node:FuncDeclNode) -> None:
        params = ''
        for p in node.params.vars:
            if len(params) > 0:
                params += ', '
            params += f'{MSIL_TYPE_NAMES[p.type.type.base_type]} {str(p.vars[0].name)}'
        self.add(f' .method public static {MSIL_TYPE_NAMES[node.type.type.base_type]} {node.name}({params}) cil managed')
        self.add('  {')
        node.body.msil_gen(self)

        if node.res is None:
            self.add('      ret')
        
        self.add('  }')

    @visitor.when(StmtListNode)
    def msil_gen(self, node: StmtListNode) -> None:
        for stmt in node.stmts:
            stmt.msil_gen(self)

    def msil_gen_program(self, prog: StmtListNode):
        self.start()
        global_vars_decls = find_vars_decls(prog)
        for node in global_vars_decls:
            for var in node.vars:
                if var is None: continue
                if isinstance(var, AssignNode):
                    var = var.var
                if var.node_ident.scope in (ScopeType.GLOBAL, ScopeType.GLOBAL_LOCAL):
                    self.add(f' .field public static {MSIL_TYPE_NAMES[var.node_type.base_type]} _gv{var.node_ident.index}')
        if node.vars and len(node.vars) > 0:
            self.add('')
        for stmt in prog.stmts:
            if isinstance(stmt, FuncDeclNode):
                self.msil_gen(stmt)
        self.add('')
        self.add('  .method public static void Main()')
        self.add('  {')
        self.add('  .entrypoint')
        for stmt in prog.children:
            if not isinstance(stmt, FuncDeclNode):
                self.msil_gen(stmt)
        
        self.add('  ret')

        self.add('  }')
        self.end()
