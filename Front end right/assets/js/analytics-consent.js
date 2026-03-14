(function () {
  const measurementId = (window.GA_MEASUREMENT_ID || '').trim();
  const consentKey = 'otsiauto_analytics_consent';
  const loadedFlagKey = 'otsiauto_analytics_loaded';

  function hasValidMeasurementId() {
    return /^G-[A-Z0-9]+$/i.test(measurementId);
  }

  function trackEvent(eventName, params) {
    if (typeof window.gtag !== 'function') return;
    window.gtag('event', eventName, params || {});
  }

  function loadAnalytics() {
    if (!hasValidMeasurementId()) return;
    if (window[loadedFlagKey]) return;
    window[loadedFlagKey] = true;

    const script = document.createElement('script');
    script.async = true;
    script.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(measurementId);
    document.head.appendChild(script);

    window.dataLayer = window.dataLayer || [];
    window.gtag = function () {
      window.dataLayer.push(arguments);
    };

    window.gtag('js', new Date());
    window.gtag('config', measurementId, {
      anonymize_ip: true
    });
  }

  function removeBanner() {
    const el = document.getElementById('analytics-consent-banner');
    if (el) el.remove();
  }

  function saveConsent(value) {
    localStorage.setItem(consentKey, value);
    if (value === 'accepted') {
      loadAnalytics();
      trackEvent('consent_accepted', { source: 'banner' });
    }
    if (value === 'rejected') {
      trackEvent('consent_rejected', { source: 'banner' });
    }
    removeBanner();
  }

  function createBanner() {
    if (!hasValidMeasurementId()) return;
    if (document.getElementById('analytics-consent-banner')) return;

    const banner = document.createElement('div');
    banner.id = 'analytics-consent-banner';
    banner.style.position = 'fixed';
    banner.style.left = '16px';
    banner.style.right = '16px';
    banner.style.bottom = '16px';
    banner.style.zIndex = '99999';
    banner.style.background = '#ffffff';
    banner.style.border = '1px solid #d9d9d9';
    banner.style.borderRadius = '10px';
    banner.style.boxShadow = '0 6px 20px rgba(0,0,0,0.15)';
    banner.style.padding = '12px 14px';
    banner.style.fontFamily = 'inherit';
    banner.innerHTML = [
      '<div style="display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap;">',
      '<div style="color:#333;font-size:14px;line-height:1.4;max-width:820px;">',
      'Kasutame analüütikat, et mõõta külastusi ja parandada kasutajakogemust. Kas lubad analüütika küpsised?',
      '</div>',
      '<div style="display:flex;gap:8px;">',
      '<button id="analytics-reject-btn" type="button" style="border:1px solid #ccc;background:#fff;color:#333;padding:8px 12px;border-radius:8px;cursor:pointer;">Ei luba</button>',
      '<button id="analytics-accept-btn" type="button" style="border:1px solid #1f7a3a;background:#2ea44f;color:#fff;padding:8px 12px;border-radius:8px;cursor:pointer;">Luba analüütika</button>',
      '</div>',
      '</div>'
    ].join('');

    document.body.appendChild(banner);

    const acceptBtn = document.getElementById('analytics-accept-btn');
    const rejectBtn = document.getElementById('analytics-reject-btn');

    if (acceptBtn) {
      acceptBtn.addEventListener('click', function () {
        saveConsent('accepted');
      });
    }

    if (rejectBtn) {
      rejectBtn.addEventListener('click', function () {
        saveConsent('rejected');
      });
    }
  }

  function setupBasicEvents() {
    document.addEventListener('submit', function (event) {
      const form = event.target;
      if (!(form instanceof HTMLFormElement)) return;

      if (form.id === 'brand-search-form') {
        trackEvent('search_submit', { origin: 'landing' });
      } else if (form.closest('.filters-sidebar')) {
        trackEvent('search_submit', { origin: 'results_filters' });
      }
    });

    document.addEventListener('click', function (event) {
      const anchor = event.target && event.target.closest ? event.target.closest('a.share-btn') : null;
      if (!anchor) return;
      trackEvent('view_listing_click', {
        destination: anchor.href || ''
      });
    });
  }

  function init() {
    if (!hasValidMeasurementId()) return;

    const consent = localStorage.getItem(consentKey);
    if (consent === 'accepted') {
      loadAnalytics();
    } else if (!consent) {
      createBanner();
    }

    setupBasicEvents();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
