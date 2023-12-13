# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 6.0+master, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2023 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

"""
Handle writing of LCOV files.

The LCOV format is described in https://github.com/linux-test-project/lcov/blob/07a1127c2b4390abf4a516e9763fb28a956a9ce4/man/geninfo.1#L989
and generated by https://github.com/linux-test-project/lcov/blob/07a1127c2b4390abf4a516e9763fb28a956a9ce4/bin/geninfo
"""

from ...options import Options

from ...utils import force_unix_separator, get_md5_hexdigest, open_text_for_writing
from ...coverage import CovData, sort_coverage


def write_report(covdata: CovData, output_file: str, options: Options) -> None:
    """produce gcovr csv report"""

    with open_text_for_writing(output_file, "coverage.lcov") as fh:
        keys = sort_coverage(
            covdata,
            by_branch=options.sort_branches,
            by_num_uncovered=options.sort_uncovered,
            by_percent_uncovered=options.sort_percent,
            reverse=options.sort_reverse,
        )
        if options.lcov_comment is not None:
            # #comment_string
            fh.write(f"#{options.lcov_comment}\n")
        # TN:<test name>
        fh.write(f"TN:{options.lcov_test_name}\n")

        for key in keys:
            filename = force_unix_separator(covdata[key].filename)

            # SF:<path to the source file>
            fh.write(f"SF:{filename}\n")

            # VER:<version ID>
            # Generate md5 hash of file contents
            with open(filename, "rb") as file_handle:
                contents = file_handle.read()
            fh.write(f"VER:{get_md5_hexdigest(contents)}\n")

            functions = 0
            function_hits = 0
            for function_name in sorted(covdata[key].functions):
                linenos = list(covdata[key].functions[function_name].count)
                functions += len(linenos)

                def postfix():
                    return f"_{lineno}" if len(linenos) > 1 else ""

                for lineno in sorted(linenos):
                    # FN:<line number of function start>,[<line number of function end>,]<function name>
                    fh.write(f"FN:{lineno},{function_name}{postfix()}\n")
                for lineno in sorted(covdata[key].functions[function_name].count):
                    count = covdata[key].functions[function_name].count[lineno]
                    if count:
                        function_hits += 1
                    # FNDA:<execution count>,<function name>
                    fh.write(f"FNDA:{count},{function_name}{postfix()}\n")
            # FNF:<number of functions found>
            fh.write(f"FNF:{functions}\n")
            # FNH:<number of function hit>
            fh.write(f"FNH:{function_hits}\n")

            sorted_lines = sorted(covdata[key].lines)

            branches = 0
            branch_hits = 0
            for lineno in sorted_lines:
                line_coverage = covdata[key].lines[lineno]
                if line_coverage.excluded:
                    next
                branches += len(line_coverage.branches)
                for branch in sorted(line_coverage.branches):
                    branch_coverage = line_coverage.branches[branch]
                    if branch_coverage.count:
                        branch_hits += 1
                    # BRDA:<line_number>,[<exception>]<block>,<branch>,<taken>
                    fh.write(
                        f"BRDA:{lineno},{'e' if branch_coverage.throw else ''}{branch_coverage.blockno},{branch},{branch_coverage.count if branch_coverage.count else '-'}\n"
                    )

            # BRF:<number of branches found>
            fh.write(f"BRF:{branches}\n")
            # BRH:<number of branches hit>
            fh.write(f"BRH:{branch_hits}\n")

            lines_covered = 0
            for lineno in sorted_lines:
                line_coverage = covdata[key].lines[lineno]
                if line_coverage.count:
                    lines_covered += 1
                # DA:<line number>,<execution count>[,<checksum>]
                fh.write(f"DA:{lineno},{line_coverage.count},{line_coverage.md5}\n")

            # LH:<number of lines with a non\-zero execution count>
            fh.write(f"LH:{lines_covered}\n")
            # LF:<number of instrumented lines>
            fh.write(f"LF:{len(covdata[key].lines)}\n")

            # End of file section
            fh.write("end_of_record\n")
