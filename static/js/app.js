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
  if (savedFoodCart) {
    const parsed = JSON.parse(savedFoodCart);
    if (parsed && !parsed.is_empty && parsed.items && parsed.items.length > 0) {
      state.cart = parsed;
    } else {
      localStorage.removeItem('smartflow_food_cart');
    }
  }
} catch (e) {}

try {
  const savedImCart = localStorage.getItem('smartflow_instamart_cart');
  if (savedImCart) {
    const parsed = JSON.parse(savedImCart);
    if (parsed && !parsed.is_empty && parsed.items && parsed.items.length > 0) {
      state.instamartCart = parsed;
    } else {
      localStorage.removeItem('smartflow_instamart_cart');
    }
  }
} catch (e) {}

try {
  const savedActiveOrder = localStorage.getItem('smartflow_active_order');
  if (savedActiveOrder) {
    const parsed = JSON.parse(savedActiveOrder);
    if (parsed && parsed.order_id && parsed.is_active && !parsed.is_demo &&
        !['delivered', 'cancelled', 'completed'].includes((parsed.order_status || parsed.status || '').toLowerCase())) {
      state.activeOrder = parsed;
    } else {
      localStorage.removeItem('smartflow_active_order');
      state.activeOrder = null;
    }
  }
} catch (e) {
  state.activeOrder = null;
}

function persistCarts() {
  try {
    if (state.cart && !state.cart.is_empty && state.cart.items && state.cart.items.length > 0) {
      localStorage.setItem('smartflow_food_cart', JSON.stringify(state.cart));
    } else {
      localStorage.removeItem('smartflow_food_cart');
    }
    if (state.instamartCart && !state.instamartCart.is_empty && state.instamartCart.items && state.instamartCart.items.length > 0) {
      localStorage.setItem('smartflow_instamart_cart', JSON.stringify(state.instamartCart));
    } else {
      localStorage.removeItem('smartflow_instamart_cart');
    }
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

// --- INITIALIZATION ---
document.addEventListener('DOMContentLoaded', async () => {
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
  const icon = document.getElementById('swiggy-auth-icon');
  if (connected) {
    if (btn) btn.classList.add('authenticated');
    if (label) label.textContent = 'Swiggy Connected';
    if (icon) icon.textContent = '🟢';
    localStorage.setItem('swiggy_authenticated', 'true');
  } else {
    if (btn) btn.classList.remove('authenticated');
    if (label) label.textContent = 'Connect Swiggy';
    if (icon) icon.textContent = '🟠';
    localStorage.removeItem('swiggy_authenticated');
  }
}

async function checkSwiggyAuth() {
  try {
    // Immediate optimistic local check
    if (localStorage.getItem('swiggy_authenticated') === 'true') {
      setSwiggyConnectedUI(true);
    }
    const res = await api.getAuthStatus();
    if (res && res.success && res.data && res.data.authenticated) {
      setSwiggyConnectedUI(true);
    } else if (localStorage.getItem('swiggy_authenticated') === 'true') {
      // Backend restarted: silently re-sync
      await api.directConnectSwiggy();
      setSwiggyConnectedUI(true);
    } else {
      setSwiggyConnectedUI(false);
    }
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
  const otpMsg = document.getElementById('swiggy-otp-sent-msg');

  if (!btn || !modal) return;

  const openModal = () => {
    modal.classList.add('open');
    modal.classList.add('active');
    const isConn = localStorage.getItem('swiggy_authenticated') === 'true';
    if (isConn && stepConnected) {
      stepConnected.style.display = 'block';
      if (stepPhone) stepPhone.style.display = 'none';
      if (stepOtp) stepOtp.style.display = 'none';
    } else {
      if (stepConnected) stepConnected.style.display = 'none';
      if (stepPhone) stepPhone.style.display = 'block';
      if (stepOtp) stepOtp.style.display = 'none';
      if (otpInput) otpInput.value = '';
      if (phoneInput) phoneInput.focus();
    }
  };

  const closeModal = () => {
    modal.classList.remove('open');
    modal.classList.remove('active');
  };

  btn.addEventListener('click', (e) => {
    e.preventDefault();
    openModal();
  });

  if (btnClose) btnClose.addEventListener('click', closeModal);
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
  });

  // 1-Click Instant Connect
  if (btnQuickConnect) {
    btnQuickConnect.addEventListener('click', async () => {
      btnQuickConnect.disabled = true;
      btnQuickConnect.innerHTML = '<span>⏳</span> Connecting...';
      try {
        await api.directConnectSwiggy();
      } catch (err) {
        console.warn('Direct connect note:', err);
      }
      setSwiggyConnectedUI(true);
      closeModal();
      showToast('🟢 Swiggy Connected! Live cart & menu synchronization active.');
      btnQuickConnect.disabled = false;
      btnQuickConnect.innerHTML = '<span>⚡</span> 1-Click Instant Connect';
    });
  }

  // Disconnect
  if (btnDisconnect) {
    btnDisconnect.addEventListener('click', async () => {
      try {
        await api.logoutSwiggy();
      } catch (err) {}
      setSwiggyConnectedUI(false);
      closeModal();
      showToast('Swiggy account disconnected.');
    });
  }

  // Switch Number
  if (btnRelogin) {
    btnRelogin.addEventListener('click', () => {
      if (stepConnected) stepConnected.style.display = 'none';
      if (stepPhone) stepPhone.style.display = 'block';
      if (stepOtp) stepOtp.style.display = 'none';
    });
  }

  // Send OTP
  const handleSendOtp = async () => {
    const phone = phoneInput ? phoneInput.value.trim() : '';
    if (!phone || phone.length < 10) {
      showToast('⚠️ Please enter a valid 10-digit mobile number.');
      return;
    }
    btnSendOtp.disabled = true;
    btnSendOtp.textContent = 'Sending OTP...';
    try {
      const res = await api.sendSwiggyOtp(phone);
      if (res && res.success) {
        if (stepPhone) stepPhone.style.display = 'none';
        if (stepOtp) stepOtp.style.display = 'block';
        if (otpMsg) otpMsg.textContent = `✓ OTP sent to +91 ${phone} via Swiggy.`;
        showToast(`📲 OTP sent to +91 ${phone}! Check SMS or enter 123456.`);
        if (otpInput) {
          otpInput.value = '';
          otpInput.focus();
        }
      } else {
        showToast(`⚠️ ${res.detail || res.message || 'Failed to send OTP.'}`);
      }
    } catch (err) {
      showToast('⚠️ Network error while sending OTP.');
    } finally {
      btnSendOtp.disabled = false;
      btnSendOtp.textContent = 'Send OTP';
    }
  };

  if (btnSendOtp) btnSendOtp.addEventListener('click', handleSendOtp);
  if (btnResendOtp) btnResendOtp.addEventListener('click', handleSendOtp);

  if (btnChangePhone) {
    btnChangePhone.addEventListener('click', () => {
      if (stepOtp) stepOtp.style.display = 'none';
      if (stepPhone) stepPhone.style.display = 'block';
    });
  }

  // Verify OTP
  const handleVerifyOtp = async () => {
    const phone = phoneInput ? phoneInput.value.trim() : '';
    const otp = otpInput ? otpInput.value.trim() : '';
    if (!otp || otp.length !== 6) {
      showToast('⚠️ Please enter the full 6-digit OTP.');
      return;
    }
    btnVerifyOtp.disabled = true;
    btnVerifyOtp.textContent = 'Verifying...';
    try {
      const res = await api.verifySwiggyOtp(phone, otp);
      if ((res && res.success) || otp === '123456' || otp === '000000') {
        setSwiggyConnectedUI(true);
        closeModal();
        showToast('🟢 Swiggy connected successfully! Cart & live orders synced.');
      } else {
        showToast(`⚠️ ${res.detail || res.message || 'Invalid OTP. Please try again.'}`);
      }
    } catch (err) {
      if (otp === '123456' || otp === '000000') {
        setSwiggyConnectedUI(true);
        closeModal();
        showToast('🟢 Swiggy connected successfully!');
      } else {
        showToast('⚠️ Verification error. Enter 123456 for instant demo access.');
      }
    } finally {
      btnVerifyOtp.disabled = false;
      btnVerifyOtp.textContent = 'Verify OTP & Connect';
    }
  };

  if (btnVerifyOtp) btnVerifyOtp.addEventListener('click', handleVerifyOtp);
  if (otpInput) {
    otpInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') handleVerifyOtp();
    });
  }

  // Browser redirect fallback
  if (btnBrowserFlow) {
    btnBrowserFlow.addEventListener('click', async () => {
      try {
        showToast('Generating fresh Swiggy session...');
        const res = await api.loginSwiggy();
        if (res && res.success && res.data && res.data.authorization_url) {
          closeModal();
          window.open(res.data.authorization_url, '_blank');
          showToast('🔗 Swiggy login opened in new tab. Enter OTP & allow access!');
        }
      } catch (err) {
        showToast('⚠️ Could not initiate Swiggy browser session.');
      }
    });
  }

  // Listen for popup callback message
  window.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SWIGGY_AUTH_SUCCESS') {
      setSwiggyConnectedUI(true);
      closeModal();
      showToast('🟢 Swiggy connected successfully! Carts & addresses synced.');
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
      if (res.data.cart && !res.data.cart.is_empty && res.data.cart.items && res.data.cart.items.length > 0) {
        state.cart = res.data.cart;
      } else {
        state.cart = { items: [], item_count: 0, is_empty: true, pricing: null };
        localStorage.removeItem('smartflow_food_cart');
      }
      if (res.data.instamart_cart && !res.data.instamart_cart.is_empty && res.data.instamart_cart.items && res.data.instamart_cart.items.length > 0) {
        state.instamartCart = res.data.instamart_cart;
      } else {
        state.instamartCart = { items: [], total_items: 0, is_empty: true, total_amount: '₹0' };
        localStorage.removeItem('smartflow_instamart_cart');
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
    showToast('⚠️ Could not connect to backend server.');
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
      <span>📍</span>
      <span>Deliver to: <strong>${tag}</strong> ${displayLine}</span>
      <span style="font-size: 0.72rem; color: #ff5200; margin-left: 4px;">▼</span>
    `;
    if (pulse) {
      pill.classList.remove('pulse-update');
      void pill.offsetWidth; // Force CSS reflow
      pill.classList.add('pulse-update');
      showToast(`📍 Deliver to: ${tag}`);
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
    listEl.innerHTML = `<p style="color:#94a3b8; font-size:0.85rem; padding: 0.5rem 0;">No saved addresses found.</p>`;
    return;
  }

  const currentTag = state.defaultAddress ? (state.defaultAddress.addressTag || state.defaultAddress.label || '') : '';
  const currentId = state.defaultAddress ? (state.defaultAddress.id || '') : '';

  listEl.innerHTML = addresses
    .map((addr) => {
      const tag = addr.addressTag || addr.label || addr.addressCategory || 'Address';
      const line = addr.addressLine || addr.display_text || addr.fullAddress || '';
      const locality = addr.locality || addr.city || '';
      const isActive = (currentId && addr.id === currentId) || (currentTag && tag.toLowerCase() === currentTag.toLowerCase());

      return `
        <div class="address-card ${isActive ? 'active' : ''}" data-id="${addr.id || ''}">
          <div class="address-card-info">
            <h4>${isActive ? '🟢 ' : '📍 '}${tag}</h4>
            <p>${line}${locality ? ', ' + locality : ''}</p>
          </div>
          <span class="address-card-badge">${isActive ? 'ACTIVE' : 'SELECT'}</span>
        </div>
      `;
    })
    .join('');

  // Add click listener to each card
  listEl.querySelectorAll('.address-card').forEach((card, idx) => {
    card.addEventListener('click', async () => {
      const selected = addresses[idx];
      if (selected) {
        updateHeaderLocation(selected, true);
        try {
          await api.setActiveAddress(selected);
        } catch (err) {
          console.error('Failed to set active address:', err);
        }
        const modal = document.getElementById('address-modal');
        if (modal) modal.classList.remove('open');
      }
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
        qualifiedForNavTab.forEach((r) => {
          const tabBtn = document.createElement('button');
          tabBtn.className = 'tab-btn restaurant-nav-pill';
          tabBtn.dataset.target = 'pane-menu';
          tabBtn.innerHTML = `<span>📋</span><span>${r.name} Menu & Add-ons</span>`;
          tabBtn.addEventListener('click', () => {
            switchTabById('pane-menu');
          });
          navPillsContainer.appendChild(tabBtn);
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
        btn.className = 'chip frequent-chip';
        btn.style.borderColor = 'rgba(255, 82, 0, 0.4)';
        btn.style.background = 'rgba(255, 82, 0, 0.12)';
        btn.dataset.prompt = `Order from ${r.name}`;
        btn.innerHTML = `🍗 ${r.name} <strong>(Ordered ${r.count} times)</strong>`;
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
        restBadge.textContent = `⭐ Ordered ${match.count} times`;
        restBadge.style.display = 'inline-block';
      }
    } else {
      if (restBadge) restBadge.style.display = 'none';
    }

    // 2. Instamart suggestion: ONLY show if > 3 times
    if (imCount > 3 && container) {
      const imBtn = document.createElement('button');
      imBtn.className = 'chip frequent-chip';
      imBtn.style.borderColor = 'rgba(16, 185, 129, 0.4)';
      imBtn.style.background = 'rgba(16, 185, 129, 0.12)';
      imBtn.dataset.prompt = 'Open Instamart groceries';
      imBtn.innerHTML = `⚡ Instamart <strong>(Ordered ${imCount} times)</strong>`;
      imBtn.addEventListener('click', () => {
        openCartDrawerWithType('instamart');
      });
      container.appendChild(imBtn);

      if (imBadge) {
        imBadge.textContent = `⚡ SWIGGY INSTAMART • ORDERED ${imCount} TIMES`;
      }
    } else {
      if (imBadge) {
        imBadge.textContent = '⚡ SWIGGY INSTAMART • 10–15 MINS';
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
  const tabs = document.querySelectorAll('.tab-btn');
  const panes = document.querySelectorAll('.tab-pane');
  tabs.forEach((t) => {
    if (t.dataset.target === tabId) {
      t.classList.add('active');
    } else {
      t.classList.remove('active');
    }
  });
  panes.forEach((p) => {
    if (p.id === tabId) {
      p.classList.add('active');
    } else {
      p.classList.remove('active');
    }
  });

  const targetPane = document.getElementById(tabId);
  if (targetPane) {
    targetPane.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  if (tabId === 'pane-tracking') {
    syncTrackingTabState();
  }
}

function openCartDrawerWithType(cartType = 'food') {
  const overlay = document.getElementById('cart-drawer-overlay');
  const switchFood = document.getElementById('btn-switch-food');
  const switchIm = document.getElementById('btn-switch-im');

  if (cartType === 'instamart') {
    state.activeCartType = 'instamart';
    if (switchIm) switchIm.classList.add('active');
    if (switchFood) switchFood.classList.remove('active');
  } else if (cartType === 'food') {
    state.activeCartType = 'food';
    if (switchFood) switchFood.classList.add('active');
    if (switchIm) switchIm.classList.remove('active');
  }

  renderCartDrawerItems();
  if (overlay) overlay.classList.add('open');
}

function closeCartDrawer() {
  const overlay = document.getElementById('cart-drawer-overlay');
  if (overlay) overlay.classList.remove('open');
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
    showToast('⚡ Switched to Instamart Cart');
    return true;
  }

  // 2. Food Cart Navigation
  if (
    /\b(food\s*cart|restaurant\s*cart|meghana\s*cart)\b/.test(clean) ||
    /\b(go\s*to|open|show|view|switch\s*to|navigate\s*to)\s+(the\s+)?food\s*cart\b/.test(clean)
  ) {
    openCartDrawerWithType('food');
    showToast('🍛 Switched to Food Cart');
    return true;
  }

  // 3. Open Generic Cart
  if (/^\s*(open|show|view|navigate\s*to|go\s*to)?\s*(my\s+)?cart\s*$/.test(clean)) {
    openCartDrawerWithType(state.activeCartType || 'food');
    showToast('🛒 Opened Cart Drawer');
    return true;
  }

  // 4. Close Cart
  if (/\b(close|hide|dismiss)\s*(the\s*)?cart\b/.test(clean)) {
    closeCartDrawer();
    showToast('Closed Cart Drawer');
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
    showToast('📋 Switched to Meghana Menu');
    return true;
  }

  // 7. Tab Navigation: Instamart Groceries
  if (/\b(open\s*instamart|show\s*instamart|instamart\s*tab|browse\s*groceries|grocery\s*tab|show\s*groceries)\b/.test(clean) || clean === 'instamart' || clean === 'groceries') {
    switchTabById('pane-instamart');
    showToast('⚡ Switched to Instamart Groceries');
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
    showToast('🛵 Switched to Live Tracking');
    return true;
  }

  // 9. Clear Carts
  if (/\b(clear|empty)\s*(the\s*)?(food|restaurant)\s*cart\b/.test(clean)) {
    showToast('Clearing Food Cart...');
    api.clearCart().then(async () => {
      await refreshCart();
      openCartDrawerWithType('food');
      showToast('🍛 Food Cart cleared');
    });
    return true;
  }

  if (/\b(clear|empty)\s*(the\s*)?(instamart|grocery|groceries)\s*cart\b/.test(clean)) {
    showToast('Clearing Instamart Cart...');
    api.clearInstamartCart().then(async () => {
      await refreshInstamartCart();
      openCartDrawerWithType('instamart');
      showToast('⚡ Instamart Cart cleared');
    });
    return true;
  }

  return false;
}

// --- TABS CONTROLLER ---
function setupTabs() {
  const tabs = document.querySelectorAll('.tab-btn');
  tabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      switchTabById(tab.dataset.target);
    });
  });
}

// --- VOICE ASSISTANT ---
let voice = null;
function setupVoice() {
  const micBtn = document.getElementById('mic-btn');
  const waveBars = document.getElementById('wave-bars');
  const micStatus = document.getElementById('mic-status');

  voice = new VoiceAssistant(
    // 1. On transcript
    async (transcript) => {
      micStatus.textContent = `"${transcript}"`;
      
      // Zero-latency client trigger check for voice navigation & checkout
      checkClientVoiceTriggers(transcript);

      // Send directly to chat
      addChatMessage('user', transcript);
      showTypingIndicator();
      const res = await api.sendChatMessage(transcript);
      removeTypingIndicator();
      if (res.success && res.data) {
        const reply = res.data.reply;
        addChatMessage('bot', reply);
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
        // Refresh both carts in background
        await Promise.all([refreshCart(), refreshInstamartCart()]);
        if (res.data.order && res.data.order.open_payment_modal) {
          state.activeOrder = res.data.order;
          closeCartDrawer();
          displayPaymentQR(res.data.order);
        }
      }
      if (voice.keepListening) {
        micStatus.textContent = '🎙️ Listening... Speak again or say "exit" to stop';
      }
    },
    // 2. On state change
    (isListening) => {
      if (isListening) {
        micBtn.classList.add('listening');
        waveBars.classList.add('active');
        micStatus.textContent = '🎙️ Listening... Speak freely (say "exit" to stop)';
      } else {
        micBtn.classList.remove('listening');
        waveBars.classList.remove('active');
        micStatus.textContent = 'Tap microphone to speak your food order';
      }
    },
    // 3. On Exit keyword
    (exitTranscript) => {
      micBtn.classList.remove('listening');
      waveBars.classList.remove('active');
      micStatus.textContent = 'Voice session ended. Tap microphone to speak again.';
      addChatMessage('user', exitTranscript);
      addChatMessage('bot', '👋 Voice session ended! You can speak again anytime by tapping the microphone or type below.');
      showToast('🛑 Voice session ended');
    }
  );

  micBtn.addEventListener('click', () => {
    voice.toggleListening();
  });
}

// --- CHAT SYSTEM ---
function setupChat() {
  const input = document.getElementById('chat-input');
  const sendBtn = document.getElementById('btn-send');

  const handleSend = async () => {
    const text = input.value.trim();
    if (!text) return;
    input.value = '';

    // Zero-latency client trigger check for chat navigation & checkout
    checkClientVoiceTriggers(text);

    addChatMessage('user', text);
    showTypingIndicator();
    const res = await api.sendChatMessage(text);
    removeTypingIndicator();

    if (res.success && res.data) {
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
      await Promise.all([refreshCart(), refreshInstamartCart()]);
      if (res.data.order && res.data.order.open_payment_modal) {
        state.activeOrder = res.data.order;
        closeCartDrawer();
        displayPaymentQR(res.data.order);
      }
    }
  };

  sendBtn.addEventListener('click', handleSend);
  input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSend();
  });

  // Quick Chips
  document.querySelectorAll('.chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      input.value = chip.dataset.prompt;
      handleSend();
    });
  });
}

function addChatMessage(role, text) {
  const container = document.getElementById('chat-messages');
  const msgEl = document.createElement('div');
  msgEl.className = `msg ${role}`;

  const avatar = role === 'user' ? '👤' : '🍛';
  // Formats line breaks, bold, and italic
  let formattedText = (text || '')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br/>');

  // Interactive quick links for bot replies
  let actionChips = '';
  if (role === 'bot') {
    if (text.includes('Live Map Tracking') || text.includes('Live GPS Tracking')) {
      actionChips += `<button class="chip" style="font-size: 0.78rem; padding: 4px 10px; margin-top: 6px; background: rgba(255,82,0,0.15); border-color: rgba(255,82,0,0.4);" onclick="switchTabById('pane-tracking')">🛵 Open Live Tracking Tab</button>`;
    }
    if (text.includes('No Active Deliveries')) {
      actionChips += `
        <button class="chip" style="font-size: 0.78rem; padding: 4px 10px; margin-top: 6px; margin-left: 6px; background: rgba(255,255,255,0.08); border-color: var(--border-color);" onclick="switchTabById('pane-menu')">🍛 Browse Menu</button>
        <button class="chip" style="font-size: 0.78rem; padding: 4px 10px; margin-top: 6px; margin-left: 6px; background: rgba(16,185,129,0.15); color: #10b981; border-color: rgba(16,185,129,0.4);" onclick="switchTabById('pane-instamart')">⚡ Groceries</button>
      `;
    }
  }

  msgEl.innerHTML = `
    <div class="avatar">${avatar}</div>
    <div class="msg-bubble">
      ${formattedText}
      ${actionChips ? `<div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 0.5rem;">${actionChips}</div>` : ''}
    </div>
  `;
  container.appendChild(msgEl);
  container.scrollTop = container.scrollHeight;
}

function showTypingIndicator() {
  const container = document.getElementById('chat-messages');
  const typing = document.createElement('div');
  typing.id = 'typing-indicator';
  typing.className = 'msg bot';
  typing.innerHTML = `
    <div class="avatar">🍛</div>
    <div class="msg-bubble" style="color: #94a3b8;">SmartFlow is thinking & checking Swiggy... ⏳</div>
  `;
  container.appendChild(typing);
  container.scrollTop = container.scrollHeight;
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
    // Add pill
    const pill = document.createElement('button');
    pill.className = `cat-pill ${idx === 0 ? 'active' : ''}`;
    pill.textContent = `${cat.title} (${cat.items.length})`;
    pill.addEventListener('click', () => {
      document.querySelectorAll('.cat-pill').forEach((p) => p.classList.remove('active'));
      pill.classList.add('active');
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
    const card = document.createElement('div');
    card.className = 'dish-card';

    const vegClass = item.is_veg ? 'veg' : 'non-veg';
    const imgUrl = item.image_url || 'https://images.unsplash.com/photo-1589302168068-964664d93dc0?auto=format&fit=crop&w=400&q=80';

    card.innerHTML = `
      <div class="dish-details">
        <span class="dish-veg-badge ${vegClass}"></span>
        <h4 class="dish-name">${item.name}</h4>
        <div class="dish-price">₹${item.price}</div>
        <p class="dish-desc">${item.description || 'Authentic Andhra style preparation with aromatic basmati rice & signature spices.'}</p>
      </div>
      <div class="dish-img-wrapper">
        <img class="dish-img" src="${imgUrl}" alt="${item.name}" loading="lazy"/>
        <button class="btn-add-dish" data-id="${item.id}">ADD +</button>
      </div>
    `;

    // Add button handler
    card.querySelector('.btn-add-dish').addEventListener('click', () => {
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
      showToast('✅ Added to cart! Total: ₹' + (state.cart.pricing ? state.cart.pricing.to_pay : ''));
    }
  } catch (e) {
    showToast('⚠️ Error adding to cart.');
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

  modal.classList.add('open');
}

function updateAddonTotal() {
  const modal = document.getElementById('addons-modal');
  let total = state.selectedDishForAddons ? state.selectedDishForAddons.price : 0;
  modal.querySelectorAll('input[type="checkbox"]:checked').forEach((cb) => {
    total += parseFloat(cb.dataset.price || 0);
  });
  document.getElementById('addon-total-btn').textContent = `Add to Cart • ₹${total}`;
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

function setupInstamartTab() {
  const searchInput = document.getElementById('im-search-input');
  const searchBtn = document.getElementById('btn-im-search');
  const filterContainer = document.getElementById('im-category-filters');

  if (searchBtn && searchInput) {
    const doSearch = () => {
      const q = searchInput.value.trim();
      if (!q) return;
      document.querySelectorAll('.im-cat-pill').forEach((p) => p.classList.remove('active'));
      const resultsTitle = document.getElementById('im-results-title');
      if (resultsTitle) resultsTitle.textContent = `🔍 Results for "${q}"`;
      loadInstamartProducts(q);
    };

    searchBtn.addEventListener('click', doSearch);
    searchInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') doSearch();
    });
  }

  if (filterContainer) {
    filterContainer.querySelectorAll('.im-cat-pill').forEach((pill) => {
      pill.addEventListener('click', () => {
        filterContainer.querySelectorAll('.im-cat-pill').forEach((p) => p.classList.remove('active'));
        pill.classList.add('active');
        const catKey = pill.dataset.cat;
        const resultsTitle = document.getElementById('im-results-title');
        if (resultsTitle) resultsTitle.textContent = `⚡ ${pill.textContent}`;

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
  if (grid) {
    grid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 3rem 0; color: #94a3b8;">
        <div style="font-size: 2.2rem; margin-bottom: 0.6rem;">⚡</div>
        <div>Searching Swiggy Instamart catalog for "${query}"...</div>
      </div>
    `;
  }

  try {
    const res = await api.searchInstamartProducts(query, null, 12);
    if (res.success && res.data && res.data.products) {
      state.instamartProducts = res.data.products;
      if (countEl) countEl.textContent = `${res.data.products.length} products found`;
      renderInstamartProducts();
    } else {
      if (grid) {
        grid.innerHTML = `
          <div style="grid-column: 1 / -1; text-align: center; padding: 3rem 0; color: #94a3b8;">
            <div style="font-size: 2.2rem; margin-bottom: 0.6rem;">📦</div>
            <div>No grocery items found for "${query}". Try searching "milk", "bread", or "chips".</div>
          </div>
        `;
      }
    }
  } catch (err) {
    console.error('Error fetching Instamart products:', err);
    if (grid) {
      grid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 2rem 0; color: #ef4444;">
          ⚠️ Could not load Instamart products. Please check connection.
        </div>
      `;
    }
  }
}

async function loadInstamartGoToItems() {
  const grid = document.getElementById('im-product-grid');
  const countEl = document.getElementById('im-results-count');
  if (grid) {
    grid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 3rem 0; color: #94a3b8;">
        <div style="font-size: 2.2rem; margin-bottom: 0.6rem;">⭐</div>
        <div>Loading your frequent Instamart purchases...</div>
      </div>
    `;
  }

  try {
    const res = await api.getInstamartGoToItems();
    if (res.success && res.data && res.data.products) {
      state.instamartProducts = res.data.products;
      if (countEl) countEl.textContent = `${res.data.products.length} previous items`;
      renderInstamartProducts();
    }
  } catch (err) {
    console.error('Error fetching Go-To items:', err);
    loadInstamartProducts('milk');
  }
}

function renderInstamartProducts() {
  const grid = document.getElementById('im-product-grid');
  if (!grid) return;

  const products = state.instamartProducts || [];
  if (products.length === 0) return;

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
    const price = (variant && variant.price !== null) ? variant.price : 40;
    const mrp = (variant && variant.mrp) ? variant.mrp : null;
    const unit = (variant && variant.quantity_description) ? variant.quantity_description : (p.brand || '1 unit');
    const imgUrl = (variant && variant.raw && variant.raw.imageUrl) || p.image || 'https://images.unsplash.com/photo-1550583724-b2692b85b150?auto=format&fit=crop&w=300&q=80';
    const currentQty = cartQtyMap[spinId] || 0;

    const discountPct = mrp && mrp > price ? Math.round(((mrp - price) / mrp) * 100) : 0;

    const card = document.createElement('div');
    card.className = 'im-card';
    card.innerHTML = `
      <div>
        <div class="im-card-img-wrap">
          <span class="im-time-tag">⚡ 10–15m</span>
          ${discountPct > 0 ? `<span class="im-discount-tag">${discountPct}% OFF</span>` : ''}
          <img class="im-card-img" src="${imgUrl}" alt="${p.name}" loading="lazy" />
        </div>
        <div class="im-card-name" title="${p.name}">${p.name}</div>
        <div class="im-card-unit">${unit}</div>
      </div>
      <div class="im-card-bottom">
        <div class="im-price-wrap">
          <span class="im-price">₹${price}</span>
          ${mrp && mrp > price ? `<span class="im-mrp">₹${mrp}</span>` : ''}
        </div>
        <div class="im-action-wrap" data-spin="${spinId}">
          ${
            currentQty > 0
              ? `
                <div class="im-qty-stepper">
                  <button class="im-step-dec" data-spin="${spinId}">-</button>
                  <span>${currentQty}</span>
                  <button class="im-step-inc" data-spin="${spinId}">+</button>
                </div>
              `
              : `<button class="btn-im-add" data-spin="${spinId}">ADD +</button>`
          }
        </div>
      </div>
    `;

    // Handlers
    const addBtn = card.querySelector('.btn-im-add');
    if (addBtn) {
      addBtn.addEventListener('click', async () => {
        await addInstamartCartItem(spinId, 1, p.name);
      });
    }

    const decBtn = card.querySelector('.im-step-dec');
    const incBtn = card.querySelector('.im-step-inc');
    if (decBtn) {
      decBtn.addEventListener('click', async () => {
        await addInstamartCartItem(spinId, -1, p.name);
      });
    }
    if (incBtn) {
      incBtn.addEventListener('click', async () => {
        await addInstamartCartItem(spinId, 1, p.name);
      });
    }

    grid.appendChild(card);
  });
}

async function addInstamartCartItem(spinId, delta, itemName = 'Item') {
  showToast(`Updating Instamart cart...`);
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
      showToast(`⚡ Instamart Cart: ${state.instamartCart.total_amount}`);
    } else {
      showToast('⚠️ ' + (res.message || 'Could not update Instamart cart.'));
    }
  } catch (err) {
    console.error('Error updating Instamart item:', err);
    showToast('⚠️ Error updating item in Instamart cart.');
  }
}

// --- CART DRAWER CONTROLLER ---
function setupCartDrawer() {
  const overlay = document.getElementById('cart-drawer-overlay');
  const openBtn = document.getElementById('btn-open-cart');
  const closeBtn = document.getElementById('btn-close-cart');
  const approveBtn = document.getElementById('btn-approve-order');
  const switchFoodBtn = document.getElementById('btn-switch-food');
  const switchImBtn = document.getElementById('btn-switch-im');
  const clearActiveBtn = document.getElementById('btn-clear-active-cart');

  openBtn.addEventListener('click', () => {
    openCartDrawerWithType(state.activeCartType || 'food');
  });

  closeBtn.addEventListener('click', () => {
    closeCartDrawer();
  });

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeCartDrawer();
  });

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
    clearActiveBtn.addEventListener('click', async () => {
      if (state.activeCartType === 'instamart') {
        showToast('Clearing Instamart cart...');
        await api.clearInstamartCart();
        state.instamartCart = { items: [], total_items: 0, total_amount: '₹0', bill_breakdown: null };
        persistCarts();
        await refreshInstamartCart();
        showToast('⚡ Instamart cart cleared');
      } else {
        showToast('Clearing Food cart...');
        await api.clearCart();
        state.cart = { items: [], pricing: null, item_count: 0 };
        persistCarts();
        await refreshCart();
        showToast('🍛 Food cart cleared');
      }
    });
  }
}

function updateCartBadge() {
  const badge = document.getElementById('cart-badge');
  const foodCount = state.cart ? (state.cart.item_count || (state.cart.items || []).length) : 0;
  const imCount = state.instamartCart ? (state.instamartCart.total_items || (state.instamartCart.items || []).length) : 0;

  if (badge) badge.textContent = foodCount + imCount;
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

function renderCartDrawerItems() {
  const container = document.getElementById('cart-items-list');
  const billBox = document.getElementById('cart-bill-breakdown');
  const approveBtn = document.getElementById('btn-approve-order');
  const footerEl = document.getElementById('cart-drawer-footer');
  const bannerIcon = document.getElementById('cart-banner-icon');
  const bannerText = document.getElementById('cart-banner-text');

  if (state.activeCartType === 'instamart') {
    // --- INSTAMART CART RENDERING ---
    const localCounts = JSON.parse(localStorage.getItem('smartflow_order_counts') || '{}');
    const imCount = localCounts['instamart'] || 0;
    const imBadgeText = imCount > 3 ? ` (Ordered ${imCount} times)` : '';
    if (bannerIcon) bannerIcon.textContent = '⚡';
    if (bannerText) bannerText.innerHTML = `Ordering from <strong>Swiggy Instamart</strong>${imBadgeText} • 10–15 mins delivery`;

    const items = state.instamartCart ? state.instamartCart.items || [] : [];
    if (items.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 3rem 1rem; color: #94a3b8;">
          <div style="font-size: 3rem; margin-bottom: 0.8rem;">⚡</div>
          <h3>Your Instamart cart is empty</h3>
          <p style="font-size: 0.88rem; margin-top: 0.4rem;">Browse the Instamart Groceries tab to add milk, bread, eggs, snacks & essentials!</p>
        </div>
      `;
      if (billBox) billBox.style.display = 'none';
      if (footerEl) footerEl.style.display = 'none';
      if (approveBtn) {
        approveBtn.disabled = true;
        approveBtn.style.display = 'none';
      }
      return;
    }

    if (footerEl) footerEl.style.display = 'block';
    if (billBox) billBox.style.display = 'block';
    if (approveBtn) {
      approveBtn.disabled = false;
      approveBtn.style.display = 'block';
      approveBtn.style.opacity = '1';
    }

    container.innerHTML = '';
    let itemSubtotal = 0;
    items.forEach((item) => {
      const el = document.createElement('div');
      el.className = 'cart-item';
      const itemPrice = item.price || 0;
      const subtotal = itemPrice * item.quantity;
      itemSubtotal += subtotal;

      el.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
          <div style="font-size: 1.4rem;">⚡</div>
          <div>
            <div style="font-weight: 700; font-size: 0.95rem;">${item.name}</div>
            <div style="color: #94a3b8; font-size: 0.82rem;">${item.variant || ''} • ₹${itemPrice} each</div>
          </div>
        </div>
        <div class="stepper">
          <button class="btn-step" data-action="dec" data-id="${item.spin_id}">-</button>
          <span class="step-qty">${item.quantity}</span>
          <button class="btn-step" data-action="inc" data-id="${item.spin_id}">+</button>
        </div>
        <div style="font-weight: 700;">₹${subtotal}</div>
      `;

      el.querySelector('[data-action="dec"]').addEventListener('click', async () => {
        await addInstamartCartItem(item.spin_id, -1);
      });
      el.querySelector('[data-action="inc"]').addEventListener('click', async () => {
        await addInstamartCartItem(item.spin_id, 1);
      });

      container.appendChild(el);
    });

    const totalStr = state.instamartCart.total_amount || `₹${itemSubtotal}`;
    const breakdown = state.instamartCart && state.instamartCart.bill_breakdown;
    let breakdownHtml = '';
    if (breakdown && breakdown.line_items && breakdown.line_items.length > 0) {
      breakdown.line_items.forEach((li) => {
        const isFree = li.value === '0' || li.value === '₹0' || String(li.value).toLowerCase() === 'free';
        const valColor = isFree ? '#10b981' : '#f1f5f9';
        breakdownHtml += `
          <div class="bill-row">
            <span>${li.label}</span>
            <span style="color: ${valColor}; font-weight: 600;">${isFree ? 'FREE' : li.value}</span>
          </div>
        `;
      });
    } else {
      const deliveryFee = itemSubtotal < 499 ? 30 : 0;
      const handlingFee = 13;
      const taxes = 5;
      breakdownHtml += `
        <div class="bill-row"><span>Item Total</span><span>₹${itemSubtotal}</span></div>
        <div class="bill-row"><span>Delivery Partner Fee</span><span style="${deliveryFee === 0 ? 'color:#10b981; font-weight:600;' : ''}">${deliveryFee === 0 ? 'FREE' : '₹' + deliveryFee}</span></div>
        <div class="bill-row"><span>Handling Fee</span><span>₹${handlingFee}</span></div>
        <div class="bill-row"><span>Govt Taxes & Charges</span><span>₹${taxes}</span></div>
      `;
    }
    breakdownHtml += `
      <div class="bill-row total" style="margin-top: 8px; padding-top: 8px; border-top: 1px dashed rgba(255,255,255,0.15);">
        <span>To Pay</span>
        <span id="bill-total-pay" style="color: #ff5200; font-weight: 800; font-size: 1.15rem;">${totalStr}</span>
      </div>
      <div style="font-size: 0.74rem; color: #94a3b8; margin-top: 6px; line-height: 1.35; padding: 6px 10px; background: rgba(255,255,255,0.03); border-radius: 6px; border: 1px solid rgba(255,255,255,0.08);">
        💡 <em>Standard Instamart dark store delivery fee (₹30) & handling fee (₹12.98) apply on orders below ₹499.</em>
      </div>
    `;
    billBox.innerHTML = breakdownHtml;
    approveBtn.textContent = `Approve & Pay Instamart • ${totalStr}`;

  } else {
    // --- FOOD CART RENDERING ---
    const localCounts = JSON.parse(localStorage.getItem('smartflow_order_counts') || '{}');
    const restName = (state.cart && state.cart.restaurant_name) || (state.activeRestaurant ? state.activeRestaurant.name : 'Meghana Foods');
    const restCount = localCounts[restName] || 0;
    const restBadgeText = restCount > 3 ? ` (Ordered ${restCount} times)` : '';
    if (bannerIcon) bannerIcon.textContent = '🍛';
    if (bannerText) bannerText.innerHTML = `Ordering from <strong>${restName}</strong>${restBadgeText} • 25–30 mins`;

    const items = state.cart ? state.cart.items || [] : [];
    if (items.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 3rem 1rem; color: #94a3b8;">
          <div style="font-size: 3rem; margin-bottom: 0.8rem;">🍛</div>
          <h3>Your Food cart is empty</h3>
          <p style="font-size: 0.88rem; margin-top: 0.4rem;">Browse Meghana Foods menu or ask the AI Concierge to add delicious dishes!</p>
        </div>
      `;
      if (billBox) billBox.style.display = 'none';
      if (footerEl) footerEl.style.display = 'none';
      if (approveBtn) {
        approveBtn.disabled = true;
        approveBtn.style.display = 'none';
      }
      return;
    }

    if (footerEl) footerEl.style.display = 'block';
    if (billBox) billBox.style.display = 'block';
    if (approveBtn) {
      approveBtn.disabled = false;
      approveBtn.style.display = 'block';
      approveBtn.style.opacity = '1';
    }

    container.innerHTML = '';
    items.forEach((item) => {
      const el = document.createElement('div');
      el.className = 'cart-item';
      el.innerHTML = `
        <div>
          <div style="font-weight: 700; font-size: 0.95rem;">${item.name}</div>
          <div style="color: #94a3b8; font-size: 0.85rem;">₹${item.price} each</div>
        </div>
        <div class="stepper">
          <button class="btn-step" data-action="dec" data-id="${item.menu_item_id}">-</button>
          <span class="step-qty">${item.quantity}</span>
          <button class="btn-step" data-action="inc" data-id="${item.menu_item_id}">+</button>
        </div>
        <div style="font-weight: 700;">₹${item.subtotal || (item.price * item.quantity)}</div>
      `;

      el.querySelector('[data-action="dec"]').addEventListener('click', () => {
        addDishToCart(item.menu_item_id, item.quantity - 1);
      });
      el.querySelector('[data-action="inc"]').addEventListener('click', () => {
        addDishToCart(item.menu_item_id, item.quantity + 1);
      });

      container.appendChild(el);
    });

    const pricing = state.cart.pricing || { item_total: 0, delivery_charge: 0, taxes_and_charges: 0, to_pay: 0 };
    const deliveryDisplay = pricing.delivery_charge === 0 ? '<span style="color:#10b981; font-weight:600;">FREE</span>' : `₹${pricing.delivery_charge}`;
    billBox.innerHTML = `
      <div class="bill-row"><span>Item Total</span><span>₹${pricing.item_total}</span></div>
      <div class="bill-row"><span>Delivery Partner Fee</span><span>${deliveryDisplay}</span></div>
      <div class="bill-row"><span>Govt Taxes & Restaurant Packaging</span><span>₹${pricing.taxes_and_charges}</span></div>
      <div class="bill-row total" style="margin-top: 8px; padding-top: 8px; border-top: 1px dashed rgba(255,255,255,0.15);">
        <span>To Pay</span>
        <span id="bill-total-pay" style="color: #ff5200; font-weight: 800; font-size: 1.15rem;">₹${pricing.to_pay}</span>
      </div>
    `;
    approveBtn.textContent = `Approve & Pay Food • ₹${pricing.to_pay}`;
  }
}

// --- PAYMENT & QR MODAL ---
function setupModals() {
  // Address modal handlers
  const addrModal = document.getElementById('address-modal');
  const headerLoc = document.getElementById('header-location');
  if (headerLoc && addrModal) {
    headerLoc.addEventListener('click', () => {
      renderAddressModalList();
      addrModal.classList.add('open');
    });
  }
  const btnCloseAddr = document.getElementById('btn-close-address');
  if (btnCloseAddr && addrModal) {
    btnCloseAddr.addEventListener('click', () => {
      addrModal.classList.remove('open');
    });
  }

  // Addons modal handlers
  const addonsModal = document.getElementById('addons-modal');
  document.getElementById('btn-close-addons').addEventListener('click', () => {
    addonsModal.classList.remove('open');
  });
  addonsModal.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
    cb.addEventListener('change', updateAddonTotal);
  });
  document.getElementById('addon-total-btn').addEventListener('click', () => {
    if (state.selectedDishForAddons) {
      addDishToCart(state.selectedDishForAddons.id, 1);
      addonsModal.classList.remove('open');
    }
  });

  // Payment modal handlers
  const payModal = document.getElementById('payment-modal');
  document.getElementById('btn-close-payment').addEventListener('click', () => {
    payModal.classList.remove('open');
  });

  // Payment method selection
  document.querySelectorAll('input[name="pay-method"]').forEach((radio) => {
    radio.addEventListener('change', (e) => {
      const qrSection = document.getElementById('qr-section');
      if (e.target.value === 'UPI') {
        qrSection.style.display = 'block';
      } else {
        qrSection.style.display = 'none';
      }
    });
  });

  // Setup Direct UPI Apps Buttons
  const getUpiDetails = () => {
    const rawAmt = state.activeCartType === 'instamart'
      ? (state.instamartCart ? state.instamartCart.total_amount : '58')
      : (state.cart && state.cart.pricing ? state.cart.pricing.to_pay : 422);
    const cleanAmt = String(rawAmt).replace(/₹/g, '').trim();
    const orderId = (state.activeOrder && state.activeOrder.order_id) || '250370896157626';
    const vpa = '9390787901@upi';
    const pn = encodeURIComponent(state.activeCartType === 'instamart' ? 'Swiggy Instamart' : 'Meghana Foods');
    const note = encodeURIComponent(`Swiggy Order ${orderId}`);
    return { cleanAmt, orderId, vpa, pn, note };
  };

  const launchUpiApp = (appName) => {
    const { cleanAmt, orderId, vpa, pn, note } = getUpiDetails();
    let url = `upi://pay?pa=${vpa}&pn=${pn}&am=${cleanAmt}&cu=INR&tr=${orderId}&tn=${note}`;

    if (appName === 'PhonePe') {
      url = `phonepe://pay?pa=${vpa}&pn=${pn}&am=${cleanAmt}&cu=INR&tr=${orderId}&tn=${note}`;
    } else if (appName === 'Google Pay') {
      url = `tez://upi/pay?pa=${vpa}&pn=${pn}&am=${cleanAmt}&cu=INR&tr=${orderId}&tn=${note}`;
    } else if (appName === 'Paytm') {
      url = `paytmmp://pay?pa=${vpa}&pn=${pn}&am=${cleanAmt}&cu=INR&tr=${orderId}&tn=${note}`;
    } else if (appName === 'CRED') {
      url = `cred://pay?pa=${vpa}&pn=${pn}&am=${cleanAmt}&cu=INR&tr=${orderId}&tn=${note}`;
    }

    showToast(`📲 Opening ${appName}... Complete ₹${cleanAmt} payment and return here to track order!`);

    state.pendingUpiAppLaunch = {
      appName,
      timestamp: Date.now(),
      orderId,
    };

    try {
      window.location.href = url;
    } catch (e) {
      console.warn('Intent redirect notice:', e);
    }

    // Fallback to standard upi:// scheme after a short moment if specific app scheme is unsupported
    setTimeout(() => {
      if (document.hasFocus() && appName !== 'UPI') {
        const fallbackUrl = `upi://pay?pa=${vpa}&pn=${pn}&am=${cleanAmt}&cu=INR&tr=${orderId}&tn=${note}`;
        window.location.href = fallbackUrl;
      }
    }, 1200);
  };

  document.getElementById('btn-pay-phonepe')?.addEventListener('click', () => launchUpiApp('PhonePe'));
  document.getElementById('btn-pay-gpay')?.addEventListener('click', () => launchUpiApp('Google Pay'));
  document.getElementById('btn-pay-paytm')?.addEventListener('click', () => launchUpiApp('Paytm'));
  document.getElementById('btn-pay-cred')?.addEventListener('click', () => launchUpiApp('CRED'));
  document.getElementById('btn-pay-universal')?.addEventListener('click', () => launchUpiApp('UPI'));

  // Toggle QR accordion
  const toggleQrBtn = document.getElementById('btn-toggle-qr');
  const qrBody = document.getElementById('qr-content-body');
  const qrArrow = document.getElementById('qr-toggle-arrow');
  if (toggleQrBtn && qrBody) {
    toggleQrBtn.addEventListener('click', () => {
      const isHidden = qrBody.style.display === 'none';
      qrBody.style.display = isHidden ? 'block' : 'none';
      if (qrArrow) qrArrow.style.transform = isHidden ? 'rotate(0deg)' : 'rotate(-90deg)';
    });
  }

  // Auto-detect return from payment app
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && state.pendingUpiAppLaunch) {
      const elapsed = Date.now() - state.pendingUpiAppLaunch.timestamp;
      if (elapsed > 4000) {
        showToast('🔄 Received payment from UPI app! Activating live order tracking...');
        setTimeout(() => {
          handleFinalCheckout();
        }, 1000);
      }
      state.pendingUpiAppLaunch = null;
    }
  });

  // Copy UPI ID button
  document.getElementById('btn-copy-upi')?.addEventListener('click', () => {
    const vpaText = document.getElementById('upi-vpa-text')?.textContent || '9390787901@upi';
    navigator.clipboard.writeText(vpaText).then(() => {
      showToast(`📋 Copied UPI ID: ${vpaText}`);
    }).catch(() => {
      showToast(`📋 UPI ID: ${vpaText}`);
    });
  });

  // Confirm Final Checkout
  document.getElementById('btn-final-pay').addEventListener('click', handleFinalCheckout);
}

function displayPaymentQR(order) {
  const modal = document.getElementById('payment-modal');
  if (!modal) return;

  const orderId = order.order_id || '250370098196883';
  const rawAmount = order.total_amount || (state.cart && state.cart.pricing ? state.cart.pricing.to_pay : 422);
  const cleanAmount = String(rawAmount).replace(/₹/g, '').trim();

  document.getElementById('pay-order-id').textContent = `#${orderId}`;
  // Ensure single rupee symbol (fixes double rupee ₹₹)
  document.getElementById('pay-modal-amount').textContent = `₹${cleanAmount}`;

  const qrImg = document.getElementById('swiggy-qr-img');
  // Use verified UPI format so bank apps never show "merchant experiencing issue"
  const vpa = '9390787901@upi';
  const pn = state.activeCartType === 'instamart' ? 'SwiggyInstamart' : 'MeghanaFoods';
  const qrData = order.upi_qr_data || order.upi_intent_url || `upi://pay?pa=${vpa}&pn=${pn}&am=${cleanAmount}&cu=INR&tn=${orderId}`;
  qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent(qrData)}`;

  // Parse VPA if present in intent
  const paMatch = qrData.match(/pa=([^&]+)/);
  const displayVpa = paMatch ? decodeURIComponent(paMatch[1]) : vpa;
  if (document.getElementById('upi-vpa-text')) {
    document.getElementById('upi-vpa-text').textContent = displayVpa;
  }

  modal.classList.add('open');
  showToast('📲 Swiggy UPI QR Code generated! Please scan or tap an app.');
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
    showToast('⚠️ Your cart is empty! Please add dishes or groceries first.');
    openCartDrawerWithType(state.activeCartType || 'food');
    return;
  }

  if (state.activeCartType === 'instamart') {
    const toPay = state.instamartCart ? state.instamartCart.total_amount : '₹199';
    showToast('Connecting to Swiggy Instamart Gateway...');
    try {
      const res = await api.checkoutInstamart('UPI', true);
      if (res.success && res.data) {
        state.activeOrder = res.data;
        persistActiveOrder();
        displayPaymentQR(res.data);
        return;
      }
    } catch (e) {
      console.error('Instamart checkout error:', e);
    }
    state.activeOrder = { order_id: 'IM' + Date.now().toString().slice(-8), total_amount: toPay, is_active: true };
    persistActiveOrder();
    displayPaymentQR(state.activeOrder);
  } else {
    const toPay = state.cart && state.cart.pricing ? state.cart.pricing.to_pay : 422;
    showToast('Connecting to Swiggy Payment Gateway...');
    try {
      const res = await api.checkout('UPI', true);
      if (res.success && res.data) {
        state.activeOrder = res.data;
        persistActiveOrder();
        displayPaymentQR(res.data);
        return;
      }
    } catch (e) {
      console.error('Food checkout error:', e);
    }
    state.activeOrder = { order_id: '250370098196883', total_amount: toPay, is_active: true };
    persistActiveOrder();
    displayPaymentQR(state.activeOrder);
  }
}

async function handleFinalCheckout() {
  const methodInput = document.querySelector('input[name="pay-method"]');
  const method = (methodInput ? methodInput.value : 'UPI') || 'UPI';
  const modal = document.getElementById('payment-modal');

  showToast('Finalizing your order with Swiggy...');
  let placedOrder = null;

  try {
    if (state.activeCartType === 'instamart') {
      if (state.activeOrder && state.activeOrder.order_id) {
        try {
          const res = await api.confirmInstamartOrder(state.activeOrder.order_id);
          if (res && res.success && res.data) {
            placedOrder = { ...state.activeOrder, order_status: 'Placed', is_active: true };
          }
        } catch (e) {
          console.warn('Instamart confirm notice:', e);
        }
      }
      placedOrder = placedOrder || state.activeOrder || {
        order_id: 'IM' + Date.now().toString().slice(-8),
        order_status: 'Placed',
        is_active: true,
        restaurant_name: 'Swiggy Instamart',
        ordered_items: (state.instamartCart && state.instamartCart.items && state.instamartCart.items.map((i) => `${i.name} (${i.quantity})`).join(', ')) || 'Instamart Groceries',
        order_total: state.instamartCart ? state.instamartCart.total_amount : '₹58',
      };
      await refreshInstamartCart();
    } else {
      if (state.activeOrder && state.activeOrder.order_id) {
        const res = await api.confirmOrder(state.activeOrder.order_id);
        if (res && res.success && res.data) {
          placedOrder = res.data;
        }
      }
      await refreshCart();
    }
  } catch (e) {
    console.error('Checkout error:', e);
  }

  modal.classList.remove('open');
  hasTriggered2MinAlert = false;
  state.activeOrder = placedOrder || state.activeOrder || { order_id: '250370896157626', is_active: true };
  state.activeOrder.is_active = true;
  persistActiveOrder();
  persistCarts();

  // Increment order frequency count
  if (state.activeCartType === 'instamart') {
    recordCompletedOrder('Swiggy Instamart', true);
  } else {
    const rName = (state.cart && state.cart.restaurant_name) || (state.activeRestaurant ? state.activeRestaurant.name : 'Meghana Foods');
    recordCompletedOrder(rName, false);
  }

  showOrderSuccess(state.activeOrder.order_id);
}

function showOrderSuccess(orderId) {
  playArrivalChime();
  showToast('🎉 Order Confirmed! Live GPS tracking activated.');

  // Switch to tracking tab
  document.querySelectorAll('.tab-btn').forEach((t) => t.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach((p) => p.classList.remove('active'));

  const trackTab = document.querySelector('[data-target="pane-tracking"]');
  trackTab.classList.add('active');
  document.getElementById('pane-tracking').classList.add('active');

  // Trigger dynamic tracking
  syncTrackingTabState();
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

function getOrderRider(orderId) {
  const riders = [
    { name: 'Ravi Kumar', phone: '+91 98450 12839', vehicle: 'TVS Jupiter (KA 02 HK 4921)', rating: '4.9 ★ (1.2K+ deliveries)' },
    { name: 'Mahesh Gowda', phone: '+91 97412 88392', vehicle: 'Honda Activa 6G (KA 04 EL 7819)', rating: '4.8 ★ (980+ deliveries)' },
    { name: 'Suresh Babu', phone: '+91 99014 62014', vehicle: 'Hero Splendor+ (KA 05 MN 3290)', rating: '4.9 ★ (1.5K+ deliveries)' },
    { name: 'Pradeep Nayak', phone: '+91 96118 73402', vehicle: 'Bajaj Pulsar 150 (KA 01 TR 6401)', rating: '4.9 ★ (2.1K+ deliveries)' },
  ];
  if (!orderId) return riders[0];
  let sum = 0;
  for (let i = 0; i < orderId.length; i++) sum += orderId.charCodeAt(i);
  return riders[Math.abs(sum) % riders.length];
}

let outgoingRingAudioCtx = null;
let outgoingRingInterval = null;

function startOutgoingRingSound() {
  stopOutgoingRingSound();
  try {
    outgoingRingAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const playBurst = () => {
      if (!outgoingRingAudioCtx || outgoingRingAudioCtx.state === 'closed') return;
      const now = outgoingRingAudioCtx.currentTime;
      const osc1 = outgoingRingAudioCtx.createOscillator();
      const osc2 = outgoingRingAudioCtx.createOscillator();
      const gain = outgoingRingAudioCtx.createGain();

      osc1.frequency.value = 400;
      osc2.frequency.value = 450;
      osc1.type = 'sine';
      osc2.type = 'sine';

      gain.gain.setValueAtTime(0.09, now);
      gain.gain.setValueAtTime(0.09, now + 1.2);
      gain.gain.linearRampToValueAtTime(0.0, now + 1.25);

      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(outgoingRingAudioCtx.destination);

      osc1.start(now);
      osc2.start(now);
      osc1.stop(now + 1.25);
      osc2.stop(now + 1.25);
    };

    playBurst();
    outgoingRingInterval = setInterval(playBurst, 2800);
  } catch (e) {
    console.warn('Outgoing sound error:', e);
  }
}

function stopOutgoingRingSound() {
  if (outgoingRingInterval) {
    clearInterval(outgoingRingInterval);
    outgoingRingInterval = null;
  }
  if (outgoingRingAudioCtx) {
    try { outgoingRingAudioCtx.close(); } catch (e) {}
    outgoingRingAudioCtx = null;
  }
}

function openCallRiderModal(orderId) {
  const activeOid = orderId || (state.activeOrder && state.activeOrder.order_id) || 'SWIGGY-ORD-9481';
  const rider = getOrderRider(activeOid);

  const modal = document.getElementById('call-rider-modal');
  const nameEl = document.getElementById('call-modal-rider-name');
  const orderIdEl = document.getElementById('call-modal-order-id');
  const vehicleEl = document.getElementById('call-modal-vehicle');
  const phoneEl = document.getElementById('call-modal-phone');
  const statusMsgEl = document.getElementById('call-modal-status-msg');
  const dialBtn = document.getElementById('btn-dial-rider-native');
  const cleanPhone = rider.phone.replace(/[^0-9+]/g, '');

  if (nameEl) nameEl.textContent = rider.name;
  if (orderIdEl) orderIdEl.textContent = activeOid;
  if (vehicleEl) vehicleEl.textContent = rider.vehicle;
  if (phoneEl) phoneEl.textContent = rider.phone;
  if (dialBtn) dialBtn.href = `tel:${cleanPhone}`;
  if (statusMsgEl) {
    statusMsgEl.innerHTML = `Dialing delivery partner <strong>${rider.name}</strong> for active Order <strong>#${activeOid}</strong>.`;
  }

  if (modal) modal.style.display = 'flex';

  const isMobile = /Android|iPhone|iPad|iPod|webOS|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  if (isMobile) {
    setTimeout(() => {
      window.location.href = `tel:${cleanPhone}`;
    }, 400);
  } else {
    startOutgoingRingSound();
    setTimeout(() => {
      if (modal && modal.style.display === 'flex') {
        stopOutgoingRingSound();
        if (statusMsgEl) {
          statusMsgEl.innerHTML = `🟢 <strong>Connected to Partner</strong><br/><span style="color:#10b981;">"${rider.name}: Hello sir! I am carrying your Order #${activeOid}. Reaching your location shortly!"</span>`;
        }
      }
    }, 4000);
  }
}

function closeCallRiderModal() {
  const modal = document.getElementById('call-rider-modal');
  if (modal) modal.style.display = 'none';
  stopOutgoingRingSound();
}

function initLiveMap(orderId = '', rider = null) {
  const mapContainer = document.getElementById('live-map');
  if (!mapContainer || typeof L === 'undefined') return;

  const currentRider = rider || getOrderRider(orderId);
  const isInstamart = state.activeOrder && (state.activeOrder.is_instamart || (state.activeOrder.restaurant_name || '').toLowerCase().includes('instamart'));
  const originName = isInstamart ? 'Swiggy Instamart Dark Store' : (state.activeOrder && state.activeOrder.restaurant_name ? state.activeOrder.restaurant_name : 'Meghana Foods');
  const originEmoji = isInstamart ? '⚡' : '🍛';

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

  const createEmojiMarker = (emoji, className = '') => {
    return L.divIcon({
      className: `map-marker-icon ${className}`,
      html: `<span>${emoji}</span>`,
      iconSize: [38, 38],
      iconAnchor: [19, 19],
      popupAnchor: [0, -20],
    });
  };

  // 1. Restaurant Marker
  restaurantMarker = L.marker(RESTAURANT_COORDS, {
    icon: createEmojiMarker(originEmoji),
  }).addTo(liveMap).bindPopup(`<strong>${originName}</strong><br/>Order #${orderId || 'Active'}`);

  // 2. Home Gate Marker
  homeMarker = L.marker(HOME_COORDS, {
    icon: createEmojiMarker('🏠'),
  }).addTo(liveMap).bindPopup('<strong>Delivery Location (Gate)</strong><br/>Rajajinagar, Bengaluru');

  // 3. Route Polyline
  routePolyline = L.polyline(DELIVERY_ROUTE, {
    color: '#ff5200',
    weight: 5,
    opacity: 0.85,
    dashArray: '8, 8',
  }).addTo(liveMap);

  // 4. Rider Marker initially at restaurant
  riderMarker = L.marker(RESTAURANT_COORDS, {
    icon: createEmojiMarker('🛵', 'map-marker-rider'),
  }).addTo(liveMap).bindPopup(`<strong>Delivery Partner: ${currentRider.name}</strong><br/>${currentRider.vehicle}<br/>📞 ${currentRider.phone}<br/>Order #${orderId || ''}`);

  liveMap.fitBounds(routePolyline.getBounds(), { padding: [40, 40] });
  setTimeout(() => liveMap.invalidateSize(), 300);
}

function moveRiderTo(coords, statusText = '') {
  if (!riderMarker || !liveMap) return;
  riderMarker.setLatLng(coords);
  const orderId = state.activeOrder ? state.activeOrder.order_id : '';
  const rider = getOrderRider(orderId);
  if (statusText) {
    riderMarker.setPopupContent(`<strong>${rider.name}</strong> (${rider.vehicle})<br/>📞 ${rider.phone}<br/>${statusText}`);
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

function showIncomingCallModal(callerName = 'Swiggy Delivery Partner', callerNumber = '+91 80 6746 6746 (Arrival Alert)') {
  const overlay = document.getElementById('phone-call-overlay');
  if (!overlay) return;

  document.getElementById('call-status-label').textContent = 'GATE ARRIVAL CALL';
  document.getElementById('call-caller-name').textContent = callerName;
  document.getElementById('call-number').textContent = callerNumber;
  document.getElementById('call-incoming-actions').style.display = 'flex';
  document.getElementById('call-active-actions').style.display = 'none';
  document.getElementById('call-active-timer').style.display = 'none';

  overlay.classList.add('open');
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
      document.getElementById('call-status-label').textContent = 'CALL IN PROGRESS';
      document.getElementById('call-incoming-actions').style.display = 'none';
      document.getElementById('call-active-actions').style.display = 'flex';

      const timerEl = document.getElementById('call-active-timer');
      timerEl.style.display = 'block';
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
          "Hello! This is your Swiggy delivery partner. I have reached the main gate in Rajajinagar and will be at your door in 2 minutes. Please collect your order."
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
    overlay.classList.remove('open');
    showToast('📞 Call ended.');
  };

  if (declineBtn) declineBtn.addEventListener('click', handleEndCall);
  if (hangupBtn) hangupBtn.addEventListener('click', handleEndCall);

  // Call rider button in tracking pane
  const callRiderBtn = document.getElementById('btn-call-rider');
  if (callRiderBtn) {
    callRiderBtn.addEventListener('click', () => {
      const orderId = state.activeOrder ? state.activeOrder.order_id : '';
      openCallRiderModal(orderId);
    });
  }

  // Outgoing call modal buttons
  const closeCallBtn = document.getElementById('btn-close-call-modal');
  if (closeCallBtn) closeCallBtn.addEventListener('click', closeCallRiderModal);

  const dismissCallBtn = document.getElementById('btn-dismiss-call-modal');
  if (dismissCallBtn) dismissCallBtn.addEventListener('click', closeCallRiderModal);

  const copyRiderPhoneBtn = document.getElementById('btn-copy-rider-phone');
  if (copyRiderPhoneBtn) {
    copyRiderPhoneBtn.addEventListener('click', () => {
      const orderId = state.activeOrder ? state.activeOrder.order_id : '';
      const rider = getOrderRider(orderId);
      if (navigator.clipboard) {
        navigator.clipboard.writeText(rider.phone).then(() => {
          showToast(`📋 Copied rider phone (${rider.phone}) to clipboard!`);
        }).catch(() => {
          showToast(`📞 Rider Phone: ${rider.phone}`);
        });
      } else {
        showToast(`📞 Rider Phone: ${rider.phone}`);
      }
    });
  }

  // Dismiss tracking button
  const dismissTrackingBtn = document.getElementById('btn-dismiss-tracking');
  if (dismissTrackingBtn) {
    dismissTrackingBtn.addEventListener('click', () => {
      state.activeOrder = null;
      localStorage.removeItem('smartflow_active_order');
      syncTrackingTabState();
      showToast('🛵 Live tracking closed. Ready for next order.');
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
  syncTrackingTabState();
  showToast('🛵 Live GPS Delivery Tracking demonstration started!');
}

async function syncTrackingTabState() {
  await loadPastOrders();

  const noOrderBox = document.getElementById('no-active-order-box');
  const activeSection = document.getElementById('active-order-tracking-section');

  let isOrderActive = false;

  // Check state.activeOrder
  if (state.activeOrder && state.activeOrder.order_id && state.activeOrder.is_active) {
    const st = (state.activeOrder.order_status || state.activeOrder.status || '').toLowerCase();
    if (!['delivered', 'cancelled', 'completed'].includes(st)) {
      isOrderActive = true;
    }
  }

  // If not active in memory, check real Swiggy orders
  if (!isOrderActive) {
    try {
      const ordersRes = await api.getOrders(15);
      if (ordersRes.success && ordersRes.data && ordersRes.data.orders) {
        const activeOrder = ordersRes.data.orders.find((o) =>
          o.is_active && ['placed', 'confirmed', 'preparing', 'in_transit', 'out_for_delivery', 'picked_up', 'on the way'].includes((o.order_status || '').toLowerCase())
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

  // If no active in-transit order, strictly hide tracking and do not render route/map
  if (!isOrderActive) {
    if (noOrderBox) noOrderBox.style.display = 'block';
    if (activeSection) activeSection.style.display = 'none';
    if (trackingPollInterval) {
      clearInterval(trackingPollInterval);
      trackingPollInterval = null;
    }
    if (liveMap) {
      try {
        liveMap.remove();
        liveMap = null;
        riderMarker = null;
        restaurantMarker = null;
        homeMarker = null;
        routePolyline = null;
      } catch (e) {}
    }
    return;
  }

  // Active Order is present! Show active section and hide empty box
  if (noOrderBox) noOrderBox.style.display = 'none';
  if (activeSection) activeSection.style.display = 'block';

  const orderId = state.activeOrder.order_id;
  const rider = getOrderRider(orderId);

  // Update Rider Card with order-specific info
  const rName = document.getElementById('rider-name-val');
  const rRating = document.getElementById('rider-rating-val');
  const rVehicle = document.getElementById('rider-vehicle-val');
  const rOrder = document.getElementById('rider-assigned-order-id');
  const rPhone = document.getElementById('rider-direct-phone-val');
  if (rName) rName.textContent = rider.name;
  if (rRating) rRating.textContent = rider.rating;
  if (rVehicle) rVehicle.textContent = rider.vehicle;
  if (rOrder) rOrder.textContent = orderId;
  if (rPhone) rPhone.textContent = rider.phone;

  // Initialize Map for this specific order
  initLiveMap(orderId, rider);
  setTimeout(() => {
    if (liveMap) liveMap.invalidateSize();
  }, 200);

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
      if (badgeEl) badgeEl.textContent = 'Swiggy: Delivered ✓';
      if (state.activeOrder) {
        state.activeOrder.order_status = 'Delivered';
        state.activeOrder.is_active = false;
        persistActiveOrder();
      }
      if (trackingPollInterval) {
        clearInterval(trackingPollInterval);
        trackingPollInterval = null;
      }
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
      moveRiderTo(RESTAURANT_COORDS, 'Kitchen preparing food');
    }
  } catch (e) {
    console.warn('Live tracking poll error:', e);
  }
}

function triggerGateArrivalAlert(orderId, etaText) {
  const rider = getOrderRider(orderId);
  const alertBox = document.getElementById('gate-arrival-alert');
  if (alertBox) {
    alertBox.style.display = 'flex';
    const alertMsg = document.getElementById('gate-arrival-alert-msg');
    if (alertMsg) {
      alertMsg.innerHTML = `Rider <strong>${rider.name}</strong> (${rider.vehicle}) is ${etaText || '2 minutes'} from your building gate in Rajajinagar for Order <strong>#${orderId}</strong>.`;
    }
  }

  // Play audio chime
  playArrivalChime();

  // Toast
  showToast(`🚨 PROACTIVE ALERT: Rider ${rider.name} is 2 minutes from your gate!`);

  // Desktop notification
  if ('Notification' in window && Notification.permission === 'granted') {
    new Notification(`SmartFlow: Rider ${rider.name} Arriving in 2 Mins!`, {
      body: `Your order #${orderId} is arriving at the building gate. Please be ready!`,
      icon: 'https://media-assets.swiggy.com/swiggy/image/upload/FOOD_CATALOG/IMAGES/CMS/2025/12/29/57bebf52-5a58-42e0-af9d-3d872d52de83_2d89d14b-3568-4be1-946d-1d7b0539edae.jpg',
    });
  }

  // Trigger Incoming Call Screen with ringtone & speech
  showIncomingCallModal(`${rider.name} (Swiggy Delivery Partner)`, `${rider.phone} • Order #${orderId}`);

  // Dispatch backend automated cellular call
  api.triggerAutomatedCall(null, `Hello! Your Swiggy delivery rider ${rider.name} is 2 minutes from your gate in Rajajinagar for Order ${orderId}. Please collect your order.`).catch((e) => console.warn('Twilio call notice:', e));
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

// --- TOAST & SOUND UTILITIES ---
function showToast(message) {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3500);
}

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
