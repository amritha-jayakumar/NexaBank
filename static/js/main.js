/* ═══════════════════════════════════════════════════════════
   NexaBank — main.js
   Handles: password toggle, strength meter, transfer preview,
            balance hide/show, filter, flash auto-dismiss
   ═══════════════════════════════════════════════════════════ */

/* ── 1. Password eye toggle ──────────────────────────────────── */
function toggleEye(fieldId, btn) {
  const f = document.getElementById(fieldId);
  if (!f) return;
  const isHidden = f.type === 'password';
  f.type = isHidden ? 'text' : 'password';
  btn.style.color = isHidden ? 'var(--blue)' : '';
}

/* ── 2. Password strength meter (signup) ─────────────────────── */
(function () {
  const pwd    = document.getElementById('sp1');
  const fill   = document.getElementById('sfill');
  const label  = document.getElementById('stext');
  if (!pwd || !fill || !label) return;

  const levels = [
    { w: '15%', c: '#e53935', t: 'Too weak'    },
    { w: '35%', c: '#fb8c00', t: 'Weak'        },
    { w: '58%', c: '#fdd835', t: 'Fair'        },
    { w: '80%', c: '#43a047', t: 'Strong'      },
    { w: '100%',c: '#1e8449', t: 'Very Strong' },
  ];

  function score(v) {
    let s = 0;
    if (v.length >= 8)           s++;
    if (v.length >= 12)          s++;
    if (/[A-Z]/.test(v))         s++;
    if (/[0-9]/.test(v))         s++;
    if (/[^A-Za-z0-9]/.test(v))  s++;
    return Math.min(s, 4);
  }

  pwd.addEventListener('input', function () {
    if (!this.value) { fill.style.width = '0'; label.textContent = ''; return; }
    const l = levels[score(this.value)];
    fill.style.width      = l.w;
    fill.style.background = l.c;
    label.textContent     = l.t;
    label.style.color     = l.c;
  });
})();

/* ── 3. Balance show / hide ──────────────────────────────────── */
let balanceVisible = true;
let realBalance = '';

function toggleBalance() {
  const el = document.getElementById('balance-val');
  if (!el) return;
  if (balanceVisible) {
    realBalance = el.textContent;
    el.textContent = '••••••';
    balanceVisible = false;
  } else {
    el.textContent = realBalance;
    balanceVisible = true;
  }
}

/* ── 4. Transfer page — type tabs ────────────────────────────── */
function setType(type, btn) {
  document.querySelectorAll('.ttype-tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('txnTypeInput').value = type;

  const accLabel = document.getElementById('acc-label');
  const accField = document.getElementById('accField');
  const ifscField = document.getElementById('ifscField');
  if (!accField) return;

  if (type === 'upi') {
    accLabel.textContent = 'UPI ID';
    accField.placeholder = 'e.g. name@upi or 9876543210@paytm';
    if (ifscField) ifscField.closest('.form-field').style.display = 'none';
  } else {
    accLabel.textContent = 'Account Number';
    accField.placeholder = 'Enter 12-digit account number';
    if (ifscField) ifscField.closest('.form-field').style.display = '';
  }

  const tp = document.getElementById('tp-type');
  if (tp) tp.textContent = type.toUpperCase();
  updatePreview(document.getElementById('amountField')?.value || 0);
}

/* ── 5. Transfer preview ─────────────────────────────────────── */
function updatePreview(val) {
  const preview = document.getElementById('txPreview');
  const tpAmt   = document.getElementById('tp-amt');
  const tpBal   = document.getElementById('tp-bal');
  const balText = document.getElementById('balance-display')?.textContent || '';

  if (!preview || !tpAmt) return;

  const amount = parseFloat(val);
  if (isNaN(amount) || amount <= 0) {
    preview.style.display = 'none';
    return;
  }

  preview.style.display = 'block';
  tpAmt.textContent = '₹' + amount.toLocaleString('en-IN', { minimumFractionDigits: 2 });

  // Extract current balance from page
  const balMatch = balText.match(/[\d,]+\.\d{2}/);
  if (balMatch && tpBal) {
    const currentBal = parseFloat(balMatch[0].replace(/,/g, ''));
    const afterBal   = currentBal - amount;
    tpBal.textContent = '₹' + afterBal.toLocaleString('en-IN', { minimumFractionDigits: 2 });
    tpBal.style.color = afterBal < 0 ? '#c0392b' : '#1e8449';
  }
}

/* ── 6. Transfer confirm dialog ──────────────────────────────── */
function confirmTransfer() {
  const amount = document.getElementById('amountField')?.value;
  const bene   = document.querySelector('[name="beneficiary"]')?.value;
  if (!amount || !bene) return true; // Let server-side handle empty
  return confirm(`Confirm transfer of ₹${parseFloat(amount).toLocaleString('en-IN')} to ${bene}?`);
}

/* ── 7. Transaction filter (history page) ────────────────────── */
function filterTxns() {
  const val  = document.getElementById('dirFilter')?.value;
  const rows = document.querySelectorAll('.txn-tr');
  rows.forEach(row => {
    if (!val || row.classList.contains(val)) {
      row.style.display = '';
    } else {
      row.style.display = 'none';
    }
  });
}

/* ── 8. Auto-dismiss flash messages ─────────────────────────── */
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.flash').forEach(function (f) {
    setTimeout(function () {
      f.style.transition = 'opacity .5s, transform .5s';
      f.style.opacity    = '0';
      f.style.transform  = 'translateX(20px)';
      setTimeout(() => f.remove(), 500);
    }, 4500);
  });
});


/* ── OTP: Auto-move between boxes ───────────────────────────── */
function otpMove(current, nextId) {
  const val = current.value.replace(/[^0-9]/g,'');
  current.value = val;
  if (val) {
    current.classList.add('filled');
    if (nextId) {
      const next = document.getElementById(nextId);
      if (next) next.focus();
    }
  } else {
    current.classList.remove('filled');
  }
}

function otpBack(event, current, prevId) {
  if (event.key === 'Backspace' && !current.value && prevId) {
    const prev = document.getElementById(prevId);
    if (prev) { prev.value = ''; prev.focus(); prev.classList.remove('filled'); }
  }
}

/* Collect 6 boxes → hidden input before submit */
function collectOtp() {
  const boxes = ['o1','o2','o3','o4','o5','o6'];
  const otp = boxes.map(id => document.getElementById(id)?.value || '').join('');
  const hidden = document.getElementById('otpHidden');
  if (hidden) hidden.value = otp;
  if (otp.length !== 6) {
    alert('Please enter the complete 6-digit OTP.');
    return false;
  }
  return true;
}

/* ── OTP: 5-minute countdown timer ──────────────────────────── */
(function () {
  const timerEl = document.getElementById('timerCount');
  if (!timerEl) return;

  let seconds = 300; // 5 minutes

  const interval = setInterval(function () {
    seconds--;
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    timerEl.textContent = m + ':' + s;

    if (seconds <= 60) timerEl.style.color = '#fb8c00';
    if (seconds <= 0) {
      timerEl.textContent = 'Expired';
      timerEl.classList.add('expired');
      clearInterval(interval);
      document.getElementById('timerText').textContent = 'OTP has ';
      // Disable verify button
      const btn = document.querySelector('#otpForm button[type="submit"]');
      if (btn) { btn.disabled = true; btn.style.opacity = '.5'; btn.style.cursor = 'not-allowed'; }
    }
  }, 1000);
})();

/* Auto-focus first OTP box on page load */
document.addEventListener('DOMContentLoaded', function () {
  const first = document.getElementById('o1');
  if (first) setTimeout(() => first.focus(), 300);
});
