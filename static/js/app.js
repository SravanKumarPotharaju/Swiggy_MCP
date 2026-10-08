// SmartFlow Main UI Controller

let state = {
  cart: { items: [], pricing: null, item_count: 0 },
  instamartCart: { items: [], total_items: 0, total_amount: '₹0', bill_breakdown: null },
  activeCartType: 'food', // 'food' or 'instamart'
  defaultAddress: null,
  savedAddresses: [],
  activeRestaurant: { id: '288893', name: 'Meghana Foods' },
  activeOrder: null,
  menuItems: [],
  selectedDishForAddons: null,
  instamartProducts: [],
};

// Immediately restore persisted state from localStorage
try {
  const savedFoodCart = localStorage.getItem('smartflow_food_cart');
  if (savedFoodCart) state.cart = JSON.parse(savedFoodCart);
} catch (e) {}

try {
  const savedImCart = localStorage.getItem('smartflow_instamart_cart');
  if (savedImCart) state.instamartCart = JSON.parse(savedImCart);
} catch (e) {}

try {
  const savedActiveOrder = localStorage.getItem('smartflow_active_order');
  if (savedActiveOrder) state.activeOrder = JSON.parse(savedActiveOrder);
} catch (e) {}

function persistCarts() {
  try {
    if (state.cart) localStorage.setItem('smartflow_food_cart', JSON.stringify(state.cart));
    if (state.instamartCart) localStorage.setItem('smartflow_instamart_cart', JSON.stringify(state.instamartCart));
  } catch (e) {}
}

function persistActiveOrder() {
  try {
    if (state.activeOrder) {
      localStorage.setItem('smartflow_active_order', JSON.stringify(state.activeOrder));
    } else {
      localStorage.removeItem('smartflow_active_order');
    }
  } catch (e) {}
}

// --- RALLY UI HELPERS ---
const SVG_STROKE_ATTRS =
  'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"';

// Escape API and user strings before they are interpolated into HTML.
function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (ch) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]
  ));
}

// First human-readable message in an API envelope; FastAPI validation errors put an object in detail.
function apiErrorMessage(res, fallback) {
  const message = [res?.detail, res?.message].find((v) => typeof v === 'string' && v);
  return message || fallback;
}

// Icon from the inline sprite in index.html (symbol ids are "i-<name>").
function iconUse(name, extraClass = '') {
  return `<svg class="r-icon ${extraClass}" ${SVG_STROKE_ATTRS}><use href="#i-${name}"/></svg>`;
}

// Icon drawn from raw stroke path data, for glyphs the sprite does not have.
function iconPath(pathData, extraClass = '') {
  return `<svg class="r-icon ${extraClass}" ${SVG_STROKE_ATTRS}><path d="${pathData}"/></svg>`;
}

// Rally busy state (.r-btn.is-busy): label hidden, linear sweep shown. Ignores re-entry.
// Buttons without a __label/__amount child (bare text) fall back to disabled, since
// .is-busy only hides element children.
async function withBusy(btn, action) {
  if (!btn || btn.disabled || btn.classList.contains('is-busy')) return undefined;
  const useSweep = btn.querySelector('.r-btn__label, .r-btn__amount') !== null;
  if (useSweep) {
    btn.classList.add('is-busy');
    btn.setAttribute('aria-busy', 'true');
  } else {
    btn.disabled = true;
  }
  try {
    return await action();
  } finally {
    if (useSweep) {
      btn.classList.remove('is-busy');
      btn.removeAttribute('aria-busy');
    } else {
      btn.disabled = false;
    }
  }
}

// Writes the amount slot of a CTA button; leaves the label untouched. Empty when unknown.
function setButtonAmount(btn, amountText) {
  const slot = btn ? btn.querySelector('.r-btn__amount') : null;
  if (slot) slot.textContent = amountText || '';
}

// Rally empty state (.r-empty). actionsHtml is trusted markup built by the caller.
function emptyStateHtml(icon, title, text, actionsHtml = '') {
  return `
    <div class="r-empty">
      <div class="r-empty__icon">${iconUse(icon)}</div>
      <h3 class="r-empty__title">${escapeHtml(title)}</h3>
      <p class="r-empty__text">${escapeHtml(text)}</p>
      ${actionsHtml ? `<div class="r-empty__actions">${actionsHtml}</div>` : ''}
    </div>
  `;
}

// Clickable list row: button semantics plus Enter/Space activation.
function bindRowAction(row, handler) {
  row.addEventListener('click', handler);
  row.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handler(e);
    }
  });
}

// --- TOAST ---
const TOAST_DURATION_MS = 2400; // matches --sp-dur-toast
let toastTimer = null;

// Plain toast, or the Rally error variant (alert icon + message) with { error: true }.
function showToast(message, { error = false } = {}) {
  const toast = document.getElementById('toast');
  if (!toast) return;
  const text = String(message ?? '');
  toast.classList.toggle('r-toast--error', error);
  if (error) {
    toast.innerHTML = `${iconUse('alert', 'r-toast__icon')}<div class="r-toast__body"><p class="r-toast__title">${escapeHtml(text)}</p></div>`;
  } else {
    toast.textContent = text;
  }
  toast.classList.add('is-visible');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('is-visible'), TOAST_DURATION_MS);
}

// --- SHEETS (.r-sheet-layer) ---
const SHEET_DISMISS_DISTANCE_PX = 120;
const SHEET_DISMISS_VELOCITY_PX_PER_MS = 0.5;
const sheetOpeners = new WeakMap();

function syncBodyLock() {
  document.body.classList.toggle('r-lock', document.querySelector('.r-sheet-layer.is-open') !== null);
}

function resetSheetDrag(sheet) {
  ['transform', 'transition', 'animation'].forEach((prop) => sheet.style.removeProperty(prop));
}

function openSheet(layer, opener = document.activeElement) {
  // Already open (for example switching cart tabs): keep focus and the original opener
  if (!layer || layer.classList.contains('is-open')) return;
  const sheet = layer.querySelector('.r-sheet');
  sheetOpeners.set(layer, opener);
  if (sheet) resetSheetDrag(sheet);
  layer.classList.add('is-open');
  layer.setAttribute('aria-hidden', 'false');
  syncBodyLock();
  if (sheet) {
    sheet.setAttribute('tabindex', '-1');
    sheet.style.outline = 'none';
    sheet.focus({ preventScroll: true });
  }
}

function closeSheet(layer) {
  if (!layer) return;
  const sheet = layer.querySelector('.r-sheet');
  if (sheet) resetSheetDrag(sheet);
  layer.classList.remove('is-open');
  layer.setAttribute('aria-hidden', 'true');
  syncBodyLock();
  const opener = sheetOpeners.get(layer);
  sheetOpeners.delete(layer);
  if (opener && opener.isConnected && typeof opener.focus === 'function') {
    opener.focus({ preventScroll: true });
  }
}

// Drag the grabber or header down past 120px (or faster than .5px/ms) to dismiss.
function setupSheetDrag(layer) {
  const sheet = layer.querySelector('.r-sheet');
  const closeBtn = layer.querySelector('.r-sheet__close');
  if (!sheet || !closeBtn) return;
  const isSideDrawer = () =>
    sheet.classList.contains('r-sheet--drawer') && window.matchMedia('(min-width: 1024px)').matches;
  let dragging = false;
  let startY = 0;
  let startTime = 0;
  let offset = 0;

  const endDrag = (e) => {
    if (!dragging) return;
    dragging = false;
    const velocity = offset / Math.max(1, e.timeStamp - startTime);
    if (e.type !== 'pointercancel' && (offset > SHEET_DISMISS_DISTANCE_PX || velocity > SHEET_DISMISS_VELOCITY_PX_PER_MS)) {
      closeBtn.click();
    } else {
      sheet.style.transition = 'transform 200ms var(--sp-ease-standard)';
      sheet.style.transform = 'none';
    }
  };

  sheet.querySelectorAll('.r-sheet__grabber, .r-sheet__header').forEach((handle) => {
    handle.style.touchAction = 'none';
    handle.addEventListener('pointerdown', (e) => {
      if (e.target.closest('button') || isSideDrawer()) return;
      dragging = true;
      startY = e.clientY;
      startTime = e.timeStamp;
      offset = 0;
      handle.setPointerCapture(e.pointerId);
      sheet.style.animation = 'none';
      sheet.style.transition = 'none';
    });
    handle.addEventListener('pointermove', (e) => {
      if (!dragging) return;
      offset = Math.max(0, e.clientY - startY);
      sheet.style.transform = `translateY(${offset}px)`;
    });
    handle.addEventListener('pointerup', endDrag);
    handle.addEventListener('pointercancel', endDrag);
  });
}

// Scrim click and Escape press the topmost sheet's own close button, so each
// sheet keeps a single close path.
function setupSheets() {
  document.querySelectorAll('.r-sheet-layer').forEach(setupSheetDrag);
  document.addEventListener('click', (e) => {
    const scrim = e.target.closest?.('.r-scrim');
    if (scrim) scrim.closest('.r-sheet-layer')?.querySelector('.r-sheet__close')?.click();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    const open = document.querySelectorAll('.r-sheet-layer.is-open');
    open[open.length - 1]?.querySelector('.r-sheet__close')?.click();
  });
}

// --- INITIALIZATION ---
document.addEventListener('DOMContentLoaded', async () => {
  setupSheets();
  setupTabs();
  setupVoice();
  setupChat();
  setupInstamartTab();
  setupCartDrawer();
  setupModals();
  setupPhoneCallOverlay();
  setupSwiggyAuthButton();
  updateCartBadge();
  await loadInitialState();
  await checkSwiggyAuth();
});

function setSwiggyConnectedUI(connected = true) {
  const btn = document.getElementById('btn-swiggy-auth');
  const label = document.getElementById('swiggy-auth-label');
  if (btn) btn.classList.toggle('is-connected', connected);
  if (label) label.textContent = connected ? 'Swiggy connected' : 'Connect Swiggy';
  if (connected) {
    localStorage.setItem('swiggy_authenticated', 'true');
  } else {
    localStorage.removeItem('swiggy_authenticated');
  }
}

async function checkSwiggyAuth() {
  try {
    // Optimistic local hint while the status request is in flight
    if (localStorage.getItem('swiggy_authenticated') === 'true') {
      setSwiggyConnectedUI(true);
    }
    const res = await api.getAuthStatus();
    setSwiggyConnectedUI(Boolean(res && res.success && res.data && res.data.authenticated));
  } catch (e) {
    console.error('Error checking Swiggy auth:', e);
  }
}

function setupSwiggyAuthButton() {
  const btn = document.getElementById('btn-swiggy-auth');
  const modal = document.getElementById('swiggy-modal');
  const btnClose = document.getElementById('btn-close-swiggy');
  const stepConnected = document.getElementById('swiggy-step-connected');
  const stepPhone = document.getElementById('swiggy-step-phone');
  const stepOtp = document.getElementById('swiggy-step-otp');
  const phoneInput = document.getElementById('swiggy-phone-input');
  const otpInput = document.getElementById('swiggy-otp-input');
  const btnSendOtp = document.getElementById('btn-swiggy-send-otp');
  const btnVerifyOtp = document.getElementById('btn-swiggy-verify-otp');
  const btnResendOtp = document.getElementById('btn-swiggy-resend-otp');
  const btnChangePhone = document.getElementById('btn-swiggy-change-phone');
  const btnBrowserFlow = document.getElementById('btn-swiggy-browser-flow');
  const btnQuickConnect = document.getElementById('btn-swiggy-quick-connect');
  const btnDisconnect = document.getElementById('btn-swiggy-disconnect');
  const btnRelogin = document.getElementById('btn-swiggy-relogin');
  const otpMsgText = document.querySelector('#swiggy-otp-sent-msg .r-banner__text');
  const otpBoxes = modal ? modal.querySelectorAll('.r-otp__box') : [];

  if (!btn || !modal) return;

  const showStep = (step) => {
    [stepConnected, stepPhone, stepOtp].forEach((el) => {
      if (el) el.style.display = el === step ? 'block' : 'none';
    });
  };

  // Mirror the real input into the six visual boxes; the next empty box is active while focused.
  const mirrorOtp = () => {
    if (!otpInput) return;
    const digits = otpInput.value;
    const focused = document.activeElement === otpInput;
    const activeIndex = Math.min(digits.length, otpBoxes.length - 1);
    otpBoxes.forEach((box, i) => {
      box.textContent = digits[i] || '';
      box.classList.toggle('is-filled', i < digits.length);
      box.classList.toggle('is-active', focused && i === activeIndex);
    });
  };

  const resetOtp = () => {
    if (!otpInput) return;
    otpInput.value = '';
    mirrorOtp();
  };

  const openModal = () => {
    openSheet(modal, btn);
    const isConn = localStorage.getItem('swiggy_authenticated') === 'true';
    if (isConn && stepConnected) {
      showStep(stepConnected);
    } else {
      showStep(stepPhone);
      resetOtp();
      if (phoneInput) phoneInput.focus();
    }
  };

  const closeModal = () => closeSheet(modal);

  btn.addEventListener('click', openModal);
  if (btnClose) btnClose.addEventListener('click', closeModal);

  if (otpInput) {
    otpInput.addEventListener('input', () => {
      otpInput.value = otpInput.value.replace(/\D/g, '');
      mirrorOtp();
    });
    otpInput.addEventListener('focus', mirrorOtp);
    otpInput.addEventListener('blur', mirrorOtp);
  }

  // 1-Click Instant Connect: the backend returns the Swiggy authorization URL; only
  // the authenticated callback may mark the account connected.
  if (btnQuickConnect) {
    btnQuickConnect.addEventListener('click', () => withBusy(btnQuickConnect, async () => {
      try {
        const res = await api.directConnectSwiggy();
        if (res?.success && res.data?.authorization_url) {
          window.location.assign(res.data.authorization_url);
        } else {
          showToast(apiErrorMessage(res, 'Could not start Swiggy connect. Try the OTP sign-in.'), { error: true });
        }
      } catch (err) {
        console.warn('Direct connect failed:', err);
        showToast('Network error while connecting to Swiggy.', { error: true });
      }
    }));
  }

  // Disconnect
  if (btnDisconnect) {
    btnDisconnect.addEventListener('click', async () => {
      try {
        await api.logoutSwiggy();
      } catch (err) {
        console.warn('Swiggy logout request failed:', err);
      }
      setSwiggyConnectedUI(false);
      closeModal();
      showToast('Swiggy account disconnected.');
    });
  }

  // Switch Number
  if (btnRelogin) btnRelogin.addEventListener('click', () => showStep(stepPhone));

  // Send OTP (also used by Resend; the busy state sits on whichever button was pressed)
  const handleSendOtp = (trigger) => withBusy(trigger, async () => {
    const phone = phoneInput ? phoneInput.value.trim() : '';
    if (!phone || phone.length < 10) {
      showToast('Enter a valid 10-digit mobile number.', { error: true });
      return;
    }
    try {
      const res = await api.sendSwiggyOtp(phone);
      if (res && res.success) {
        showStep(stepOtp);
        if (otpMsgText) otpMsgText.textContent = `OTP sent to +91 ${phone} via Swiggy.`;
        showToast(`OTP sent to +91 ${phone}. Check your SMS.`);
        resetOtp();
        if (otpInput) otpInput.focus();
      } else {
        showToast(apiErrorMessage(res, 'Failed to send OTP.'), { error: true });
      }
    } catch (err) {
      showToast('Network error while sending OTP.', { error: true });
    }
  });

  if (btnSendOtp) btnSendOtp.addEventListener('click', () => handleSendOtp(btnSendOtp));
  if (btnResendOtp) btnResendOtp.addEventListener('click', () => handleSendOtp(btnResendOtp));
  if (btnChangePhone) btnChangePhone.addEventListener('click', () => showStep(stepPhone));

  // Verify OTP: only a successful backend response connects the account.
  const handleVerifyOtp = () => withBusy(btnVerifyOtp, async () => {
    const phone = phoneInput ? phoneInput.value.trim() : '';
    const otp = otpInput ? otpInput.value.trim() : '';
    if (!otp || otp.length !== 6) {
      showToast('Enter the full 6-digit OTP.', { error: true });
      return;
    }
    try {
      const res = await api.verifySwiggyOtp(phone, otp);
      if (res && res.success) {
        setSwiggyConnectedUI(true);
        closeModal();
        showToast('Swiggy connected. Cart and live orders synced.');
      } else {
        showToast(apiErrorMessage(res, 'Invalid OTP. Try again.'), { error: true });
      }
    } catch (err) {
      showToast('Verification failed. Check your connection and try again.', { error: true });
    }
  });

  if (btnVerifyOtp) btnVerifyOtp.addEventListener('click', handleVerifyOtp);
  if (otpInput) {
    otpInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') handleVerifyOtp();
    });
  }

  // Browser redirect fallback
  if (btnBrowserFlow) {
    btnBrowserFlow.addEventListener('click', () => withBusy(btnBrowserFlow, async () => {
      try {
        const res = await api.loginSwiggy();
        if (res && res.success && res.data && res.data.authorization_url) {
          closeModal();
          window.open(res.data.authorization_url, '_blank');
          showToast('Swiggy login opened in a new tab. Enter the OTP and allow access.');
        } else {
          showToast(apiErrorMessage(res, 'Could not start the Swiggy browser login.'), { error: true });
        }
      } catch (err) {
        showToast('Could not initiate Swiggy browser session.', { error: true });
      }
    }));
  }

  // Listen for popup callback message (same-origin only)
  window.addEventListener('message', (event) => {
    if (event.origin !== window.location.origin) return;
    if (event.data && event.data.type === 'SWIGGY_AUTH_SUCCESS') {
      setSwiggyConnectedUI(true);
      closeModal();
      showToast('Swiggy connected. Carts and addresses synced.');
    }
  });
}

async function loadInitialState() {
  updateCartBadge();
  try {
    const res = await api.getInitialState();
    if (res.success && res.data) {
      state.defaultAddress = res.data.default_address;
      state.savedAddresses = res.data.all_addresses || [];
      if (res.data.cart) {
        state.cart = res.data.cart;
      }
      if (res.data.instamart_cart) {
        state.instamartCart = res.data.instamart_cart;
      }
      persistCarts();

      // Update location pill
      if (state.defaultAddress) {
        updateHeaderLocation(state.defaultAddress, false);
      }
      renderAddressModalList();

      // Update Cart UI
      updateCartBadge();

      // Render Menu
      if (res.data.featured_restaurant) {
        renderMenuCategories(res.data.featured_restaurant.categories);
      }

      // Pre-load default Instamart grocery products
      loadInstamartProducts('milk');

      // Frequent Suggestions: ONLY show if ordered > 3 times
      await updateFrequentOrderSuggestions();

      // Load Past Orders History immediately on page load so it's always ready and visible
      await loadPastOrders();

      // Check if an active order exists to sync tracking
      if (state.activeOrder && state.activeOrder.order_id) {
        syncTrackingTabState();
      }
    }
  } catch (e) {
    console.error('Error loading initial state:', e);
    showToast('Could not connect to the backend server.', { error: true });
  }
}

// --- ADDRESS MANAGEMENT ---
function updateHeaderLocation(address, pulse = true) {
  if (!address) return;
  state.defaultAddress = address;

  const tag = address.addressTag || address.label || address.addressCategory || address.annotation || 'Delivery Location';
  const fullAddr = address.addressLine || address.display_text || address.fullAddress || address.locality || '';
  const displayLine = fullAddr ? `(${fullAddr.slice(0, 36)}${fullAddr.length > 36 ? '...' : ''})` : '';

  const pill = document.getElementById('header-location');
  if (pill) {
    pill.innerHTML = `
      ${iconUse('pin', 'r-icon--sm')}
      <span>Deliver to <strong>${escapeHtml(tag)}</strong> ${escapeHtml(displayLine)}</span>
    `;
    if (pulse) {
      pill.classList.remove('r-scale-in');
      void pill.offsetWidth; // Force CSS reflow so the animation restarts
      pill.classList.add('r-scale-in');
      showToast(`Deliver to ${tag}`);
    }
  }

  // Also update active state in address modal list if rendered
  renderAddressModalList();
}

function renderAddressModalList() {
  const listEl = document.getElementById('address-list');
  if (!listEl) return;

  const addresses = state.savedAddresses || [];
  if (addresses.length === 0) {
    listEl.innerHTML = `<li>${emptyStateHtml('pin', 'No saved addresses.', 'Your saved Swiggy addresses will show up here.')}</li>`;
    return;
  }

  const currentTag = state.defaultAddress ? (state.defaultAddress.addressTag || state.defaultAddress.label || '') : '';
  const currentId = state.defaultAddress ? (state.defaultAddress.id || '') : '';

  listEl.innerHTML = addresses
    .map((addr, idx) => {
      const tag = addr.addressTag || addr.label || addr.addressCategory || 'Address';
      const line = addr.addressLine || addr.display_text || addr.fullAddress || '';
      const locality = addr.locality || addr.city || '';
      const isActive = (currentId && addr.id === currentId) || (currentTag && tag.toLowerCase() === currentTag.toLowerCase());

      return `
        <li class="r-row r-row--interactive${isActive ? ' r-row--selected' : ''}" role="button" tabindex="0" data-index="${idx}"${isActive ? ' aria-current="true"' : ''}>
          <span class="r-row__lead"><span class="r-avatar">${iconUse('pin')}</span></span>
          <div class="r-row__main">
            <p class="r-row__title">${escapeHtml(tag)}</p>
            <p class="r-row__sub">${escapeHtml(line + (locality ? ', ' + locality : ''))}</p>
          </div>
          <span class="r-row__trail"><span class="r-check"><span class="r-check__box"></span></span></span>
        </li>
      `;
    })
    .join('');

  listEl.querySelectorAll('.r-row').forEach((row) => {
    bindRowAction(row, async () => {
      const selected = addresses[Number(row.dataset.index)];
      if (!selected) return;
      updateHeaderLocation(selected, true);
      try {
        await api.setActiveAddress(selected);
      } catch (err) {
        console.error('Failed to set active address:', err);
        showToast('Could not save the delivery address.', { error: true });
      }
      closeSheet(document.getElementById('address-modal'));
    });
  });
}

// --- FREQUENT ORDER SUGGESTIONS CONTROLLER ---
// Rule: Suggestions ONLY appear if ordered more than 3 times (> 3). Otherwise do not show!
async function updateFrequentOrderSuggestions() {
  const container = document.getElementById('frequent-suggestions-container');
  const restBadge = document.getElementById('restaurant-frequent-badge');
  const imBadge = document.getElementById('im-hero-badge');

  if (container) container.innerHTML = '';
  if (restBadge) restBadge.style.display = 'none';

  try {
    const res = await api.getFrequentOrders();
    const frequentRests = (res.success && res.data && res.data.frequent_restaurants) ? res.data.frequent_restaurants : [];
    const instamartData = (res.success && res.data && res.data.instamart) ? res.data.instamart : {};

    // Local storage overrides or sync if customer ordered in this session
    const localCounts = JSON.parse(localStorage.getItem('smartflow_order_counts') || '{}');

    // Aggregate counts
    const rawBackendCounts = (res.success && res.data && res.data.counts_by_restaurant) ? res.data.counts_by_restaurant : {};
    const countsMap = {};
    Object.keys(rawBackendCounts).forEach((k) => {
      countsMap[k] = rawBackendCounts[k];
    });
    frequentRests.forEach((r) => {
      countsMap[r.restaurant_name] = Math.max(countsMap[r.restaurant_name] || 0, r.order_count);
    });
    Object.keys(localCounts).forEach((k) => {
      countsMap[k] = Math.max(countsMap[k] || 0, localCounts[k]);
    });

    // 0. RESTAURANT NAVIGATION TAB PILL
    // Rule: Pill is shown ONLY if ordered MORE THAN 2 TIMES (> 2). Otherwise do not show!
    const navPillsContainer = document.getElementById('restaurant-nav-pills');
    if (navPillsContainer) {
      navPillsContainer.innerHTML = '';
      const qualifiedForNavTab = Object.keys(countsMap)
        .filter((name) => name.toLowerCase() !== 'instamart' && countsMap[name] > 2)
        .map((name) => ({ name, count: countsMap[name] }))
        .sort((a, b) => b.count - a.count);

      if (qualifiedForNavTab.length > 0) {
        const activeName = (state.activeRestaurant ? state.activeRestaurant.name : '').toLowerCase();
        qualifiedForNavTab.forEach((r) => {
          const isCurrent = r.name.toLowerCase() === activeName;
          const chip = document.createElement('button');
          chip.type = 'button';
          chip.className = `r-chip${isCurrent ? ' r-chip--selected' : ''}`;
          chip.setAttribute('role', 'tab');
          chip.setAttribute('aria-selected', String(isCurrent));
          chip.textContent = r.name;
          chip.addEventListener('click', () => switchTabById('pane-menu'));
          navPillsContainer.appendChild(chip);
        });
      }
    }

    // STRICT THRESHOLD FOR SUGGESTION CHIPS: Order count must be MORE THAN 3 (> 3)
    const qualifiedRests = Object.keys(countsMap)
      .filter((name) => name !== 'instamart' && countsMap[name] > 3)
      .map((name) => ({ name, count: countsMap[name] }))
      .sort((a, b) => b.count - a.count);

    const imCount = Math.max(instamartData.order_count || 0, localCounts['instamart'] || 0);

    // 1. Restaurant suggestion: ONLY show if > 3 times
    if (qualifiedRests.length > 0 && container) {
      qualifiedRests.forEach((r) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'r-chip';
        btn.dataset.prompt = `Order from ${r.name}`;
        btn.textContent = `${r.name} (ordered ${r.count} times)`;
        btn.addEventListener('click', () => {
          const input = document.getElementById('chat-input');
          if (input) {
            input.value = btn.dataset.prompt;
            document.getElementById('btn-send').click();
          }
        });
        container.appendChild(btn);
      });

      // Update active restaurant meta badge if currently showing that restaurant
      const activeRestName = state.activeRestaurant ? state.activeRestaurant.name : 'Meghana Foods';
      const match = qualifiedRests.find((r) => r.name.toLowerCase() === activeRestName.toLowerCase());
      if (match && restBadge) {
        restBadge.textContent = `Ordered ${match.count} times`;
        restBadge.style.display = '';
      }
    } else {
      if (restBadge) restBadge.style.display = 'none';
    }

    // 2. Instamart suggestion: ONLY show if > 3 times
    if (imCount > 3 && container) {
      const imBtn = document.createElement('button');
      imBtn.type = 'button';
      imBtn.className = 'r-chip';
      imBtn.dataset.prompt = 'Open Instamart groceries';
      imBtn.textContent = `Instamart (ordered ${imCount} times)`;
      imBtn.addEventListener('click', () => {
        openCartDrawerWithType('instamart');
      });
      container.appendChild(imBtn);

      if (imBadge) {
        imBadge.textContent = `Instamart, ordered ${imCount} times`;
      }
    } else {
      if (imBadge) {
        imBadge.textContent = 'Instamart, 10 to 15 min';
      }
    }
  } catch (err) {
    console.warn('Frequent order suggestions check:', err);
  }
}

function recordCompletedOrder(restaurantName, isInstamart = false) {
  try {
    const counts = JSON.parse(localStorage.getItem('smartflow_order_counts') || '{}');
    if (isInstamart) {
      counts['instamart'] = (counts['instamart'] || 0) + 1;
    } else if (restaurantName) {
      counts[restaurantName] = (counts[restaurantName] || 0) + 1;
    }
    localStorage.setItem('smartflow_order_counts', JSON.stringify(counts));
    updateFrequentOrderSuggestions();
  } catch (e) {
    console.warn('Could not record order count:', e);
  }
}

// --- TABS & NAVIGATION HELPERS ---
function switchTabById(tabId) {
  document.querySelectorAll('.r-tabbar__tab').forEach((t) => {
    const isTarget = t.dataset.target === tabId;
    t.classList.toggle('is-active', isTarget);
    t.setAttribute('aria-selected', String(isTarget));
    if (isTarget) {
      t.setAttribute('aria-current', 'page');
    } else {
      t.removeAttribute('aria-current');
    }
  });
  document.querySelectorAll('.r-screen').forEach((p) => {
    const isTarget = p.id === tabId;
    p.classList.toggle('is-active', isTarget);
    p.hidden = !isTarget;
  });

  const targetPane = document.getElementById(tabId);
  if (targetPane) {
    targetPane.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  if (tabId === 'pane-tracking') {
    syncTrackingTabState();
  }
}

function setChipSelected(btn, selected) {
  if (!btn) return;
  btn.classList.toggle('r-chip--selected', selected);
  btn.setAttribute('aria-selected', String(selected));
}

function openCartDrawerWithType(cartType = 'food') {
  if (cartType === 'instamart' || cartType === 'food') {
    state.activeCartType = cartType;
    setChipSelected(document.getElementById('btn-switch-food'), cartType === 'food');
    setChipSelected(document.getElementById('btn-switch-im'), cartType === 'instamart');
  }

  renderCartDrawerItems();
  openSheet(document.getElementById('cart-drawer-overlay'));
}

function closeCartDrawer() {
  closeSheet(document.getElementById('cart-drawer-overlay'));
}

function handleUIAction(uiAction) {
  if (!uiAction) return;
  const action = (uiAction.action || '').toLowerCase();
  const cartType = (uiAction.cart_type || '').toLowerCase();

  console.log('[UI Action]', action, cartType);

  if (uiAction.order) {
    state.activeOrder = uiAction.order;
  }

  if (action === 'open_cart' || action === 'food_cart' || action === 'instamart_cart') {
    const targetType = cartType || (action === 'instamart_cart' ? 'instamart' : 'food');
    openCartDrawerWithType(targetType);
  } else if (action === 'close_cart') {
    closeCartDrawer();
  } else if (action === 'open_payment' || action === 'payment_checkout' || action === 'checkout') {
    closeCartDrawer();
    openPaymentModal();
  } else if (action === 'switch_tab') {
    if (uiAction.tab) switchTabById(uiAction.tab);
  } else if (action === 'menu' || action === 'food_menu') {
    switchTabById('pane-menu');
  } else if (action === 'instamart_groceries' || action === 'instamart') {
    switchTabById('pane-instamart');
  } else if (action === 'tracking') {
    switchTabById('pane-tracking');
  }
}

function checkClientVoiceTriggers(text) {
  if (!text) return false;
  const clean = text.trim().toLowerCase().replace(/[^\w\s]/g, ' ');

  // 1. Instamart Cart Navigation
  if (
    /\b(instamart\s*cart|grocery\s*cart|groceries\s*cart|im\s*cart)\b/.test(clean) ||
    /\b(go\s*to|open|show|view|switch\s*to|navigate\s*to)\s+(the\s+)?(instamart|grocery|groceries)\s*cart\b/.test(clean)
  ) {
    openCartDrawerWithType('instamart');
    showToast('Switched to Instamart cart');
    return true;
  }

  // 2. Food Cart Navigation
  if (
    /\b(food\s*cart|restaurant\s*cart|meghana\s*cart)\b/.test(clean) ||
    /\b(go\s*to|open|show|view|switch\s*to|navigate\s*to)\s+(the\s+)?food\s*cart\b/.test(clean)
  ) {
    openCartDrawerWithType('food');
    showToast('Switched to food cart');
    return true;
  }

  // 3. Open Generic Cart
  if (/^\s*(open|show|view|navigate\s*to|go\s*to)?\s*(my\s+)?cart\s*$/.test(clean)) {
    openCartDrawerWithType(state.activeCartType || 'food');
    showToast('Opened cart');
    return true;
  }

  // 4. Close Cart
  if (/\b(close|hide|dismiss)\s*(the\s*)?cart\b/.test(clean)) {
    closeCartDrawer();
    showToast('Closed cart');
    return true;
  }

  // 5. Payment or Checkout Navigation
  if (
    /\b(checkout|payment|pay\s*now|proceed\s*to\s*pay|proceed\s*to\s*checkout|open\s*payment|open\s*checkout|upi\s*payment|pay\s*food|pay\s*instamart)\b/.test(clean) ||
    clean === 'pay' || clean === 'pay now'
  ) {
    closeCartDrawer();
    openPaymentModal();
    return true;
  }

  // 6. Tab Navigation: Menu
  if (/\b(show\s*menu|open\s*menu|food\s*menu|meghana\s*menu|browse\s*menu|food\s*tab)\b/.test(clean) || clean === 'menu') {
    switchTabById('pane-menu');
    showToast('Switched to Meghana menu');
    return true;
  }

  // 7. Tab Navigation: Instamart Groceries
  if (/\b(open\s*instamart|show\s*instamart|instamart\s*tab|browse\s*groceries|grocery\s*tab|show\s*groceries)\b/.test(clean) || clean === 'instamart' || clean === 'groceries') {
    switchTabById('pane-instamart');
    showToast('Switched to Instamart groceries');
    return true;
  }

  // 8. Tab Navigation: Live Tracking
  if (
    /\b(tracking\s*tab|open\s*tracking|show\s*tracking|go\s*to\s*tracking|navigate\s*to\s*tracking|view\s*tracking|switch\s*to\s*tracking|track\s*order|live\s*tracking|where\s*is\s*my\s*(order|food)|track\s*status)\b/.test(clean) ||
    clean === 'tracking' ||
    clean === 'tracking tab' ||
    clean === 'open tracking' ||
    clean === 'track'
  ) {
    switchTabById('pane-tracking');
    showToast('Switched to live tracking');
    return true;
  }

  // 9. Clear Carts
  if (/\b(clear|empty)\s*(the\s*)?(food|restaurant)\s*cart\b/.test(clean)) {
    showToast('Clearing Food Cart...');
    api.clearCart().then(async () => {
      await refreshCart();
      openCartDrawerWithType('food');
      showToast('Food cart cleared');
    }).catch(() => showToast('Could not clear the food cart.', { error: true }));
    return true;
  }

  if (/\b(clear|empty)\s*(the\s*)?(instamart|grocery|groceries)\s*cart\b/.test(clean)) {
    showToast('Clearing Instamart Cart...');
    api.clearInstamartCart().then(async () => {
      await refreshInstamartCart();
      openCartDrawerWithType('instamart');
      showToast('Instamart cart cleared');
    }).catch(() => showToast('Could not clear the Instamart cart.', { error: true }));
    return true;
  }

  return false;
}

// --- TABS CONTROLLER ---
function setupTabs() {
  document.querySelectorAll('.r-tabbar__tab').forEach((tab) => {
    tab.addEventListener('click', () => switchTabById(tab.dataset.target));
  });
}

// --- VOICE ASSISTANT ---
let voice = null;
const MIC_IDLE_TEXT = 'Tap the mic to speak. Say "exit" to stop.';

function setupVoice() {
  const composer = document.querySelector('.r-composer');
  const micBtn = document.getElementById('mic-btn');
  const micStatus = document.getElementById('mic-status');

  const setListeningUI = (listening) => {
    if (composer) composer.classList.toggle('is-listening', listening);
    micBtn.setAttribute('aria-pressed', String(listening));
  };

  voice = new VoiceAssistant(
    // 1. On transcript
    async (transcript) => {
      micStatus.textContent = `"${transcript}"`;
      await sendAgentMessage(transcript);
      if (voice.keepListening) {
        micStatus.textContent = 'Listening. Speak again or say "exit" to stop.';
      }
    },
    // 2. On state change
    (isListening) => {
      setListeningUI(isListening);
      micStatus.textContent = isListening ? 'Listening. Speak freely, or say "exit" to stop.' : MIC_IDLE_TEXT;
    },
    // 3. On Exit keyword
    (exitTranscript) => {
      setListeningUI(false);
      micStatus.textContent = 'Voice session ended. Tap the mic to speak again.';
      addChatMessage('user', exitTranscript);
      addChatMessage('bot', 'Voice session ended. You can speak again anytime by tapping the mic, or type below.');
      showToast('Voice session ended');
    }
  );

  micBtn.addEventListener('click', () => {
    if (!voice.recognition) {
      showToast('Voice input is not supported in this browser. Type your order instead.', { error: true });
      return;
    }
    voice.toggleListening();
  });

  // Call my phone button: the call sheet is shown only once the backend confirms the
  // call, using the number it dialled.
  const callBtn = document.getElementById('btn-call-phone');
  if (callBtn) {
    callBtn.addEventListener('click', () => withBusy(callBtn, async () => {
      try {
        const res = await api.triggerAutomatedCall();
        if (res && res.success) {
          showIncomingCallModal('SmartFlow AI Concierge', res.data?.to || '');
        } else {
          showToast(apiErrorMessage(res, 'Could not place the call.'), { error: true });
        }
      } catch (err) {
        console.warn('Automated call failed:', err);
        showToast('Could not place the call. Check your connection.', { error: true });
      }
    }));
  }
}

// --- CHAT SYSTEM ---
// Sends one user message through the agent and applies the reply to the UI.
// Shared by typed input, quick chips and voice transcripts.
async function sendAgentMessage(text) {
  // Zero-latency client trigger check for navigation and checkout phrases
  checkClientVoiceTriggers(text);

  addChatMessage('user', text);
  showTypingIndicator();
  let res;
  try {
    res = await api.sendChatMessage(text);
  } catch (err) {
    console.error('Chat request failed:', err);
    showToast('Could not reach SmartFlow. Check your connection.', { error: true });
    return;
  } finally {
    removeTypingIndicator();
  }

  if (!(res && res.success && res.data)) {
    showToast(apiErrorMessage(res, 'SmartFlow could not process that message.'), { error: true });
    return;
  }

  addChatMessage('bot', res.data.reply);
  if (res.data.updated_address) {
    updateHeaderLocation(res.data.updated_address, true);
  }
  if (res.data.ui_action) {
    handleUIAction(res.data.ui_action);
  } else if (res.data.cart_type === 'instamart') {
    openCartDrawerWithType('instamart');
  } else if (res.data.cart_type === 'food') {
    openCartDrawerWithType('food');
  }
  // Refresh both carts
  await Promise.all([refreshCart(), refreshInstamartCart()]);
  if (res.data.order && res.data.order.open_payment_modal) {
    state.activeOrder = res.data.order;
    closeCartDrawer();
    displayPaymentQR(res.data.order);
  }
}

function setupChat() {
  const input = document.getElementById('chat-input');
  const sendBtn = document.getElementById('btn-send');
  const composer = document.querySelector('.r-composer');

  // The send button replaces the mic while the field has text
  const syncComposerText = () => composer.classList.toggle('has-text', input.value.trim().length > 0);

  const handleSend = async () => {
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    syncComposerText();
    await sendAgentMessage(text);
  };

  sendBtn.addEventListener('click', handleSend);
  input.addEventListener('input', syncComposerText);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.isComposing) handleSend();
  });

  // Quick chips (frequent-order chips are created later and bind their own handlers)
  document.querySelectorAll('#quick-action-chips > .r-chip[data-prompt]').forEach((chip) => {
    chip.addEventListener('click', () => sendAgentMessage(chip.dataset.prompt));
  });
}

function addChatMessage(role, text) {
  const container = document.getElementById('chat-messages');
  const isUser = role === 'user';
  const msgEl = document.createElement('div');
  msgEl.className = `r-msg ${isUser ? 'r-msg--user' : 'r-msg--agent'}`;

  const body = text || '';
  // Escape first, then format line breaks, bold and italic
  const formattedText = escapeHtml(body)
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br/>');

  // Interactive quick links for agent replies
  const quickLinks = [];
  if (!isUser) {
    if (body.includes('Live Map Tracking') || body.includes('Live GPS Tracking')) {
      quickLinks.push({ tab: 'pane-tracking', label: 'Open live tracking' });
    }
    if (body.includes('No Active Deliveries')) {
      quickLinks.push({ tab: 'pane-menu', label: 'Browse menu' }, { tab: 'pane-instamart', label: 'Groceries' });
    }
  }

  const actionsHtml = quickLinks.length
    ? `<div class="r-msg__actions">${quickLinks
        .map((link) => `<button type="button" class="r-chip r-chip--outline" data-tab="${link.tab}">${escapeHtml(link.label)}</button>`)
        .join('')}</div>`
    : '';

  msgEl.innerHTML = `<div class="r-msg__bubble">${formattedText}${actionsHtml}</div>`;
  msgEl.querySelectorAll('[data-tab]').forEach((chip) => {
    chip.addEventListener('click', () => switchTabById(chip.dataset.tab));
  });
  container.appendChild(msgEl);
  // The page scrolls (not the thread); bring the end of the thread, with its composer clearance, into view
  container.scrollIntoView({ block: 'end', behavior: 'smooth' });
}

function showTypingIndicator() {
  const container = document.getElementById('chat-messages');
  const typing = document.createElement('div');
  typing.id = 'typing-indicator';
  typing.className = 'r-msg r-msg--agent';
  typing.innerHTML = `
    <div class="r-typing" role="status">
      <span class="r-visually-hidden">SmartFlow is thinking</span>
      <span class="r-typing__dot"></span>
      <span class="r-typing__dot"></span>
      <span class="r-typing__dot"></span>
    </div>
  `;
  container.appendChild(typing);
  container.scrollIntoView({ block: 'end', behavior: 'smooth' });
}

function removeTypingIndicator() {
  const el = document.getElementById('typing-indicator');
  if (el) el.remove();
}

// --- MENU & ADD-ONS ---
function renderMenuCategories(categories) {
  const filterContainer = document.getElementById('category-filters');
  const gridContainer = document.getElementById('menu-grid');
  filterContainer.innerHTML = '';
  gridContainer.innerHTML = '';

  let allDishes = [];

  categories.forEach((cat, idx) => {
    // Add category chip
    const pill = document.createElement('button');
    pill.type = 'button';
    pill.className = 'r-chip';
    pill.setAttribute('role', 'tab');
    pill.textContent = `${cat.title} (${cat.items.length})`;
    setChipSelected(pill, idx === 0);
    pill.addEventListener('click', () => {
      filterContainer.querySelectorAll('.r-chip').forEach((p) => setChipSelected(p, p === pill));
      renderDishes(cat.items);
    });
    filterContainer.appendChild(pill);

    cat.items.forEach((item) => {
      item.category = cat.title;
      allDishes.push(item);
    });
  });

  state.menuItems = allDishes;
  if (categories.length > 0) {
    renderDishes(categories[0].items);
  }
}

function renderDishes(items) {
  const gridContainer = document.getElementById('menu-grid');
  gridContainer.innerHTML = '';

  items.forEach((item) => {
    const card = document.createElement('article');
    card.className = 'r-dish r-card';

    const unavailable = item.in_stock === false;
    const vegClass = item.is_veg ? 'r-dish__veg--veg' : 'r-dish__veg--nonveg';
    const vegLabel = item.is_veg ? 'Vegetarian' : 'Non-vegetarian';
    const media = item.image_url
      ? `<img class="r-dish__img" src="${escapeHtml(item.image_url)}" alt="${escapeHtml(item.name)}" loading="lazy" />`
      : '<span class="r-dish__img" aria-hidden="true"></span>';
    const addLabel = unavailable ? '' : ` aria-label="Add ${escapeHtml(item.name)}"`;

    card.innerHTML = `
      <div class="r-dish__body">
        <span class="r-dish__veg ${vegClass}" role="img" aria-label="${vegLabel}"></span>
        <h3 class="r-dish__name">${escapeHtml(item.name)}</h3>
        <p class="r-dish__price">₹${escapeHtml(item.price)}</p>
        ${item.description ? `<p class="r-dish__desc">${escapeHtml(item.description)}</p>` : ''}
      </div>
      <div class="r-dish__media">
        ${media}
        <div class="r-dish__action">
          <button type="button" class="r-btn r-btn--secondary r-btn--sm r-btn--pill"${addLabel}${unavailable ? ' disabled' : ''}>${unavailable ? 'Unavailable' : 'Add'}</button>
        </div>
      </div>
    `;

    // Add button handler
    card.querySelector('.r-dish__action button').addEventListener('click', () => {
      handleDishAddClick(item);
    });

    gridContainer.appendChild(card);
  });
}

// Add dish or open add-ons modal
function handleDishAddClick(dish) {
  // Check if dish has add-on options (e.g. Biryanis)
  if (dish.has_addons || dish.name.toLowerCase().includes('biryani')) {
    openAddonsModal(dish);
  } else {
    // Add directly to cart
    addDishToCart(dish.id, 1);
  }
}

async function addDishToCart(itemId, quantity = 1) {
  showToast('Adding item to Swiggy cart...');
  try {
    const res = await api.updateCart([{ menu_item_id: String(itemId), quantity: quantity }]);
    if (res.success) {
      state.cart = res.data;
      persistCarts();
      updateCartBadge();
      renderCartDrawerItems();
      showToast('Added to cart. Total: ₹' + (state.cart.pricing ? state.cart.pricing.to_pay : ''));
    } else {
      showToast(apiErrorMessage(res, 'Could not add the item to your cart.'), { error: true });
    }
  } catch (e) {
    showToast('Error adding to cart.', { error: true });
  }
}

// Addons Modal
function openAddonsModal(dish) {
  state.selectedDishForAddons = dish;
  const modal = document.getElementById('addons-modal');
  document.getElementById('addon-dish-name').textContent = dish.name;
  document.getElementById('addon-base-price').textContent = `Base: ₹${dish.price}`;

  // Reset checkboxes
  modal.querySelectorAll('input[type="checkbox"]').forEach((cb) => (cb.checked = false));
  updateAddonTotal();

  openSheet(modal);
}

function updateAddonTotal() {
  const modal = document.getElementById('addons-modal');
  let total = state.selectedDishForAddons ? state.selectedDishForAddons.price : 0;
  modal.querySelectorAll('input[type="checkbox"]:checked').forEach((cb) => {
    total += parseFloat(cb.dataset.price || 0);
  });
  setButtonAmount(document.getElementById('addon-total-btn'), `₹${total}`);
}

// --- SWIGGY INSTAMART TAB CONTROLLER ---

const IM_CATEGORY_MAP = {
  milk: 'milk',
  bread: 'bread bakery',
  eggs: 'eggs',
  snacks: 'chips snacks munchies',
  drinks: 'coke thums up juice cold drink',
  fruits: 'fresh fruits vegetables',
  maggi: 'maggi instant noodles',
  popular: 'milk bread eggs curd butter',
};

const ICON_PLUS_PATH = 'M12 5v14M5 12h14';
const ICON_MINUS_PATH = 'M5 12h14';

// Rally quantity stepper (.r-stepper). dataAttrs is a trusted attribute string added to both buttons.
function stepperHtml(qty, itemName, dataAttrs = '') {
  const name = escapeHtml(itemName);
  return `
    <div class="r-stepper" role="group" aria-label="Quantity of ${name}">
      <button type="button" class="r-stepper__btn" data-action="dec" ${dataAttrs} aria-label="Remove one ${name}">${iconPath(ICON_MINUS_PATH)}</button>
      <span class="r-stepper__qty" aria-live="polite">${escapeHtml(qty)}</span>
      <button type="button" class="r-stepper__btn" data-action="inc" ${dataAttrs} aria-label="Add one ${name}">${iconPath(ICON_PLUS_PATH)}</button>
    </div>
  `;
}

// Loading placeholders shaped like product tiles, and a full-width block for grid messages.
function productSkeletonHtml(count = 4) {
  const tile = '<div class="r-card" aria-hidden="true"><div class="r-skeleton r-skeleton--tile"></div><div class="r-skeleton r-skeleton--line"></div><div class="r-skeleton r-skeleton--line-sm"></div></div>';
  return tile.repeat(count);
}

function gridMessageHtml(innerHtml) {
  return `<div style="grid-column: 1 / -1;">${innerHtml}</div>`;
}

function setProductGridBusy(busy) {
  const grid = document.getElementById('im-product-grid');
  if (!grid) return;
  if (busy) {
    grid.innerHTML = productSkeletonHtml();
    grid.setAttribute('aria-busy', 'true');
  } else {
    grid.removeAttribute('aria-busy');
  }
}

function setupInstamartTab() {
  const searchInput = document.getElementById('im-search-input');
  const searchBtn = document.getElementById('btn-im-search');
  const filterContainer = document.getElementById('im-category-filters');

  if (searchBtn && searchInput) {
    const doSearch = () => {
      const q = searchInput.value.trim();
      if (!q) return;
      if (filterContainer) filterContainer.querySelectorAll('.r-chip').forEach((p) => setChipSelected(p, false));
      const resultsTitle = document.getElementById('im-results-title');
      if (resultsTitle) resultsTitle.textContent = `Results for "${q}"`;
      loadInstamartProducts(q);
    };

    searchBtn.addEventListener('click', doSearch);
    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') doSearch();
    });
  }

  if (filterContainer) {
    filterContainer.querySelectorAll('.r-chip').forEach((pill) => {
      pill.addEventListener('click', () => {
        filterContainer.querySelectorAll('.r-chip').forEach((p) => setChipSelected(p, p === pill));
        const catKey = pill.dataset.cat;
        const resultsTitle = document.getElementById('im-results-title');
        if (resultsTitle) resultsTitle.textContent = pill.textContent;

        if (catKey === 'goto') {
          loadInstamartGoToItems();
        } else {
          const q = IM_CATEGORY_MAP[catKey] || catKey;
          loadInstamartProducts(q);
        }
      });
    });
  }
}

async function loadInstamartProducts(query) {
  const grid = document.getElementById('im-product-grid');
  const countEl = document.getElementById('im-results-count');
  setProductGridBusy(true);
  if (countEl) countEl.textContent = 'Searching...';

  try {
    const res = await api.searchInstamartProducts(query, null, 12);
    const products = res.success && res.data ? res.data.products : null;
    if (Array.isArray(products) && products.length > 0) {
      state.instamartProducts = products;
      if (countEl) countEl.textContent = `${products.length} products found`;
      renderInstamartProducts();
    } else {
      state.instamartProducts = [];
      if (countEl) countEl.textContent = '0 products found';
      if (grid) {
        grid.innerHTML = gridMessageHtml(
          emptyStateHtml('bag', 'No items found.', `Nothing matched "${query}". Try searching for milk, bread or chips.`)
        );
      }
    }
  } catch (err) {
    console.error('Error fetching Instamart products:', err);
    if (countEl) countEl.textContent = '';
    if (grid) {
      grid.innerHTML = gridMessageHtml(
        emptyStateHtml('alert', 'Could not load products.', 'Check your connection and try again.')
      );
    }
  } finally {
    setProductGridBusy(false);
  }
}

async function loadInstamartGoToItems() {
  const grid = document.getElementById('im-product-grid');
  const countEl = document.getElementById('im-results-count');
  setProductGridBusy(true);
  if (countEl) countEl.textContent = 'Loading your frequent items...';

  try {
    const res = await api.getInstamartGoToItems();
    const products = res.success && res.data ? res.data.products : null;
    if (Array.isArray(products) && products.length > 0) {
      state.instamartProducts = products;
      if (countEl) countEl.textContent = `${products.length} previous items`;
      renderInstamartProducts();
    } else {
      state.instamartProducts = [];
      if (countEl) countEl.textContent = '0 previous items';
      if (grid) {
        grid.innerHTML = gridMessageHtml(
          emptyStateHtml('bag', 'No go-to items yet.', 'Items you order often on Instamart will show up here.')
        );
      }
    }
  } catch (err) {
    console.error('Error fetching Go-To items:', err);
    if (countEl) countEl.textContent = '';
    if (grid) {
      grid.innerHTML = gridMessageHtml(
        emptyStateHtml('alert', 'Could not load your go-to items.', 'Check your connection and try again.')
      );
    }
  } finally {
    setProductGridBusy(false);
  }
}

function renderInstamartProducts() {
  const grid = document.getElementById('im-product-grid');
  if (!grid) return;

  const products = state.instamartProducts || [];
  if (products.length === 0) return;

  // Re-rendering replaces the focused control; remember it so keyboard users keep their place
  const focused = document.activeElement;
  const focusedCard = focused && grid.contains(focused) ? focused.closest('.r-product') : null;
  const refocus = focusedCard ? { spin: focusedCard.dataset.spin, action: focused.dataset.action || 'add' } : null;

  grid.innerHTML = '';

  // Helper map for cart item quantities by spinId
  const cartQtyMap = {};
  if (state.instamartCart && state.instamartCart.items) {
    state.instamartCart.items.forEach((it) => {
      cartQtyMap[it.spin_id] = it.quantity;
    });
  }

  products.forEach((p) => {
    const variant = (p.variants && p.variants.length > 0) ? p.variants[0] : null;
    const spinId = variant ? variant.spin_id : p.product_id;
    // No price from the API means the tile cannot be bought; never invent one
    const price = parseFloat(variant ? variant.price : NaN);
    const hasPrice = Number.isFinite(price);
    const mrp = (variant && variant.mrp) ? variant.mrp : null;
    const unit = (variant && variant.quantity_description) || p.brand || '';
    const imgUrl = (variant && variant.raw && variant.raw.imageUrl) || p.image || '';
    const currentQty = cartQtyMap[spinId] || 0;
    const discountPct = hasPrice && mrp && mrp > price ? Math.round(((mrp - price) / mrp) * 100) : 0;
    const name = escapeHtml(p.name);

    let action;
    if (currentQty > 0) {
      action = stepperHtml(currentQty, p.name);
    } else if (hasPrice) {
      action = `<button type="button" class="r-btn r-btn--secondary r-btn--sm r-btn--pill" data-action="add" aria-label="Add ${name}">Add</button>`;
    } else {
      action = '<button type="button" class="r-btn r-btn--secondary r-btn--sm r-btn--pill" data-action="add" disabled>Unavailable</button>';
    }

    const card = document.createElement('article');
    card.className = 'r-product r-card';
    card.dataset.spin = spinId;
    card.innerHTML = `
      <div class="r-product__media">
        ${imgUrl ? `<img class="r-product__img" src="${escapeHtml(imgUrl)}" alt="${name}" loading="lazy" />` : ''}
        <span class="r-tag r-tag--neutral r-product__time">10 to 15 min</span>
        ${discountPct > 0 ? `<span class="r-tag r-tag--success r-product__discount">${discountPct}% off</span>` : ''}
      </div>
      <h3 class="r-product__name" title="${name}">${name}</h3>
      ${unit ? `<p class="r-product__unit">${escapeHtml(unit)}</p>` : ''}
      <div class="r-product__footer">
        <div class="r-product__price-row">
          <span class="r-product__price">${hasPrice ? `₹${escapeHtml(price)}` : 'Price unavailable'}</span>
          ${hasPrice && mrp && mrp > price ? `<span class="r-product__mrp">₹${escapeHtml(mrp)}</span>` : ''}
        </div>
        <div class="r-product__action">${action}</div>
      </div>
    `;

    // Handlers
    card.querySelectorAll('.r-product__action [data-action]:not([disabled])').forEach((btn) => {
      btn.addEventListener('click', async () => {
        await addInstamartCartItem(spinId, btn.dataset.action === 'dec' ? -1 : 1, p.name);
      });
    });

    grid.appendChild(card);
  });

  if (refocus) {
    const card = grid.querySelector(`.r-product[data-spin="${CSS.escape(String(refocus.spin))}"]`);
    const target = card && (card.querySelector(`[data-action="${refocus.action}"]`) || card.querySelector('.r-product__action [data-action]'));
    if (target) target.focus();
  }
}

async function addInstamartCartItem(spinId, delta, itemName = 'Item') {
  showToast('Updating Instamart cart...');
  try {
    const res = await api.addOrUpdateInstamartItem(spinId, delta);
    if (res.success && res.data) {
      state.instamartCart = res.data;
      persistCarts();
      updateCartBadge();
      renderInstamartProducts();
      if (state.activeCartType === 'instamart') {
        renderCartDrawerItems();
      }
      showToast(`Instamart cart: ${state.instamartCart.total_amount}`);
    } else {
      showToast(apiErrorMessage(res, 'Could not update the Instamart cart.'), { error: true });
    }
  } catch (err) {
    console.error('Error updating Instamart item:', err);
    showToast('Error updating item in Instamart cart.', { error: true });
  }
}

// --- CART DRAWER CONTROLLER ---
function setupCartDrawer() {
  const openBtn = document.getElementById('btn-open-cart');
  const closeBtn = document.getElementById('btn-close-cart');
  const approveBtn = document.getElementById('btn-approve-order');
  const switchFoodBtn = document.getElementById('btn-switch-food');
  const switchImBtn = document.getElementById('btn-switch-im');
  const clearActiveBtn = document.getElementById('btn-clear-active-cart');

  openBtn.addEventListener('click', () => {
    openCartDrawerWithType(state.activeCartType || 'food');
  });

  closeBtn.addEventListener('click', closeCartDrawer);

  approveBtn.addEventListener('click', () => {
    closeCartDrawer();
    openPaymentModal();
  });

  if (switchFoodBtn && switchImBtn) {
    switchFoodBtn.addEventListener('click', () => {
      openCartDrawerWithType('food');
    });

    switchImBtn.addEventListener('click', () => {
      openCartDrawerWithType('instamart');
    });
  }

  if (clearActiveBtn) {
    clearActiveBtn.addEventListener('click', () => withBusy(clearActiveBtn, async () => {
      const isInstamart = state.activeCartType === 'instamart';
      showToast(isInstamart ? 'Clearing Instamart cart...' : 'Clearing food cart...');
      try {
        if (isInstamart) {
          await api.clearInstamartCart();
          state.instamartCart = { items: [], total_items: 0, total_amount: '₹0', bill_breakdown: null };
          persistCarts();
          await refreshInstamartCart();
        } else {
          await api.clearCart();
          state.cart = { items: [], pricing: null, item_count: 0 };
          persistCarts();
          await refreshCart();
        }
        showToast(isInstamart ? 'Instamart cart cleared' : 'Food cart cleared');
      } catch (err) {
        console.error('Error clearing cart:', err);
        showToast('Could not clear the cart.', { error: true });
      }
    }));
  }
}

function updateCartBadge() {
  const badge = document.getElementById('cart-badge');
  const foodCount = state.cart ? (state.cart.item_count || (state.cart.items || []).length) : 0;
  const imCount = state.instamartCart ? (state.instamartCart.total_items || (state.instamartCart.items || []).length) : 0;
  const total = foodCount + imCount;

  if (badge) {
    badge.textContent = total;
    badge.hidden = total === 0;
  }
  const openBtn = document.getElementById('btn-open-cart');
  if (openBtn) openBtn.setAttribute('aria-label', total > 0 ? `Open cart, ${total} items` : 'Open cart');
  const foodPill = document.getElementById('cart-food-count');
  if (foodPill) foodPill.textContent = foodCount;
  const imPill = document.getElementById('cart-im-count');
  if (imPill) imPill.textContent = imCount;
}

async function refreshCart() {
  try {
    const res = await api.getCart();
    if (res.success && res.data) {
      state.cart = res.data;
      persistCarts();
      updateCartBadge();
      if (state.activeCartType === 'food') {
        renderCartDrawerItems();
      }
    }
  } catch (e) {
    console.error('Error refreshing food cart:', e);
  }
}

async function refreshInstamartCart() {
  try {
    const res = await api.getInstamartCart();
    if (res.success && res.data) {
      state.instamartCart = res.data;
      persistCarts();
      updateCartBadge();
      if (state.activeCartType === 'instamart') {
        renderCartDrawerItems();
      }
      renderInstamartProducts();
    }
  } catch (e) {
    console.error('Error refreshing Instamart cart:', e);
  }
}

// One bill line (.r-bill__row); the optional id keeps the legacy value-element ids.
function billRowHtml(label, value, { id = '', free = false, total = false } = {}) {
  return `
    <div class="r-bill__row${total ? ' r-bill__row--total' : ''}">
      <span class="r-bill__label">${escapeHtml(label)}</span>
      <span class="r-bill__value${free ? ' r-bill__value--free' : ''}"${id ? ` id="${id}"` : ''}>${escapeHtml(value)}</span>
    </div>
  `;
}

// One cart line (.r-row): name and detail, then quantity stepper and line amount.
function cartRowEl({ name, sub, qty, amount, dataAttrs }, onDec, onInc) {
  const el = document.createElement('div');
  el.className = 'r-row';
  el.innerHTML = `
    <div class="r-row__main">
      <p class="r-row__title">${escapeHtml(name)}</p>
      ${sub ? `<p class="r-row__sub">${escapeHtml(sub)}</p>` : ''}
    </div>
    <div class="r-row__trail">
      ${stepperHtml(qty, name, dataAttrs)}
      ${amount ? `<span class="r-row__amount">${escapeHtml(amount)}</span>` : ''}
    </div>
  `;
  el.querySelector('[data-action="dec"]').addEventListener('click', onDec);
  el.querySelector('[data-action="inc"]').addEventListener('click', onInc);
  return el;
}

// Bill card, footer and approve button. The CTA amount stays empty when the backend sent no total.
function setCartCheckout(visible, { billHtml = '', amountText = '' } = {}) {
  const billBox = document.getElementById('cart-bill-breakdown');
  const footerEl = document.getElementById('cart-drawer-footer');
  const approveBtn = document.getElementById('btn-approve-order');
  if (billBox) {
    billBox.innerHTML = billHtml;
    billBox.style.display = visible && billHtml ? '' : 'none';
  }
  if (footerEl) footerEl.style.display = visible ? '' : 'none';
  if (approveBtn) approveBtn.disabled = !visible;
  setButtonAmount(approveBtn, amountText);
}

function renderCartEmpty(icon, title, text, browseTab, browseLabel) {
  const container = document.getElementById('cart-items-list');
  container.innerHTML = emptyStateHtml(
    icon,
    title,
    text,
    `<button type="button" class="r-btn r-btn--primary r-btn--pill" data-browse="${browseTab}">${escapeHtml(browseLabel)}</button>`
  );
  container.querySelector('[data-browse]').addEventListener('click', (e) => {
    closeCartDrawer();
    switchTabById(e.currentTarget.dataset.browse);
  });
  setCartCheckout(false);
}

function renderActiveCart() {
  const container = document.getElementById('cart-items-list');
  const bannerIcon = document.getElementById('cart-banner-icon');
  const bannerText = document.getElementById('cart-banner-text');
  const localCounts = JSON.parse(localStorage.getItem('smartflow_order_counts') || '{}');
  // The banner icon is an inline SVG; only its sprite reference changes
  const setBannerIcon = (name) => bannerIcon?.querySelector('use')?.setAttribute('href', `#i-${name}`);

  if (state.activeCartType === 'instamart') {
    // --- INSTAMART CART RENDERING ---
    const imCount = localCounts['instamart'] || 0;
    const orderedTimes = imCount > 3 ? ` (ordered ${imCount} times)` : '';
    setBannerIcon('bag');
    if (bannerText) bannerText.innerHTML = `Ordering from <strong>Swiggy Instamart</strong>${orderedTimes}, 10 to 15 min`;

    const items = state.instamartCart ? state.instamartCart.items || [] : [];
    if (items.length === 0) {
      renderCartEmpty('bag', 'Your Instamart cart is empty.', 'Add milk, bread, eggs, snacks and daily essentials from the Instamart tab.', 'pane-instamart', 'Browse groceries');
      return;
    }

    container.innerHTML = '';
    let itemSubtotal = 0;
    items.forEach((item) => {
      const price = parseFloat(item.price);
      const hasPrice = Number.isFinite(price);
      if (hasPrice) itemSubtotal += price * item.quantity;
      container.appendChild(cartRowEl(
        {
          name: item.name,
          sub: [item.variant, hasPrice ? `₹${price} each` : ''].filter(Boolean).join(' · '),
          qty: item.quantity,
          amount: hasPrice ? `₹${price * item.quantity}` : '',
          dataAttrs: `data-id="${escapeHtml(item.spin_id)}"`,
        },
        () => addInstamartCartItem(item.spin_id, -1, item.name),
        () => addInstamartCartItem(item.spin_id, 1, item.name)
      ));
    });

    // Fees and total come from the backend only; nothing is estimated here
    const totalStr = state.instamartCart.total_amount || '';
    const breakdown = state.instamartCart.bill_breakdown;
    const lineItems = (breakdown && breakdown.line_items) || [];
    let billHtml = '';
    if (lineItems.length > 0) {
      lineItems.forEach((li) => {
        const isFree = li.value === '0' || li.value === '₹0' || String(li.value).toLowerCase() === 'free';
        billHtml += billRowHtml(li.label, isFree ? 'Free' : li.value, { free: isFree });
      });
    } else {
      billHtml += billRowHtml('Item total', `₹${itemSubtotal}`, { id: 'bill-item-total' });
    }
    if (totalStr) billHtml += billRowHtml('To pay', totalStr, { id: 'bill-total-pay', total: true });
    setCartCheckout(true, { billHtml, amountText: totalStr });
    return;
  }

  // --- FOOD CART RENDERING ---
  const restName = (state.cart && state.cart.restaurant_name) || (state.activeRestaurant ? state.activeRestaurant.name : 'Meghana Foods');
  const restCount = localCounts[restName] || 0;
  const orderedTimes = restCount > 3 ? ` (ordered ${restCount} times)` : '';
  setBannerIcon('food');
  if (bannerText) bannerText.innerHTML = `Ordering from <strong>${escapeHtml(restName)}</strong>${orderedTimes}, 25 to 30 min`;

  const items = state.cart ? state.cart.items || [] : [];
  if (items.length === 0) {
    renderCartEmpty('food', 'Your food cart is empty.', 'Browse the menu or ask the concierge to add dishes.', 'pane-menu', 'Browse menu');
    return;
  }

  container.innerHTML = '';
  items.forEach((item) => {
    container.appendChild(cartRowEl(
      {
        name: item.name,
        sub: `₹${item.price} each`,
        qty: item.quantity,
        amount: `₹${item.subtotal || (item.price * item.quantity)}`,
        dataAttrs: `data-id="${escapeHtml(item.menu_item_id)}"`,
      },
      () => addDishToCart(item.menu_item_id, item.quantity - 1),
      () => addDishToCart(item.menu_item_id, item.quantity + 1)
    ));
  });

  const pricing = state.cart.pricing;
  if (!pricing) {
    setCartCheckout(true);
    return;
  }
  const freeDelivery = pricing.delivery_charge === 0;
  const billHtml =
    billRowHtml('Item total', `₹${pricing.item_total}`, { id: 'bill-item-total' }) +
    billRowHtml('Delivery partner fee', freeDelivery ? 'Free' : `₹${pricing.delivery_charge}`, { id: 'bill-delivery-fee', free: freeDelivery }) +
    billRowHtml('Taxes and other charges', `₹${pricing.taxes_and_charges}`, { id: 'bill-taxes' }) +
    billRowHtml('To pay', `₹${pricing.to_pay}`, { id: 'bill-total-pay', total: true });
  setCartCheckout(true, { billHtml, amountText: `₹${pricing.to_pay}` });
}

// Re-rendering replaces the focused stepper button; put focus back on its replacement.
function renderCartDrawerItems() {
  const container = document.getElementById('cart-items-list');
  const focused = document.activeElement;
  const refocus = focused && container.contains(focused) && focused.dataset.id
    ? { id: focused.dataset.id, action: focused.dataset.action }
    : null;

  renderActiveCart();

  if (refocus) {
    const selector = `[data-id="${CSS.escape(refocus.id)}"][data-action="${refocus.action}"]`;
    const target = container.querySelector(selector);
    if (target) target.focus();
  }
}

// --- PAYMENT & QR MODAL ---
// Amount text without the currency symbol; empty when the backend sent no figure.
function cleanAmountText(amount) {
  return amount === null || amount === undefined ? '' : String(amount).replace(/₹/g, '').trim();
}

// Rally amount: small currency symbol followed by the figure, empty when unknown.
function setAmountText(el, amount) {
  if (!el) return;
  const clean = cleanAmountText(amount);
  el.innerHTML = clean ? `<span class="r-amount__sym">₹</span>${escapeHtml(clean)}` : '';
}

// Payment links and QR data come only from the order the backend returned; never built locally.
function getUpiUrl() {
  const order = state.activeOrder;
  return (order && (order.upi_intent_url || order.upi_qr_data)) || '';
}

// Navigation sink guard for backend-supplied links.
function isLaunchableUrl(url) {
  return typeof url === 'string' && !/^\s*(javascript|data|vbscript):/i.test(url);
}

function setupModals() {
  // Address sheet
  const addrModal = document.getElementById('address-modal');
  const headerLoc = document.getElementById('header-location');
  if (headerLoc && addrModal) {
    headerLoc.addEventListener('click', () => {
      renderAddressModalList();
      openSheet(addrModal, headerLoc);
    });
  }
  const btnCloseAddr = document.getElementById('btn-close-address');
  if (btnCloseAddr && addrModal) {
    btnCloseAddr.addEventListener('click', () => closeSheet(addrModal));
  }

  // Add-ons sheet
  const addonsModal = document.getElementById('addons-modal');
  document.getElementById('btn-close-addons').addEventListener('click', () => closeSheet(addonsModal));
  addonsModal.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
    cb.addEventListener('change', updateAddonTotal);
  });
  document.getElementById('addon-total-btn').addEventListener('click', () => {
    if (state.selectedDishForAddons) {
      addDishToCart(state.selectedDishForAddons.id, 1);
      closeSheet(addonsModal);
    }
  });

  // Payment sheet
  const payModal = document.getElementById('payment-modal');
  document.getElementById('btn-close-payment').addEventListener('click', () => closeSheet(payModal));

  // Direct UPI app buttons open the backend-provided payment link
  const launchUpiApp = (appName) => {
    const upiUrl = getUpiUrl();
    if (!upiUrl || !isLaunchableUrl(upiUrl)) {
      showToast('No UPI link came back for this order. Scan the QR code instead.', { error: true });
      return;
    }
    showToast(`Opening ${appName}. Come back and tap "I have paid" after the transfer.`);
    window.location.href = upiUrl;
  };

  document.getElementById('btn-pay-gpay')?.addEventListener('click', () => launchUpiApp('Google Pay'));
  document.getElementById('btn-pay-phonepe')?.addEventListener('click', () => launchUpiApp('PhonePe'));
  document.getElementById('btn-pay-paytm')?.addEventListener('click', () => launchUpiApp('Paytm'));
  document.getElementById('btn-pay-cred')?.addEventListener('click', () => launchUpiApp('CRED'));

  // Copy UPI ID button
  document.getElementById('btn-copy-upi')?.addEventListener('click', () => {
    const vpaText = document.getElementById('upi-vpa-text')?.textContent || '';
    if (!vpaText) return;
    const copied = navigator.clipboard
      ? navigator.clipboard.writeText(vpaText)
      : Promise.reject(new Error('Clipboard unavailable'));
    copied
      .then(() => showToast(`Copied UPI ID: ${vpaText}`))
      .catch(() => showToast(`UPI ID: ${vpaText}`));
  });

  // Confirm Final Checkout
  document.getElementById('btn-final-pay').addEventListener('click', handleFinalCheckout);
}

function displayPaymentQR(order) {
  const modal = document.getElementById('payment-modal');
  if (!modal) return;

  document.getElementById('pay-order-id').textContent = order.order_id ? `#${order.order_id}` : '';

  // The order's own total, else the backend total of the cart being paid
  const cartTotal = state.activeCartType === 'instamart'
    ? (state.instamartCart ? state.instamartCart.total_amount : null)
    : (state.cart && state.cart.pricing ? state.cart.pricing.to_pay : null);
  const amount = cleanAmountText(order.total_amount ?? cartTotal);
  setAmountText(document.getElementById('pay-modal-amount'), amount);
  setButtonAmount(document.getElementById('btn-final-pay'), amount ? `₹${amount}` : '');

  // QR, UPI ID and app links are shown only when the backend returned payment data
  const qrData = order.upi_qr_data || order.upi_intent_url || '';
  const qrSection = document.getElementById('qr-section');
  const qrImg = document.getElementById('swiggy-qr-img');
  const vpaEl = document.getElementById('upi-vpa-text');
  const trust = modal.querySelector('.r-pay__trust');
  if (trust) {
    trust.dataset.defaultText = trust.dataset.defaultText || trust.textContent;
    trust.textContent = qrData
      ? trust.dataset.defaultText
      : 'Swiggy did not return UPI payment details for this order. Finish payment in the Swiggy app, then tap the button below.';
  }

  let vpa = '';
  const paMatch = qrData.match(/[?&]pa=([^&]+)/);
  if (paMatch) {
    try {
      vpa = decodeURIComponent(paMatch[1]);
    } catch (e) {
      vpa = '';
    }
  }
  if (qrSection) qrSection.hidden = !qrData;
  if (qrImg) {
    if (qrData) {
      qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent(qrData)}`;
    } else {
      qrImg.removeAttribute('src');
    }
  }
  if (vpaEl) {
    vpaEl.textContent = vpa;
    const vpaRow = vpaEl.closest('.r-pay__vpa');
    if (vpaRow) vpaRow.hidden = !vpa;
  }

  openSheet(modal);
  if (qrData) {
    showToast('UPI QR ready. Scan it or open a UPI app.');
  } else {
    showToast('No UPI payment details came back for this order.', { error: true });
  }
}

async function openPaymentModal() {
  closeCartDrawer();

  const foodCount = state.cart ? (state.cart.item_count || (state.cart.items || []).length) : 0;
  const imCount = state.instamartCart ? (state.instamartCart.total_items || (state.instamartCart.items || []).length) : 0;

  // Auto-switch to active cart with items if current active is empty
  if (state.activeCartType === 'food' && foodCount === 0 && imCount > 0) {
    state.activeCartType = 'instamart';
  } else if (state.activeCartType === 'instamart' && imCount === 0 && foodCount > 0) {
    state.activeCartType = 'food';
  }
  if (foodCount === 0 && imCount === 0) {
    showToast('Your cart is empty. Add dishes or groceries first.', { error: true });
    openCartDrawerWithType(state.activeCartType || 'food');
    return;
  }

  const isInstamart = state.activeCartType === 'instamart';
  showToast(isInstamart ? 'Connecting to Swiggy Instamart...' : 'Connecting to Swiggy payments...');
  try {
    const res = isInstamart ? await api.checkoutInstamart('UPI', true) : await api.checkout('UPI', true);
    if (res.success && res.data) {
      state.activeOrder = res.data;
      persistActiveOrder();
      displayPaymentQR(res.data);
      return;
    }
    showToast(apiErrorMessage(res, 'Could not start checkout.'), { error: true });
  } catch (e) {
    console.error(`${isInstamart ? 'Instamart' : 'Food'} checkout error:`, e);
    showToast('Could not reach Swiggy checkout. Try again.', { error: true });
  }
  // Checkout failed: no order exists, so return to the cart instead of showing a payment sheet
  openCartDrawerWithType(state.activeCartType);
}

async function handleFinalCheckout() {
  const modal = document.getElementById('payment-modal');
  const order = state.activeOrder;
  if (!order || !order.order_id) {
    showToast('No order to confirm. Review your cart and try again.', { error: true });
    return;
  }
  const isInstamart = state.activeCartType === 'instamart';

  await withBusy(document.getElementById('btn-final-pay'), async () => {
    showToast('Finalizing your order with Swiggy...');
    let placedOrder = null;
    try {
      const res = isInstamart
        ? await api.confirmInstamartOrder(order.order_id)
        : await api.confirmOrder(order.order_id);
      if (res && res.success && res.data) {
        placedOrder = isInstamart ? { ...order, order_status: 'Placed', is_active: true } : res.data;
      } else {
        showToast(apiErrorMessage(res, 'Swiggy could not confirm this order. Check your payment and try again.'), { error: true });
      }
    } catch (e) {
      console.error('Checkout error:', e);
      showToast('Could not reach Swiggy to confirm the order. Try again.', { error: true });
    }
    // Not confirmed: keep the payment sheet open so the user can retry
    if (!placedOrder) return;

    const restaurantName = (state.cart && state.cart.restaurant_name) || (state.activeRestaurant ? state.activeRestaurant.name : 'Meghana Foods');
    await (isInstamart ? refreshInstamartCart() : refreshCart());

    closeSheet(modal);
    hasTriggered2MinAlert = false;
    state.activeOrder = { ...placedOrder, is_active: true };
    persistActiveOrder();
    persistCarts();

    // Increment order frequency count
    if (isInstamart) {
      recordCompletedOrder('Swiggy Instamart', true);
    } else {
      recordCompletedOrder(restaurantName, false);
    }

    showOrderSuccess(state.activeOrder.order_id);
  });
}

function showOrderSuccess(orderId) {
  playArrivalChime();
  showToast('Order confirmed. Live tracking is on.');

  // Switch to tracking tab (also syncs the live tracking state)
  switchTabById('pane-tracking');
}

// --- LEAFLET LIVE GPS MAP CONTROLLER ---
let liveMap = null;
let riderMarker = null;
let restaurantMarker = null;
let homeMarker = null;
let routePolyline = null;

const RESTAURANT_COORDS = [12.9902, 77.5538]; // Meghana Foods, Rajajinagar
const HOME_COORDS = [12.9835, 77.5510];       // Delivery Gate / Srinivasa PG, Rajajinagar
const DELIVERY_ROUTE = [
  [12.9902, 77.5538], // Meghana Foods
  [12.9890, 77.5532], // 10th Main Road
  [12.9878, 77.5526], // 3rd Block Junction
  [12.9865, 77.5520], // Rajajinagar Main Road
  [12.9852, 77.5515], // Approaching 2nd Block
  [12.9840, 77.5512], // 2 Min Gate Waypoint
  [12.9835, 77.5510]  // Home Gate
];

function initLiveMap() {
  const mapContainer = document.getElementById('live-map');
  if (!mapContainer || typeof L === 'undefined') return;

  if (liveMap) {
    setTimeout(() => liveMap.invalidateSize(), 150);
    return;
  }

  // Initialize Map centered on Rajajinagar
  liveMap = L.map('live-map', {
    center: [12.9870, 77.5524],
    zoom: 15,
    zoomControl: true,
  });

  // OpenStreetMap Tile Layer
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors | Swiggy Fleet Tracking',
    maxZoom: 19,
  }).addTo(liveMap);

  // Rally pins (.r-map__pin): an icon in a round pin, or the plain blue dot when no icon is given
  const createPin = (variantClass, iconName) => {
    const size = iconName ? 28 : 16;
    return L.divIcon({
      className: `r-map__pin ${variantClass}`.trim(),
      html: iconName ? iconUse(iconName) : '',
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2],
      popupAnchor: [0, -(size / 2 + 2)],
    });
  };

  // 1. Restaurant Marker
  restaurantMarker = L.marker(RESTAURANT_COORDS, {
    icon: createPin('', 'food'),
    title: 'Restaurant',
  }).addTo(liveMap).bindPopup('<strong>Meghana Foods</strong><br/>Rajajinagar 1st Block, Bengaluru');

  // 2. Home Gate Marker
  homeMarker = L.marker(HOME_COORDS, {
    icon: createPin('r-map__pin--user'),
    title: 'Delivery gate',
  }).addTo(liveMap).bindPopup('<strong>Delivery Location (Gate)</strong><br/>Srinivasa P.G., Rajajinagar');

  // 3. Route Polyline (ink, from the Rally token)
  routePolyline = L.polyline(DELIVERY_ROUTE, {
    color: getComputedStyle(document.documentElement).getPropertyValue('--sp-content-primary').trim(),
    weight: 4,
    opacity: 0.85,
    dashArray: '8, 8',
  }).addTo(liveMap);

  // 4. Rider Marker initially at restaurant
  riderMarker = L.marker(RESTAURANT_COORDS, {
    icon: createPin('r-map__pin--selected', 'scooter'),
    title: 'Delivery partner',
  }).addTo(liveMap).bindPopup('<strong>Rider: Ravi Kumar</strong><br/>TVS Jupiter (KA 02 HK 4921)');

  liveMap.fitBounds(routePolyline.getBounds(), { padding: [40, 40] });
  setTimeout(() => liveMap.invalidateSize(), 300);
}

function moveRiderTo(coords, statusText = '') {
  if (!riderMarker || !liveMap) return;
  riderMarker.setLatLng(coords);
  if (statusText) {
    riderMarker.setPopupContent(`<strong>Rider: Ravi Kumar</strong><br/>${escapeHtml(statusText)}`);
  }
}

// --- PHONE CALL SIMULATION & WEBAUDIO RINGTONE ---
let ringtoneInterval = null;
let ringtoneAudioCtx = null;
let callTimerInterval = null;

function startRingtone() {
  stopRingtone();
  try {
    ringtoneAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const playBurst = () => {
      if (!ringtoneAudioCtx || ringtoneAudioCtx.state === 'closed') return;
      const now = ringtoneAudioCtx.currentTime;

      const osc1 = ringtoneAudioCtx.createOscillator();
      const osc2 = ringtoneAudioCtx.createOscillator();
      const gain = ringtoneAudioCtx.createGain();

      osc1.frequency.value = 400; // Dual tone 400Hz + 450Hz
      osc2.frequency.value = 450;
      osc1.type = 'sine';
      osc2.type = 'sine';

      // Ring burst 1 (0 to 0.4s)
      gain.gain.setValueAtTime(0.2, now);
      gain.gain.setValueAtTime(0, now + 0.4);
      // Ring burst 2 (0.6s to 1.0s)
      gain.gain.setValueAtTime(0.2, now + 0.6);
      gain.gain.setValueAtTime(0, now + 1.0);

      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(ringtoneAudioCtx.destination);

      osc1.start(now);
      osc2.start(now);
      osc1.stop(now + 1.05);
      osc2.stop(now + 1.05);
    };

    playBurst();
    ringtoneInterval = setInterval(playBurst, 2800);
  } catch (e) {
    console.warn('Ringtone AudioContext error:', e);
  }
}

function stopRingtone() {
  if (ringtoneInterval) {
    clearInterval(ringtoneInterval);
    ringtoneInterval = null;
  }
  if (ringtoneAudioCtx) {
    try { ringtoneAudioCtx.close(); } catch (e) {}
    ringtoneAudioCtx = null;
  }
}

function showIncomingCallModal(callerName, callerNumber = '') {
  const overlay = document.getElementById('phone-call-overlay');
  if (!overlay) return;

  document.getElementById('call-status-label').textContent = 'Incoming call';
  document.getElementById('call-caller-name').textContent = callerName;
  const numberEl = document.getElementById('call-number');
  numberEl.textContent = callerNumber;
  numberEl.hidden = !callerNumber;
  // .r-call__actions is a flex row: clearing the inline style restores it
  document.getElementById('call-incoming-actions').style.display = '';
  document.getElementById('call-active-actions').style.display = 'none';
  document.getElementById('call-active-timer').style.display = 'none';

  openSheet(overlay);
  startRingtone();
}

function setupPhoneCallOverlay() {
  const overlay = document.getElementById('phone-call-overlay');
  const declineBtn = document.getElementById('btn-call-decline');
  const acceptBtn = document.getElementById('btn-call-accept');
  const hangupBtn = document.getElementById('btn-call-hangup');

  // Accept Call Handler
  if (acceptBtn) {
    acceptBtn.addEventListener('click', () => {
      stopRingtone();
      document.getElementById('call-status-label').textContent = 'Call in progress';
      document.getElementById('call-incoming-actions').style.display = 'none';
      document.getElementById('call-active-actions').style.display = '';

      const timerEl = document.getElementById('call-active-timer');
      timerEl.style.display = '';
      timerEl.textContent = '00:00';

      let callSeconds = 0;
      if (callTimerInterval) clearInterval(callTimerInterval);
      callTimerInterval = setInterval(() => {
        callSeconds++;
        const mins = String(Math.floor(callSeconds / 60)).padStart(2, '0');
        const secs = String(callSeconds % 60).padStart(2, '0');
        timerEl.textContent = `${mins}:${secs}`;
      }, 1000);

      // Speak rider announcement through speech synthesis
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const speechMsg = new SpeechSynthesisUtterance(
          "Hello! This is your Swiggy delivery partner Ravi Kumar. I have reached the main road and will be at your building gate in Rajajinagar in 2 minutes. Please come downstairs to collect your hot Meghana Foods order."
        );
        speechMsg.rate = 1.0;
        speechMsg.pitch = 1.0;
        window.speechSynthesis.speak(speechMsg);
      }
    });
  }

  // Decline or Hangup Handlers
  const handleEndCall = () => {
    stopRingtone();
    if (callTimerInterval) {
      clearInterval(callTimerInterval);
      callTimerInterval = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    closeSheet(overlay);
    showToast('Call ended.');
  };

  if (declineBtn) declineBtn.addEventListener('click', handleEndCall);
  if (hangupBtn) hangupBtn.addEventListener('click', handleEndCall);

  // Call rider button in tracking pane
  const callRiderBtn = document.getElementById('btn-call-rider');
  if (callRiderBtn) {
    callRiderBtn.addEventListener('click', () => {
      showIncomingCallModal('Ravi Kumar (Delivery Partner)', '+91 98450 12839 (KA 02 HK 4921)');
    });
  }
}

// --- DYNAMIC REAL-TIME TRACKING CONTROLLER ---
let trackingPollInterval = null;
let hasTriggered2MinAlert = false;
let demoStepIndex = 0;

function startLiveTrackingDemo() {
  demoStepIndex = 0;
  hasTriggered2MinAlert = false;
  state.activeOrder = {
    order_id: 'SWIGGY-DEMO-9481',
    restaurant_name: 'Meghana Foods',
    ordered_items: 'Meghana Special Chicken Biryani (1), Extra Gravy (1)',
    order_status: 'On The Way',
    is_active: true,
    is_demo: true,
  };
  persistActiveOrder();
  syncTrackingTabState();
  showToast('🛵 Live GPS Delivery Tracking demonstration started!');
}

async function syncTrackingTabState() {
  await loadPastOrders();

  const noOrderBox = document.getElementById('no-active-order-box');
  const activeSection = document.getElementById('active-order-tracking-section');

  let isOrderActive = false;

  // Check state.activeOrder
  if (state.activeOrder && state.activeOrder.order_id) {
    const st = (state.activeOrder.order_status || state.activeOrder.status || '').toLowerCase();
    if (state.activeOrder.is_demo || state.activeOrder.is_active || ['placed', 'confirmed', 'preparing', 'in_transit', 'out_for_delivery', 'picked_up', 'on the way'].includes(st)) {
      isOrderActive = true;
    }
  }

  // If not active in memory, check real Swiggy orders
  if (!isOrderActive) {
    try {
      const ordersRes = await api.getOrders(15);
      if (ordersRes.success && ordersRes.data && ordersRes.data.orders) {
        const activeOrder = ordersRes.data.orders.find((o) =>
          o.is_active || ['placed', 'confirmed', 'preparing', 'in_transit', 'out_for_delivery', 'picked_up', 'on the way'].includes((o.order_status || '').toLowerCase())
        );
        if (activeOrder) {
          state.activeOrder = {
            order_id: activeOrder.order_id,
            restaurant_name: activeOrder.restaurant_name,
            ordered_items: activeOrder.ordered_items,
            order_status: activeOrder.order_status,
            is_active: true,
          };
          persistActiveOrder();
          isOrderActive = true;
        }
      }
    } catch (e) {
      console.warn('Could not check for active orders:', e);
    }
  }

  // If no active in-transit order, show clean "No Active Order" banner
  if (!isOrderActive) {
    if (noOrderBox) noOrderBox.style.display = 'block';
    if (activeSection) activeSection.style.display = 'none';
    if (trackingPollInterval) {
      clearInterval(trackingPollInterval);
      trackingPollInterval = null;
    }
    return;
  }

  // Active or Demo Order is present
  if (noOrderBox) noOrderBox.style.display = 'none';
  if (activeSection) activeSection.style.display = 'block';

  // Initialize Map
  initLiveMap();
  setTimeout(() => {
    if (liveMap) liveMap.invalidateSize();
  }, 200);

  const orderId = state.activeOrder.order_id;
  const itemsText = state.activeOrder.ordered_items || state.activeOrder.items_summary || 'Food order';
  const itemsSummaryEl = document.getElementById('tracking-items-summary');
  if (itemsSummaryEl) itemsSummaryEl.textContent = `${state.activeOrder.restaurant_name || 'Meghana Foods'} • ${itemsText}`;

  // Poll immediately and start interval
  pollLiveTracking(orderId);
  if (trackingPollInterval) clearInterval(trackingPollInterval);
  trackingPollInterval = setInterval(() => {
    pollLiveTracking(orderId);
  }, 8000);
}

async function pollLiveTracking(orderId) {
  if (!orderId) return;

  // Handle Demo mode simulation
  if (state.activeOrder && state.activeOrder.is_demo) {
    demoStepIndex = (demoStepIndex + 1) % 4;
    const orderIdEl = document.getElementById('tracking-order-id');
    if (orderIdEl) orderIdEl.textContent = `Order #${state.activeOrder.order_id}`;
    const etaEl = document.getElementById('tracking-eta');
    const badgeEl = document.getElementById('tracking-status-badge');
    const progressBar = document.getElementById('timeline-progress');
    const steps = [
      document.getElementById('step-1'),
      document.getElementById('step-2'),
      document.getElementById('step-3'),
      document.getElementById('step-4'),
    ];
    steps.forEach((s) => { if (s) s.className = 'step'; });

    if (demoStepIndex === 0) {
      if (etaEl) etaEl.textContent = 'ETA: ~18 mins';
      if (badgeEl) badgeEl.textContent = 'Swiggy: Order Confirmed';
      if (steps[0]) steps[0].className = 'step active';
      if (progressBar) progressBar.style.width = '20%';
      moveRiderTo(RESTAURANT_COORDS, 'Meghana Foods • Order Confirmed');
    } else if (demoStepIndex === 1) {
      if (etaEl) etaEl.textContent = 'ETA: ~12 mins';
      if (badgeEl) badgeEl.textContent = 'Swiggy: Food Preparing in Kitchen';
      if (steps[0]) steps[0].className = 'step done';
      if (steps[1]) steps[1].className = 'step active';
      if (progressBar) progressBar.style.width = '45%';
      moveRiderTo(RESTAURANT_COORDS, 'Meghana Foods • Chef packing biryani');
    } else if (demoStepIndex === 2) {
      if (etaEl) etaEl.textContent = 'ETA: ~6 mins';
      if (badgeEl) badgeEl.textContent = 'Swiggy: On The Way (Ravi Kumar)';
      if (steps[0]) steps[0].className = 'step done';
      if (steps[1]) steps[1].className = 'step done';
      if (steps[2]) steps[2].className = 'step active';
      if (progressBar) progressBar.style.width = '75%';
      moveRiderTo(DELIVERY_ROUTE[3], 'On the way • Speed: 34 km/h');
      if (liveMap) liveMap.panTo(DELIVERY_ROUTE[3]);
    } else {
      if (etaEl) etaEl.textContent = 'ETA: ~2 mins (Gate Arrival)';
      if (badgeEl) badgeEl.textContent = 'Swiggy: Arriving at Gate';
      if (steps[0]) steps[0].className = 'step done';
      if (steps[1]) steps[1].className = 'step done';
      if (steps[2]) steps[2].className = 'step done';
      if (steps[3]) steps[3].className = 'step active';
      if (progressBar) progressBar.style.width = '100%';
      moveRiderTo(DELIVERY_ROUTE[5], '🚨 Arriving at Gate in 2 mins!');
      if (riderMarker) riderMarker.openPopup();
      if (liveMap) liveMap.setView(DELIVERY_ROUTE[5], 16);
      if (!hasTriggered2MinAlert) {
        hasTriggered2MinAlert = true;
        triggerGateArrivalAlert(state.activeOrder.order_id, '2 minutes');
      }
    }
    return;
  }

  try {
    const res = await api.trackOrder(orderId);
    if (!res.success || !res.data) return;

    const data = res.data;
    const etaText = data.eta_text || (data.estimated_arrival_minutes ? `${data.estimated_arrival_minutes} mins` : '15 mins');
    const status = (data.status || '').toLowerCase();
    const fallbackStatus = (state.activeOrder && state.activeOrder.order_status) ? state.activeOrder.order_status : 'In Transit';
    const title = (data.status === 'NOT_FOUND' || (data.status_message && data.status_message.includes('No tracking')))
      ? fallbackStatus
      : (data.title || data.status_message || fallbackStatus);
    const progressPct = data.progress_percentage !== null && data.progress_percentage !== undefined ? data.progress_percentage : 75;

    // Update Header
    const orderIdEl = document.getElementById('tracking-order-id');
    if (orderIdEl) orderIdEl.textContent = `Order #${orderId}`;

    const etaEl = document.getElementById('tracking-eta');
    if (etaEl) etaEl.textContent = `ETA: ~${etaText}`;

    const badgeEl = document.getElementById('tracking-status-badge');
    if (badgeEl) badgeEl.textContent = `Swiggy: ${title}`;

    // Stepper updates
    const progressBar = document.getElementById('timeline-progress');
    const steps = [
      document.getElementById('step-1'),
      document.getElementById('step-2'),
      document.getElementById('step-3'),
      document.getElementById('step-4'),
    ];

    steps.forEach((s) => {
      if (s) s.className = 'step';
    });

    // Dynamic step calculation based on real Swiggy progress
    if (status === 'delivered' || progressPct >= 100) {
      steps.forEach((s) => {
        if (s) s.className = 'step done';
      });
      if (progressBar) progressBar.style.width = '100%';
      moveRiderTo(HOME_COORDS, 'Delivered at Gate');
    } else if (progressPct >= 85 || (etaText && etaText.includes('2 min')) || status === 'arriving') {
      if (steps[0]) steps[0].className = 'step done';
      if (steps[1]) steps[1].className = 'step done';
      if (steps[2]) steps[2].className = 'step done';
      if (steps[3]) steps[3].className = 'step active';
      if (progressBar) progressBar.style.width = '100%';

      // Move rider marker to 2-min gate waypoint
      moveRiderTo(DELIVERY_ROUTE[5], '🚨 Arriving at Gate in 2 mins!');
      if (riderMarker) riderMarker.openPopup();
      if (liveMap) liveMap.setView(DELIVERY_ROUTE[5], 16);

      // TRIGGER PROACTIVE 2-MINUTE GATE ARRIVAL ALERT (ONLY ONCE)
      if (!hasTriggered2MinAlert) {
        hasTriggered2MinAlert = true;
        triggerGateArrivalAlert(orderId, etaText);
      }
    } else if (status === 'picked_up' || status === 'out_for_delivery' || progressPct >= 50) {
      if (steps[0]) steps[0].className = 'step done';
      if (steps[1]) steps[1].className = 'step done';
      if (steps[2]) steps[2].className = 'step active';
      if (progressBar) progressBar.style.width = `${Math.max(50, progressPct)}%`;

      moveRiderTo(DELIVERY_ROUTE[3], `On the way • Speed: 32 km/h (${etaText})`);
      if (liveMap) liveMap.panTo(DELIVERY_ROUTE[3]);
    } else {
      // Preparing
      if (steps[0]) steps[0].className = 'step done';
      if (steps[1]) steps[1].className = 'step active';
      if (progressBar) progressBar.style.width = '25%';
      moveRiderTo(RESTAURANT_COORDS, 'At Meghana Foods • Kitchen preparing food');
    }
  } catch (e) {
    console.warn('Live tracking poll error:', e);
  }
}

function triggerGateArrivalAlert(orderId, etaText) {
  const alertBox = document.getElementById('gate-arrival-alert');
  if (alertBox) {
    alertBox.style.display = 'flex';
    const alertMsg = document.getElementById('gate-arrival-alert-msg');
    if (alertMsg) {
      alertMsg.innerHTML = `Rider <strong>Ravi Kumar</strong> is ${etaText || '2 minutes'} from your building gate in Rajajinagar. Incoming call triggered!`;
    }
  }

  // Play audio chime
  playArrivalChime();

  // Toast
  showToast('🚨 PROACTIVE ALERT: Rider is 2 minutes from your gate in Rajajinagar!');

  // Desktop notification
  if ('Notification' in window && Notification.permission === 'granted') {
    new Notification('SmartFlow: Rider Arriving in 2 Mins!', {
      body: 'Your Meghana Foods food order is arriving at the building gate. Please be ready!',
      icon: 'https://media-assets.swiggy.com/swiggy/image/upload/FOOD_CATALOG/IMAGES/CMS/2025/12/29/57bebf52-5a58-42e0-af9d-3d872d52de83_2d89d14b-3568-4be1-946d-1d7b0539edae.jpg',
    });
  }

  // Trigger Incoming Call Screen with ringtone & speech
  showIncomingCallModal('Ravi Kumar (Swiggy Delivery)', '+91 80 6746 6746 (Arrival Alert)');

  // Dispatch backend automated cellular call
  api.triggerAutomatedCall(null, 'Hello Sravan! Your Swiggy delivery rider Ravi is 2 minutes from your gate in Rajajinagar. Please collect your food.').catch((e) => console.warn('Twilio call notice:', e));
}


async function loadPastOrders() {
  const container = document.getElementById('past-orders-list');
  if (!container) return;
  try {
    const res = await api.getOrders(15);
    if (res.success && res.data && res.data.orders) {
      container.innerHTML = '';
      res.data.orders.forEach((o) => {
        const card = document.createElement('div');
        card.className = 'order-history-card';
        const isLive = o.is_active || ['processing', 'picked_up', 'out_for_delivery', 'placed', 'confirmed', 'on the way'].includes((o.order_status || '').toLowerCase());
        const statusColor = isLive ? '#f59e0b' : '#10b981';

        card.innerHTML = `
          <div>
            <div style="font-weight: 700; display: flex; align-items: center; gap: 8px;">
              <span>${o.restaurant_name}</span>
              ${isLive ? '<span style="font-size: 0.72rem; background: rgba(245, 158, 11, 0.2); color: #f59e0b; padding: 1px 6px; border-radius: 4px;">ACTIVE IN-FLIGHT</span>' : ''}
            </div>
            <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 2px;">${o.ordered_items}</div>
            <div style="font-size: 0.78rem; color: #64748b; margin-top: 2px;">
              ${o.ordered_time || 'Past Order'} • <span style="color: ${statusColor}; font-weight: 600;">${o.order_status}</span>
            </div>
          </div>
          <div style="text-align: right;">
            <div style="font-weight: 800; font-size: 1rem;">${o.order_total}</div>
            ${isLive 
              ? `<button class="chip" style="margin-top: 0.4rem; padding: 4px 12px; background: rgba(245, 158, 11, 0.2); color: #f59e0b; border-color: rgba(245,158,11,0.4);" onclick="trackSpecificOrder('${o.order_id}')">Track Live 🛵</button>`
              : `<button class="chip" style="margin-top: 0.4rem; padding: 2px 10px;" onclick="addDishToCart('86416530', 1)">Reorder 🔁</button>`
            }
          </div>
        `;
        container.appendChild(card);
      });
    }
  } catch (e) {
    console.warn('Could not load past orders:', e);
  }
}

function trackSpecificOrder(orderId) {
  state.activeOrder = { order_id: orderId, is_active: true };
  persistActiveOrder();
  hasTriggered2MinAlert = false;
  syncTrackingTabState();
}

// --- SOUND UTILITIES ---

function playArrivalChime() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
    osc.frequency.setValueAtTime(880, ctx.currentTime + 0.15); // A5
    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.5);
    osc.start();
    osc.stop(ctx.currentTime + 0.5);
  } catch (e) {
    console.warn('Audio not allowed without gesture:', e);
  }
}

// Request Notification Permission on first click
document.body.addEventListener(
  'click',
  () => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  },
  { once: true }
);
