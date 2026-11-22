#!/usr/bin/env python3
"""Reading-role palette check for the four Outis themes.

Spec: docs/superpowers/specs/2026-11-22-outis-themes-reading-audit-design.md. Stdlib only:
  /usr/bin/python3 -B scripts/outis-palette-check.py      # prints ALL PASS or each miss, exit 1 on a miss
The hex values below mirror src/outis-*.css; change both together. TH-38 checks the live colours."""
import itertools, math, sys
def rgb(h): h=h.lstrip('#'); return [int(h[i:i+2],16) for i in (0,2,4)]
def lin(c): c/=255; return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
def wcag(a,b):
    L=lambda h: sum(w*lin(c) for w,c in zip((0.2126,0.7152,0.0722),rgb(h)))
    x,y=sorted((L(a),L(b)),reverse=True); return (x+.05)/(y+.05)
def apca(txt,bg):
    Y=lambda h: sum(w*(c/255)**2.4 for w,c in zip((0.2126729,0.7151522,0.0721750),rgb(h)))
    t,b=Y(txt),Y(bg)
    t=t+(0.022-t)**1.414 if t<0.022 else t
    b=b+(0.022-b)**1.414 if b<0.022 else b
    if abs(b-t)<0.0005: return 0.0
    if b>t: s=(b**0.56-t**0.57)*1.14; o=0 if s<0.1 else s-0.027
    else:   s=(b**0.65-t**0.62)*1.14; o=0 if s>-0.1 else s+0.027
    return abs(o*100)
def oklab_lin(r,g,b):
    l=0.4122214708*r+0.5363325363*g+0.0514459929*b; m=0.2119034982*r+0.6806995451*g+0.1073969566*b; s=0.0883024619*r+0.2817188376*g+0.6299787005*b
    l,m,s=[x**(1/3) if x>0 else 0 for x in (l,m,s)]
    return (0.2104542553*l+0.7936177850*m-0.0040720468*s, 1.9779984951*l-2.4285922050*m+0.4505937099*s, 0.0259040371*l+0.7827717662*m-0.8086757660*s)
def oklab(h): return oklab_lin(*[lin(c) for c in rgb(h)])
def deut(h):  # Vienot 1999 deuteranopia, linear RGB
    r,g,b=[lin(c) for c in rgb(h)]
    return oklab_lin(0.29275*r+0.70725*g, 0.29275*r+0.70725*g, -0.02234*r+0.02234*g+b)
def dE(a,b): return 100*math.dist(a,b)
def lch(h): L,a,b=oklab(h); return L, math.hypot(a,b), math.degrees(math.atan2(b,a))%360
assert abs(wcag("#000000", "#ffffff") - 21) < 0.01 and abs(apca("#000000", "#ffffff") - 106.04) < 0.1

T = {
	'Outis Dark': {'bg': '#1a1713', 'card': '#211d1a', 'body': '#d7d2cb', 'head': '#e7e2dc', 'muted': '#a9a49e', 'accent': '#84b9e6', 'link': '#93c4ed', 'key': '#f2a06e', 'em': '#75bca3', 'code': '#79c0ff', 'math': '#f0c674', 'success': '#8bcd99', 'warn': '#edbf71', 'error': '#f69b94'},
	'Outis Light': {'bg': '#fbf9f5', 'card': '#f3f0ea', 'body': '#33302b', 'head': '#1d1a16', 'muted': '#6e6b67', 'accent': '#2266a4', 'link': '#1a588f', 'key': '#a3471a', 'em': '#1f7265', 'code': '#0550ae', 'math': '#7a4f00', 'success': '#2b7440', 'warn': '#975c16', 'error': '#b33832'},
	'Outis Spark': {'bg': '#171e14', 'card': '#20271b', 'body': '#d0d5c8', 'head': '#e6eadd', 'muted': '#acb2a4', 'accent': '#76b900', 'link': '#92d400', 'key': '#e6a3a2', 'em': '#98a6ea', 'code': '#c2ec5c', 'math': '#cba35e', 'success': '#a4e100', 'warn': '#edbf71', 'error': '#f69b94'},
	'Outis FT': {'bg': '#fff1e0', 'card': '#f5ebdd', 'body': '#33302e', 'head': '#1f1d1b', 'muted': '#66615c', 'accent': '#005b7f', 'link': '#005b7f', 'key': '#7a2439', 'em': '#1f7265', 'code': '#005b7f', 'math': '#7a4f00', 'success': '#276b4d', 'warn': '#8a6100', 'error': '#b31f33'},
}
bad = []
for n,t in T.items():
    dark=apca(t['body'],t['bg'])<90 and lch(t['bg'])[0]<0.5
    floor=75 if dark else 90
    for s in ('bg','card'):
        if apca(t['body'],t[s])<floor-3: bad.append(f'{n} body Lc on {s}')
    if apca(t['head'],t['bg'])<=apca(t['body'],t['bg']): bad.append(f'{n} heading not above body')
    for r in ('link','key','em','math','success','warn','error','muted'):
        if wcag(t[r],t['card'])<4.5: bad.append(f'{n} {r} {wcag(t[r],t["card"]):.2f}:1 on card')
    for r in ('link','key','em','math'):
        if apca(t[r],t['bg'])>apca(t['body'],t['bg']): bad.append(f'{n} {r} louder than body')
    for a,b in itertools.combinations(('link','key','em','math','body'),2):
        nv,dv=dE(oklab(t[a]),oklab(t[b])),dE(deut(t[a]),deut(t[b]))
        need_d = 5 if {a,b}=={'key','math'} else 8   # key/math: shape cue (bold vs KaTeX italic serif) carries CVD
        if nv<8 or dv<need_d: bad.append(f'{n} {a}/{b} ΔE {nv:.1f}/{dv:.1f}')
print('\n'.join(bad) or 'ALL PASS'); sys.exit(1 if bad else 0)
