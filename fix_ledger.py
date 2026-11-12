p = '/Users/amre/Projects/GameStewKit/src/main.gd'
lines = open(p).read().split('\n')

# Replace lines 1277..1305 (1-based) with the correctly-indented ledger block.
start = 1277 - 1
end = 1305 - 1
assert lines[start].strip() == 'head.add_child(_label("Day", COL_DIM_P, 13))', lines[start]
assert lines[end].strip() == '_content.add_child(row)', lines[end]

block = """\t\thead.add_child(_label("Day", COL_DIM_P, 13))
\t\thead.add_child(_label("Takings", COL_DIM_P, 13))
\t\thead.add_child(_label("Costs", COL_DIM_P, 13))
\t\thead.add_child(_label("Net", COL_DIM_P, 13))
\t\thead.add_child(_label("Cur", COL_DIM_P, 13))
\t\thead.add_child(_label("Stol", COL_DIM_P, 13))

\t\tvar n := rev.size()
\t\tvar start := maxi(0, n - 40)
\t\tfor i in range(n - 1, start - 1, -1):
\t\t\tvar net := int(rev[i]) - int(opx[i]) if i < opx.size() else 0
\t\t\tvar row := HBoxContainer.new()
\t\t\trow.add_theme_constant_override("separation", 6)
\t\t\trow.add_child(_label("%d" % (i + 1), COL_TEXT, 13))
\t\t\trow.add_child(_label("%d" % int(rev[i]), COL_TEXT, 13))
\t\t\trow.add_child(_label("%d" % (int(opx[i]) if i < opx.size() else 0), COL_DIM_P, 13))
\t\t\t# Net: the sign carries the meaning, the chip carries the mood.
\t\t\trow.add_child(_chip(COL_MOSS if net >= 0 else COL_RUST))
\t\t\trow.add_child(_label("%s%d" % ["+" if net >= 0 else "-", absi(net)],
\t\t\t\tCOL_TEXT, 13))
\t\t\trow.add_child(_label("%d" % (int(cur[i]) if i < cur.size() else 0), COL_TEXT, 13))
\t\t\tif i < stol.size() and int(stol[i]) > 0:
\t\t\t\trow.add_child(_chip(COL_RUST))
\t\t\trow.add_child(_label("%d" % (int(stol[i]) if i < stol.size() else 0),
\t\t\t\tCOL_TEXT, 13))
\t\t\t_content.add_child(row)""".split('\n')

lines[start:end + 1] = block
open(p, 'w').write('\n'.join(lines))
print("ledger block re-indented")
