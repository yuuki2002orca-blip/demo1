'use strict';

(function () {
  const form         = document.getElementById('loginForm');
  const employeeId   = document.getElementById('employeeId');
  const password     = document.getElementById('password');
  const submitBtn    = document.getElementById('submitBtn');
  const btnText      = submitBtn.querySelector('.btn-text');
  const btnLoading   = submitBtn.querySelector('.btn-loading');
  const loginError   = document.getElementById('loginError');
  const togglePwd    = document.getElementById('togglePassword');
  const eyeIcon      = document.getElementById('eyeIcon');
  const eyeOffIcon   = document.getElementById('eyeOffIcon');
  const forgotLink   = document.getElementById('forgotPassword');
  const modal        = document.getElementById('forgotModal');
  const modalClose   = document.getElementById('modalClose');
  const modalOverlay = document.getElementById('modalOverlay');

  /* パスワード表示切替 */
  togglePwd.addEventListener('click', function () {
    const isText = password.type === 'text';
    password.type = isText ? 'password' : 'text';
    eyeIcon.style.display    = isText ? 'block' : 'none';
    eyeOffIcon.style.display = isText ? 'none'  : 'block';
    togglePwd.setAttribute('aria-label', isText ? 'パスワードを表示' : 'パスワードを非表示');
  });

  /* バリデーション */
  function validateField(input, errorId, message) {
    const el = document.getElementById(errorId);
    if (!input.value.trim()) {
      input.classList.add('is-error');
      el.textContent = message;
      return false;
    }
    input.classList.remove('is-error');
    el.textContent = '';
    return true;
  }

  function clearError(input, errorId) {
    input.classList.remove('is-error');
    document.getElementById(errorId).textContent = '';
    loginError.style.display = 'none';
  }

  employeeId.addEventListener('input', () => clearError(employeeId, 'employeeIdError'));
  password.addEventListener('input',   () => clearError(password,   'passwordError'));

  /* フォーム送信 */
  form.addEventListener('submit', function (e) {
    e.preventDefault();

    const idOk  = validateField(employeeId, 'employeeIdError', '従業員番号を入力してください。');
    const pwOk  = validateField(password,   'passwordError',   'パスワードを入力してください。');

    if (!idOk || !pwOk) return;

    setLoading(true);

    /* 認証リクエストのシミュレーション（実際はサーバー通信に置き換える） */
    setTimeout(function () {
      setLoading(false);
      /* デモ用：常にエラー表示（本番では認証結果に応じてリダイレクト） */
      loginError.style.display = 'flex';
      document.getElementById('loginErrorMsg').textContent =
        '従業員番号またはパスワードが正しくありません。';
      employeeId.classList.add('is-error');
      password.classList.add('is-error');
      employeeId.focus();
    }, 1200);
  });

  function setLoading(state) {
    submitBtn.disabled    = state;
    btnText.style.display    = state ? 'none'  : 'inline';
    btnLoading.style.display = state ? 'flex'  : 'none';
  }

  /* パスワードリセットモーダル */
  forgotLink.addEventListener('click', function (e) {
    e.preventDefault();
    openModal();
  });

  modalClose.addEventListener('click', closeModal);
  modalOverlay.addEventListener('click', closeModal);

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && modal.classList.contains('is-open')) closeModal();
  });

  function openModal() {
    modal.classList.add('is-open');
    document.body.style.overflow = 'hidden';
    modalClose.focus();
  }

  function closeModal() {
    modal.classList.remove('is-open');
    document.body.style.overflow = '';
    forgotLink.focus();
  }

  /* ログイン状態保持：チェック復元 */
  const rememberMe = document.getElementById('rememberMe');
  const saved = localStorage.getItem('rememberMe') === '1';
  if (saved) {
    rememberMe.checked = true;
    const savedId = localStorage.getItem('savedEmployeeId');
    if (savedId) employeeId.value = savedId;
  }

  rememberMe.addEventListener('change', function () {
    if (!rememberMe.checked) {
      localStorage.removeItem('rememberMe');
      localStorage.removeItem('savedEmployeeId');
    }
  });
}());
