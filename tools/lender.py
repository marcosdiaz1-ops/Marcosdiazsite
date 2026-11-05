APPLY='https://homeloan.charterwest.com/homehub/signup/gperez@charterwest.com'
def lender(es, img_prefix, compact=False):
    t=lambda e,s: s if es else e
    cls='lender-card compact' if compact else 'lender-card'
    return f'''<div class="{cls}">
  <img src="{img_prefix}images/lender-gisselle-perez.jpg" alt="Gisselle Perez, CharterWest Bank" width="96" height="96" loading="lazy">
  <div class="lender-info">
    <p class="eyebrow">{t('Get Pre-Approved', 'Obtenga su preaprobación')}</p>
    <h3>Gisselle Perez</h3>
    <p class="lender-title">{t('Mortgage Loan Advisor', 'Asesora de préstamos hipotecarios')} · CharterWest Bank Mortgage Center · NMLS #2840295</p>
    <p class="lender-lang">{t('Bilingual: English &amp; Español', 'Bilingüe: español e inglés')}</p>
    <p class="lender-contact"><a href="tel:+16052507967">605-250-7967</a> · <a href="mailto:gperez@charterwest.com">gperez@charterwest.com</a></p>
    <a href="{APPLY}" target="_blank" rel="noopener" class="btn btn-gold">{t('Apply / Pre-Qualify Online', 'Solicitar en línea')}</a>
    <p class="lender-fine">{t('Marcos Diaz and Keller Williams are not lenders. You are free to choose any lender. Loans offered by CharterWest Bank, NMLS #466077, Equal Housing Lender. Subject to credit approval.', 'Marcos Diaz y Keller Williams no son prestamistas. Usted puede escoger cualquier prestamista. Préstamos ofrecidos por CharterWest Bank, NMLS #466077, Prestamista de Igualdad de Vivienda. Sujeto a aprobación de crédito.')}</p>
  </div>
</div>'''
