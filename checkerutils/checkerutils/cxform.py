#!/usr/bin/env python3

import sys
import pycparser
from pycparser import c_generator, c_ast, parse_file

class Transformer(object):
    def matches(self, node):
        return False

    def transform(self, node):
        return node

class PrintfTransformer(Transformer):
    xform_name = 'printfX'

    def matches(self, node):
        if isinstance(node, c_ast.FuncCall) and isinstance(node.name, c_ast.ID):
            return node.name.name == 'printf'

    def transform(self, node):
        node.name.name = self.xform_name
        return node

class PostconditionTransformer(Transformer):
    def __init__(self, args):
        ct = args.get('condition_text', args["condition"])
        condition = f"__CPROVER_assert({args['condition']}, \"{ct}\");"

        p = pycparser.c_parser.CParser()
        code = "void anon() {" + condition + "}"
        code_ast = p.parse(code, filename="<insert.c>")
        self.code_ast = code_ast.ext[0].body.block_items

    def matches(self, node):
        return isinstance(node, c_ast.Return)

    def transform(self, node):
        y = c_ast.Compound([x for x in self.code_ast] + [node])
        return y

# rather stupid way ...
class ASTTransformer(c_generator.CGenerator):
    def __init__(self, transformers):
        self.xformers = transformers
        self.seen = set()
        super(ASTTransformer).__init__()
        self.indent_level = 0

    def visit(self, node):
        if node in self.seen:
            return super(ASTTransformer, self).visit(node)

        self.seen.add(node)

        nn = node
        for xf in self.xformers:
            if xf.matches(node):
                nn = xf.transform(node)
                break

        if nn is not None: # node got deleted
            if not isinstance(nn, list):
                return super(ASTTransformer, self).visit(nn)
            else:
                # TODO
                pass
        else:
            return ''


    def transform_string(self, c_code):
        p = pycparser.c_parser.CParser()
        ast = p.parse(c_code)

        newcode = self.visit(ast)
        return newcode

    def transform(self, node):
        newcode = self.visit(node)
        p = pycparser.c_parser.CParser()
        newast = p.parse(newcode)

        return newast

if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Test for C transformer")
    p.add_argument("inputfile", help="Input file")

    args = p.parse_args()

    ast = parse_file(args.inputfile)
    att = ASTTransformer([PrintfTransformer()])
    newast = att.transform(ast)
    newast.show()

