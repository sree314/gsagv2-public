#!/usr/bin/env python3

from __future__ import print_function
import argparse
import yaml
import sys
import pycparser
from pycparser import c_generator, c_ast
import os
import tempfile
import subprocess
import cxform


def preprocess_c(c_code):
    p = subprocess.Popen(["cpp", "-E"], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)

    stdout, stderr = p.communicate(c_code.encode('utf-8'))

    if p.returncode == 0:
        return stdout.decode('utf-8')
    else:
        print("ERROR: preprocessor failed.\n", file=sys.stderr)
        print(stderr, file=sys.stderr)
        sys.exit(1)


class CodeEditor(object):
    def __init__(self, ccode, cfilename):
        self.ccode = ccode
        self.cfilename = cfilename

        p = pycparser.c_parser.CParser()
        self.ast = p.parse(preprocess_c(ccode), filename=self.cfilename)

    def insert_at_fn_exit(self, fn_name, code):
        p = pycparser.c_parser.CParser()
        code = "void anon() {" + preprocess_c(code) + "}"
        code_ast = p.parse(code, filename="<insert.c>")
        code_ast = code_ast.ext[0].body.block_items

        for tl in self.ast.ext:
            if isinstance(tl, pycparser.c_ast.FuncDef) and tl.decl.name == fn_name:
                tl.body.block_items.extend(code_ast)

    def output(self):
        c_gen = c_generator.CGenerator()
        self.ccode = c_gen.visit(self.ast)

        return self.ccode

class Preprocessor(object):
    def __init__(self, ppfile):
        self.ppfile = ppfile
        self._preprocessed = False

        with open(self.ppfile, "r") as f:
            self.pp = yaml.safe_load(f)

    def set_input(self, cinputfile):
        self.cinputfile = cinputfile
        with open(self.cinputfile, "r") as f:
            self.cinput = f.read()

        self.cprocessed = self.cinput

    def apply_transformers(self):
        if 'transformers' in self.pp:
            xformers = []
            for x in self.pp['transformers']:
                if x['name'] == 'PrintfTransformer':
                    print("INFO: Adding PrintfTransformer", file=sys.stderr)
                    xformers.append(cxform.PrintfTransformer())
                elif x['name'] == 'PostconditionTransformer':
                    print(f"INFO: Adding {x['name']}", file=sys.stderr)
                    xformers.append(cxform.PostconditionTransformer(x))
                elif x['name'] == 'PreconditionTransformer':
                    print(f"INFO: Adding {x['name']}", file=sys.stderr)
                    xformers.append(cxform.PreconditionTransformer(x))
                else:
                    assert False, "Unknown transformer: '%s'" % (x['name'],)

            print("INFO: Transforming code", file=sys.stderr)
            att = cxform.ASTTransformer(xformers)
            self.cprocessed = att.transform_string(self.cprocessed)

    def apply_insert_at_exit(self):
        if 'insert_at_exit' in self.pp:

            ce = CodeEditor(self.cprocessed, self.cinputfile)

            for e in self.pp['insert_at_exit']: # lexical exit
                code = e['code']
                fn = e['function_name']
                print("INFO: Processed insert_at_exit for '%s' function" % (fn,), file=sys.stderr)

                ce.insert_at_fn_exit(fn, code)

            self.cprocessed = ce.output()
        else:
            print("INFO: No insert_at_exit section found in %s" % (self.ppfile,), file=sys.stderr)

    def apply_templates(self):
        if 'template' in self.pp:
            pre = self.pp['template'].get('pre', '').strip()
            if pre:
                print("INFO: Applying pre template section", file=sys.stderr)
                pre += "\n\n"
            else:
                pre = "/* empty pre */\n\n"

            post = self.pp['template'].get('post', '')
            if post:
                print("INFO: Applying post template section", file=sys.stderr)
                post = "\n\n" + post
            else:
                post = "/* empty post */\n\n"

            self.cprocessed = pre + self.cprocessed + post
        else:
            print("WARNING: No template section found in %s" % (self.ppfile,), file=sys.stderr)

    def get_output(self):
        if not self._preprocessed:
            self.apply_transformers()
            self.apply_insert_at_exit()
            self.apply_templates()
            self._preprocessed = True

        return self.cprocessed

    def run_cbmc(self, inputfile):
        if not 'cbmc' in self.pp:
            print("WARNING: No `cbmc' section found, using defaults", file=sys.stderr)
            out = []
        else:
            translate = {'cstd': {'c99': '--c99'},
                         'define': {None: '-D'}}

            out = []
            for k, v in self.pp['cbmc'].items():
                if k in translate:
                    if v in translate[k]:
                        out.append(translate[k][v])
                    elif None in translate[k]:
                        out.append(f"{translate[k][None]}")
                        out.append(v)
                    else:
                        assert False, k
                else:
                    k = k.replace("_", "-")
                    if v == True:
                        out.append("--%s" % (k,))
                    elif v == False:
                        out.append("--no-%s" % (k,))
                    else:
                        if len(k) == 1:
                            out.append("-%s" % k)
                        else:
                            out.append("--%s" % k)
                        out.append(str(v))

        if args.json_ui:
            out.append("--json-ui")

        cmdline = ["cbmc", inputfile] + out
        print("INFO: Running %s" % (' '.join(cmdline)))

        try:
            output = subprocess.check_output(cmdline, stderr=subprocess.STDOUT)
            print("SUCCESS: Test passed")
            if not args.quiet:
                print(">>>=== CBMC Output ===<<<")
                print(output.decode('utf-8'))
                print(">>>=== CBMC Output End ===<<<")

            if args.output:
                with open(args.output, "wb") as f:
                    f.write(output)

            return True
        except subprocess.CalledProcessError as e:
            print("FAILURE: Test failed")
            print("ERROR: Command failed: Return code '%s'" % (e.returncode,), 
                  file=sys.stderr)
            print("\tOutput was:\n>>>=== CBMC Output ===<<<\n%s>>>=== CBMC Output End ===<<<\n\n" % (e.output.decode('utf-8'),), file=sys.stderr)

            if args.output:
                with open(args.output, "wb") as f:
                    f.write(e.output)
            return False

    def check(self, preserve_output = False):
        h, tmpfile = tempfile.mkstemp(".c")
        os.close(h)

        print("INFO: Storing output in `%s`" % (tmpfile,))

        with open(tmpfile, "w") as f:
            f.write(self.get_output())

        x = self.run_cbmc(tmpfile,)
        if not preserve_output:
            print("INFO: Removing `%s`" % (tmpfile,))
            os.unlink(tmpfile)

        return x

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Preprocess a file and run it through cbmc")

    p.add_argument("cfile", help="File to check")
    p.add_argument("preprocessoryaml", help="Preprocessing instructions")
    p.add_argument("--keep", action="store_true", help="Keep temporary output")
    p.add_argument("--json-ui", action="store_true", help="Use JSON UI")
    p.add_argument("-o", dest="output", help="Output file for cbmc output")
    p.add_argument("-q", dest="quiet", action="store_true", help="Don't show cbmc output")

    args = p.parse_args()

    x = Preprocessor(args.preprocessoryaml)
    x.set_input(args.cfile)

    if x.check(args.keep,):
        sys.exit(0)
    else:
        sys.exit(1)
