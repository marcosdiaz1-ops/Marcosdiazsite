# Home page FAQ (EN + ES). Imported by tools/build_es.py; also used to (re)insert into index.html.
import json, html, re
FAQ = [
 ("Do you work with Spanish-speaking buyers and sellers?",
  "Yes. I'm bilingual and can guide you through the whole process in English or Spanish, from the first call to closing day.",
  "¿Trabaja con compradores y vendedores que hablan español?",
  "Sí. Soy bilingüe y le puedo guiar en todo el proceso en español o en inglés, desde la primera llamada hasta el día del cierre."),
 ("How much do I need for a down payment in Sioux Falls?",
  "Less than many people think. Some loans need 3% to 3.5% down, VA loans can be $0 down for eligible veterans, and South Dakota Housing has programs that help first-time buyers with the down payment. A lender can tell you exactly what you qualify for.",
  "¿Cuánto necesito para el pago inicial en Sioux Falls?",
  "Menos de lo que mucha gente cree. Algunos préstamos piden de 3% a 3.5% de pago inicial, los préstamos VA pueden ser con $0 para veteranos que califiquen, y South Dakota Housing tiene programas que ayudan con el pago inicial a quienes compran su primera casa. Un prestamista le puede decir exactamente para qué califica."),
 ("Should I get pre-approved before I look at homes?",
  "Yes. A pre-approval tells you your price range and shows sellers you're serious. In a competitive market, offers without one are often passed over.",
  "¿Debo obtener una preaprobación antes de ver casas?",
  "Sí. La preaprobación le dice cuánto puede gastar y le muestra al vendedor que usted va en serio. Cuando hay competencia, las ofertas sin preaprobación muchas veces no se toman en cuenta."),
 ("How are buyer's agents paid?",
  "Buyers now sign a written agreement with their agent before touring homes, and it spells out how the agent is paid. Often the seller ends up covering some or all of it, but it's negotiable. I'll walk you through your options before we start.",
  "¿Cómo se le paga al agente del comprador?",
  "Hoy en día el comprador firma un acuerdo por escrito con su agente antes de ver casas, y ahí se explica cómo se le paga. Muchas veces el vendedor termina cubriendo parte o todo, pero es negociable. Le explico sus opciones antes de empezar."),
 ("How long does it take to buy a home?",
  "Finding the right home can take a few days or a few months. Once your offer is accepted, closing often takes about 30 to 45 days, depending on your loan.",
  "¿Cuánto tiempo toma comprar una casa?",
  "Encontrar la casa indicada puede tomar unos días o unos meses. Una vez aceptada su oferta, el cierre suele tomar de 30 a 45 días, según su préstamo."),
 ("How do I find out what my home is worth?",
  "Online estimates can be way off. Request a free home value report and I'll compare your home to real recent sales nearby.",
  "¿Cómo sé cuánto vale mi casa?",
  "Los cálculos en línea pueden fallar mucho. Pida un reporte gratis y comparo su casa con ventas reales y recientes cerca de usted."),
 ("What areas do you serve?",
  "All of Sioux Falls plus Tea, Harrisburg, Brandon, Garretson, Hartford, Crooks, Lennox, Canton and nearby communities in Minnehaha and Lincoln counties.",
  "¿En qué áreas trabaja?",
  "Todo Sioux Falls, además de Tea, Harrisburg, Brandon, Garretson, Hartford, Crooks, Lennox, Canton y comunidades cercanas en los condados de Minnehaha y Lincoln."),
 ("Can you help veterans and military families?",
  "Yes. I work with military families and veterans and can help you use your VA home loan benefit, including $0-down options for eligible buyers.",
  "¿Ayuda a veteranos y familias militares?",
  "Sí. Trabajo con familias militares y veteranos y le ayudo a usar su beneficio de préstamo VA, incluidas opciones con $0 de pago inicial para quienes califiquen."),
]
LINKS_EN = {5: ('home-value/', 'Get my home value'), 7: ('blog/va-home-loans-sioux-falls/', 'Read the VA loan guide'), 1: ('blog/give-me-five-down-payment-assistance/', 'About Give Me Five')}
LINKS_ES = {5: ('valor-de-casa/', 'Recibir mi reporte'), 7: ('blog/prestamos-va-sioux-falls/', 'Leer la guía VA'), 1: ('blog/give-me-five-ayuda-pago-inicial/', 'Sobre Give Me Five')}

def section(es):
    items = ''
    for i, (qe, ae, qs, as_) in enumerate(FAQ):
        q, a = (qs, as_) if es else (qe, ae)
        link = (LINKS_ES if es else LINKS_EN).get(i)
        extra = f' <a href="{link[0]}">{link[1]} →</a>' if link else ''
        items += f'        <details><summary>{q}</summary><p>{a}{extra}</p></details>\n'
    head = ('<p class="eyebrow">Preguntas frecuentes</p>\n        <h2>Respuestas rápidas.</h2>' if es else
            '<p class="eyebrow">FAQ</p>\n        <h2>Quick answers.</h2>')
    return f'''  <!-- FAQ -->
  <section id="faq" class="faq">
    <div class="wrap guide-grid">
      <div class="guide-head">
        {head}
      </div>
      <div class="accordions">
{items}      </div>
    </div>
  </section>
'''

def ld(es):
    return '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": (q[2] if es else q[0]),
                        "acceptedAnswer": {"@type": "Answer", "text": (q[3] if es else q[1])}} for q in FAQ]}, ensure_ascii=False) + '</script>\n'

if __name__ == '__main__':
    import os
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = os.path.join(ROOT, 'index.html'); s = open(p).read()
    s = re.sub(r'  <!-- FAQ -->\n  <section id="faq".*?</section>\n', '', s, flags=re.S)
    s = re.sub(r'<script type="application/ld\+json">\{"@context": "https://schema.org", "@type": "FAQPage".*?</script>\n', '', s)
    s = s.replace('  <!-- CONTACT -->', section(False) + '\n  <!-- CONTACT -->', 1)
    s = s.replace('</head>', ld(False) + '</head>', 1)
    open(p, 'w').write(s); print('faq inserted')
