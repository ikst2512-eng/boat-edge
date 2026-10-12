'use strict';
(function () {
  const dayJst = value => new Date(new Date(value).getTime() + 9 * 3600000)
    .toISOString().slice(0, 10).replace(/-/g, '');
  const count = value => Number.isInteger(value) && value >= 0;
  function view(data, now = new Date()) {
    if (data.schema !== 'BOAT_EDGE_V237_SITE_SELF_DRIVE_HEALTH_V1' ||
        data.formal_guard_closed !== true || data.formal_results_read_by_v237 !== false ||
        data.production_model_changed !== false || data.model_promotion_authorized !== false ||
        data.accuracy_improvement_proven !== false) throw Error('監査の整合性を確認できません');
    const sameDay = data.day_jst === dayJst(now);
    const source = data.current_reference;
    const wallet = data.simulator;
    if (!source || !wallet || wallet.virtual_only !== true || wallet.daily_budget_yen !== 50000)
      throw Error('仮想運用の設定を確認できません');
    const currentWallet = sameDay && wallet.current_day_verified === true &&
      wallet.source_day_jst === dayJst(now);
    if (currentWallet && (!count(wallet.today_spent_yen) || wallet.today_spent_yen > 50000 ||
        wallet.today_remaining_yen !== 50000 - wallet.today_spent_yen))
      throw Error('本日の仮想資金を確認できません');
    const rate = (hits, races) => count(hits) && count(races) && hits <= races && races > 0
      ? `${hits}/${races}（${(hits / races * 100).toFixed(1)}%）` : '採点待ち';
    const band = data.odds_band_at_freeze || {};
    return {sameDay, currentWallet,
      registered: sameDay ? source.registered_today : '更新待ち',
      candidates: sameDay ? data.research_candidates.pre_result_registered_today : '更新待ち',
      spent: currentWallet ? `${wallet.today_spent_yen.toLocaleString('ja-JP')}円` : '本日分の更新待ち',
      remaining: currentWallet ? `${wallet.today_remaining_yen.toLocaleString('ja-JP')}円` : '—',
      metrics: [['先頭買い目の頭', rate(source.head_hits, source.settled_total)],
        ['Top3', rate(source.top3_hits, source.settled_total)],
        ['Top5', rate(source.top5_hits, source.settled_total)],
        ['Top10', rate(source.top10_hits, source.settled_total)]],
      band: rate(band.hits, band.eligible_races), rate};
  }
  if (typeof module !== 'undefined') module.exports = {view, dayJst};
  if (typeof document === 'undefined') return;
  const put = (id, value) => {document.getElementById(id).textContent = value ?? '—';};
  const row = (target, cells) => {
    const tr = document.createElement('tr');
    cells.forEach(value => {const td = document.createElement('td'); td.textContent = value; tr.append(td);});
    document.getElementById(target).append(tr);
  };
  // BOAT_EDGE_V242_UI_REFRESH: keep user-initiated saved-data reloads.
  async function refreshHealth() {
    const button = document.getElementById('refreshHealth');
    if (button.disabled) return;
    button.disabled = true;
    document.getElementById('stats').hidden = true;
    document.getElementById('observed').replaceChildren();
    document.getElementById('rates').replaceChildren();
    document.getElementById('message').className = 'muted';
    put('message', '監査ファイルを取得中…');
    try {
      const response = await fetch('./data/site_autopilot/v237_current.json?t=' + Date.now(), {cache:'no-store'});
      if (!response.ok) throw Error('監査ファイル未公開');
      const data = await response.json(), display = view(data);
      put('registered', display.registered); put('comparators', display.candidates);
      put('settled', data.current_reference.settled_total); put('paired', data.research_candidates.scored_total);
      display.metrics.forEach(values => row('observed', values));
      put('band', display.band); put('spent', display.spent); put('remaining', display.remaining);
      const names = {hit10:'現行Top10',balance10:'バランス10点',scenario7plus3:'上位7点＋別展開3点',coverage15:'参考：最大15点'};
      Object.entries(names).forEach(([key, name]) => {
        const value = data.research_candidates.comparisons[key];
        row('rates', [name, display.rate(value.hits, value.races)]);
      });
      put('updated', `監査更新：${data.as_of_jst || '不明'} ／ 表示版：V271`);
      put('message', display.sameDay ? '精度改善の証明：未成立。未見比較を継続中。' : '本日分は更新待ちです。以下の成績は過去の累計です。');
      document.getElementById('stats').hidden = false;
    } catch (error) {
      document.getElementById('message').className = 'danger';
      put('message', '現在の監査を表示できません：' + error.message);
    } finally {
      button.disabled = false;
    }
  }
  document.getElementById('refreshHealth').addEventListener('click', refreshHealth);
  refreshHealth();
})();
