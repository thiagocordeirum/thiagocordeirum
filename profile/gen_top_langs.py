"""Gera profile/top-langs.svg com as linguagens dos repositórios públicos.

Uso: GITHUB_TOKEN=... python profile/gen_top_langs.py <usuario>

Notebooks Jupyter ficam de fora: o GitHub conta os bytes das saídas
(imagens, tabelas), o que esconderia todas as outras linguagens.
"""

import json
import os
import sys
import urllib.request
from collections import Counter
from pathlib import Path

IGNORAR = {"Jupyter Notebook", "HTML", "CSS", "Stata", "Standard ML", "Scheme"}
MAX_LINGUAGENS = 6
CORES = {
    "Python": "#3572A5",
    "Vue": "#41B883",
    "TypeScript": "#3178C6",
    "JavaScript": "#F1E05A",
    "Java": "#B07219",
    "Kotlin": "#A97BFF",
    "Verilog": "#B2B7F8",
    "C++": "#F34B7D",
    "C": "#555555",
    "Shell": "#89E051",
}


def api(caminho: str):
    req = urllib.request.Request(f"https://api.github.com{caminho}")
    req.add_header("Accept", "application/vnd.github+json")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def coletar(usuario: str) -> Counter:
    total = Counter()
    pagina = 1
    while True:
        repos = api(f"/users/{usuario}/repos?type=owner&per_page=100&page={pagina}")
        if not repos:
            break
        for repo in repos:
            if repo["fork"] or repo["private"] or repo["name"] == usuario:
                continue
            total.update(api(f"/repos/{usuario}/{repo['name']}/languages"))
        pagina += 1
    for nome in IGNORAR:
        total.pop(nome, None)
    return total


def svg(total: Counter) -> str:
    itens = total.most_common(MAX_LINGUAGENS)
    soma = sum(v for _, v in itens) or 1
    largura, x0, barra_w = 360, 20, 320

    partes, x = [], x0
    for nome, v in itens:
        w = barra_w * v / soma
        cor = CORES.get(nome, "#8B949E")
        partes.append(f'<rect x="{x:.2f}" y="48" width="{w:.2f}" height="8" fill="{cor}"/>')
        x += w

    legenda = []
    for i, (nome, v) in enumerate(itens):
        cx = x0 + (i % 2) * 170
        cy = 82 + (i // 2) * 24
        cor = CORES.get(nome, "#8B949E")
        legenda.append(
            f'<circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{cor}"/>'
            f'<text x="{cx + 16}" y="{cy}" class="t">{nome} {100 * v / soma:.1f}%</text>'
        )

    altura = 82 + ((len(itens) + 1) // 2) * 24
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" height="{altura}" viewBox="0 0 {largura} {altura}" role="img" aria-label="Linguagens mais usadas">
<style>
  .bg {{ fill: #FFFFFF; stroke: #D0D7DE; }}
  .h {{ font: 600 15px 'Segoe UI', Ubuntu, sans-serif; fill: #1F2328; }}
  .t {{ font: 400 12px 'Segoe UI', Ubuntu, sans-serif; fill: #424A53; }}
  @media (prefers-color-scheme: dark) {{
    .bg {{ fill: #0D1117; stroke: #30363D; }}
    .h {{ fill: #E6EDF3; }}
    .t {{ fill: #9198A1; }}
  }}
</style>
<rect class="bg" x="0.5" y="0.5" width="{largura - 1}" height="{altura - 1}" rx="6"/>
<text x="{x0}" y="32" class="h">Linguagens mais usadas</text>
<clipPath id="r"><rect x="{x0}" y="48" width="{barra_w}" height="8" rx="4"/></clipPath>
<g clip-path="url(#r)">{''.join(partes)}</g>
{''.join(legenda)}
</svg>
"""


if __name__ == "__main__":
    usuario = sys.argv[1] if len(sys.argv) > 1 else "thiagocordeirum"
    destino = Path(__file__).with_name("top-langs.svg")
    destino.write_text(svg(coletar(usuario)), encoding="utf-8")
    print(f"gerado: {destino}")
