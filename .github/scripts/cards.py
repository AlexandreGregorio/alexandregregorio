"""Gera dois cards SVG (estatísticas e linguagens) com dados públicos do GitHub.
Uso: python3 cards.py <pasta_saida>   (precisa de GH_TOKEN e USUARIO no ambiente)"""
import json, os, sys, urllib.request
from datetime import datetime, timezone

USUARIO = os.environ["USUARIO"]; TOKEN = os.environ["GH_TOKEN"]; SAIDA = sys.argv[1]
os.makedirs(SAIDA, exist_ok=True)

def gql(q, v):
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query": q, "variables": v}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))["data"]

d = gql("""query($u:String!){ user(login:$u){
  name createdAt followers{totalCount}
  contributionsCollection{ totalCommitContributions contributionCalendar{totalContributions} }
  repositories(first:100, ownerAffiliations:OWNER, isFork:false){
    totalCount nodes{ stargazerCount languages(first:10, orderBy:{field:SIZE,direction:DESC}){ edges{ size node{name color} } } } } } }""",
  {"u": USUARIO})["user"]

repos = d["repositories"]["nodes"]
estrelas = sum(r["stargazerCount"] for r in repos)
langs = {}
for r in repos:
    for e in r["languages"]["edges"]:
        n = e["node"]["name"]; langs.setdefault(n, [0, e["node"]["color"] or "#8b949e"]); langs[n][0] += e["size"]
top = sorted(langs.items(), key=lambda x: -x[1][0])[:6]
total = sum(v[0] for _, v in top) or 1
anos = datetime.now(timezone.utc).year - int(d["createdAt"][:4])

# Paleta escura que combina com o tema do perfil
BG, BORDA, TXT, SUB, AZ = "#0d1117", "#30363d", "#e6edf3", "#8b949e", "#7B9CD2"
FONTE = "font-family:'Segoe UI',Ubuntu,Helvetica,Arial,sans-serif"

itens = [("Contribuições no último ano", d["contributionsCollection"]["contributionCalendar"]["totalContributions"]),
         ("Commits no último ano", d["contributionsCollection"]["totalCommitContributions"]),
         ("Repositórios públicos", d["repositories"]["totalCount"]),
         ("Estrelas recebidas", estrelas),
         ("Seguidores", d["followers"]["totalCount"])]
linhas = "".join(
    f'<text x="25" y="{72+i*25}" style="{FONTE};font-size:14px" fill="{SUB}">{t}</text>'
    f'<text x="370" y="{72+i*25}" text-anchor="end" style="{FONTE};font-size:14px;font-weight:700" fill="{TXT}">{v}</text>'
    for i, (t, v) in enumerate(itens))
stats = f'''<svg xmlns="http://www.w3.org/2000/svg" width="395" height="215" viewBox="0 0 395 215">
<rect x="0.5" y="0.5" width="394" height="214" rx="10" fill="{BG}" stroke="{BORDA}"/>
<text x="25" y="38" style="{FONTE};font-size:17px;font-weight:700" fill="{AZ}">Estatísticas no GitHub</text>
{linhas}
<text x="25" y="203" style="{FONTE};font-size:11px" fill="{SUB}">No GitHub há {anos} anos · atualizado em {datetime.now(timezone.utc):%d/%m/%Y}</text>
</svg>'''

# barra empilhada + legenda em 2 colunas
x = 25; barra = ""
for n, (s, c) in top:
    w = 345 * s / total; barra += f'<rect x="{x:.1f}" y="55" width="{max(w,1):.1f}" height="10" fill="{c}"/>'; x += w
leg = ""
for i, (n, (s, c)) in enumerate(top):
    cx = 25 + (i % 2) * 175; cy = 95 + (i // 2) * 27
    leg += (f'<circle cx="{cx+5}" cy="{cy-4}" r="5" fill="{c}"/>'
            f'<text x="{cx+16}" y="{cy}" style="{FONTE};font-size:13px" fill="{TXT}">{n} <tspan fill="{SUB}">{100*s/total:.1f}%</tspan></text>')
langs_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="395" height="215" viewBox="0 0 395 215">
<defs><clipPath id="b"><rect x="25" y="55" width="345" height="10" rx="5"/></clipPath></defs>
<rect x="0.5" y="0.5" width="394" height="214" rx="10" fill="{BG}" stroke="{BORDA}"/>
<text x="25" y="38" style="{FONTE};font-size:17px;font-weight:700" fill="{AZ}">Linguagens mais usadas</text>
<g clip-path="url(#b)">{barra}</g>
{leg}
</svg>'''

open(f"{SAIDA}/stats.svg", "w", encoding="utf-8").write(stats)
open(f"{SAIDA}/langs.svg", "w", encoding="utf-8").write(langs_svg)
print("cards gerados:", [n for n, _ in top])
