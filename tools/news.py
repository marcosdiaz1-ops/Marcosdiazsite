# Monthly market-update email signup band (EN/ES). Used by page() and the homepage.
NEWS_SHEET = 'https://script.google.com/macros/s/AKfycbw5PdoEEaGDAquTmKqO_1SkhtTaJG3G0584Xy4VIqG74FsaaH-tnxYpeIdrqTcCjZ0w/exec'

def news_band(es=False):
    t = (lambda e, s: s if es else e)
    return f'''<section class="news-band">
  <div class="wrap news-inner">
    <div>
      <p class="eyebrow light">{t('Free Monthly Update', 'Reporte mensual gratis')}</p>
      <h2>{t('Get the Sioux Falls market in your inbox.', 'Reciba el mercado de Sioux Falls en su correo.')}</h2>
      <p>{t('Once a month: prices, homes sold, and what it means for buyers and sellers. No spam, unsubscribe anytime.', 'Una vez al mes: precios, casas vendidas y lo que significa para compradores y vendedores. Sin spam, cancele cuando quiera.')}</p>
    </div>
    <form class="news-form" action="https://api.web3forms.com/submit" method="POST" data-sheet="{NEWS_SHEET}" novalidate>
      <input type="hidden" name="access_key" value="d0023d26-ed18-4970-8a35-c3de9e5f7e6c">
      <input type="hidden" name="subject" value="{t('Market update signup', 'Market update signup (ESPAÑOL)')}">
      <input type="hidden" name="from_name" value="Marcos Diaz Website">
      <input type="checkbox" name="botcheck" class="hidden" tabindex="-1" autocomplete="off">
      <label><span class="sr-only">{t('First name', 'Nombre')}</span><input type="text" name="Name" placeholder="{t('First name', 'Nombre')}" autocomplete="given-name" required></label>
      <label><span class="sr-only">{t('Email', 'Correo electrónico')}</span><input type="email" name="email" placeholder="{t('Email address', 'Correo electrónico')}" autocomplete="email" required></label>
      <button type="submit" class="btn btn-gold">{t('Sign Me Up', 'Suscribirme')}</button>
      <p class="news-msg" role="status"></p>
    </form>
  </div>
</section>
'''
