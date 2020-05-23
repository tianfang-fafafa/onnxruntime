#!/usr/bin/env python
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


from collections import defaultdict
import io
import os
import argparse

from typing import Type
import onnxruntime.capi.onnxruntime_pybind11_state as rtpy


def format_version_range(v):
    if (v[1] >= 2147483647):
        return str(v[0])+'+'
    else:
        return '['+str(v[0])+', '+str(v[1])+']'


def format_type_constraints(tc):
    counter = 0
    tcstr = ''
    firsttcitem = True
    for tcitem in tc:
        counter += 1
        if firsttcitem:
            firsttcitem = False
        else:
            tcstr += ', '
        tcstr += tcitem
    return tcstr


def format_param_strings(params):
    firstparam = True
    s = ''
    if params:
        for param in sorted(params):
            if firstparam:
                firstparam = False
            else:
                s += ' or '
            s += param
    return s


def main(args):  # type: (Type[Args]) -> None

    with io.open(args.output, 'w', newline='', encoding="utf-8") as fout:
        fout.write('## Supported Operators Data Types\n')
        fout.write(
            "*This file is automatically generated from the\n"
            "            [def files](/onnxruntime/core/providers/cpu/cpu_execution_provider.cc) via "
            "[this script](/tools/python/gen_opkernel_doc.py).\n"
            "            Do not modify directly and instead edit operator definitions.*\n")
        opdef = rtpy.get_all_operator_schema()
        paramdict = {}
        for schema in opdef:
            inputs = schema.inputs
            domain = schema.domain
            if (domain == ''):
                domain = 'ai.onnx.ml'
            fullname = domain+'.'+schema.name
            paramstr = '('
            firstinput = True
            if inputs:
                for inp in inputs:
                    if firstinput:
                        firstinput = False
                    else:
                        paramstr += ', '
                    paramstr += '*in* {}:**{}**'.format(inp.name, inp.typeStr)

            outputs = schema.outputs
            if outputs:
                for outp in outputs:
                    if firstinput:
                        firstinput = False
                    else:
                        paramstr += ', '
                    paramstr += '*out* {}:**{}**'.format(outp.name, outp.typeStr)

            paramstr += ')'
            paramset = paramdict.get(fullname, None)
            if paramset is None:
                paramdict[fullname] = set()

            paramdict[fullname].add(paramstr)

        index = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        for op in rtpy.get_all_opkernel_def():
            domain = op.domain
            if (domain == ''):
                domain = 'ai.onnx.ml'
            index[op.provider][domain][op.op_name].append(op)

        fout.write('\n')
        for provider, domainmap in sorted(index.items()):
            fout.write('\n\n## Operators implemented by '+provider+'\n\n')
            fout.write('| Op Name | Parameters | OpSet Version | Types Supported |\n')
            fout.write('|---------|------------|---------------|-----------------|\n')
            for domain, namemap in sorted(domainmap.items()):
                fout.write('**Operator Domain:** *'+domain+'*\n')
                for name, ops in sorted(namemap.items()):
                    version_type_index = defaultdict(lambda: defaultdict(set))
                    for op in ops:
                        formatted_version_range = format_version_range(op.version_range)
                        for tname, tclist in op.type_constraints.items():
                            for c in tclist:
                                version_type_index[formatted_version_range][tname].add(c)

                    namefirsttime = True
                    for version, typemap in sorted(version_type_index.items()):
                        versionfirsttime = True
                        for tname, tcset in sorted(typemap.items()):
                            if (namefirsttime):
                                params = paramdict.get(domain+'.'+name, None)
                                fout.write('|'+name+'|'+format_param_strings(params) + '|')
                                namefirsttime = False
                            else:
                                fout.write('| | |')
                            if (versionfirsttime):
                                versionfirsttime = False
                                fout.write(version+'|')
                            else:
                                fout.write('|')

                            tclist = []
                            for tc in sorted(tcset):
                                tclist.append(tc)
                            fout.write('**'+tname+'** = '+format_type_constraints(tclist)+'|\n')

                fout.write('| |\n| |\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ONNX Runtime Operator Kernel Documentation Generator')
    parser.add_argument('--output_path', help='output markdown file path',
                        default=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'OperatorKernels.md')
                        )
    args = parser.parse_args()

    class Args(object):
        output = args.output_path
    main(Args)
