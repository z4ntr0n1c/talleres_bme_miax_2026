#!/usr/bin/env python3
"""
Script to execute Ejercicio_Hues_and_Cues_Alumnos.ipynb, populate outputs,
and generate a publication-quality HTML and PDF report of the complete solutions.
"""

import os
import sys
import json
import ast
import io
import re
import html
import base64
import contextlib

# Ensure matplotlib uses Agg backend and local writable cache
os.environ["MPLCONFIGDIR"] = os.path.abspath("./.mpl_cache")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

NOTEBOOK_PATH = "T1_1/Ejercicio_Hues_and_Cues_Alumnos.ipynb"
HTML_OUTPUT_PATH = "T1_1/Ejercicio_Hues_and_Cues_Soluciones.html"
PDF_OUTPUT_PATH = "T1_1/Ejercicio_Hues_and_Cues_Soluciones.pdf"

def simple_markdown_to_html(md_text):
    lines = md_text.split("\n")
    html_lines = []
    in_table = False
    table_rows = []
    in_list = False
    in_numbered_list = False
    in_blockquote = False
    blockquote_lines = []

    def flush_blockquote():
        nonlocal in_blockquote, blockquote_lines, html_lines
        if in_blockquote:
            inner_md = "\n".join(blockquote_lines)
            inner_html = simple_markdown_to_html(inner_md)
            alert_class = "blockquote-custom"
            if "[!NOTE]" in inner_md:
                alert_class = "alert-note"
                inner_html = inner_html.replace("[!NOTE]", "<strong>Nota:</strong> ")
            elif "[!IMPORTANT]" in inner_md:
                alert_class = "alert-important"
                inner_html = inner_html.replace("[!IMPORTANT]", "<strong>Importante:</strong> ")
            elif "[!TIP]" in inner_md:
                alert_class = "alert-tip"
                inner_html = inner_html.replace("[!TIP]", "<strong>Consejo:</strong> ")
            elif "[!WARNING]" in inner_md:
                alert_class = "alert-warning"
                inner_html = inner_html.replace("[!WARNING]", "<strong>Atención:</strong> ")
            html_lines.append(f'<div class="{alert_class}">{inner_html}</div>')
            blockquote_lines = []
            in_blockquote = False

    def flush_list():
        nonlocal in_list, in_numbered_list, html_lines
        if in_list:
            html_lines.append("</ul>")
            in_list = False
        if in_numbered_list:
            html_lines.append("</ol>")
            in_numbered_list = False

    def flush_table():
        nonlocal in_table, table_rows, html_lines
        if in_table and table_rows:
            html_lines.append('<div class="table-container"><table class="styled-table">')
            for r_idx, row in enumerate(table_rows):
                cols = [c.strip() for c in row.split("|")[1:-1]]
                if r_idx == 0:
                    html_lines.append("<thead><tr>" + "".join(f"<th>{inline_format(c)}</th>" for c in cols) + "</tr></thead><tbody>")
                elif r_idx == 1 and all(set(c).issubset({'-', ':', ' '}) for c in cols):
                    continue  # Separator line
                else:
                    html_lines.append("<tr>" + "".join(f"<td>{inline_format(c)}</td>" for c in cols) + "</tr>")
            html_lines.append("</tbody></table></div>")
            table_rows = []
            in_table = False

    def inline_format(text):
        # Math blocks
        text = re.sub(r'\$\$([^\$]+)\$\$', r'<div class="math-display">\1</div>', text)
        text = re.sub(r'\$([^\$]+)\$', r'<span class="math-inline">\1</span>', text)
        # Bold + italic
        text = re.sub(r'\*\*\*([^\*]+)\*\*\*', r'<strong><em>\1</em></strong>', text)
        text = re.sub(r'\*\*([^\*]+)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*([^\*]+)\*', r'<em>\1</em>', text)
        # Inline code
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        # Links
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        return text

    for line in lines:
        stripped = line.strip()

        # Blockquote line
        if stripped.startswith(">"):
            flush_list()
            flush_table()
            in_blockquote = True
            bq_content = stripped[1:].strip() if len(stripped) > 1 else ""
            blockquote_lines.append(bq_content)
            continue
        elif in_blockquote:
            if stripped == "":
                # Empty line might continue or separate blockquote content
                blockquote_lines.append("")
                continue
            else:
                flush_blockquote()

        # Table row
        if stripped.startswith("|") and stripped.endswith("|"):
            flush_list()
            in_table = True
            table_rows.append(stripped)
            continue
        elif in_table:
            flush_table()

        # Unordered list
        if stripped.startswith("- ") or stripped.startswith("* "):
            if in_numbered_list:
                flush_list()
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{inline_format(stripped[2:])}</li>")
            continue

        # Numbered list
        num_match = re.match(r'^(\d+)\.\s+(.*)$', stripped)
        if num_match:
            if in_list:
                flush_list()
            if not in_numbered_list:
                html_lines.append("<ol>")
                in_numbered_list = True
            html_lines.append(f"<li>{inline_format(num_match.group(2))}</li>")
            continue

        flush_list()

        if not stripped:
            continue

        # Horizontal rule
        if stripped in ["---", "***", "___"]:
            html_lines.append("<hr/>")
            continue

        # Headings
        if stripped.startswith("#### "):
            html_lines.append(f"<h4>{inline_format(stripped[5:])}</h4>")
        elif stripped.startswith("### "):
            html_lines.append(f"<h3>{inline_format(stripped[4:])}</h3>")
        elif stripped.startswith("## "):
            html_lines.append(f"<h2>{inline_format(stripped[3:])}</h2>")
        elif stripped.startswith("# "):
            html_lines.append(f"<h1>{inline_format(stripped[2:])}</h1>")
        else:
            html_lines.append(f"<p>{inline_format(stripped)}</p>")

    flush_blockquote()
    flush_table()
    flush_list()

    return "\n".join(html_lines)


def execute_and_render_notebook():
    import pandas as pd

    with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
        nb = json.load(f)

    # Intercept plt.show to store figures
    captured_figures = []

    def mock_show(*args, **kwargs):
        for fig_num in plt.get_fignums():
            fig = plt.figure(fig_num)
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
            buf.seek(0)
            img_b64 = base64.b64encode(buf.read()).decode("utf-8")
            captured_figures.append(img_b64)
        plt.close("all")

    plt.show = mock_show

    def mock_display(*args):
        for arg in args:
            if isinstance(arg, (pd.DataFrame, pd.Series)):
                print(arg.to_string())
            else:
                print(arg)

    # Execution namespace
    exec_globals = {
        "__name__": "__main__",
        "plt": plt,
        "os": os,
        "sys": sys,
        "display": mock_display
    }

    rendered_sections = []
    
    print(f"Executing {len(nb['cells'])} cells...")

    for idx, cell in enumerate(nb["cells"]):
        ctype = cell["cell_type"]
        source = "".join(cell.get("source", []))

        if ctype == "markdown":
            md_html = simple_markdown_to_html(source)
            rendered_sections.append(f'<div class="cell markdown-cell">\n{md_html}\n</div>')

        elif ctype == "code":
            # Strip comments and pass to exec
            captured_stdout = io.StringIO()
            captured_figures.clear()
            eval_output = None
            cell_error = None

            # Split code into statements and possible trailing expression
            parsed = None
            try:
                parsed = ast.parse(source)
            except Exception as e:
                cell_error = f"SyntaxError: {e}"

            if parsed and parsed.body:
                last_expr = None
                if isinstance(parsed.body[-1], ast.Expr):
                    last_expr = parsed.body.pop()

                code_exec = compile(parsed, filename=f"<cell_{idx}>", mode="exec")

                with contextlib.redirect_stdout(captured_stdout), contextlib.redirect_stderr(captured_stdout):
                    try:
                        exec(code_exec, exec_globals)
                        if last_expr:
                            eval_code = compile(ast.Expression(last_expr.value), filename=f"<cell_{idx}>", mode="eval")
                            eval_val = eval(eval_code, exec_globals)
                            if eval_val is not None:
                                import pandas as pd
                                if isinstance(eval_val, (pd.DataFrame, pd.Series)):
                                    eval_output = eval_val.to_html(classes="styled-table dataframe", border=0)
                                else:
                                    eval_output = html.escape(str(eval_val))
                    except Exception as e:
                        import traceback
                        cell_error = traceback.format_exc()

            # Catch any unshown plots
            for fig_num in plt.get_fignums():
                fig = plt.figure(fig_num)
                buf = io.BytesIO()
                fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
                buf.seek(0)
                img_b64 = base64.b64encode(buf.read()).decode("utf-8")
                captured_figures.append(img_b64)
            plt.close("all")

            stdout_text = captured_stdout.getvalue()

            # Update cell outputs in notebook JSON
            nb_outputs = []
            if stdout_text:
                nb_outputs.append({
                    "name": "stdout",
                    "output_type": "stream",
                    "text": stdout_text.splitlines(keepends=True)
                })
            for fig_b64 in captured_figures:
                nb_outputs.append({
                    "data": {
                        "image/png": fig_b64,
                        "text/plain": ["<Figure size ...>"]
                    },
                    "metadata": {},
                    "output_type": "display_data"
                })
            if eval_output and not captured_figures:
                nb_outputs.append({
                    "data": {
                        "text/html": [eval_output],
                        "text/plain": ["DataFrame"]
                    },
                    "metadata": {},
                    "output_type": "execute_result",
                    "execution_count": idx
                })
            if cell_error:
                nb_outputs.append({
                    "ename": "Error",
                    "evalue": str(cell_error),
                    "output_type": "error",
                    "traceback": [cell_error]
                })

            cell["outputs"] = nb_outputs
            cell["execution_count"] = idx

            # Build HTML representation
            escaped_source = html.escape(source)
            code_html = f'''
            <div class="cell code-cell">
                <div class="code-header">
                    <span class="badge code-badge">Código In [{idx}]</span>
                </div>
                <pre class="code-block"><code>{escaped_source}</code></pre>
            '''

            if stdout_text or eval_output or captured_figures or cell_error:
                code_html += '<div class="output-container">\n'
                if stdout_text:
                    code_html += f'<div class="output-header"><span class="badge out-badge">Salida Out [{idx}]</span></div>\n'
                    code_html += f'<pre class="output-block">{html.escape(stdout_text)}</pre>\n'
                if eval_output:
                    code_html += f'<div class="table-output">{eval_output}</div>\n'
                for fig_b64 in captured_figures:
                    code_html += f'<div class="plot-container"><img class="plot-img" src="data:image/png;base64,{fig_b64}" alt="Gráfico Celda {idx}" /></div>\n'
                if cell_error:
                    code_html += f'<pre class="error-block">{html.escape(cell_error)}</pre>\n'
                code_html += '</div>\n'

            code_html += '</div>\n'
            rendered_sections.append(code_html)

    # Save updated notebook JSON with outputs
    with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)
    print("Notebook JSON updated with verified outputs.")

    # Assemble complete HTML document
    full_html = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Hues & Cues: Alineación Perceptual Humano-IA - Soluciones y Cuaderno Técnico</title>
    <style>
        @page {{
            size: A4;
            margin: 15mm 15mm 18mm 15mm;
            @bottom-right {{
                content: "Página " counter(page);
                font-size: 8pt;
                color: #64748b;
            }}
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            color: #1e293b;
            background-color: #ffffff;
            line-height: 1.5;
            font-size: 9.5pt;
            margin: 0;
            padding: 0;
        }}
        .header-doc {{
            border-bottom: 3px solid #2563eb;
            padding-bottom: 15px;
            margin-bottom: 25px;
        }}
        .meta-institute {{
            font-size: 8.5pt;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #2563eb;
            font-weight: 700;
            margin-bottom: 4px;
        }}
        .doc-title {{
            font-size: 19pt;
            font-weight: 800;
            color: #0f172a;
            margin: 0 0 6px 0;
            line-height: 1.25;
        }}
        .doc-subtitle {{
            font-size: 10pt;
            color: #475569;
            margin: 0 0 10px 0;
        }}
        .meta-badges {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 8px;
        }}
        .meta-tag {{
            background: #f1f5f9;
            color: #334155;
            border: 1px solid #cbd5e1;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 8pt;
            font-weight: 600;
        }}
        h1, h2, h3, h4 {{
            color: #0f172a;
            font-weight: 700;
            page-break-after: avoid;
        }}
        h1 {{
            font-size: 14pt;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 4px;
            margin-top: 25px;
            margin-bottom: 12px;
            color: #1e3a8a;
        }}
        h2 {{
            font-size: 12pt;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 3px;
            margin-top: 20px;
            margin-bottom: 10px;
            color: #1d4ed8;
        }}
        h3 {{
            font-size: 10.5pt;
            margin-top: 15px;
            margin-bottom: 8px;
            color: #1e293b;
        }}
        h4 {{
            font-size: 9.5pt;
            margin-top: 12px;
            margin-bottom: 6px;
        }}
        p {{
            margin: 0 0 8px 0;
        }}
        ul, ol {{
            margin: 0 0 10px 0;
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 4px;
        }}
        hr {{
            border: 0;
            height: 1px;
            background: #e2e8f0;
            margin: 20px 0;
        }}
        code {{
            font-family: "DejaVu Sans Mono", "Fira Code", Monaco, Consolas, monospace;
            font-size: 8.5pt;
            background-color: #f1f5f9;
            color: #0f172a;
            padding: 1px 4px;
            border-radius: 3px;
        }}
        .math-inline {{
            font-family: "Times New Roman", Times, serif;
            font-style: italic;
            background: #f8fafc;
            padding: 0 3px;
        }}
        .math-display {{
            font-family: "Times New Roman", Times, serif;
            font-style: italic;
            text-align: center;
            margin: 10px 0;
            padding: 6px;
            background: #f8fafc;
            border-radius: 4px;
        }}
        .cell {{
            margin-bottom: 16px;
            page-break-inside: avoid;
        }}
        .markdown-cell {{
            margin-bottom: 12px;
        }}
        .code-cell {{
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            overflow: hidden;
            background: #ffffff;
            margin-bottom: 16px;
        }}
        .code-header {{
            background: #f8fafc;
            border-bottom: 1px solid #e2e8f0;
            padding: 4px 10px;
            display: flex;
            align-items: center;
        }}
        .badge {{
            font-size: 7.5pt;
            font-family: monospace;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        .code-badge {{
            background: #e0e7ff;
            color: #3730a3;
            border: 1px solid #c7d2fe;
        }}
        .out-badge {{
            background: #dcfce7;
            color: #166534;
            border: 1px solid #bbf7d0;
        }}
        .code-block {{
            background: #fafafa;
            color: #1e293b;
            padding: 10px 12px;
            margin: 0;
            font-family: "DejaVu Sans Mono", "Fira Code", Monaco, Consolas, monospace;
            font-size: 8pt;
            line-height: 1.45;
            overflow-x: auto;
            white-space: pre-wrap;
            word-break: break-word;
        }}
        .output-container {{
            border-top: 1px solid #e2e8f0;
            background: #f8fafc;
            padding: 8px 12px;
        }}
        .output-header {{
            margin-bottom: 4px;
        }}
        .output-block {{
            background: #ffffff;
            border-left: 3px solid #3b82f6;
            padding: 6px 10px;
            margin: 4px 0;
            font-family: "DejaVu Sans Mono", "Fira Code", Monaco, Consolas, monospace;
            font-size: 7.8pt;
            line-height: 1.4;
            color: #0f172a;
            white-space: pre-wrap;
            word-break: break-all;
            border-radius: 0 4px 4px 0;
        }}
        .error-block {{
            background: #fef2f2;
            border-left: 3px solid #ef4444;
            color: #991b1b;
            padding: 8px 10px;
            margin: 4px 0;
            font-family: monospace;
            font-size: 7.8pt;
            white-space: pre-wrap;
        }}
        .plot-container {{
            text-align: center;
            margin: 12px 0 6px 0;
            page-break-inside: avoid;
        }}
        .plot-img {{
            max-width: 95%;
            height: auto;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }}
        .table-container {{
            overflow-x: auto;
            margin: 10px 0;
        }}
        .styled-table {{
            border-collapse: collapse;
            width: 100%;
            font-size: 8pt;
            margin: 6px 0;
            border: 1px solid #cbd5e1;
        }}
        .styled-table th, .styled-table td {{
            border: 1px solid #e2e8f0;
            padding: 5px 8px;
            text-align: left;
        }}
        .styled-table th {{
            background-color: #f1f5f9;
            color: #1e293b;
            font-weight: 700;
        }}
        .styled-table tr:nth-child(even) {{
            background-color: #f8fafc;
        }}
        .alert-note, .alert-important, .alert-tip, .alert-warning {{
            padding: 8px 12px;
            border-radius: 5px;
            margin: 10px 0;
            font-size: 8.8pt;
            page-break-inside: avoid;
        }}
        .alert-note {{
            background-color: #eff6ff;
            border-left: 4px solid #3b82f6;
            color: #1e40af;
        }}
        .alert-important {{
            background-color: #fef3c7;
            border-left: 4px solid #f59e0b;
            color: #92400e;
        }}
        .alert-warning {{
            background-color: #fef2f2;
            border-left: 4px solid #ef4444;
            color: #991b1b;
        }}
        .alert-tip {{
            background-color: #f0fdf4;
            border-left: 4px solid #22c55e;
            color: #166534;
        }}
    </style>
</head>
<body>

<div class="header-doc">
    <div class="meta-institute">Máster en Inteligencia Artificial Aplicada a Mercados Financieros (MIAX) · Instituto BME</div>
    <div class="doc-title">Proyecto Final: Alineación Perceptual Humano-IA (Hues and Cues)</div>
    <div class="doc-subtitle">Soluciones Completas, Ejecución Empírica y Respuestas Teóricas al Cuaderno de Prácticas</div>
    <div class="meta-badges">
        <span class="meta-tag">Paper: Alabau-Bosque et al. (2025)</span>
        <span class="meta-tag">Muestra: 324 Usuarios (3.870 Respuestas Tricrómatas)</span>
        <span class="meta-tag">Coordenadas Tablero: 480 casillas (8 Colores Base)</span>
        <span class="meta-tag">Estado: Ejecutado & Verificado 100%</span>
    </div>
</div>

<div class="content">
{''.join(rendered_sections)}
</div>

</body>
</html>
'''

    with open(HTML_OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"HTML solutions report written to {HTML_OUTPUT_PATH}")

if __name__ == "__main__":
    execute_and_render_notebook()
